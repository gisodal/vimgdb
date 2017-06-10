from __future__ import print_function, unicode_literals
import subprocess
import os

from .vimgdbexception import VimgdbError
from .viminterface import Vim
from .settings import settings

class Gdb:

    def __init__(self):
        self.executable = "gdb"

    def Start(self,args=[],check=True):
        """Start GNU Gdb."""
        library_dir = os.path.abspath(os.path.dirname(__file__))
        gdbinit = os.path.join(library_dir, 'config/gdbinit')

        cmd = [self.executable,
            "-q","-iex","source {0}".format(gdbinit)] + args
        subprocess.call(cmd)

    def GetValue(self,variable):
        """Return value of GNU Gdb parameter "<variable name>".

            Using GNU Gdb python API:
            >>> gdb = Gdb()
            >>> value = gdb.GetValue("variable name")
            >>> print("value:",value)
            >>>   value: "value string"
        """
        import gdb
        try:
            return gdb.parameter(variable)
        except:
            return ""

    def SetValue(self,variable,value):
        """Set string value of GNU Gdb parameter '<variable name>'.

            Using GNU Gdb python API:
            >>> gdb = Gdb()
            >>> gdb.SetValue("variable name","value string")
        """
        import gdb
        param = gdb.Parameter(variable, gdb.COMMAND_NONE,gdb.PARAM_STRING)
        param.value = str(value)

    def IsRunning(self):
        """Return true if currently executing code in gdb."""
        import gdb
        frame_fullsource,_,_ = self.GetFrameLocation()
        if frame_fullsource == None:
            return False

        try:
            fullsource,_,_ = self.GetLocation()
            if frame_fullsource != fullsource:
                return False
            else:
                return True
        except:
            return True

    def IsFunction(self,location):
        """Check if provided location is a function.

        >>> IsFunction("main") -> True
        """
        symbol = gdb.lookup_global_symbol(location)
        if symbol != None:
            return symbol.is_function
        else:
            return False;

    def GetFrameLocation(self):
        """Get location of current line of execution from active frame."""
        import gdb
        try:
            frame = gdb.selected_frame()
            pc = frame.pc()
            symbol_table_and_line = gdb.find_pc_line(pc)
            symbol_table = symbol_table_and_line.symtab
            fullsource = symbol_table.fullname()
            source = symbol_table.filename
            line = symbol_table_and_line.line
            return fullsource,source,line
        except:
            return None,None,None

    def GetLocation(self,location=None):
        """Get location of current line of execution, or location of provided location name."""
        import gdb
        try:
            if location == None:
                current_line = gdb.decode_line()
            else:
                try:
                    current_line = gdb.decode_line(location)
                except:
                    locationalt = "{0}:1".format(location)
                    current_line = gdb.decode_line(locationalt)

            symbol_table_and_line = current_line[1][0]
            symbol_table = symbol_table_and_line.symtab
            fullsource = symbol_table.fullname()
            source = symbol_table.filename
            line = symbol_table_and_line.line

            return fullsource,source,line
        except:
            if location == None:
                raise VimgdbError("Current location not detected")
            else:
                raise VimgdbError("Location '{0}' not found".format(location))

    def GetBreakpointLines(self,source):
        """Return all lines that have breakpoints in provided source file."""
        import re
        import gdb
        raw_break_info = gdb.execute('info break',to_string=True).split('\n')
        match = '^([0-9]+).*{0}:([0-9]+)$'.format(source)
        breakpoints = [ re.findall(match,line) for line in raw_break_info ]
        breakpoints = [ breakpoint[0] for breakpoint in breakpoints if breakpoint ]
        breakpoints = { int(x[0]): int(x[1]) for x in breakpoints }
        return breakpoints

    def GetBreakpoints(self,source,delete_breakpoint=None,update_breakpoint=None):
        """Return all lines that have breakpoints in provided source file.

        This function is equal to GetBreakpoints, but does not require 'info break'.
        NOTE: Occasionally provides function breakpoints with an offset of 1."""
        import gdb
        breaklines = set()
        enabled = dict()

        breakpointlines = self.GetBreakpointLines(source)
        if update_breakpoint != None and update_breakpoint in breakpointlines:
            update_breakline = breakpointlines[update_breakpoint]
        else:
            update_breakline = None

        for breakpoint in gdb.breakpoints():
            key = breakpoint.number
            if breakpoint.number is not delete_breakpoint and key in breakpointlines:
                breakline = breakpointlines[key]
                breaklines.add(breakline)
                if breakline in enabled:
                    enabled[breakline] = enabled[breakline] or breakpoint.enabled
                else:
                    enabled[breakline] = breakpoint.enabled

        return breaklines,enabled,update_breakline

