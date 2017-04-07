
class Gdb:

    def Start(self):
        import os
        from subprocess import call
        library_dir = os.path.abspath(os.path.dirname(__file__))
        gdbinit = os.path.join(library_dir, 'config/gdbinit')
        cmd = "gdb -n -iex 'source {0}'".format(gdbinit)
        call(cmd, shell=True)

