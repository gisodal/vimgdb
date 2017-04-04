
class Gdb:

    def Start(self):
        import os
        from subprocess import call
        gdbinit = os.path.join(os.path.dirname(__file__), "gdbinit")
        cmd = "gdb -iex 'source {0}'".format(gdbinit)
        call(cmd, shell=True)

