from storm.locals import *
from flibrary.attribute import Attribute
from flibrary.objects2attributes import AssociatedAttribute
from flibfs.errors import *
from flibrary.object import Object
import re
from flibfs.formatting import buildFormattingChain, resolveFormatting
from fuse import Stat, Direntry
import os
import stat

FSNODE_FOLDER = 0
FSNODE_FILE = 1
FSNODE_GENERATOR = 2 # generates folder nodes for 

FSFILTER_EXACT = 0
FSFILTER_STARTS_WITH = 1
FSFILTER_ENDS_WITH = 2
FSFILTER_CONTAINS = 3
FSFILTER_LIKE = 4
FSFILTER_REGEX = 5
FSFILTER_GENERATOR = 6

FSNODE_ATTRIB_DISPLAY_NAME_FORMAT = 0

UNTAGGED_NAME = u"< untagged >"

STAT_UMASK = os.umask(0)
os.umask(STAT_UMASK)

STAT_UMASK = (~STAT_UMASK) & (stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

class Filesystem(object):
    __storm_table__ = "filesystems"
    id = Int(primary = True)
    refName = Unicode()
    
    def __storm_loaded__(self):
        self.store = Store.of(self)
        
    def __init__(self, store):
        self.store = store
    
    def getRootDir(self):
        store = Store.of(self)
        rootDir = store.find(FSNode, FSNode.fs_id == self.id, FSNode.parent_id == 0).any()
        if rootDir is None:
            rootDir = FSNode()
            rootDir.fs_id = self.id
            rootDir.parent_id = 0
            rootDir.displayName = u""
            rootDir.fullPath = u""
            rootDir.kind = FSNODE_FOLDER
            rootDir.hidden = False
            rootDir.showLeafs = False
            rootDir.relative = 0
            store.add(rootDir)
        return rootDir
        
    def getNode(self, path):
        node = self.store.find(FSNode, FSNode.fullPath == path).any()
        return node
    
class FSFilter(object):
    __storm_table__ = "fsfilter"
    id = Int(primary = True)
    attribute_id = Int()
    attribute = Reference(attribute_id, Attribute.id)
    kind = Int()
    value = Unicode()
    
    def _escape(self, s):
        return s.replace(u"'", u"\\'").replace(u'"', u'\\"')
    
    def getStormFilter(self):
        if self.kind == FSFILTER_EXACT:
            return [AssociatedAttribute.attribute_id == self.attribute_id, AssociatedAttribute.value == self.value]
        elif self.kind == FSFILTER_STARTS_WITH:
            return [AssociatedAttribute.attribute_id == self.attribute_id, AssociatedAttribute.value.like(self.value+u'%')]
        elif self.kind == FSFILTER_ENDS_WITH:
            return [AssociatedAttribute.attribute_id == self.attribute_id, AssociatedAttribute.value.like(u'%'+self.value)]
        elif self.kind == FSFILTER_CONTAINS:
            return [AssociatedAttribute.attribute_id == self.attribute_id, AssociatedAttribute.value.like(u'%'+self.value+u'%')]
        elif self.kind == FSFILTER_LIKE:
            return [AssociatedAttribute.attribute_id == self.attribute_id, AssociatedAttribute.value.like(self.value)]
        elif self.kind == FSFILTER_GENERATOR:
            return []
        else:
            raise FLibFSError("Invalid filter kind")
            
    @staticmethod
    def findFilter(store, attribute_id, kind, value):
        filter = store.find(FSFilter, FSFilter.attribute_id == attribute_id, FSFilter.kind == kind, FSFilter.value == value).any()
        if filter is None:
            filter = FSFilter()
            filter.attribute_id = attribute_id
            filter.kind = kind
            filter.value = value
            store.add(filter)
        return filter

class FSNode(object):
    __storm_table__ = "fsnode"
    
    id = Int(primary = True)
    fs_id = Int()
    fs = Reference(fs_id, Filesystem.id)
    parent_id = Int()
    parent = Reference(parent_id, id)
    children = ReferenceSet(id, parent_id)
    displayName = Unicode()
    fullPath = Unicode()
    kind = Int()
    hidden = Bool()
    showLeafs = Bool()
    relative = Int()
    size = Int()
    atime = Int()
    mtime = Int()
    ctime = Int()
    
    def __init__(self):
        self._cachedSelection = None
        self.wasRebuilt = False
    
    def __storm_loaded__(self):
        self._cachedSelection = None
        self.wasRebuilt = False
    
    def hasNode(self, displayName):
        return Store.of(self).find(FSNode, FSNode.parent_id == self.id, FSNode.displayName == displayName, FSNode.kind != FSNODE_GENERATOR).count() != 0
    
    def createDirectory(self, displayName, asGenerator = False, hidden = False, showLeafs = False, size = None, atime = None, mtime = None, ctime = None, relative = None):
        if not asGenerator and (len(displayName) == 0 or self.hasNode(displayName)):
            raise FLibFSValidityError("Duplicate or empty display name (%s)." % displayName)
        obj = FSNode()
        obj.fs = self.fs
        obj.parent_id = self.id
        obj.displayName = displayName
        obj.fullPath = self.fullPath + "/" + displayName
        if asGenerator:
            obj.kind = FSNODE_GENERATOR
            obj.hidden = True
        else:
            obj.kind = FSNODE_FOLDER
            obj.hidden = hidden
        obj.showLeafs = showLeafs
        if size is not None:
            obj.size = size
        if atime is not None:
            obj.atime = atime
        if mtime is not None:
            obj.mtime = mtime
        if ctime is not None:
            obj.ctime = ctime
        if relative is not None:
            obj.relative = relative
        return obj
        
    def createFile(self, libObj, displayName):
        obj = FSNode()
        obj.fs = self.fs
        obj.parent = self
        obj.displayName = displayName
        obj.fullPath = self.fullPath + "/" + displayName
        obj.kind = FSNODE_FILE
        obj.showLeafs = False
        obj.hidden = False
        obj.size = len(libObj.realFileName)
        obj.relative = libObj.id
        return obj
        
    def delete(self):
        store = Store.of(self)
        children = list(self.children) # store it as it will change during this operation
        for child in children:
            child.delete()
        self.filters.clear()
        store.remove(self)
        
    def cloneTo(self, newParent):
        if self.kind == FSNODE_FILE:
            raise FLibFSError("Cannot clone a file")
        newNode = newParent.createDirectory(self.displayName, self.kind == FSNODE_GENERATOR, self.hidden, self.showLeafs)
        for child in self.children:
            child.cloneTo(newNode)
        for filter in self.filters:
            newNode.filters.add(filter)
            
    def inheritingAttribute(self, attribute_id):
        for attrib in self.attributes:
            if attrib.attribute_id == attribute_id:
                return attrib.value
        if self.parent is not None:
            return self.parent.inheritingAttribute(attribute_id)
        else:
            return None
    
    def getFilters(self):
        if self.parent is not None:
            filters = self.parent.getFilters()
        else:
            filters = []
        for filter in self.filters:
            filters += [filter.getStormFilter()]
        return filters
        
    def cachedSelection(self):
        if self._cachedSelection is None:
            if self.parent is not None:
                previousSelection = self.parent.cachedSelection()
            else:
                previousSelection = None
            filters = self.getFilters()
            store = Store.of(self)
            for filter in filters:
                if previousSelection is not None:
                    filters = [Object.id.is_in(previousSelection.values(Object.id)), Object.id == AssociatedAttribute.object_id] + filter
                else:
                    filters = [Object.id == AssociatedAttribute.object_id] + filter
                previousSelection = store.find(Object, *filters)
            return previousSelection
        else:
            return self._cachedSelection
            
    def invalidateSelectionCache(self):
        self._cachedSelection = None
        
    def _buildAsFolder(self):
        store = Store.of(self)
        # Rebuild the generators first as they may create new children
        for generator in store.find(FSNode, FSNode.parent_id == self.id, FSNode.kind == FSNODE_GENERATOR):
            generator.rebuild()
        for child in self.children:
            child.rebuild()
        if not self.showLeafs:
            return
        
        selection = self.cachedSelection()
        
        formattingChain = buildFormattingChain(self.inheritingAttribute(FSNODE_ATTRIB_DISPLAY_NAME_FORMAT))
        for obj in selection:
            self.createFile(obj, resolveFormatting(formattingChain, obj))
    
    def _buildAsGenerator(self):
        store = Store.of(self)
        generatedList = store.find(FSNode, FSNode.kind == FSNODE_FOLDER, FSNode.relative == self.id)
        for generated in generatedList:
            generated.delete()
        if self.filters.count() != 1:
            raise FLibFSValidityError("A generator must have exactly one filter (%d found)" % self.filters.count())
        attribId = self.filters.any().attribute_id
        
        if self.parent is not None:
            selection = self.parent.cachedSelection()
        else:
            selection = None
        if selection is None:
            filters = [AssociatedAttribute.attribute_id == attribId]
        else:
            filters = [AssociatedAttribute.object_id.is_in(selection.values(Object.id)), AssociatedAttribute.attribute_id == attribId]
        attributes = store.find(AssociatedAttribute, *filters).group_by(AssociatedAttribute.value)
        parentNode = self.parent
        for attribute in attributes:
            name = attribute.value
            if len(name) == 0:
                name = UNTAGGED_NAME
            newNode = parentNode.createDirectory(self.displayName + name, asGenerator = False, hidden = False, showLeafs = self.showLeafs, relative = self.id)
            for child in self.children:
                child.cloneTo(newNode)
            newNode.filters.add(FSFilter.findFilter(store, attribId, FSFILTER_EXACT, attribute.value))
        
    def resetRebuilt(self):
        self.wasRebuilt = False
        for child in self.children:
            child.resetRebuilt()
            
    def clean(self):
        if self.kind == FSNODE_FILE:
            delete(self)
        elif self.kind == FSNODE_FOLDER:
            for child in self.children:
                child.clean()
        elif self.kind == FSNODE_GENERATOR:
            store = Store.of(self)
            generatedList = store.find(FSNode, FSNode.kind == FSNODE_FOLDER, FSNode.relative == self.id)
            for generated in generatedList:
                generated.delete()
        else:
            raise FLibFSError("Unknown kind")
        
    
    def rebuild(self):
        if self.wasRebuilt:
            return
        if self.kind == FSNODE_FILE:
            return
        
        if self.kind == FSNODE_FOLDER:
            self._buildAsFolder()
        elif self.kind == FSNODE_GENERATOR: 
            self._buildAsGenerator()
        else:
            raise FLibFSError("Unknown kind")
        self.wasRebuilt = True
        
    def stat(self):
        statobj = Stat(st_ino = self.id, st_uid = os.getuid(), st_gid = os.getgid(), st_size = self.size, st_atime = self.atime, st_mtime = self.mtime, st_ctime = self.ctime, st_nlink = 0)
        if self.kind == FSNODE_FOLDER:
            statobj.st_mode = STAT_UMASK | stat.S_IFDIR
        else:
            statobj.st_mode = STAT_UMASK | stat.S_IFLNK
        return statobj
    
    def readlink(self):
        return Store.of(self).get(Object, self.relative).realFileName.encode("utf-8")
    
    def getDirentry(self):
        if self.kind == FSNODE_FOLDER:
            mode = stat.S_IFDIR
        else:
            mode = stat.S_IFLNK
        return Direntry(self.displayName.encode("utf-8"), type = mode, ino = self.id)
    
class FSNodeFilter(object):
    __storm_table__ = "fsnodefilter"
    __storm_primary__ = "node_id", "filter_id"
    
    node_id = Int()
    filter_id = Int()
    
class FSNodeAttribute(object):
    __storm_table__ = "fsnodeattribute"
    __storm_primary__ = "attribute_id", "node_id"
    
    attribute_id = Int()
    node_id = Int()
    node = Reference(node_id, FSNode.id)
    value = Unicode()
    
    
FSNode.filters = ReferenceSet(  FSNode.id,
                                FSNodeFilter.node_id,
                                FSNodeFilter.filter_id,
                                FSFilter.id)

FSNode.attributes = ReferenceSet(   FSNode.id, FSNodeAttribute.node_id) 
