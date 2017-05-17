from __future__ import absolute_import, division, print_function, unicode_literals
import subprocess
import os


def IsTextfile(filename):
    """Check if a file is a text file."""
    import mimetypes
    import os
    if os.path.isfile(filename):
        mtype = mimetypes.guess_type(filename)
        if mtype != None and "text" in str(mtype[0]):
            return True

    return False


class Vim:

    def __init__(self):
        self.servername = u"VIMGDB"
        self.executable = "vim"
        self.cle_id = 999998
        self.use_file = True
        self.debug = False

    def Start(self,args=[],check=True):
        """Start vim as a server."""
        from os import path

        if check and self.IsRunning():
            raise RuntimeError("Vim server already running")

        library_dir = path.abspath(path.dirname(__file__))
        vimrc = path.join(library_dir, 'config/vimrc')

        if not path.exists(vimrc):
            raise RuntimeError("Config file '{0}' not found".format(vimrc))

        for arg in args:
            if not IsTextfile(arg):
                print("Argument '{0}' is not a text file".format(arg))
                from sys import exit; exit(1)

        cmd = [self.executable,
            "--servername","{0}".format(self.servername),
            "-n",
            "-c","source {0}".format(vimrc)] + args

        subprocess.call(cmd)

    def GetServerlist(self):
        """Get list of running vim servers."""
        output = subprocess.check_output([self.executable, '--serverlist'])
        output.decode('utf-8')
        return output

    def IsRunning(self):
        """Return True if vim server is running."""
        servers = self.GetServerlist()
        if self.servername in servers:
            return True
        else:
            return False

    def NewCommand(self):
        """Create new vimgdb batch: a set of commands that will be sent the vim server."""
        self.command = []

    def AddCommand(self,command):
        """Add command to the vimgdb batch."""
        self.command.append(command)

    def RunCommand(self):
        """Send all commands in the vimgdb batch."""
        if len(self.command) > 0:
            self.Redraw()
            if self.debug:
                print("*** Commands sent **************************************\n   ",
                    "\n    ".join(self.command),
                    "\n********************************************************")

            if self.use_file:
                home = os.path.expanduser('~')
                cmdfile = home+"/.vimgdb-command"
                f = open(cmdfile, 'w')
                f.write("\n".join(self.command))
                f.close()
                command = "<Esc>:source {0}<Enter>".format(cmdfile)
            else:
                function = [ 'silent execute "function! Vimgdb()' ]
                function.extend([ cmd.replace('"','\\"') for cmd in self.command] )
                function.extend(['endfunction"'])
                function = '\\n'.join(function)
                function = [function, 'call Vimgdb()']
                function = " | ".join(function)
                command = '<Esc>:{0}<Enter>'.format(function)

            cmd = [ self.executable,
                "--servername",self.servername,
                "--remote-send",command]

            if self.debug:
                return subprocess.call(cmd)
            else:
                DEVNULL = open(os.devnull, 'w')
                return subprocess.call(cmd,stdout=DEVNULL,stderr=subprocess.STDOUT)
        else:
            return 0

    def RemoveSigns(self,sign_id):
        """Remove all signs."""
        self.AddCommand('execute "sign unplace {0}"'.format(sign_id))

    def RemoveSign(self,sign_id):
        """Remove particular sign."""
        self.AddCommand('execute "sign unplace {0} file=" . expand("%:p")'.format(sign_id))

    def AddSign(self,line,sign_type,sign_id=-1):
        """Add a particular sign on a provide line."""
        if sign_id < 0:
            sign_id = line
        self.AddCommand('execute "sign place {0} line={1} name={2} file=" . expand("%:p")'.format(sign_id,line,sign_type))

    def EnableSignColumn(self):
        """Add the sign column."""
        self.AddSign(1,"VimgdbDummy",999999)

    def DisableSignColumn(self):
        """Remove sign column in current file."""
        self.AddCommand('execute "sign unplace * file=" . expand("%:p")')

    def DisableSignColumns(self):
        """Remove all sign columns."""
        self.AddCommand('execute "sign unplace *"')

    def InitSignColumn(self):
        """Create empty sign column."""
        self.DisableSignColumn()
        self.EnableSignColumn()

    def RemoveBreakpoints(self,breakpoints):
        """Remove breakpoints."""
        for breakline in breakpoints:
            self.RemoveSign(breakline)

    def AddBreakpoints(self,breakpoints,enabled):
        """Add breakpoints."""
        for breakline in breakpoints:
            if enabled[breakline]:
                self.AddSign(breakline,"VimgdbBreakpointSign")
            else:
                self.AddSign(breakline,"VimgdbDisabledBreakpointSign")

    def UpdateBreakpoints(self,breakpoints,enabled,remove_breakpoints=set()):
        """Add and remove breakpoints."""
        self.AddBreakpoints(breakpoints,enabled)
        self.RemoveBreakpoints(remove_breakpoints)

    def Redraw(self):
        """Redraw vim screen."""
        self.command.append("redraw!")

    def GotoLine(self,line):
        """Move cursor to particular line."""
        self.AddCommand("call cursor({0},1)".format(line))

    def RemoveCle(self):
        """Remove current line of execution highlighting."""
        self.RemoveSigns(self.cle_id)

    def Cle(self,line):
        """Highlight current line of execution."""
        self.RemoveCle()
        self.AddSign(line,"VimgdbLocationSign",self.cle_id)

    def GotoFile(self,filename,check=False):
        """Open file."""
        self.AddCommand("edit {0}".format(filename))


