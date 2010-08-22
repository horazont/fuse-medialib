from node import NodeContainer, NodeRegistry, NodeError
from folder import NodeFolder
from flibrary.object import Object
from storm.locals import *
from flibrary.objects2attributes import AssociatedAttribute
from flibrary.attribute import Attribute
from flibfs.fsnode import FSNodeStructureObject, FSNodeLibraryObject

class NodeFilter(NodeFolder):
    def __init__(self, parent, attrib = "class", value = None, showleafs = False, prefix = u"", **kwargs):
        NodeFolder.__init__(self, parent, **kwargs)
        self.attrib = attrib
        self.attrib_id = self._getAttributeId(attrib)
        self.value = value
        self.prefix = prefix
        self.showleafs = showleafs
        
    def addNode(self, node):
        if self.showleafs:
            raise NodeError("Cannot add child to node which will show leafs.")
        super(NodeFilter, self).addNode(node)
        
    def select(self):
        return self.filterWithParent(self.getStore().find(Object,
                    Object.id == AssociatedAttribute.object_id,
                    AssociatedAttribute.attribute_id == self.attrib_id,
                    AssociatedAttribute.value == self.value))
        
    def __iter__(self):
        if self.showleafs:
            fsnodes = []
            selection = self.select()
            for obj in selection:
                fsnodes += [FSNodeLibraryObject(obj, self.getLeafAttrib())]
            return iter(fsnodes)
        else:
            fsnodes = []
            for node in self.nodes:
                if node.expands():
                    fsnodes += [fsnode for fsnode in node]
                else:
                    fsnodes += [FSNodeStructureObject(node)]
            return iter(fsnodes)
        
    def __unicode__(self):
        return u"filtering attribute \"%s\": %s" % (self.attrib, self.value)
        
    def cloneForParent(self, newParent):
        node = NodeFolder(parent, attrib = self.attrib, value = self.value, library = self.library, leafattrib = self.leafAttrib)
        super(NodeFilter, self).initCloneForParent(node)
        return node
        
    def getName(self):
        if len(self.value) > 0:
            return self.prefix+self.value
        else:
            return self.prefix+u"< Untagged >"

NodeRegistry["filter"] = NodeFilter


