from node import Node, NodeRegistry
from flibfs.fsnode import FSNodeLibraryObject

class NodeLeafFolder(Node):
    def __init__(self, parent, name = None, **kwargs):
        Node.__init__(self, parent, **kwargs)
        self.name = name
    
    def __iter__(self):
        fsnodes = []
        selection = self.select()
        for obj in selection:
            fsnodes += [FSNodeLibraryObject(obj, self.getLeafAttrib())]
        return iter(fsnodes)
        
    def __unicode__(self):
        return u"showing all objects in current selection" % (self.attrib, self.value)
        
    def cloneForParent(self, newParent):
        node = NodeLeafFolder(newParent, name = self.name, library = self.library, leafattrib = self.leafAttrib, nameformat = self.nameFormat, nameargs = self.nameArgs)
        super(NodeLeafFolder, self).initCloneForParent(node)
        return node
        
    def getName(self):
        return self.name

NodeRegistry["leaffolder"] = NodeLeafFolder
