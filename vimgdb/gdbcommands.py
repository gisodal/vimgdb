from __future__ import with_statement,print_function, unicode_literals
from .vimgdb import Vimgdb
from .settings import settings
from .vimgdbexception import VimgdbError
import gdb

vimgdb = Vimgdb()

def HandleException(function, *args, **kwargs):
    try:
        ret = function(*args, **kwargs)
        if ret != 0 and settings.debug:
            print("Connection to Vim server failed")
        return ret
    except VimgdbError as error:
        if settings.debug:
            import traceback
            print(traceback.format_exc())
        print("{0}".format(str(error)))
    except KeyboardInterrupt:
        pass
    except Exception as error:
        if settings.debug:
            import traceback
            print(traceback.format_exc())
        print("Vimgdb Exception: {0}".format(str(error)))


class VimgdbCommand(gdb.Command):
    """Vimgdb interface."""

    def __init__ (self):
        super (VimgdbCommand, self).__init__ (
            "vimgdb", gdb.COMMAND_SUPPORT, gdb.COMPLETE_NONE, True)

class VimgdbGotoCommand(gdb.Command):
    """Goto provided location with vim.

    The provided location is decoded in the way that GDB's inbuilt break or edit commands do.
    example:
        vimgdb goto test.cc:8
        vimgdb goto main"""

    def __init__ (self):
        super (VimgdbGotoCommand, self).__init__(
            "vimgdb goto", gdb.COMMAND_SUPPORT, gdb.COMPLETE_NONE)

    def invoke (self, arg, from_tty):
        if arg == "":
            arg = None

        HandleException(vimgdb.Update,force=True,update_file=False,goto_line=True,location=arg)


class VimgdbDisableCommand(gdb.Command):
    """Removes vimgdb interface layer from vim session."""

    def __init__ (self):
        super (VimgdbDisableCommand, self).__init__(
            "vimgdb disable", gdb.COMMAND_SUPPORT, gdb.COMPLETE_NONE)

    def invoke (self, arg, from_tty):
        HandleException(vimgdb.Disable)


class VimgdbKillCommand(gdb.Command):
    """Removes current line of execution highlighting from vim session."""

    def __init__ (self):
        super (VimgdbKillCommand, self).__init__(
            "vimgdb kill", gdb.COMMAND_SUPPORT, gdb.COMPLETE_NONE)

    def invoke (self, arg, from_tty):
        HandleException(vimgdb.Kill)


class VimgdbUpdateCommand(gdb.Command):
    """Update breakpoints and highlighting in vim."""

    def __init__ (self):
        super (VimgdbUpdateCommand, self).__init__(
            "vimgdb update", gdb.COMMAND_SUPPORT, gdb.COMPLETE_NONE)

    def invoke (self, arg, from_tty):
        HandleException(vimgdb.Update,force=False,update_file=False,goto_line=True)


class VimgdbReloadCommand(gdb.Command):
    """Resynchronize vim and gdb.
    Reloads file, breakpoints and highlighting in vim session.
    This function can be used in case vim and gdb get desynchronized."""

    def __init__ (self):
        super (VimgdbReloadCommand, self).__init__(
            "vimgdb reload", gdb.COMMAND_SUPPORT, gdb.COMPLETE_NONE)

    def invoke (self, arg, from_tty):
        HandleException(vimgdb.Update,force=True,update_file=True,goto_line=True)


def StopEvent(stop_event):
    HandleException(vimgdb.Update,force=True,goto_line=True)

def BreakEvent(breakpoint):
    HandleException(vimgdb.Update,force=True,goto_line=False)

def BreakModifyEvent(breakpoint):
    HandleException(vimgdb.Update,force=True,goto_line=False,update_breakpoint=int(breakpoint.number))

def BreakDeleteEvent(breakpoint):
    HandleException(vimgdb.Update,force=True,goto_line=False,delete_breakpoint=int(breakpoint.number))

def ObjectLoadEvent(obj):
    try:
        vimgdb.Update(goto_line=True,force=True,location="main")
    except: pass


def Register():
    """Register all commands and events required by Vimgdb. (Call from GNU Gdb)."""

    # register commands
    VimgdbCommand()
    VimgdbGotoCommand()
    VimgdbDisableCommand()
    VimgdbKillCommand()
    VimgdbUpdateCommand()
    VimgdbReloadCommand()

    # register events
    gdb.events.stop.connect(StopEvent)
    gdb.events.breakpoint_created.connect(BreakEvent)
    gdb.events.breakpoint_modified.connect(BreakModifyEvent)
    gdb.events.breakpoint_deleted.connect(BreakDeleteEvent)
    gdb.events.new_objfile.connect(ObjectLoadEvent)

