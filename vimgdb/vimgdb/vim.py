
class Vim:

    def __init__(self):
        self.servername = u"VIMGDB"
        self.executable = "vim"
        self.command = []

    def Start(self,check=True):
        from os import path,exists
        from subprocess import call

        if check and self.IsRunning():
            raise RuntimeError("Vim server already running")

        library_dir = path.abspath(path.dirname(__file__))
        vimrc = path.join(library_dir, 'config/vimrc')

        if not path.exists(vimrc):
            raise RuntimeError("Config file '{0}' not found".format(self.__vimrc))

        cmd = [self.__executable,
            "--servername","{0}".format(self.servername),
            "-n",
            "-c","source {0}".format(vimrc)]

        call(cmd)

    def GetServerlist(self):
        from subprocess import check_output
        output = check_output([self.executable, '--serverlist'])
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
        from subprocess import call
        if len(self.command) > 0:
            self.Redraw()
            command = "<Esc>:{0}<Enter>".format(" | ".join(self.command))
            cmd = [ self.executable,
                "--servername",self.servername,
                "--remove-send",command]

            call(cmd)

    def UpdateBreakpoints(self,breakpoints):
        if len(breakpoints) > 0:
            command = ""
            for breakpoint in breakpoints:
                if command != "":
                    command += "\\|"
                command += "\\%{0}l".format(breakpoint)

            command = "2match GdbBreakpoint /{0}/".format(command)
            self.AddCommand(command)

    def Redraw(self)
        self.command.append("redraw!")

    def GotoLine(self,line):
        command = "3match GdbLocation /\\%{0}l/".format(line)
        self.AddCommand(command)

    def GotoFile(self,filename,check=False):
        self.AddCommand("edit {0}".format(filename))

