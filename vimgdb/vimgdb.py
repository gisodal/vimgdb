from __future__ import print_function
from .viminterface import Vim
from .gdbinterface import Gdb
from .vimgdbexception import VimgdbError
from .settings import settings
from .version import Version


class Vimgdb:

    def __init__(self):
        self.vim = Vim()
        self.gdb = Gdb()
        self.vim_breakpoints = set()
        self.vim_file = None

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
        self.vim_breakpoints = set()
        return ret

    def Kill(self):
        """Remove current line of execution highlighting. (Call from GNU Gdb)."""
        self.vim.NewCommand()
        self.vim.RemoveCle()
        ret = self.vim.RunCommand()
        return ret

    def Clear(self):
        self.vim_file = None
        self.vim_breakpoints = set()

    def Update(self,
            force=False,
            update_file=False,
            update_cle=True,
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
        update_file = self.vim_file != fullsource or update_file

        # update file open in vim
        if update_file:
            self.vim.GotoFile(fullsource)

        # update breakpoints
        breakpoints,enabled,update_breakline = self.gdb.GetBreakpoints(source,delete_breakpoint,update_breakpoint)
        if update_file:
            self.vim.InitSignColumn()
            self.vim.UpdateBreakpoints(breakpoints,enabled)
        else:
            add_breakpoints = breakpoints - self.vim_breakpoints
            if update_breakline != None:
                add_breakpoints.add(update_breakline)
            remove_breakpoints = self.vim_breakpoints - breakpoints
            self.vim.UpdateBreakpoints(add_breakpoints,enabled,remove_breakpoints)

        # goto line
        if goto_line:
            self.vim.GotoLine(line)

        # highlight current line of execution
        if update_cle:
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

        # store vim state
        if ret != 0:
            self.Clear()
        elif update_file:
            self.vim_file = fullsource
            self.vim_breakpoints = breakpoints
        else:
            self.vim_breakpoints = breakpoints

        return ret

