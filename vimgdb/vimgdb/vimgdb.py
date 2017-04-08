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

    def Connect(self):
        if not self.IsRunning():
            raise RuntimeError("Server is not running")

        servers = vimrunner.Server().server_list()
        index = servers.index(self._server_name)
        self._server = vimrunner.Server(servers[index])
        self._vim = self._server.connect(timeout=1)

    def _GotoLine(self,line):
        cmd_highlightline = "/\\%{0}l/\<Enter>".format(line)
        self._vim.type(cmd_highlightline)
        #cmd_gotoline = ":{0}\<Enter>".format(line)
        #self._vim.type(cmd_gotoline)
        #self._vim.type("z.")
        self._vim.command("set cursorline")
        self._vim.command("set cursorline")

    def _GotoFile(self,filename,redraw=True):
        if filename != self._filename:
            if self.Exists(filename):
                self._filename = filename
                self._vim.edit(filename)
                if redraw:
                    self._vim.command("redraw")
            else:
                raise RuntimeError("Source file '{0}' not found".format(filename))

    def _Escape(self):
        self._vim.type("\<Esc>")

    def GotoLocation(self,filename,line):
        self.VerifyConnection()
        self._Escape()
        self._GotoFile(filename,redraw=False)
        self._GotoLine(line)

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
        cmd = "gdb -n -iex 'source {0}'".format(self._gdbinit)
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
            self._Escape()
            self._GotoFile("/home/gdal/.vimrc")
            self._GotoLine(2)
            time.sleep(1)
            self._GotoLine(3)
            time.sleep(1)
            self._GotoLine(10)

        except RuntimeError as e:
            print("{0}".format(e))
            raise Exception(str(e))
        except Exception as e:
            print("Could not connect to vim session.")
            #print("Unexpected error:", sys.exc_info()[0])
            raise Exception(str(e))

