from flibrary.attribute import Attribute
from storm.store import ResultSet
from flibrary.object import Object

class NodeError(Exception):
    pass

class Node(object):
    def __init__(self, parent, library=None, leafattrib=None):
        self.parent = parent
        self.library = library
        self.objectIdCache = None
        self.leafAttrib = leafattrib
        
    def _getAttributeId(self, name):
        store = self.getStore()
        attribSelect = store.find(Attribute, Attribute.name == name)
        if attribSelect.count() == 0:
            raise NodeError("Attribute not found or duplicated: %s" % name)
        return attribSelect[0].id
    
    def addNode(self, node):
        raise NodeError("Cannot add a node here.")
        
    def getLeafAttrib(self):
        if self.leafAttrib is not None:
            return self.leafAttrib
        elif self.parent is not None:
            return self.parent.getLeafAttrib()
        else:
            return u"generic/title"
        
    def getStore(self):
        if self.parent == None:
            if self.library == None:
                raise NodeError("Root node has no library assigned")
            return self.library.store
        else:
            return self.parent.getStore()
    
    def getFindable(self):
        if self.parent == None:
            if self.library == None:
                raise NodeError("Root node has no library assigned")
            return self.library.store
        else:
            return self.parent.select()
    
    def getObjectIds(self):
        if self.objectIdCache == None:
            selection = self.select()
            if isinstance(selection, ResultSet):
                self.objectIdCache = list(self.select().values(Object.id))
            else:
                return None
        return self.objectIdCache
    
    def filterWithParent(self, results):
        if self.parent == None:
            return results
        else:
            parentIdList = self.parent.getObjectIds()
            if parentIdList is not None:
                return results.find(Object.id.is_in(parentIdList))
            else:
                return results
        
    def select(self):
        return self.getFindable()
        
    def __iter__(self):
        return self.select();
        
    def __unicode__(self):
        return unicode(self.__class__.__name__)
        
    def expands(self):
        return False
        
    def cloneForParent(self, newParent):
        node = Node(newParent, library = self.library, leafattrib = self.leafAttrib)
    
    def initCloneForParent(self, node):
        pass
        
class NodeContainer(Node):
    def __init__(self, parent, **kwargs):
        Node.__init__(self, parent, **kwargs)
        self.nodes = []
    
    def addNode(self, node):
        self.nodes += [node]
        
    def __unicode__(self):
        s = u""
        for node in self.nodes:
            s += unicode(node)+", "
        if not s == u"":
            s = s[:-2]
        return unicode(self.__class__.__name__)+"("+s+")"
        
    def cloneForParent(self, newParent):
        node = NodeContainer(parent, library = self.library, leafattrib = self.leafAttrib)
        self.initCloneForParent(self, node)
        return node
        
    def initCloneForParent(self, node):
        for subnode in self.nodes:
            node.addNode(subnode.cloneForParent(node))

NodeRegistry = {}
