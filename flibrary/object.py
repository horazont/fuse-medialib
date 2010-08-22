from storm.locals import *
from errors import *

class Object(object):
    __storm_table__ = "objects"
    id = Int(primary = True)
    realFileName = Unicode()
    mtime = Int()
    atime = Int()
    ctime = Int()
    attributes = None
  
    def __init__(self, realFileName):
        self.realFileName = unicode(realFileName)
        # This is to be set later ...
        Object._initAttributeDict(self)
    
    def __getitem__(self, name):
        if self.attributes is None:
            Object._initAttributeDict(self)
        return self.attributes[name]
    
    def __setitem__(self, name, value):
        if self.attributes is None:
            Object._initAttributeDict(self)
        self.attributes[name] = value
