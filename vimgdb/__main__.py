from __future__ import print_function
from .vimgdb import Vimgdb
import sys

try:
    vimgdb = Vimgdb()
    if "--version" in sys.argv:
        print("Version {0}".format(vimgdb.Version()))
    else:
        if not vimgdb.Running():
            vimgdb.StartVim(sys.argv[1:])
        else:
            vimgdb.StartGdb(sys.argv[1:])

except Exception as error:
    print(traceback.format_exc())
    print(str(error))
    sys.exit(1)

