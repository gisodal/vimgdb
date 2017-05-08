from __future__ import absolute_import, division, print_function, unicode_literals
import subprocess
import os


def IsBinary(filename):
    import mimetypes
    import os
    if os.path.isfile(filename):
        mtype = mimetypes.guess_type(filename)
        if mtype == None or "text" not in str(mtype[0]):
            return True

    return False


class Vim:

    def __init__(self):
        self.servername = u"VIMGDB"
        self.executable = "vim"
        self.debug = False

    def Start(self,args=[],check=True):
        from os import path

        if check and self.IsRunning():
            raise RuntimeError("Vim server already running")

        library_dir = path.abspath(path.dirname(__file__))
        vimrc = path.join(library_dir, 'config/vimrc')

        if not path.exists(vimrc):
            raise RuntimeError("Config file '{0}' not found".format(vimrc))

        for arg in args:
            if IsBinary(arg):
                print("File '{0}' is not a text file".format(arg))
                from sys import exit; exit(1)

        cmd = [self.executable,
            "--servername","{0}".format(self.servername),
            "-n",
            "-c","source {0}".format(vimrc)] + args

        subprocess.call(cmd)

    def GetServerlist(self):
        output = subprocess.check_output([self.executable, '--serverlist'])
        output.decode('utf-8')
        return output

    def IsRunning(self):
        servers = self.GetServerlist()
        if self.servername in servers:
            return True
        else:
            return False

    def NewCommand(self):
        self.command = []

    def AddCommand(self,command):
        self.command.append(command)

    def RunCommand(self):
        if len(self.command) > 0:
            self.Redraw()
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
                print("*** Commands sent **************************************\n   ",
                    "\n    ".join(self.command),
                    "\n********************************************************")

                return subprocess.call(cmd)
            else:
                DEVNULL = open(os.devnull, 'w')
                return subprocess.call(cmd,stdout=DEVNULL,stderr=subprocess.STDOUT)

    def RemoveSigns(self,sign_id):
        self.AddCommand('execute "sign unplace {0}"'.format(sign_id))

    def RemoveSign(self,sign_id):
        self.AddCommand('execute "sign unplace {0} file=" . expand("%:p")'.format(sign_id))

    def AddSign(self,line,sign_type,sign_id=-1):
        if sign_id < 0:
            sign_id = line
        self.AddCommand('execute "sign place {0} line={1} name={2} file=" . expand("%:p")'.format(sign_id,line,sign_type))

    def EnableSignColumn(self):
        self.AddSign(1,"VimgdbDummy",999999)

    def DisableSignColumn(self):
        self.AddCommand('execute "sign unplace * file=" . expand("%:p")')

    def DisableSignColumns(self):
        self.AddCommand('execute "sign unplace *"')

    def InitSignColumn(self):
        self.DisableSignColumn()
        self.EnableSignColumn()

    def RemoveBreakpoints(self,breakpoints):
        for breakline in breakpoints:
            self.RemoveSign(breakline)

    def AddBreakpoints(self,breakpoints):
        for breakline in breakpoints:
            self.AddSign(breakline,"VimgdbBreakpointSign")

    def UpdateBreakpoints(self,add_breakpoints=set(),remove_breakpoints=set()):
        self.AddBreakpoints(add_breakpoints)
        self.RemoveBreakpoints(remove_breakpoints)

    def Redraw(self):
        self.command.append("redraw!")

    def GotoLine(self,line):
        if line > 1:
            self.AddCommand("call cursor({0},1)".format(line))

    def UpdateLine(self,line):
        if line > 1:
            sign_id = 999998
            self.RemoveSigns(sign_id)
            self.AddSign(line,"VimgdbLocationSign",sign_id)

    def GotoFile(self,filename,check=False):
        self.AddCommand("edit {0}".format(filename))


