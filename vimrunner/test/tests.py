#!/usr/bin/python

"""For good test results, navigate to 'test' directory. Otherwise it won't
find the test file:
$: cd test
Run it:
$: ./tests.py
"""


import sys
import os.path
import unittest
import subprocess
import time

# insert the directory containing the directory with this file in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#import vimrunner
from vimrunner import Server


class TestServerInit(unittest.TestCase):
    """Tests the __init__() of vimrunner.Server() class."""
    def setUp(self):
        pass

    def test_name_no_args_supplied(self):
        vim = Server()
        self.assertTrue('VIMRUNNER#' in vim.name)

    def test_name_when_name_supplied(self):
        vim = Server(name='server')
        self.assertEqual('server', vim.name)

    def test_name_when_two_servers(self):
        vim_1 = Server()
        vim_2 = Server()
        self.assertNotEqual(vim_1.name, vim_2.name)

    def test_executable_when_default(self):
        vim = Server()
        self.assertEqual(vim.executable,
                         subprocess.check_output(['which', 'vim']).decode(
                             'utf-8').strip('\n'))

    def test_executable_when_given_as_arg(self):
        vim = Server(executable='/usr/local/bin/vim')
        self.assertEqual('/usr/local/bin/vim', vim.executable)

    def test_executable_when_gvim(self):
        vim = Server(executable='gvim')
        gvim_path = subprocess.check_output(['which', 'gvim'])
        gvim_path = gvim_path.decode('utf-8').strip('\n')
        try:
            self.assertEqual(vim.executable, gvim_path)
        except subprocess.CalledProcessError:
            return "gvim might not be installed at all."

    def test_get_abs_path(self):
        path = Server._get_abs_path(exe='gvim')
        gvim_path = subprocess.check_output(['which', 'gvim'])
        gvim_path = gvim_path.decode('utf-8').strip('\n')
        self.assertEqual(path, gvim_path)

    def test_vimrc_when_default(self):
        """In this case we don't want any user vimrc file."""
        vim = Server()
        self.assertNotEqual('', vim.vimrc)

    def test_noplugin_when_default(self):
        """In this case we don't want any user vimrc file."""
        vim = Server(vimrc="NONE")
        self.assertEqual('--noplugin', vim.noplugin)


class TestServer(unittest.TestCase):
    """
    Tests the other functions of Server class. Some functions are only
    appropriate for functional tests.
    """
    def setUp(self):
        self.vim = Server()

    def tearDown(self):
        try:
            # not all tests start a vim server
            self.vim.kill()
        except AttributeError:
            # no vim server was started in this test case
            pass

    def test_start_creates_server(self):
        try:
            # these try:except have increased by 4 times the testing time
            # because of timeout....
            self.vim.start(testing=True, timeout=5)
        except RuntimeError:
            # raised because timeout expires - no server exists, because
            # we're testing
            pass
        # .start() creates a runtime attribute: server
        self.assertTrue(hasattr(self.vim, 'server'))

    def test_server_arguments(self):
        "Test the default arguments that are sent to multiprocessing.Process."
        try:
            self.vim.start(testing=True)
        except RuntimeError:
            # raised because timeout expires - no server exists, because
            # we're testing
            pass
        self.assertTrue('/usr/bin/vim' in self.vim.server._args[0])
        self.assertTrue('-n' in self.vim.server._args[0])
        self.assertTrue('--noplugin' in self.vim.server._args[0])
        self.assertTrue('--servername' in self.vim.server._args[0])
        # server._args is a tuple which needs unpacking to get a list

    def test_start_headless(self):
        try:
            self.vim.start_headless(testing=False, timeout=5)
        except RuntimeError:
            return
        self.assertTrue(self.vim.is_running())
        self.vim.quit()
        self.assertFalse(self.vim.is_running())

    def test_start_gvim(self):
        #self.vim.start(testing=True)
        # this test might pass or not, depending if the user has gvim installed
        try:
            path = subprocess.check_output(['which', 'gvim'])
            path = path.decode('utf-8').strip('\n')
        except subprocess.CalledProcessError:
            return unittest.skip("gvim might not be installed, so this test "
                                 "won't pass")
        # TODO: self.vim.start_gvim()

    def test_kill_called_before_start(self):
        """Can't kill server because it is created after .start() is called.
        """
        self.assertRaises(AttributeError, self.vim.kill)

    def test_server_list_is_empty(self):
        # server is not started yet
        self.assertEqual([''], self.vim.server_list())

    def test_is_running_when_no_server_exists(self):
        self.assertFalse(self.vim.is_running())

    def test_is_running_when_server_exists(self):
        "This test also tests when vim is started in other terminal"
        #self.vim.start()
        self.vim.start_in_other_terminal()
        self.assertTrue(self.vim.is_running())
        time.sleep(2)
        self.vim.quit()
        pass

    def test_start(self):
        #self.vim.start()
        pass


class TestServerFunctionalTests(unittest.TestCase):
    """
    For now we mix unit tests and functional tests in same module because
    the codebase is small. Later on funtional tests will have a file of
    their own.

    Functional tests should be done with gvim, because vim messes up you
    terminal so that you need to reset it.
    """
    def setUp(self):
        self.vim = Server()
        #self.client = self.vim.start()
        #self.client = self.vim.start_in_other_terminal()
        #self.client = self.vim.start_gvim()

    def tearDown(self):
        self.client.quit()
        pass

    def test_basic_interaction(self):
        #self.client = self.vim.start()
        self.client = self.vim.start_in_other_terminal()
        #self.client = self.vim.start_gvim()
        #self.client = self.vim.start_headless()

        client = self.client

        # test server functions work alright:
        self.vim.remote_send(':ls! <Enter>')
        time.sleep(1)
        # user presses Enter key to continue, but not in vim ex mode:
        self.vim.remote_send('<Enter>')
        #active_buffer = self.vim.remote_expr("winbufnr(0)")
        # what about active_buffer?!
        client.command("ls")
        time.sleep(1)
        client.command("<Enter>")
        # edit non existing file (creates a new empty one)
        res = client.edit('client_new_test_file')
        self.assertEqual('', res)

        # edit existing file
        # case when test file is run with $PWD as its parent dir with:
        # $: py.test ./tests.py
        res = client.edit('ft_test_text')
        if not res:
            # case when test file is run with $PWD as parent of 'test' dir:
            # $: py.test test/tests.py
            # OR
            # $: python setup.py test
            res = client.edit('test/ft_test_text')
        self.assertTrue('ft_test_text' in res)

        # test search for a word, line number is returned else '0'
        out = client.search('test', 'w')
        self.assertNotEqual('0', out)
        out = client.search('inexistent', 'w')
        self.assertEqual('0', out)

        # test we can put Vim in normal mode & normal mode cmds work
        client.normal('gg')
        # gg -> go to top of buffer (file)

        # test we're at the bottom of buffer
        client.normal('G')
        # G -> go to bottom of buffer
        # get the line number of the cursor
        l = client.eval('line(".")')
        # get last line number of the buffer
        last_line = client.eval('line("$")')
        self.assertEqual(last_line, l)

        # put client back in insert mode
        client.insert("TEXT TO TEST INSERT")
        client.normal('<ESC>')

        # test feedkeys by visually selecting a word
        #client.command('map <space> viw')
        #client.feedkeys('\<Enter>')
        #client.normal('b')
        #client.normal('<space>')

        # test echo()
        # get value of bg (background) variable
        out = client.echo("&bg")
        # by default it is 'light'
        self.assertEqual('light', out)
        out = client.echo("\"testing echo function\"")
        self.assertEqual('testing echo function', out)
        out = client.echo('"testing echo function"')
        self.assertEqual('testing echo function', out)

        # test prepend_runtimepath
        client.prepend_runtimepath('/home')
        runtimepath = client.echo("&runtimepath")
        self.assertEqual('/home', runtimepath.split(",")[0])

        # test read_buffer
        one_line = client.read_buffer("6")
        self.assertEqual('sixth line is the same', one_line)
        two_lines = client.read_buffer("6", "7")
        self.assertEqual("sixth line is the same\nseventh line is fun!!", two_lines)

        # test write_buffer
        client.write_buffer("3", "write to line number 3")
        self.assertEqual("write to line number 3", client.read_buffer("3"))
        client.write_buffer("'$'", ['last line', 'add after last line'])
        time.sleep(0.5)
        self.assertEqual("last line\nadd after last line", client.read_buffer("line('$') - 1", "'$'"))

        client.write_buffer("line('$') + 1", "add after last line 2")
        self.assertEqual("add after last line 2", client.read_buffer("'$'"))

if __name__ == '__main__':
    unittest.main()
