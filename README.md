# Vimgdb

Use vim to visually step through source code with GNU Gdb.

<br>

<p align="center">
  <img style="max-width: 100%;" src="https://raw.githubusercontent.com/gisodal/vimgdb/figures/demo.gif?token=AKPkVf08cJWjnufUHu_1LHwexig4ct77ks5ZBkymwA%3D%3D" />
</p>


## Synopsis

[GNU gdb](https://www.gnu.org/software/gdb/)  is a great tool to debug your code. Many programmers develop their code using the terminal editor [Vim](http://www.vim.org/), yet have to leave their beloved (often finely tuned) editor in order to start debugging efforts, because terminal options to visually step through code are limited to the gdb [TUI](ftp://ftp.gnu.org/old-gnu/Manuals/gdb/html_chapter/gdb_19.html) or [cgdb](https://cgdb.github.io/). Vimgdb solves this, by connecting gdb to your editing session in Vim.

Note: The example demonstrates Vimgdb while using [Tmux](https://tmux.github.io/), which allows the fast creation and navigation of vertical and horizontal terminal splits. Using it allows Vim and gdb to be opened side by side.

## Installation

Vimgdb can be run from its source directory, but requires installation to be run from anywhere:

    > python setup.py install


## Usage

Start Vim:

    > python -m vimgdb

From a different terminal, start gdb:

    > python -m vimgdb [path/to/debug/binary]


## How it works

Vimgdb starts Vim as a server such that gdb can connect to it. Gdb is started upon the next call to Vimgdb if it is confirmed that the Vim server is running. Information about the current line of execution is passed from gdb to Vim upon triggering a hook, e.g., hitting a breakpoint, stepping though code, moving up and down the call stack, etc. The corresponding file will be opened in Vim, breakpoints and current  highlighted

## What it does not do

Be aware that Vim needs to be able to execute the commands it receives. For instance, if you edit a file without saving, Vim prohibits changing to a different file. This will obviously distrub stepping through code.

