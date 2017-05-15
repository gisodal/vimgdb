from __future__ import print_function, unicode_literals
import subprocess
import os

from .viminterface import Vim

class Gdb:

    def __init__(self):
        self.executable = "gdb"
        self.src = "_vimgdb_src"
        self.breakpoints = "_vimgdb_breakpoints"
        self.argv = "_vimgdb_argv"

    def Start(self,args=[],check=True):
        """Start GNU Gdb."""
        from os import path

        library_dir = path.abspath(path.dirname(__file__))
        gdbinit = path.join(library_dir, 'config/gdbinit')

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
            return None

    def SetValue(self,variable,value):
        """Set string value of GNU Gdb parameter '<variable name>'.

            Using GNU Gdb python API:
            >>> gdb = Gdb()
            >>> gdb.SetValue("variable name","value string")
        """
        import gdb
        param = gdb.Parameter(variable, gdb.COMMAND_NONE,gdb.PARAM_OPTIONAL_FILENAME)
        param.value = str(value)

    def IsRunning(self):
        """Return true if currently executing source."""
        import gdb
        try:
            gdb.selected_frame()
            return True
        except:
            return False

    def IsFunction(self,location):
        """Check if provided location is a function.

        >>> IsFunction("main") -> True
        """
        symbol = gdb.lookup_global_symbol(location)
        if symbol != None:
            return symbol.is_function
        else:
            return False;

    def GetLocation(self,location=None):
        """Get location of current line of execution, or location of provided location name."""
        import gdb
        try:
            if location == None:
                current_line = gdb.decode_line()
            else:
                current_line = gdb.decode_line(location)

            symbol_table_and_line = current_line[1][0]
            symbol_table = symbol_table_and_line.symtab
            fullsource = symbol_table.fullname()
            source = symbol_table.filename
            line = symbol_table_and_line.line

            return fullsource,source,line
        except:
            if location == None:
                raise RuntimeError("Current location not detected")
            else:
                raise RuntimeError("Location '{0}' not found".format(location))

    def GetBreakpoints(self,source):
        """Return all lines that have breakpoints in provided source file."""
        import re
        import gdb
        raw_break_info = gdb.execute('info break',to_string=True).split('\n')
        match = '([0-9]+)[ ]*([^ ]+)[ ]*([^ ]+)[ ]*([^ ]+).*{0}:([0-9]+)'.format(source)
        breakpoints = [ re.findall(match,line) for line in raw_break_info ]
        breakpoints = [ breakpoint[0] for breakpoint in breakpoints if breakpoint ]

        breaklines = set()
        enabled = dict()
        for breakpoint in breakpoints:
            num =  breakpoint[0]
            type = breakpoint[1]
            disp = breakpoint[2]
            enab = bool(breakpoint[3] == "y")
            breakline = int(breakpoint[4])
            if type == "breakpoint":
                breaklines.add(breakline)
                if breakline in enabled:
                    enabled[breakline] = enabled[breakline] or enab
                else:
                    enabled[breakline] = enab

        return breaklines,enabled

    def GetBreakpointsInternal(self,source):
        """Return all lines that have breakpoints in provided source file.
        This function is equal to GetBreakpoints, but does not require 'info break'.
        NOTE: Occasionally provides function breakpoints with an offset of 1."""
        import gdb
        breaklines = set()
        enabled = dict()
        for breakpoint in gdb.breakpoints():
            if breakpoint.visible:
                fullsource,breaksource,breakline = self.GetLocation(breakpoint.location)
                if source == breaksource:
                    breaklines.add(breakline)
                    if breakline in enabled:
                        enabled[breakline] = enabled[breakline] or breakpoint.enabled
                    else:
                        enabled[breakline] = breakpoint.enabled

        return breaklines,enabled

    def GetStoredBreakpoints(self):
        """Get previously stored breakpoint lines."""
        breakpoints = set(int(i) for i in self.GetValue(self.breakpoints).split(':') if i)
        return breakpoints

    def StoreBreakpoints(self,breakpoints):
        """Store breakpoint lines (in GNU Gdb conventience variable)."""
        self.SetValue(self.breakpoints,":".join(str(breakline) for breakline in breakpoints))

    def GetStoredFile(self):
        """Get previously stored source file holding current line of excecution."""
        return self.GetValue(self.src)

    def StoreFile(self,filename):
        """Store source file holding current line of excecution."""
        self.SetValue(self.src,filename)

