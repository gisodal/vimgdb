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
            goto_cle=True,
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

        # goto and highlight current line of execution
        if is_running:
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

        def HandleException(function, *args, **kwargs):
            try:
                ret = function(*args, **kwargs)
                if ret != 0  and settings.debug:
                    print("Connection to Vim server failed")
                return ret
            except VimgdbError as error:
                if settings.debug:
                    import traceback
                    print(traceback.format_exc())
                print("{0}".format(str(error)))

        def StopEvent(stop_event):
            HandleException(self.Update,force=True,goto_cle=True)

        def BreakEvent(breakpoint):
            HandleException(self.Update,force=True,goto_cle=False)

        def BreakModifyEvent(breakpoint):
            HandleException(self.Update,force=True,goto_cle=False,update_breakpoint=int(breakpoint.number))

        def BreakDelEvent(breakpoint):
            HandleException(self.Update,force=True,goto_cle=False,delete_breakpoint=int(breakpoint.number))

        def ObjEvent(obj):
            try:
                self.Update(goto_cle=True,force=True,location="main")
            except: pass

        gdb.events.stop.connect(StopEvent)
        gdb.events.breakpoint_created.connect(BreakEvent)
        gdb.events.breakpoint_modified.connect(BreakModifyEvent)
        gdb.events.breakpoint_deleted.connect(BreakDelEvent)
        gdb.events.new_objfile.connect(ObjEvent)


def main(args):
    vimgdb = Vimgdb()
    vimgdb.Start(args)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])

