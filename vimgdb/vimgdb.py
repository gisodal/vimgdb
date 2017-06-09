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
        self.Clear()

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
        self.Clear()
        return ret

    def Kill(self):
        """Remove current line of execution highlighting. (Call from GNU Gdb)."""
        self.vim.NewCommand()
        self.vim.RemoveCle()
        ret = self.vim.RunCommand()
        return ret

    def Clear(self):
        """Clear. (Call from GNU Gdb)."""
        self.line = None
        self.source = None
        self.fullsource = None
        self.breakpoints = set()

    def UpdateFile(self,fullsource,line=None):
        self.vim.GotoFile(fullsource,line)
        self.vim.InitSignColumn()

    def UpdateBreakpoints(self,
            source,
            update_all,
            modify_breakpoint=None,
            delete_breakpoint=None):

        breakpoints,enabled,update_breakline = self.gdb.GetBreakpoints(
                source,delete_breakpoint,modify_breakpoint)

        if update_all:
            self.vim.UpdateBreakpoints(breakpoints,enabled)
        else:
            add_breakpoints = breakpoints - self.breakpoints
            if update_breakline != None:
                add_breakpoints.add(update_breakline)
            remove_breakpoints = self.breakpoints - breakpoints
            self.vim.UpdateBreakpoints(add_breakpoints,enabled,remove_breakpoints)

        return breakpoints

    def Update(self,
            force=False,
            update_file=False,
            update_cle=True,
            update_breakpoint=False,
            goto_line=True,
            modify_breakpoint=None,
            delete_breakpoint=None,
            location=None):
        """Update breakpoints and highlighting in vim. (Call from GNU Gdb)."""

        # only update during execution
        is_running = self.gdb.IsRunning()
        if not (is_running or force):
            return 0

        # get current location in gdb or vim
        if update_breakpoint:
            if self.fullsource != None:
                # use location opened in vim
                fullsource = self.fullsource
                source = self.source
                line = self.line
            else:
                return 0
        else:
            fullsource,source,line = self.gdb.GetLocation(location)

        # get last known open file in vim
        update_file = self.fullsource != fullsource or update_file

        # create new series of vim commands
        self.vim.NewCommand()

        # update file open in vim [and go to line]
        if update_file:
            if goto_line:
                self.UpdateFile(fullsource,line)
            else:
                self.UpdateFile(fullsource)
        elif goto_line:
            self.vim.GotoLine(line)

        # update breakpoints
        breakpoints = self.UpdateBreakpoints(source,update_file,modify_breakpoint,delete_breakpoint)

        # highlight current line of execution
        if update_cle:
            if is_running:
                cle_fullsource,cle_source,cle_line = self.gdb.GetLocation()
                if cle_fullsource == fullsource:
                    self.vim.Cle(cle_line)
                else:
                    self.vim.RemoveCle()
            else:
                self.vim.RemoveCle()

        # execute commands in vim
        ret = self.vim.RunCommand()

        # store vim state
        if ret != 0:
            self.Clear()
        elif update_file:
            self.line = line
            self.source = source
            self.fullsource = fullsource
            self.breakpoints = breakpoints
        else:
            self.breakpoints = breakpoints

        return ret

