from .settings import settings

def Version():
    return "{0}.{1}.{2}".format(
            settings.major,
            settings.minor,
            settings.micro)

