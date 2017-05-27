from .viminterface import Vim
from .gdbinterface import Gdb
from .vimgdbexception import VimgdbError
from .settings import settings
from .version import Version

class Vimgdb:

    def __init__(self):
        self.vim = Vim()
        self.gdb = Gdb()

    def Version(self):
        """Return current vimgdb version."""
        return Version()

    def StartVim(self,args=[]):
        """Start vim as a server, if it is not already started."""
        if not self.vim.IsRunning():
            self.vim.Start(args)
        else:
            raise VimgdbError("Vim server already started.")

    def StartGdb(self,args=[]):
        """Start gdb."""
        self.gdb.Start(args)

    def Running(self):
        """Check if vim server is running."""
        return self.vim.IsRunning()

    def Disable(self):
        """Remove vimgdb interface layer from vim session. (Call from GNU Gdb)."""
        self.vim.NewCommand()
        self.vim.DisableSignColumns()
        ret = self.vim.RunCommand()
        return ret

    def Kill(self):
        """Remove current line of execution highlighting. (Call from GNU Gdb)."""
        self.vim.NewCommand()
        self.vim.RemoveCle()
        ret = self.vim.RunCommand()
        return ret

    def Update(self,
            force=False,
            update_file=False,
            goto_line=True,
            update_breakpoint=None,
            delete_breakpoint=None,
            location=None):
        """Update breakpoints and highlighting in vim. (Call from GNU Gdb)."""

        # only update during execution
        is_running = self.gdb.IsRunning()
        if not (is_running or force):
            return 0

        # get current location in gdb
        fullsource,source,line = self.gdb.GetLocation(location)

        # create new series of vim commands
        self.vim.NewCommand()

        # get last known open file in vim
        vim_source = self.gdb.GetStoredFile()
        update_file = vim_source != fullsource or update_file

        # update file open in vim
        if update_file:
            self.vim.GotoFile(fullsource)

        # update breakpoints
        breakpoints,enabled,update_breakline = self.gdb.GetBreakpoints(source,delete_breakpoint,update_breakpoint)
        if update_file:
            self.vim.InitSignColumn()
            self.vim.UpdateBreakpoints(breakpoints,enabled)
        else:
            stored_breakpoints = self.gdb.GetStoredBreakpoints()
            add_breakpoints = breakpoints - stored_breakpoints
            if update_breakline != None:
                add_breakpoints.add(update_breakline)
            remove_breakpoints = stored_breakpoints - breakpoints
            self.vim.UpdateBreakpoints(add_breakpoints,enabled,remove_breakpoints)

        # goto line
        if goto_line:
            self.vim.GotoLine(line)

        # highlight current line of execution
        if location != None:
            if is_running:
                cle_fullsource,cle_source,cle_line = self.gdb.GetLocation()
                if cle_fullsource == fullsource:
                    self.vim.Cle(cle_line)
                else:
                    self.vim.RemoveCle()
        else:
            if is_running:
                self.vim.Cle(line)
            else:
                self.vim.RemoveCle()

        # execute commands in vim
        ret = self.vim.RunCommand()

        # store state in gdb
        if ret != 0:
            self.gdb.StoreFile("")
            self.gdb.StoreBreakpoints(set())
        elif update_file:
            self.gdb.StoreFile(fullsource)
            self.gdb.StoreBreakpoints(breakpoints)
        else:
            self.gdb.StoreBreakpoints(breakpoints)

        return ret

