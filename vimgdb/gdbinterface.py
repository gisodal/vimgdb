from __future__ import print_function, unicode_literals
import subprocess
import os

from .viminterface import Vim

class Gdb:

    def __init__(self):
        self.executable = "gdb"
        self.src = "$_vimgdb_src"
        self.breakpoints = "$_vimgdb_breakpoints"
        self.option = "$_vimgdb_option"

    def Start(self,args=[],check=True):
        """Start GNU Gdb."""
        from os import path

        library_dir = path.abspath(path.dirname(__file__))
        gdbinit = path.join(library_dir, 'config/gdbinit')

        cmd = [self.executable,
            "-q","-iex","source {0}".format(gdbinit)] + args
        subprocess.call(cmd)

    def GetValue(self,variable):
        """Return value of GNU Gdb convenience variable "$<variable name>".

            In GNU Gdb:
            >>> gdb) set $var = "value string"

            Using GNU Gdb python API:
            >>> gdb = Gdb()
            >>> value = gdb.GetValue("$var")
            >>> print("value:",value)
            >>>   value: "value string"
        """
        import gdb
        import re
        value = str(gdb.parse_and_eval("{0}".format(variable)))
        value = re.findall('"(.*)"', value)
        if len(value) > 0:
            return value[0]
        else:
            return ""

    def SetValue(self,variable,value):
        """Set string value of GNU Gdb convenience variable '$<variable name>'.

            PRECONDITION: "$var" must be set (allocated) in GNU Gdb.

            The following are equivalent. In GNU Gdb:
            >>> set $var = "value string"

            Using GNU Gdb python API:
            >>> gdb = Gdb()
            >>> gdb.SetValue("$var","value string")
        """
        import gdb
        MAX = 250
        if len(value) > MAX:
            raise RuntimeError("Cannot store '{0}' in {1}: value longer than {2} characters".format(value,variable,MAX))
        gdb.execute("set {0} = \"{1}\"".format(variable,value))

    def GetLocation(self,location=None):
        """Get location of current line of execution, or location of privided location name."""
        import gdb
        try:
            is_function = False
            if location == None:
                current_line = gdb.decode_line()
            else:
                current_line = gdb.decode_line(location)
                symbol = gdb.lookup_global_symbol(location)
                if symbol != None:
                    is_function = symbol.is_function

            symbol_table_and_line = current_line[1][0]
            symbol_table = symbol_table_and_line.symtab
            fullsource = symbol_table.fullname()
            source = symbol_table.filename
            line = symbol_table_and_line.line

            # gdb adds breakpoints to functions on the next line
            if is_function:
                line += 1

            return fullsource,source,line
        except:
            if location == None:
                raise RuntimeError("Current location not detected")
            else:
                raise RuntimeError("Location '{0}' not found".format(location))

    def GetBreakpoints(self,source):
        """Return all lines that have breakpoints in provided source file."""
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

