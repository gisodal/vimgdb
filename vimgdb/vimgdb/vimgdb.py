from __future__ import absolute_import, division, print_function, unicode_literals
from vimrunner import vimrunner

class Vimgdb:
    _server_name = u"GDB-VIM-TMUX"
    _vimgdb_environment_variable = "VIMGDB_LIBRARY_PATH"
    _default_vimrc = ""
    _vimrc = ""

    def __init__(self):
        import os
        home = os.path.expanduser("~")
        self._default_vimrc = home + "/.vimrc"
        if not os.path.exists(self._default_vimrc):
            self._default_vimrc = ""

        self._library_dir = os.path.abspath(os.path.dirname(__file__))
        self._vimrc = os.path.join(self._library_dir, 'config/vimrc')

    def Start(self):
        self.server = vimrunner.Server(self._server_name)
        if not self.IsRunning():
            self.vim = self.server.start()
            self.LoadConfig()
        else:
            raise RuntimeError("Vim is already running")

    def Connect(self):
        if not self.IsRunning():
            raise RuntimeError("Server is not running")

        servers = vimrunner.Server().server_list()
        index = servers.index(self._server_name)
        self.server = vimrunner.Server(servers[index])
        self.vim = self.server.connect(timeout=1)

    def CheckConnection(self):
        if not self.server.is_running():
            raise RuntimeError("No connection to vim session")

    def GotoLine(self,line):
        self.CheckConnection()
        cmd_gotoline      = ":{0}\<Enter>".format(line)
        cmd_highlightline = "/\\%{0}l/\<Enter>".format(line)
        self.vim.type(cmd_gotoline)
        self.vim.type(cmd_highlightline)
        self.vim.type("z.")
        self.vim.command("set cursorline")
        self.vim.command("set cursorline")

    def GotoFile(self,filename):
        self.CheckConnection()

        self.vim.edit(filename)
        self.vim.command("redraw")

    def Escape(self):
        self.CheckConnection()
        self.vim.type("\<Esc>")

    def SetVimrc(self, vimrc):
        self._default_vimrc = vimrc

    def LoadConfig(self):
        self.CheckConnection();

        from os.path import exists
        if not self._default_vimrc == "":
            self.vim.source(self._default_vimrc)

        if exists(self._vimrc):
            self.vim.source(self._vimrc)
        else:
            raise RuntimeError("Config file '{0}' not found".format(self._vimrc))

    def IsRunning(self):
        servers = vimrunner.Server().server_list()
        try:
            servers.index(self._server_name)
            return True
        except:
            return False

    def Test(self):
        try:
            import time
            self.Escape()
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

