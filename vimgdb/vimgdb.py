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

    def UpdateBreakpoints(self,breakpoints):
        if len(breakpoints) > 0:
            command = ""
            for breakpoint in breakpoints:
                if command != "":
                    command += "\\|"
                command += "\\%{0}l".format(breakpoint)

            command = "match GdbBreakpoint /{0}/".format(command)
            self.AddCommand(command)
        else:
            self.AddCommand("match")

    def Redraw(self):
        self.command.append("redraw!")

    def GotoLine(self,line):
        self.AddCommand("{0}".format(line))

    def UpdateLine(self,line,IsBreakpoint=False):
        matchgroup = "GdbLocation"
        if IsBreakpoint:
            matchgroup = "GdbBreakpointAndLocation"

        command = "2match {0} /\\%{1}l/".format(matchgroup,line)
        self.AddCommand(command)

    def GotoFile(self,filename,check=False):
        self.AddCommand("edit {0}".format(filename))

class Gdb:

    def __init__(self):
        self.executable = "gdb"
        self.src = "$_vimgdb_src"
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
        raw_break_info = gdb.execute('info break',to_string=True)
        match = '([0-9]+)[ ]*([^ ]+)[ ]*([^ ]+)[ ]*([^ ]+).*{0}:([0-9]+)'.format(source)
        breakpoints = re.findall(match, raw_break_info)
        breaklines = []
        for breakpoint in breakpoints:
            num =  breakpoint[0]
            type = breakpoint[1]
            disp = breakpoint[2]
            enabled = breakpoint[3]
            line = breakpoint[4]
            if type == "breakpoint" and enabled == "y":
                breaklines.append(int(line))

        return breaklines


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
        fullsource,source,line = self.gdb.GetLocation()

        self.vim.NewCommand()
        vim_source = self.gdb.GetValue(self.gdb.src)

        update_file = force or vim_source != fullsource
        if update_file:
            self.vim.GotoFile(fullsource)

        breakpoints = self.gdb.GetBreakpoints(source)
        if line in breakpoints:
            breakpoints.remove(line)
            self.vim.UpdateLine(line,IsBreakpoint=True)
        else:
            self.vim.UpdateLine(line,IsBreakpoint=False)
        self.vim.UpdateBreakpoints(breakpoints)
        self.vim.GotoLine(line)

        ret = self.vim.RunCommand()
        if ret != 0:
            self.gdb.SetValue(self.gdb.src,"")
        elif update_file:
            self.gdb.SetValue(self.gdb.src,fullsource)

        return ret

def main(args):
    vimgdb = Vimgdb()
    vimgdb.Start(args)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])

