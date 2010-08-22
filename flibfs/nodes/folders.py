from node import NodeContainer, NodeRegistry, NodeError
from filter import NodeFilter
from flibrary.attribute import Attribute
from flibrary.object import Object
from flibrary.objects2attributes import AssociatedAttribute
from storm.store import ResultSet
from flibfs.fsnode import FSNodeStructureObject
import copy

class NodeFolders(NodeContainer):
    def __init__(self, parent, attrib=None, prefix=u"", showleafs=False, **kwargs):
        NodeContainer.__init__(self, parent, **kwargs)
        self.attrib = attrib
        self.attrib_id = self._getAttributeId(self.attrib)
        self.prefix = prefix
        self.showleafs = showleafs
        self.expansion = None
        
    def addNode(self, node):
        if self.showleafs:
            raise NodeError("Cannot add child to node which will show leafs.")
        super(NodeFolders, self).addNode(node)
        
    def expands(self):
        return True
        
    def getExpansion(self):
        if self.expansion is not None:
            return self.expansion
        self.expansion = []
        preselection = self.select()
        store = self.getStore()
        selection = store.find(AssociatedAttribute,
            AssociatedAttribute.object_id.is_in(preselection.values(Object.id)),
            AssociatedAttribute.attribute_id == self.attrib_id).config(distinct = True).values(AssociatedAttribute.value);
        for attribValue in selection:
            newNode = NodeFilter(self, self.attrib, attribValue, showleafs = self.showleafs, prefix = self.prefix)
            newNode.nodes = [subnode.cloneForParent(newNode) for subnode in self.nodes]
            self.expansion += [newNode]
        return self.expansion
        
    def __iter__(self):
        return iter([FSNodeStructureObject(node) for node in self.getExpansion()])
        
    def cloneForParent(self, newParent):
        node = NodeFolders(newParent, attrib = self.attrib, prefix = self.prefix, showleafs = self.showleafs, library = self.library, leafattrib = self.leafAttrib)
        super(NodeFolders, self).initCloneForParent(node)
        return node

NodeRegistry["folders"] = NodeFolders


