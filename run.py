#!/usr/bin/env python3

from vimgdb import Vimgdb
from vimgdb import Gdb

server = Vimgdb()
if not server.IsRunning():
    server.Start()
else:
    gdb = Gdb()
    gdb.Start()
    #server.Connect()
    #server.Test()
