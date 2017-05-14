from .viminterface import Vim
from .gdbinterface import Gdb

class Vimgdb:

    def __init__(self):
        self.vim = Vim()
        self.gdb = Gdb()

    def Start(self,args=[]):
        """Start vim, or start GNU Gdb if vim is already started."""
        if not self.vim.IsRunning():
            self.vim.Start(args)
        else:
            self.gdb.Start(args)

    def Disable(self):
        """Remove vimgdb interface layer from vim session. (Call from GNU Gdb)."""
        self.vim.NewCommand()
        self.vim.DisableSignColumns()
        self.vim.RunCommand()

    def Update(self,cle=True,force=False):
        """Update breakpoints and highlighting in vim. (Call from GNU Gdb)."""
        # onlu update during execution
        if not (self.gdb.IsRunning() or force):
            return 0

        # get current location in gdb
        fullsource,source,line = self.gdb.GetLocation()

        # create new series of vim commands
        self.vim.NewCommand()

        # get last known open file in vim
        vim_source = self.gdb.GetStoredFile()
        update_file = vim_source != fullsource

        # update file open in vim
        if update_file:
            self.vim.GotoFile(fullsource)

        # update breakpoints
        breakpoints,enabled = self.gdb.GetBreakpoints(source)
        if update_file:
            self.vim.InitSignColumn()
            self.vim.UpdateBreakpoints(breakpoints,enabled)
        else:
            stored_breakpoints = self.gdb.GetStoredBreakpoints()
            remove_breakpoints = stored_breakpoints - breakpoints
            self.vim.UpdateBreakpoints(breakpoints,enabled,remove_breakpoints)

        # goto and highlight current line of execution
        if cle and self.gdb.IsRunning():
            self.vim.UpdateLine(line)
            self.vim.GotoLine(line)

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

def main(args):
    vimgdb = Vimgdb()
    vimgdb.Start(args)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])

