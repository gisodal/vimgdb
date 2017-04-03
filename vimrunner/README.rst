Vimrunner
======================================================================

Module that implements a client and server interface useful for controlling a 
Vim editor, started as a server, programmatically. This module could be used 
for unit testing or integration testing for a Vim plugin written in Python. 
Or you can use it to interactively control a Vim editor by python code, for 
example, in an Ipython session.

How it all started
======================================================================

I created a class that used the `vim python module
<http://vimdoc.sourceforge.net/htmldoc/if_pyth.html#python-vim>`_
to emulate a vim buffer and that would act like a list, so you could read and 
write lines and manipulate text using python.

However, I stumbled across 
`Vimrunner <https://github.com/AndrewRadev/vimrunner>`_
which is a Ruby gem used to "spawn a Vim instance and control it 
programatically."

So, this python module is heavily inspired by the project mentioned above. 

Installation
======================================================================

There is a `vimrunner package <https://pypi.python.org/pypi/vimrunner/>`_  on 
PyPI, so you can install it with:

    pip install vimrunner

Alternatively, you can just drop vimrunner.py file into your project - it is 
self-contained.

Testing
======================================================================

You can run unit tests using the command:

    python setup.py test

Usage
======================================================================

.. code:: python

    import vimrunner
    
    # initialize vim server
    vim = vimrunner.Server()
    
    # start GVIM as server and get a client connected to it
    client = vim.start_gvim()
    client.edit('any_file')
    client.source('path/to/vim/plugin')
    
    # start Vim editor in a terminal; it should work for Debian, Ubuntu, etc.
    # that have a desktop installed
    client = vim.start_in_other_terminal()

Documentation is available at `<http://andri-ch.readthedocs.org/en/latest/>`_

For any suggestions regarding the module and its documentation, please submit 
an issue using `GitHub issue tracker
<https://github.com/andri-ch/vimrunner-python/issues>`_

