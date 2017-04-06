from vimrunner import vimrunner
import sys

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

    def GoToLine(self,kLineNumber):
        self.CheckConnection()

        cmd_gotoline      = ":{:d}\<Enter>".format(kLineNumber)
        cmd_highlightline = "/\\%{:d}l/\<Enter>".format(kLineNumber)

        self.vim.type(cmd_gotoline);
        self.vim.type(cmd_highlightline);
        self.vim.type("z.");
        self.vim.command("set cursorline")
        self.vim.command("set cursorline")

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
            index = servers.index(self._server_name)
            return True
        except:
            return False

    def Test(self):
        try:
            import time

            self.vim = self.server.connect(timeout=1)
            self.Escape()

            self.vim.edit("/home/gdal/.vimrc")
            self.vim.command("redraw")

            self.GoToLine(2)
            time.sleep(1)
            self.GoToLine(3)
            time.sleep(1)
            self.GoToLine(10)

        except RuntimeError as err:
            print("{0}".format(err))
            exit(1)
        except:
            print("Could not connect to vim session.")
            #print("Unexpected error:", sys.exc_info()[0])
            exit(1)

