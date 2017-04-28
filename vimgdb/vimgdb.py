from __future__ import absolute_import, division, print_function, unicode_literals
import subprocess
import os

class Vim:

    def __init__(self):
        self.servername = u"VIMGDB"
        self.executable = "vim"
        self.command = []

    def Start(self,args=[],check=True):
        from os import path

        if check and self.IsRunning():
            raise RuntimeError("Vim server already running")

        library_dir = path.abspath(path.dirname(__file__))
        vimrc = path.join(library_dir, 'config/vimrc')

        if not path.exists(vimrc):
            raise RuntimeError("Config file '{0}' not found".format(vimrc))

        cmd = [self.executable,
            "--servername","{0}".format(self.servername),
            "-n",
            "-c","source {0}".format(vimrc)] + args

        subprocess.call(cmd)

    def GetServerlist(self):
        output = subprocess.check_output([self.executable, '--serverlist'])
        output.decode('utf-8')
        return output

    def IsRunning(self):
        servers = self.GetServerlist()
        if self.servername in servers:
            return True
        else:
            return False

    def NewCommand(self):
        self.command = []

    def AddCommand(self,command):
        self.command.append(command)

    def RunCommand(self):
        if len(self.command) > 0:
            self.Redraw()
            command = "<Esc>:{0}<Enter>".format(" | ".join(self.command))
            cmd = [ self.executable,
                "--servername",self.servername,
                "--remote-send",command]

            DEVNULL = open(os.devnull, 'w')
            return subprocess.call(cmd,stdout=DEVNULL,stderr=subprocess.STDOUT)

    def RemoveSigns(self,sign_id):
        self.AddCommand("execute \"sign unplace {0}\"".format(sign_id))

    def RemoveSign(self,sign_id):
        self.AddCommand("execute \"sign unplace {0} file=\" . expand(\"%:p\")".format(sign_id))

    def AddSign(self,line,sign_type,sign_id=-1):
        if sign_id < 0:
            sign_id = line
        self.AddCommand("execute \"sign place {0} line={1} name={2} file=\" . expand(\"%:p\")".format(sign_id,line,sign_type))

    def EnableSignColumn(self):
        self.AddSign(1,"VimgdbDummy",999999)

    def DisableSignColumn(self):
        self.AddCommand("execute \"sign unplace * file=\" . expand(\"%:p\")")

    def DisableSignColumns(self):
        self.AddCommand("execute \"sign unplace *\"")

    def InitSignColumn(self):
        self.DisableSignColumn()
        self.EnableSignColumn()

    def RemoveBreakpoints(self,breakpoints):
        for breakline in breakpoints:
            self.RemoveSign(breakline)

    def AddBreakpoints(self,breakpoints):
        for breakline in breakpoints:
            self.AddSign(breakline,"VimgdbBreakpointSign")

    def UpdateBreakpoints(self,add_breakpoints=[],remove_breakpoints=[]):
        self.AddBreakpoints(add_breakpoints)
        self.RemoveBreakpoints(remove_breakpoints)

    def Redraw(self):
        self.command.append("redraw!")

    def GotoLine(self,line):
        if line > 1:
            self.AddCommand("{0}".format(line))

    def UpdateLine(self,line):
        if line > 1:
            sign_id = 999998
            self.RemoveSigns(sign_id)
            self.AddSign(line,"VimgdbLocationSign",sign_id)

    def GotoFile(self,filename,check=False):
        self.AddCommand("edit {0}".format(filename))


class Gdb:

    def __init__(self):
        self.executable = "gdb"
        self.src = "$_vimgdb_src"
        self.breakpoints = "$_vimgdb_breakpoints"
        self.option = "$_vimgdb_option"

    def Start(self,args=[],check=True):
        from os import path

        library_dir = path.abspath(path.dirname(__file__))
        gdbinit = path.join(library_dir, 'config/gdbinit')

        cmd = [self.executable,
            "-iex","source {0}".format(gdbinit)] + args
        subprocess.call(cmd)

    def GetValue(self,variable):
        import gdb
        import re
        value = str(gdb.parse_and_eval("{0}".format(variable)))
        value = re.findall('"(.*)"', value)
        if len(value) > 0:
            return value[0]
        else:
            return ""

    def SetValue(self,variable,value):
        import gdb
        MAX = 250
        if len(value) > MAX:
            raise RuntimeError("Cannot store '{0}' in {1}: value longer than {2} characters".format(value,variable,MAX))
        gdb.execute("set {0} = \"{1}\"".format(variable,value))

    def GetLocation(self):
        import gdb
        try:
            current_line = gdb.decode_line()
            symbol_table_and_line = current_line[1][0]
            symbol_table = symbol_table_and_line.symtab
            fullsource = symbol_table.fullname()
            source = symbol_table.filename
            line = symbol_table_and_line.line
            return fullsource,source,line
        except:
            raise RuntimeError("Current location not detected")

    def GetBreakpoints(self,source):
        import re
        import gdb
        raw_break_info = gdb.execute('info break',to_string=True).split('\n')
        match = '([0-9]+)[ ]*([^ ]+)[ ]*([^ ]+)[ ]*([^ ]+).*{0}:([0-9]+)'.format(source)
        breakpoints = [ re.findall(match,line) for line in raw_break_info ]
        breakpoints = [ breakpoint[0] for breakpoint in breakpoints if breakpoint ]

        breaklines = []
        enabled_breakpoint = {}
        for breakpoint in breakpoints:
            num =  breakpoint[0]
            type = breakpoint[1]
            disp = breakpoint[2]
            enabled = breakpoint[3]
            line = breakpoint[4]
            if type == "breakpoint":
                breakline = int(line)
                breaklines.append(breakline)
                enabled_breakpoint[breakline] = bool(enabled == "y");

        return breaklines,enabled_breakpoint

    def GetStoredBreakpoints(self):
        breakpoints = [int(i) for i in self.GetValue(self.breakpoints).split(':')]
        return breakpoints

    def StoreBreakpoints(self,breakpoints):
        self.SetValue(self.breakpoints,":".join(str(breakline) for breakline in breakpoints))

    def GetStoredFile(self):
        return self.GetValue(self.src)

    def StoreFile(self,filename):
        self.SetValue(self.src,filename)


class Vimgdb:

    def __init__(self):
        self.vim = Vim()
        self.gdb = Gdb()

    def Start(self,args=[]):
        if not self.vim.IsRunning():
            self.vim.Start(args)
        else:
            self.gdb.Start(args)

    def Update(self,force=False):
        # get current location in gdb
        fullsource,source,line = self.gdb.GetLocation()

        # create new series of vim commands
        self.vim.NewCommand()

        # get last known open file in vim
        vim_source = self.gdb.GetStoredFile()
        update_file = force or vim_source != fullsource

        # update file open in vim
        if update_file:
            self.vim.GotoFile(fullsource)

        # update breakpoints
        breakpoints,enabled = self.gdb.GetBreakpoints(source)
        if update_file:
            self.vim.InitSignColumn()
            self.vim.UpdateBreakpoints(breakpoints)
        else:
            stored_breakpoints = self.gdb.GetStoredBreakpoints()
            add_breakpoints = list(set(breakpoints) - set(stored_breakpoints))
            remove_breakpoints = list(set(stored_breakpoints) - set(breakpoints))
            self.vim.UpdateBreakpoints(add_breakpoints,remove_breakpoints)

        # update current location in source
        self.vim.UpdateLine(line)
        self.vim.GotoLine(line)

        # execute commands in vim
        ret = self.vim.RunCommand()

        # store state in gdb
        if ret != 0:
            self.gdb.StoreFile("")
            self.gdb.StoreBreakpoints([])
        elif update_file:
            self.gdb.StoreFile(fullsource)
            self.gdb.StoreBreakpoints(breakpoints)
        else:
            self.gdb.StoreBreakpoints(breakpoints)

        return ret

def main(args):
    vimgdb = Vimgdb()
    vimgdb.Start(args)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])

