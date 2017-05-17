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
        ret = self.vim.RunCommand()
        return ret

    def Kill(self):
        """Remove current line of execution highlighting. (Call from GNU Gdb)."""
        self.vim.NewCommand()
        self.vim.RemoveCle()
        ret = self.vim.RunCommand()
        return ret

    def Update(self,goto_cle=True,force=False,delete_breakpoint=None,location=None):
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
        update_file = vim_source != fullsource

        # update file open in vim
        if update_file:
            self.vim.GotoFile(fullsource)

        # update breakpoints
        breakpoints,enabled = self.gdb.GetBreakpoints(source,delete_breakpoint)
        if update_file:
            self.vim.InitSignColumn()
            self.vim.UpdateBreakpoints(breakpoints,enabled)
        else:
            stored_breakpoints = self.gdb.GetStoredBreakpoints()
            remove_breakpoints = stored_breakpoints - breakpoints
            self.vim.UpdateBreakpoints(breakpoints,enabled,remove_breakpoints)

        # goto and highlight current line of execution
        if is_running :
            self.vim.Cle(line)
        else:
            self.vim.RemoveCle()

        if goto_cle:
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

    def Register(self):
        """Register all events required by Vimgdb. (Call from GNU Gdb)."""
        import gdb
        import traceback

        def HandleException(function, *args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as error:
                print("Vimgdb Exception: {0}".format(str(error)))
                print(traceback.format_exc())

        def StopEvent(stop_event):
            HandleException(self.Update,goto_cle=True,force=False)

        def BreakEvent(breakpoint):
            HandleException(self.Update,goto_cle=False,force=True)

        def BreakDelEvent(breakpoint):
            HandleException(self.Update,goto_cle=False,force=True,delete_breakpoint=int(breakpoint.number))

        def ObjEvent(obj):
            try:
                self.Update(goto_cle=True,force=True,location="main")
            except: pass

        gdb.events.stop.connect(StopEvent)
        gdb.events.breakpoint_created.connect(BreakEvent)
        gdb.events.breakpoint_modified.connect(BreakEvent)
        gdb.events.breakpoint_deleted.connect(BreakDelEvent)
        gdb.events.new_objfile.connect(ObjEvent)


def main(args):
    vimgdb = Vimgdb()
    vimgdb.Start(args)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])

