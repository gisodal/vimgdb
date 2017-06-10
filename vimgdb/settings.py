
class settings():
    debug = False

    major = 1
    minor = 3
    micro = 2

    def Version():
        return "{0}.{1}.{2}".format(major,minor,micro)

