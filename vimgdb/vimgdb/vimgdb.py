from __future__ import absolute_import, division, print_function, unicode_literals
from vimrunner import vimrunner

class Vimgdb:
    __server_name = u"GDB-VIM-TMUX"
    __default_vimrc = None
    __vimrc = None
    __gdbinit = None
    __filename = None
    __server = None
    __vim = None
    __library_dir = None

    def __init__(self):
        import os
        home = os.path.expanduser("~")
        self.__default_vimrc = home + "/.vimrc"
        self.__library_dir = os.path.abspath(os.path.dirname(__file__))
        self.__vimrc = os.path.join(self.__library_dir, 'config/vimrc')
        self.__gdbinit = os.path.join(self.__library_dir, 'config/gdbinit')

    def Exists(self,filename):
        import os
        return os.path.exists(filename)

    def IsConnected(self):
        try:
            return self.__vim != None and self.__server.is_running()
        except:
            return False

    def IsRunning(self):
        try:
            servers = vimrunner.Server().server_list()
            servers.index(self.__server_name)
            return True
        except:
            return False

    def IsDiffentFile(self,filename):
        return filename != self.__filename

    def Connect(self):
        if not self.IsRunning():
            raise RuntimeError("Server is not running")

        servers = vimrunner.Server().server_list()
        index = servers.index(self.__server_name)
        self.__server = vimrunner.Server(servers[index])
        self.__vim = self.__server.connect(timeout=1)

    def GotoLine(self,line):
        cmd_highlight = "3match GdbLocation /\\%{0}l/".format(line)
        self.__vim.command(cmd_highlight)
        self.__vim.command("{0}".format(line))

    def GotoFile(self,filename):
        if self.Exists(filename):
            self.__filename = filename
            self.__vim.edit(filename)
        else:
            raise RuntimeError("Source file '{0}' not found".format(filename))

    def GotoLocation(self,filename,line):
        self.GotoFile(filename)
        self.GotoLine(line)

    def Redraw(self):
        self.__vim.command("redraw")

    def Escape(self):
        self.__vim.type("\<Esc>")

    def SetVimrc(self, vimrc):
        self.__default__vimrc = vimrc

    def LoadConfig(self):
        if self.Exists(self.__default_vimrc):
            self.__vim.source(self.__default_vimrc)

        if self.Exists(self.__vimrc):
            self.__vim.source(self.__vimrc)
        else:
            raise RuntimeError("Config file '{0}' not found".format(self.__vimrc))

    def StartGdb(self):
        from subprocess import call
        import sys
        arguments = " ".join(sys.argv[1:])
        cmd = "gdb -iex 'source {0}' {1}".format(self.__gdbinit,arguments)
        call(cmd, shell=True)

    def StartVim(self):
        self.__server = vimrunner.Server(self.__server_name)
        if not self.IsRunning():
            self.__vim = self.__server.start()
            self.LoadConfig()
        else:
            raise RuntimeError("Vim is already running")

    def Start(self):
        if not self.IsRunning():
            self.StartVim()
        else:
            self.StartGdb()

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
        breaklines = re.findall(match, raw_break_info)
        return breaklines

    def __UpdateBreakpoints(self,breakpoints):
        if len(breakpoints) > 0:
            cmd_breakpoint = ""
            for breakpoint in breakpoints:
                if cmd_breakpoint != "":
                    cmd_breakpoint += "\\|"
                cmd_breakpoint += "\\%{0}l".format(breakpoint)

            cmd_highlight = "2match GdbBreakpoint /{0}/".format(cmd_breakpoint)
            self.__vim.command(cmd_highlight)
        else:
            self.__vim.command("2match")

    def __Update(self,fullsource,source,line,force=False):
        if self.IsDiffentFile(fullsource) or force:
            import pdb; pdb.set_trace()
            self.GotoFile(fullsource)
            self.__UpdateBreakpoints(source)

        self.GotoLine(line)

    def Update(self,force=False):
        try:
            fullsource,source,line = self.GetLocation()
            self.__Update(fullsource,source,line,force)
            self.Redraw()
        except Exception as err:
            raise RuntimeError("No connection to vim: {0}".format(str(err)))

    def UpdateBreakpoints(self):
        try:
            fullsource,source,line = self.GetLocation()
            breakpoints = self.GetBreakpoints(source)
            self.__UpdateBreakpoints(breakpoints)
            self.Redraw()
        except Exception as err:
            raise RuntimeError("No connection to vim: {0}".format(str(err)))

    def Communicate(self):
        try:
            if self.IsRunning():
                self.Connect()
                option = self.GetValue("$_vimgdb_option")
                if option == "breakpoints":
                    self.UpdateBreakpoints()
                else:
                    self.Update()
        except Exception as error:
            print("Vimgdb Exception: {0}".format(str(error)))

