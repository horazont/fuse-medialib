from storm.locals import *
from errors import *

class Object(object):
    __storm_table__ = "objects"
    id = Int(primary = True)
    realFileName = Unicode()
    mtime = Int()
    ctime = Int()
    lastScan = Int()
    attributes = None
    
    def __new__(cls):
        instance = super(Object, cls).__new__(cls)
        Object._initAttributeDict(instance)
        return instance
    
    def __getitem__(self, name):
        if self.attributes is None:
            Object._initAttributeDict(self)
        return self.attributes[name]
    
    def __setitem__(self, name, value):
        if self.attributes is None:
            Object._initAttributeDict(self)
        self.attributes[name] = value
        
    def __contains__(self, name):
        if self.attributes is None:
            Object._initAttributeDict(self)
        return name in self.attributes
