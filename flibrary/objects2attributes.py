from storm.locals import *  
from object import Object
from attribute import Attribute
from errors import *

class AssociatedAttribute(object):
    __storm_table__ = "objects2attributes"
    __storm_primary__ = "object_id", "attribute_id"
    object_id = Int()
    attribute_id = Int()
    value = Unicode()

Object._attributes = ReferenceSet(Object.id,
                                  AssociatedAttribute.object_id,
                                  AssociatedAttribute.attribute_id,
                                  Attribute.id);

class AttributeDict(object):
    def __init__(self, obj, refset):
        self.obj = obj
        self.refset = refset
        
    def _forceStore(self):
        store = Store.of(self.obj)
        if store is None:
            raise LibraryStoreError("Store needed for this operation")
        return store
        
    def _getAttributeByName(self, name, allowCreation = True):
        store = self._forceStore()
        attribs = store.find(Attribute, Attribute.name == name)
        if attribs.count() > 1:
            raise LibraryIntegrityError("Multiple attributes for one name found.")
        attrib = None
        if attribs.count() == 0 and allowCreation:
            attrib = Attribute(name)
            store.add(attrib)
        elif attribs.count() == 1:
            attrib = attribs[0]
        return attrib
        
    def _getAssociation(self, attrib, allowAddition = True):
        store = self._forceStore()
        assoc = store.get(AssociatedAttribute, (self.obj.id, attrib.id))
        if assoc is None and allowAddition:
            self.refset.add(attrib)
            assoc = store.get(AssociatedAttribute, (self.obj.id, attrib.id))
        return assoc
        
    def __getitem__(self, name):
        attrib = self._getAttributeByName(name, False)
        if attrib is None:
            return None
        assoc = self._getAssociation(attrib, False)
        return None if assoc is None else assoc.value
        
    def __setitem__(self, name, value):
        #if name in ["obj", "refset"]:
        #    object.__setattr__(self, name, value)
        #    return
        attrib = self._getAttributeByName(name, True)
        if attrib is None:
            raise AttributeError("Library attribute \"%s\" does not exist." % name)
        assoc = self._getAssociation(attrib, True)
        assoc.value = value
    
    def __contains__(self, name):
        attrib = self._getAttributeByName(name, False)
        if attrib is None:
            return False
        assoc = self._getAssociation(attrib, False)
        return assoc is not None


def _initAttributeDict(self):
    self.attributes = AttributeDict(self, self._attributes)
    
Object._initAttributeDict = _initAttributeDict
