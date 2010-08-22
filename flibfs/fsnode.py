from flibrary.object import Object
import stat
import os
from fuse import Direntry

_uid = os.getuid()
_gid = os.getgid()
_statumask = os.umask(0)
os.umask(_statumask)
# invert it
_statumask = (stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO) - _statumask

class FSNodeError(Exception):
    pass

class FSNode(object):
    def __init__(self):
        self.parent = None
    
    def getStat(self):
        raise FSNodeError("getStat not implemented")
        
    def isLeaf(self):
        raise FSNodeError("isLeaf not implemented")
        
    def getName(self):
        raise FSNodeError("getName not implemented")
        
    def getDir(self):
        raise FSNodeError("getDir not implemented")
        
    def readLink(self):
        raise FSNodeError("readLink not implemented")
        
    def toDirentry(self):
        raise FSNodeError("toDirentry not implemented")
        
class FSNonLeafNode(FSNode):
    def __init__(self):
        FSNode.__init__(self)
        self.nodes =  []
    
    def addChild(self, node):
        if node in self.nodes:
            return
        self.nodes += [node]
        node.parent = self
        
    def removeChild(self, node):
        if not node in self.nodes:
            return
        del self.nodes[self.nodes.index(node)]
    
    def isLeaf(self):
        return False
        
    def __iter__(self):
        return list(self.nodes)
    

class FSNodeLibraryObject(FSNode):
    def __init__(self, obj, nameFormat):
        FSNode.__init__(self)
        self.obj = obj
        self.objstat = None
        if isinstance(nameFormat, basestring):
            self.name = self.obj[nameFormat]
        else:
            args = tuple([self.obj[arg] if arg in self.obj else "" for arg in nameFormat[1]])
            self.name = nameFormat[0] % args
        
    def isLeaf(self):
        return True
        
    def getStat(self):
        if self.objstat is None:
            self.objstat = os.stat(self.obj.realFileName)
        return {
            "st_mode": (stat.S_IFLNK + stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO),
            "st_ino": self.obj.id,
            "st_dev": 0,
            "st_nlink": 1,
            "st_uid": _uid,
            "st_gid": _gid,
            "st_size": len(self.obj.realFileName),
            "st_atime": self.objstat.st_atime,
            "st_mtime": self.objstat.st_mtime,
            "st_ctime": self.objstat.st_ctime
        }
        
    def readLink(self):
        return self.obj.realFileName
        
    def getName(self):
        return self.name
        
    def toDirentry(self):
        return Direntry(self.getName().encode("utf-8"))

class FSNodeStructureObject(FSNonLeafNode):
    def __init__(self, node):
        FSNonLeafNode.__init__(self)
        self.node = node
        
    def prepareIterator(self):
        for fsnode in self.node:
            self.addChild(fsnode)
        
    def __iter__(self):
        if len(self.nodes) == 0:
            self.prepareIterator()
        return iter(self.nodes)
        
    def invalidate(self):
        self.nodes = []
        
    def __unicode__(self):
        return u"Folder "+unicode(self.node)
        
    def getName(self):
        return self.node.getName()
    
    def getStat(self):
        return {
            "st_mode": (stat.S_IFDIR + _statumask),
            "st_ino": 1234,
            "st_dev": 1234,
            "st_nlink": 1,
            "st_uid": _uid,
            "st_gid": _gid,
            "st_size": 1234,
            "st_atime": 1234,
            "st_mtime": 1234,
            "st_ctime": 1234
        }
        
    def getDir(self):
        result = [
            Direntry('.'), 
            Direntry('..')
        ]
        for file in self:
            result += [file.toDirentry()]
        return result
        
    def toDirentry(self):
        return Direntry(self.getName().encode("utf-8"))
