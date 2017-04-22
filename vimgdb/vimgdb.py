from __future__ import absolute_import, division, print_function, unicode_literals
import subprocess

class Vim:

    def __init__(self):
        self.servername = u"VIMGDB"
        self.executable = "vim"
        self.command = []

    def Start(self,check=True):
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
            "-c","source {0}".format(vimrc)]

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

            subprocess.call(cmd)

    def UpdateBreakpoints(self,breakpoints):
        if len(breakpoints) > 0:
            command = ""
            for breakpoint in breakpoints:
                if command != "":
                    command += "\\|"
                command += "\\%{0}l".format(breakpoint)

            command = "3match GdbBreakpoint /{0}/".format(command)
            self.AddCommand(command)
        else:
            self.AddCommand("3match")

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

    def Start(self,check=True):
        import sys
        from os import path

        library_dir = path.abspath(path.dirname(__file__))
        gdbinit = path.join(library_dir, 'config/gdbinit')

        cmd = [self.executable,
            "-iex","source {0}".format(gdbinit)] + sys.argv[1:]
        subprocess.call(cmd)

    def GetValue(self,variable):
        import gdb
        value = str(gdb.parse_and_eval("{0}".format(variable)))
        value = value.replace("\"","")
        value = value.split("\\0")[0]
        return value

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
        match = ' {0}:([0-9]+)'.format(source)
        breaklines = [int(i) for i in re.findall(match, raw_break_info)]
        return breaklines


class Vimgdb:

    def __init__(self):
        self.vim = Vim()
        self.gdb = Gdb()

    def Start(self):
        if not self.vim.IsRunning():
            self.vim.Start()
        else:
            self.gdb.Start()

    def Update(self,force=False):
        fullsource,source,line = self.gdb.GetLocation()
        breakpoints = self.gdb.GetBreakpoints(source)

        self.vim.NewCommand()
        self.vim.GotoFile(fullsource)
        if line in breakpoints:
            breakpoints.remove(line)
            self.vim.UpdateLine(line,IsBreakpoint=True)
        else:
            self.vim.UpdateLine(line,IsBreakpoint=False)
        self.vim.UpdateBreakpoints(breakpoints)
        self.vim.GotoLine(line)

        self.vim.RunCommand()

    def UpdateBreakpoints(self):
        fullsource,source,line = self.gdb.GetLocation()
        breakpoints = self.gdb.GetBreakpoints(source)

        self.vim.NewCommand()
        if line in breakpoints:
            breakpoints.remove(line)
            self.vim.UpdateLine(line,IsBreakpoint=True)
        else:
            self.vim.UpdateLine(line,IsBreakpoint=False)
        self.vim.UpdateBreakpoints(breakpoints)
        self.vim.RunCommand()

    def Synchronize(self):
        try:
            option = self.gdb.GetValue("$_vimgdb_option")
            if option == "breakpoints":
                self.UpdateBreakpoints()
            else:
                self.Update()
        except Exception as error:
            print("Vimgdb Exception: {0}".format(str(error)))


def main():
    vimgdb = Vimgdb()
    vimgdb.Start()

if __name__ == "__main__":
    main()

