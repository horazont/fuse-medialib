from node import NodeContainer, NodeRegistry
from flibfs.fsnode import FSNodeStructureObject

class NodeFolder(NodeContainer):
    def __init__(self, parent, name = None, **kwargs):
        NodeContainer.__init__(self, parent, **kwargs)
        self.name = name
        
    def __iter__(self):
        fsnodes = []
        for node in self.nodes:
            if node.expands():
                fsnodes += [fsnode for fsnode in node]
            else:
                fsnodes += [FSNodeStructureObject(node)]
        return iter(fsnodes)
        
    def getName(self):
        return self.name
        
    def __unicode__(self):
        return u"\""+self.name+"\""
        
    def cloneForParent(self, newParent):
        node = NodeFolder(newParent, name = self.name, library = self.library, leafattrib = self.leafAttrib, nameformat = self.nameFormat, nameargs = self.nameArgs)
        super(NodeFolder, self).initCloneForParent(node)
        return node

NodeRegistry["folder"] = NodeFolder
