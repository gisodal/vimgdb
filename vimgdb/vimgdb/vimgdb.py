from __future__ import absolute_import, division, print_function, unicode_literals
from vimrunner import vimrunner

class Vimgdb:
    _server_name = u"GDB-VIM-TMUX"
    _default_vimrc = None
    _vimrc = None
    _gdbinit = None
    _filename = None
    _server = None
    _vim = None
    _library_dir = None

    def __init__(self):
        import os
        home = os.path.expanduser("~")
        self._default_vimrc = home + "/.vimrc"
        self._library_dir = os.path.abspath(os.path.dirname(__file__))
        self._vimrc = os.path.join(self._library_dir, 'config/vimrc')
        self._gdbinit = os.path.join(self._library_dir, 'config/gdbinit')

    def Exists(self,filename):
        import os
        return os.path.exists(filename)

    def IsConnected(self):
        try:
            return self._vim != None and self._server.is_running()
        except:
            return False

    def IsRunning(self):
        try:
            servers = vimrunner.Server().server_list()
            servers.index(self._server_name)
            return True
        except:
            return False

    def VerifyConnection(self):
        if not self.IsConnected():
            raise RuntimeError("No connection to vim session")

    def IsDiffentFile(self,filename):
        return filename != self._filename

    def Connect(self):
        if not self.IsRunning():
            raise RuntimeError("Server is not running")

        servers = vimrunner.Server().server_list()
        index = servers.index(self._server_name)
        self._server = vimrunner.Server(servers[index])
        self._vim = self._server.connect(timeout=1)

    def ShowBreakpoints(self, breakpoints):
        cmd_breakpoint = ""
        for breakpoint in breakpoints:
            if cmd_breakpoint != "":
                cmd_breakpoint += "\\|"
            cmd_breakpoint += "\\%{0}l".format(breakpoint)

        cmd_highlight = "match GdbBreakpoint /{0}/".format(cmd_breakpoint)
        value = self._vim.command(cmd_highlight)

    def GotoLine(self,line):
        self._vim.command("set cursorline")
        self._vim.command("{0}".format(line))
        #cmd_highlight = "match GdbLocation /\\%{0}l/".format(line)
        #value = self._vim.command(cmd_highlight)
        #self._vim.command("{0}".format(line))

    def GotoFile(self,filename):
        if filename != self._filename:
            if self.Exists(filename):
                self._filename = filename
                self._vim.edit(filename)
            else:
                raise RuntimeError("Source file '{0}' not found".format(filename))

    def Redraw(self):
        self._vim.command("redraw")

    def Escape(self):
        self._vim.type("\<Esc>")

    def GotoLocation(self,filename,line):
        self.VerifyConnection()
        self.GotoFile(filename)
        self.GotoLine(line)

    def SetVimrc(self, vimrc):
        self._default_vimrc = vimrc

    def LoadConfig(self):
        self.VerifyConnection();

        if self.Exists(self._default_vimrc):
            self._vim.source(self._default_vimrc)

        if self.Exists(self._vimrc):
            self._vim.source(self._vimrc)
        else:
            raise RuntimeError("Config file '{0}' not found".format(self._vimrc))

    def StartGdb(self):
        from subprocess import call
        import sys
        arguments = " ".join(sys.argv[1:])
        cmd = "gdb -iex 'source {0}' {1}".format(self._gdbinit,arguments)
        call(cmd, shell=True)

    def StartVim(self):
        self._server = vimrunner.Server(self._server_name)
        if not self.IsRunning():
            self._vim = self._server.start()
            self.LoadConfig()
        else:
            raise RuntimeError("Vim is already running")

    def Start(self):
        if not self.IsRunning():
            self.StartVim()
        else:
            self.StartGdb()

    def Test(self):
        try:
            import time
            self.GotoFile("/home/gdal/.vimrc")
            self.GotoLine(2)
            time.sleep(1)
            self.GotoLine(3)
            time.sleep(1)
            self.GotoLine(10)

        except RuntimeError as e:
            print("{0}".format(e))
            raise Exception(str(e))
        except Exception as e:
            print("Could not connect to vim session.")
            #print("Unexpected error:", sys.exc_info()[0])
            raise Exception(str(e))

if __name__ == "__main__":
    vimgdb = Vimgdb()
    vimgdb.Start()

