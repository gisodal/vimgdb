
class Gdb:

    def Start(self):
        import os
        from subprocess import run
        gdbinit = os.path.join(os.path.dirname(__file__), "gdbinit")
        gdb_loadinit = "gdb -iex 'source {0}'".format(gdbinit)
        run(["gdb",gdb_loadinit])

