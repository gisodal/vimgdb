from vimgdb import Vimgdb

server = Vimgdb()
if not server.IsRunning():
    server.Start()
else:
    server.Connect()
    server.Test()

