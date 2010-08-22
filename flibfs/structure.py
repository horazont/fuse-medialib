import xml.sax
from xml.sax.handler import ContentHandler
from nodes.nodes import *
from flibfs.fsnode import FSNodeStructureObject

def findName(iterable, value):
    encodedValue = value
    if not isinstance(encodedValue, unicode):
        encodedValue = unicode(value, "utf-8")
    for item in iterable:
        if item.getName() == encodedValue:
            return item
    return None

class StructureReader(ContentHandler):
    def __init__(self, library):
        self.nodeTree = None
        self.context = None
        self.library = library
        
    def startElement(self, name, attrs):
        items = attrs.items()
        attrMap = {}
        for (key, value) in items:
            attrMap[str(key)] = value
        NodeClass = NodeRegistry[name]
        print NodeClass
        newNode = NodeClass(self.context, library = self.library, **attrMap)
        if self.context == None:
            self.nodeTree = newNode
        else: 
            self.context.addNode(newNode)
        self.context = newNode
        
    def endElement(self, name):
        self.context = self.context.parent

class Structure(object):
    def __init__(self, structureFile, library):
        handler = StructureReader(library)
        xml.sax.parse(structureFile, handler)
        self.nodeTree = handler.nodeTree
        self.fsRoot = FSNodeStructureObject(self.nodeTree)
        self.nodeCache = {}
        
    def __unicode__(self):
        return unicode(self.nodeTree)
        
    def invalidateCache(self):
        self.nodeCache = {}
        
        
    def __getitem__(self, name):
        if name in self.nodeCache:
            return self.nodeCache[name]
        context = self.fsRoot
        if isinstance(name, basestring):
            if len(name) > 0:
                raise AttributeError("Invalid root")
            else:
                return context
        for pathNode in name:
            if len(pathNode) == 0:
                continue
            context = findName(context, pathNode)
            if context is None:
                raise AttributeError("File not found")
        self.nodeCache[name] = context
        return context
