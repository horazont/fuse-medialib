from storm.locals import *
from errors import *

class Directory(object):
    __storm_table__ = "directories"
    id = Int(primary = True)
    path = Unicode()
    mtime = Int()
    ctime = Int()
    lastScan = Int()
    recursively = Bool()
    followSymLinks = Bool()
