from storm.locals import *

class Attribute(object):
    __storm_table__ = "attributes"
    id = Int(primary = True)
    name = Unicode()
  
    def __init__(self, name):
        self.name = unicode(name)
