# -*- coding: <utf-8> -*-

"""
Module that implements a client and server interface useful for controlling a
vim server.
This module could be used for unit testing or integration testing
for a Vim plugin written in Python. Or you can use it to interactively control
a Vim editor by Python code, for example, in an Ipython session.

This work tries to be the python equivalent of Vimrunner ruby gem found at:
    http://rubydoc.info/gems/vimrunner/index

I thank the author(s) for the effort and nice level of abstraction
they put in this gem.

"""

import os.path
import multiprocessing
import subprocess
import random
import time

#vimrc = os.path.join(os.path.dirname(
#    os.path.abspath(__file__)), 'default_vimrc')


### utility functions ###
def create_vim_list(values):
    """creates the Vim editor's equivalent of python's repr(a_list).

        >>> create_vim_list(['first line', 'second line'])
        '["first line", "second line"]'

    values - a list of strings

    We need double quotes not single quotes to create a Vim list.
    Returns a string that is a properly written Vim list of strings.
    This result can be fed to vim's eval function to create a list in vim.
    """
    values_with_quotes = ('"' + elem + '"' for elem in values)
    return '[%s]' % ', '.join(values_with_quotes)
    # as a one liner:
    #return '[%s]' % ', '.join("\"%s\"" % elem for elem in values)


class Server(object):
    """
    Represents a remote Vim editor server. A Server has the responsibility of
    starting a Vim process and communicating with it through the
    client - server interface. The process can be started with one of the
    "start*" family of methods:

        start_in_other_terminal()

        start_gvim()

        start()

    The server can be stopped with "kill" method, but it is recommended to
    use client's "quit" method .

    If given the servername of an existing Vim instance, it can
    control that instance without the need to start a new process.

    A Client would be necessary as an actual interface, though it is possible
    to use a Server directly to invoke --remote-send and --remote-expr
    commands on its Vim instance.

    Example:

        >>> vim = Server("My_server")
        >>> client = vim.start_in_other_terminal()
        >>> client.edit("some_file.txt")

    """
    vimrc = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'default_vimrc')

    def __init__(self, name='', executable='vim', vimrc='', noplugin=True,
                 extra_args=['-n']):
        """
        Initialize a Server.

            name       - The String name of the Vim server
                         (default: "VIMRUNNER#{random.randint}").
            executable - The String 'vim' or 'gvim' (for GUI) or an absolute
                         path of Vim executable to use
                         (default: vim).
            vimrc      - The String vimrc file to source in the client. The
                         default Server.vimrc file is used, it is needed by
                         this module in order to work fine. If user wants to
                         use a custom vimrc, it should be sourced using client.
                         (default: Server.vimrc).
            noplugin   - Do not load any plugins.
            extra_args - command line args that can be given to vim before it
                         is started. It is used especially by start_gvim()
                         (default: ['-n'] to prevent using swap files.)

        Example:

            >>> # no swap file will be used:
            >>> vim = Server(extra_args=['-n']

        """
        self.name = name or 'VIMRUNNER#%s' % random.randint(1, 10000)
        self.executable = executable if os.path.isabs(executable) else \
            self._get_abs_path(executable)

        vimrc = vimrc if vimrc else Server.vimrc
        self.vimrc = '-u %s' % vimrc
        self.noplugin = '--noplugin' if noplugin else ''
        self.extra_args = extra_args
        self.cmd = None
        self._format_vim_args()

    def _format_vim_args(self):
        """Utility function used by start_*() family of functions.
        Returns nothing."""
        # format arguments list for the Vim subprocess, order matters
        self.vim_args = [self.executable, self.vimrc, self.noplugin,
                         '--servername', self.name]
        # get rid of empty strings, False arguments
        self.vim_args = [arg for arg in self.vim_args if arg]
        # add extra vim arguments
        self.vim_args.extend(self.extra_args)
        self.cmd = " ".join(self.vim_args)
        # Eg:
        # >>> self.cmd
        # "/usr/bin/gvim -n --noplugin --servername VIMRUNNER#1"

    def start(self, timeout=5, testing=False):
        """Starts Vim server in a subprocess, eg.:

            >>> subprocess.call("vim -n --servername GOTOWORD", shell=True)

        but we don't want to wait for Vim to complete and to block this script
        so we need some thread like behaviour that is obtained using the
        multiprocessing module.

        testing - flag useful for tests when you don't want to start Vim server

        Returns a client connected to Vim server.
        """
        self.server = multiprocessing.Process(
            name=self.name,
            target=subprocess.call,
            args=(self.cmd,),
            kwargs={'shell': True}
            # we need to start in a shell otherwise vim complains with error:
            # Garbage after option argument: "-u /path/to/custom/vimrc"
        )
        if not testing:
            self.server.start()
            self.check_is_running(timeout)

        return Client(self)

    def start_headless(self, timeout=5, testing=False):
        """Starts headless Vim server in a subprocess.

            vim -n --servername GOTOWORD >/dev/null 2>&1 <&1

        No input and output is connected to Vim server,
        so that you can run a unit test without a dirty log.

        testing - flag useful for tests when you don't want to start Vim server

        Returns a client connected to Vim server.
        """
        if not testing:
            self.server = subprocess.Popen(
                args=self.cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True
            )
            self.check_is_running(timeout)
        return Client(self)

    def start_in_other_terminal(self):
        """Start vim in a terminal other than the one used to run this script
        (test script) because vim will pollute the output of the test script
        and vim will malfunction.
        Returns a Client.
        We need something like:

            x-terminal-emulator -e 'sh -c "python vim_server_no_gui.py"'

        It is useful when testing a vim plugin to launch vim in other
        terminal so that the test script's output doesn't get polluted by vim.
        """
        self._format_vim_args()
        self.cmd = "x-terminal-emulator -e '%s'" % self.cmd
        # x-terminal-emulator chooses the default terminal in a cross-desktop
        # way (debian, ubuntu, mint, etc.)
        return self.start()

    def start_gvim(self):
        """Start a GUI Vim. Returns a Client()."""
        self.executable = self._get_abs_path(exe='gvim')
        # Gvim needs to be started with the -f flag so it doesn't fork and
        # kill its original process
        self.extra_args.append('-f')
        # -f seems not to work
        self._format_vim_args()
        return self.start()

    def connect(self, timeout=5):
        """Connect to a running instance of Vim server.
        Returns a client.
        Eg:

            >>> vim = Server(name="SOME_SERVER_NAME")
            >>> client = vim.connect()

        """
        self.check_is_running(timeout)
        return self.start(testing=True)
        # with testing=True we prevent Server from starting a new Vim server
        # in a subprocess

    def kill(self):
        """Kills the Vim instance started in a subprocess. Returns nothing.
        It is useless if you connected to server with connect(). In that case
        use quit() instead.

        kill() works with vim, but not with gvim.
        """
        if hasattr(self, 'server'):
            # this one is the parent of gvim: vim.server._popen.pid
            # how can I find the pid of gvim? only if I do `ps aux | grep
            # self.name`?
            #os.kill(int(self.server.pid), signal.SIGTERM)
            self.server.terminate()
        else:
            raise AttributeError("Server needs to be started first.")

    def quit(self):
        """Used to send to server the :qa! command. Useful when we connected
        to server instead of starting it in a subprocess with start().
        """
        self.remote_send(':qa!<Enter>')

    def remote_send(self, keys):
        """Sends the given keys to Vim server. A wrapper around --remote-send.

        keys - a String with a sequence of Vim-compatible keystrokes.

        Returns nothing.
        Eg:

           $ vim --servername VIMRUNNER --remote-send ':qa! <Enter>'

        """
        subprocess.call(
            [self.executable, '--servername', self.name, '--remote-send',
             keys]
        )

    def remote_expr(self, expression):
        """Evaluates an expression in the Vim server and returns the result.
        A wrapper around --remote-expr.
        Note that a command is not an expression, but a function call or a
        variable is.

        expression - a String with a Vim expression to evaluate.

        Returns the String output of the expression. Eg:

            remote_expr('&shiftwidth')

        """
        result = subprocess.check_output(
            [self.executable, '--servername', self.name, '--remote-expr',
             expression])
        return result.decode('utf-8')

    def server_list(self):
        """Retrieves a list of names of currently running Vim servers.

        Returns a List of String server names currently running.
        """
        path = subprocess.check_output([self.executable,
                                        '--serverlist'])
        path = path.decode('utf-8')
        return path.split('\n')

    def is_running(self):
        "Returns a Boolean indicating wheather server exists and is running."
        return self.name.upper() in self.server_list()

    def check_is_running(self, timeout):
        """Raises a RuntimeError exception if it can't find, during timeout,
        a Vim server with the same name as the one given at initialization
        during timeout.
        """
        while timeout:
            if self.is_running():
                break
            time.sleep(1)
            timeout -= 1
        else:
            raise RuntimeError("Could not connect to vim server before "
                               "timeout expired. Maybe you should try again.")

    @staticmethod
    def _get_abs_path(exe):
        """Uses 'which' shell command to get the absolute path of the
        executable."""
        path = subprocess.check_output(['which', "%s" % exe])
        # output from subprocess, sockets etc. is bytes even in py3, so
        # convert it to unicode
        path = path.decode('utf-8')
        return path.strip('\n')


class Client(object):
    """
    Client that has a reference to a Vim server. Useful to send keys,
    commands, expressions to manipulate Vim.
    """
    def __init__(self, server):
        self.server = server

    def type(self, keys):
        """
        Invokes one of the basic actions the Vim server supports, sending a
        key sequence. The keys are sent as-is, so it'd probably be better to
        use the wrapper methods, normal(), insert() and so on. Eg:

            >>> client.type(':ls <Enter>')

        """
        self.server.remote_send(keys)

    def command(self, cmd):
        """Send commands to a Vim server.
        Used for Vim cmds and everything except for calling functions. Eg:

            >>> client.command("ls")

        """
        output = self.eval("VimrunnerPyEvaluateCommandOutput('%s')" % cmd)
        return output
        # could have been implemented like:
        # self.type(':%s <Enter>' % cmd)

    def eval(self, expression):
        """
        Calls the server's remote_expr() method to evaluate the expression.

        Returns the String output of the expression, stripped by useless
        whitespaces. Eg:

            >>> # get the line number of the cursor
            >>> client.eval('line(".")')

        Note that Vim makes a clear distinction between ' and ".
        """
        return self.server.remote_expr(expression).strip()

    def edit(self, filename):
        """Edits the file filename with Vim.

        Note that this doesn't use the '--remote' Vim flag, it simply types
        in the command manually. This is necessary to avoid the Vim instance
        getting focus.

        filename - a String that can be a relative or absolute path

        Returns, if the file is found, a string with the name of the document
        otherwise it returns an empty string.
        Eg:

            >>> # suppose 'test' folder is in pwd:
            >>> result = client.edit('test/a-file.txt')
            >>> result
            '"test/a-file.txt" 10L, 304C'

            >>> # otherwise an absolute path is needed:
            >>> client.edit('/home/user/path_to_file/file.txt')

        """
        return self.command("edit %s" % filename)

    def feedkeys(self, keys):
        """
        Send keys as if they come from a mapping or typed by a user.
        Vim's usual remote-send functionality to send keys to a server does
        not respect mappings. As a workaround, the feedkeys() function can be
        used to more closely simulate user input.

        Example:
        We want to send 3 keys: Ctrl w p and according to Vim docs you would
        write: '<C-w>p' but these keys need to be escaped with a backslash '\':

            >>> # in Vim you would write
            >>> :call feedkeys("\<C-w>p")
            >>> # this function can be used like this:
            >>> client = Client(server)
            >>> client.feedkeys('\<C-w>p')
            >>> client.feedkeys('\<C-w>k')

        """
        #self.command('call feedkeys("%s")' % keys)
        self.eval('feedkeys("%s")' % keys)
        #self.server.remote_expr('%Q{feedkeys("%s")}' % keys)

    def source(self, script):
        """Source a script in Vim server.

        script - a filename with an absolute path.

        You can see all sourced scripts with command('script')
        """
        self.command('source %s' % script)

    def normal(self, keys=''):
        """
        Switches Vim to normal mode and types in the given keys.
        """
        #self.server.remote_send("<C-\\><C-n>%s" % keys)
        # OR
        self.type("<C-\\><C-n>%s" % keys)

    def insert(self, text):
        """
        Switches Vim to insert mode and types in the given text at current
        cursor position. Eg:

            >>> client.insert('Hello World!')

        """
        self.normal("i%s" % text)

    def search(self, text, flags='', stopline='', timeout=''):
        """
        Starts a search in Vim for the given text. The result is that the
        cursor is positioned on its first occurrence.
        For info about the rest of the args, check :help search.
        """
        #self.type('/%s<CR>' % text)
        return self.eval('search("%s", "%s", "%s", "%s")' %
                         (text, flags, stopline, timeout))

    def append_runtimepath(self, dir):
        """
        Appends a directory to Vim's runtimepath.

        dir - The directory added to the path

        Returns nothing. Eg:

            >>> client.append_runtimepath("/path/to/a/plugin/dir")

        """
        dir_path = os.path.abspath(dir)
        self.command("set runtimepath+=%s" % dir_path)

    def echo(self, expression):
        """
        Echo the expression in Vim. Eg:

            >>> # get list of directories where plugins reside
            >>> client.echo("&runtimepath")
            >>> # output color brightness
            >>> client.echo("&bg")
            >>> # echo a string in Vim
            >>> client.echo('"testing echo function with a string"')
            >>> # or double quotes need to be escaped
            >>> client.echo("\"testing echo function with a string\"")

        Returns the String output.
        """
        ## redirect message to variable local to buffer
        #self.command("redir => b:command_output")
        #self.command("silent echo %s" % expression)
        ## end redirection:
        #self.command("redir END")
        ## get value of variable from current buffer:
        #output = self.eval('getbufvar("%", "command_output")')
        ## remove variable:
        #self.command("unlet b:command_output")
        #return output
        return self.command("echo %s" % expression)

    def prepend_runtimepath(self, dir):
        """
        Prepends a directory to Vim's runtimepath. Use this instead of
        append_runtimepath() to give the directory higher priority when Vim
        runtime's a file.

        dir - The directory added to the path

        Eg:

            >>> client.prepend_runtimepath('/home/user/plugin_dir')

        """
        dir_path = os.path.abspath(dir)
        runtimepath = self.echo("&runtimepath")
        self.command("set runtimepath=%s,%s" % (dir_path, runtimepath))

    def add_plugin(self, dir, entry_script=''):
        """
        Adds a plugin to Vim's runtime. Initially, Vim is started without
        sourcing any plugins to ensure a clean state. This method can be used
        to populate the instance's environment.

        dir - The base directory of the plugin, the one that contains

            its autoload, plugin, ftplugin, etc. directories.

        entry_script - The Vim script that's runtime'd to initialize the plugin
        (optional)

        Examples:

        >>> client.add_plugin('/home/andrei/.vim/my_plugin/', 'plugin/rails.vim')

        Returns nothing.
        """
        self.append_runtimepath(dir)
        if entry_script:
            self.command("runtime %s" % entry_script)

    def read_buffer(self, lnum, end='', buf=None):
        """Reads lines from buffer with index 'buf' or, by default, from the
        current buffer in the range lnum -> end.
        Uses vim's getbufline().

        Returns one string with the lines joined with newlines '\\\\n' marking
        the end of each line.
        Eg:

            >>> one_line = client.read_buffer("1")
            >>> two_lines = client.read_buffer("1", "2")
            >>> all_lines = client.read_buffer("1", "$")
            >>> two_lines = client.read_buffer("line('$') - 1", "'$'")

        """
        if not buf:
            buf = self.get_active_buffer()
        return self.eval("getbufline(%s, %s, %s)" % (buf, lnum, end))

    def write_buffer(self, lnum, text):
        """Writes one or more lines to current buffer, starting from line
        'lnum'. Calls vim's setline() function.

        lnum - can be a number or a special character like $, '.'. etc.

        text - can be a string or a list of strings.

        Returns '0' or '1', as strings.

        Eg:

        Input is a string
          >>> client.write_buffer("2", "write to line number 2")
          >>> client.write_buffer("'$'", "write to last line")
          >>> client.write_buffer("\"$\"", "write to last line")
          >>> client.write_buffer("'$'", "['last line', 'add after last line']")
          >>> client.write_buffer("line('$') + 1", "add after last line")

        Input is a list

          >>> l = ['last line', 'add after last line']
          >>> client.write_buffer("'$'",l)

        Pay attention, simple and double quotes matter.

        """
        if type(text) == list:
            return self.eval("setline(%s, %s)" % (lnum, create_vim_list(text)))
        # text must be quoted in Vim editor:
        return self.eval("setline(%s, \"%s\")" % (lnum, text))

    def get_active_buffer(self):
        """
        Get the current (active) vim buffer. Returns a string with the buffer number.
        """
        return self.eval("winbufnr(0)")

    def quit(self):
        "Exit Vim."
        self.server.quit()


#if __name__ == '__main__':
#    vim = Server()
#
#    gvim = Server()
