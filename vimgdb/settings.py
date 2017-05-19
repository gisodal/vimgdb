
class settings():
    debug = False

    major = 1
    minor = 2
    micro = 1

    def Version():
        return "{0}.{1}.{2}".format(major,minor,micro)

