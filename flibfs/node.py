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
        self.selectiveUpdate = None
        
    def __init__(self, store):
        self.store = store
        self.selectiveUpdate = None
    
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
        
    def setupSelectiveUpdate(self, resultSet):
        self.selectiveUpdate = resultSet
        self.getRootDir().clearSelectionCache()
        
    def selectiveRebuild(self):
        if self.selectiveUpdate is None:
            raise FLibFSError("Attempt to perform a selective rebuild without a selection.")
        self.store.find(FSNode, FSNode.kind == FSNODE_FILE, FSNode.fs_id == self.id, FSNode.relative.is_in(self.selectiveUpdate.values(Object.id))).remove()
        self.getRootDir().softRebuild()
    
class FSFilter(object):
    __storm_table__ = "fsfilter"
    id = Int(primary = True)
    attributeName = Unicode()
    kind = Int()
    value = Unicode()
    
    def _escape(self, s):
        return s.replace(u"'", u"\\'").replace(u'"', u'\\"')
        
    def __init__(self, attributeName = None, kind = None, value = None):
        if attributeName is not None:
            self.attributeName = attributeName
        if kind is not None:
            self.kind = kind
        self.value = value
        
    def getAttributeId(self):
        return Store.of(self).find(Attribute, Attribute.name == self.attributeName).one().id
    
    def getStormFilter(self):
        if self.kind == FSFILTER_EXACT:
            return [Attribute.name == self.attributeName, AssociatedAttribute.attribute_id == Attribute.id, AssociatedAttribute.value == self.value]
        elif self.kind == FSFILTER_STARTS_WITH:
            return [Attribute.name == self.attributeName, AssociatedAttribute.attribute_id == Attribute.id, AssociatedAttribute.value.like(self.value+u'%')]
        elif self.kind == FSFILTER_ENDS_WITH:
            return [Attribute.name == self.attributeName, AssociatedAttribute.attribute_id == Attribute.id, AssociatedAttribute.value.like(u'%'+self.value)]
        elif self.kind == FSFILTER_CONTAINS:
            return [Attribute.name == self.attributeName, AssociatedAttribute.attribute_id == Attribute.id, AssociatedAttribute.value.like(u'%'+self.value+u'%')]
        elif self.kind == FSFILTER_LIKE:
            return [Attribute.name == self.attributeName, AssociatedAttribute.attribute_id == Attribute.id, AssociatedAttribute.value.like(self.value)]
        elif self.kind == FSFILTER_GENERATOR:
            return []
        else:
            raise FLibFSError("Invalid filter kind")
            
    @staticmethod
    def findFilter(store, attributeName, kind, value):
        filter = store.find(FSFilter, FSFilter.attributeName == attributeName, FSFilter.kind == kind, FSFilter.value == value).any()
        if filter is None:
            filter = FSFilter()
            filter.attributeName = attributeName
            filter.kind = kind
            filter.value = value
            store.add(filter)
        return filter
    
class FSNodeAttribute(object):
    __storm_table__ = "fsnodeattribute"
    __storm_primary__ = "attribute_id", "node_id"
    
    attribute_id = Int()
    node_id = Int()
    value = Unicode()

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
        
    def getChild(self, displayName):
        return Store.of(self).find(FSNode, FSNode.parent_id == self.id, FSNode.displayName == displayName, FSNode.kind != FSNODE_GENERATOR).any()
    
    def createDirectory(self, displayName, asGenerator = False, hidden = False, showLeafs = False, size = None, atime = None, mtime = None, ctime = None, relative = None):
        if not asGenerator and (len(displayName) == 0 or self.hasNode(displayName)):
            raise FLibFSValidityError("Duplicate or empty display name (%s)." % displayName)
        obj = FSNode()
        obj.fs = self.fs
        obj.parent = self
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
        store.find(FSNodeFilter, FSNodeFilter.node_id == self.id).remove()
        store.find(FSNodeAttribute, FSNodeAttribute.node_id == self.id).remove()
        store.remove(self)
        
    def cloneTo(self, newParent):
        if self.kind == FSNODE_FILE:
            raise FLibFSError("Cannot clone a file")
        newNode = newParent.createDirectory(self.displayName, self.kind == FSNODE_GENERATOR, self.hidden, self.showLeafs)
        for child in self.children:
            child.cloneTo(newNode)
        for filter in self.filters:
            newNode.filters.add(filter)
        for attrib in self.attributes:
            newAttrib = FSNodeAttribute()
            newAttrib.attribute_id = attrib.attribute_id
            newAttrib.value = attrib.value
            newNode.attributes.add(newAttrib)
            
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
        
    def clearSelectionCache(self):
        self._cachedSelection = None
        for child in self.children:
            child.clearSelectionCache()
        
    def parentSelection(self):
        if self.parent is not None:
            return self.parent.cachedSelection()
        elif self.fs.selectiveUpdate is not None:
            return self.fs.selectiveUpdate
        else:
            return None
        
    def cachedSelection(self):
        if self._cachedSelection is None:
            previousSelection = self.parentSelection()
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
            
    def parentCustomSelection(self, inputSet):
        if self.parent is not None:
            return self.parent.customSelection(inputSet)
        else:
            return inputSet
            
    def customSelection(self, inputSet):
        previousSelection = self.parentCustomSelection(inputSet)
        filters = self.getFilters()
        store = Store.of(self)
        for filter in filters:
            if previousSelection is not None:
                filters = [Object.id.is_in(previousSelection.values(Object.id)), Object.id == AssociatedAttribute.object_id] + filter
            else:
                filters = [Object.id == AssociatedAttribute.object_id] + filter
            previousSelection = store.find(Object *filters)
        return previousSelection
        
    def addLeafs(self):
        selection = self.cachedSelection()
        
        formattingChain = buildFormattingChain(self.inheritingAttribute(FSNODE_ATTRIB_DISPLAY_NAME_FORMAT))
        for obj in selection:
            self.createFile(obj, resolveFormatting(formattingChain, obj))
            
    def getFileNode(self, fileObjId):
        return Store.of(self).find(FSNode, FSNode.parent_id == self.id, FSNode.kind == FSNODE_FILE, FSNode.relative == fileObjId).any()
        
    def hasFileNode(self, fileObjId):
        return not Store.of(self).find(FSNode, FSNode.parent_id == self.id, FSNode.kind == FSNODE_FILE, FSNode.relative == fileObjId).is_empty()
        
    def _buildAsFolder(self):
        store = Store.of(self)
        # Rebuild the generators first as they may create new children
        for generator in store.find(FSNode, FSNode.parent_id == self.id, FSNode.kind == FSNODE_GENERATOR):
            generator.rebuild()
        for child in self.children:
            child.rebuild()
        if not self.showLeafs:
            return
            
        self.addLeafs()
        
    def _softBuildAsFolder(self):
        store = Store.of(self)
        for generator in store.find(FSNode, FSNode.parent_id == self.id, FSNode.kind == FSNODE_GENERATOR):
            generator.softRebuild()
        for nonGenerator in store.find(FSNode, FSNode.parent_id == self.id, FSNode.kind != FSNODE_GENERATOR):
            nonGenerator.softRebuild()
        if not self.showLeafs:
            return
        selection = self.cachedSelection()
        formattingChain = buildFormattingChain(self.inheritingAttribute(FSNODE_ATTRIB_DISPLAY_NAME_FORMAT))
        for libObj in selection:
            if not self.hasFileNode(libObj.id):
                self.createFile(libObj, resolveFormatting(formattingChain, libObj))
        
        # remove all "orphans"
        store.find(FSNode, FSNode.parent_id == self.id, FSNode.kind == FSNODE_FILE, Not(FSNode.relative.is_in(store.find(Object.id).values(Object.id)))).remove()
        
        existingSelection = store.find(Object, Object.id == FSNode.relative, FSNode.parent_id == self.id, FSNode.kind == FSNODE_FILE)
        filteredSelection = self.customSelection(existingSelection)
        if filteredSelection.count() < existingSelection.count():
            existing = set(existingSelection.values(Object.id))
            filtered = set(filteredSelection.values(Object.id))
            toDelete = existing - filtered
            
            store.find(FSNode, FSNode.parent_id == self.id, FSNode.kind == FSNODE_FILE, FSNode.relative.is_in(toDelete)).remove()
    
    def _buildAsGenerator(self):
        store = Store.of(self)
        generatedList = store.find(FSNode, FSNode.kind == FSNODE_FOLDER, FSNode.relative == self.id)
        for generated in generatedList:
            generated.delete()
        if self.filters.count() != 1:
            raise FLibFSValidityError("A generator must have exactly one filter (%d found for generator %d)" % (self.filters.count(), self.id))
        filter = self.filters.any()
        attribId = filter.getAttributeId()
        
        selection = self.cachedSelection()
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
            newNode.filters.add(FSFilter.findFilter(store, filter.attributeName, FSFILTER_EXACT, attribute.value))
            for attrib in self.attributes:
                newAttrib = FSNodeAttribute()
                newAttrib.attribute_id = attrib.attribute_id
                newAttrib.value = attrib.value
                newNode.attributes.add(newAttrib)
            
    def _softBuildAsGenerator(self):
        store = Store.of(self)
        if self.filters.count() != 1:
            raise FLibFSValidityError("A generator must have exactly one filter (%d found for generator %d)" % (self.filters.count(), self.id))
        attribId = self.filters.any().attribute_id
        
        selection = self.cachedSelection()
        if selection is None:
            filters = [AssociatedAttribute.attribute_id == attribId]
        else:
            filters = [AssociatedAttribute.object_id.is_in(selection.values(Object.id)), AssociatedAttribute.attribute_id == attribId]
        attributes = store.find(AssociatedAttribute, *filters).group_by(AssociatedAttribute.value)
        parentNode = self.parent
        rebuilt = []
        for attribute in attributes:
            name = attribute.value
            if len(name) == 0:
                name = UNTAGGED_NAME
            childNode = parentNode.getChild(name)
            if childNode is None:
                childNode = parentNode.createDirectory(self.displayName + name, asGenerator = False, hidden = False, showLeafs = self.showLeafs, relative = self.id)
                for child in self.children:
                    child.cloneTo(childNode)
                childNode.filters.add(FSFilter.findFilter(store, attribId, FSFILTER_EXACT, attribute.value))
            childNode.softRebuild()
            rebuilt += [childNode.id]
        
        toCheck = store.find(FSNode, FSNode.kind == FSNODE_FOLDER, FSNode.relative == self.id, Not(FSNode.id.is_in(rebuilt)))
        for node in toCheck:
            if node.cachedSelection().count() == 0:
                node.delete()
        
    def resetRebuilt(self):
        self.wasRebuilt = False
        for child in self.children:
            child.resetRebuilt()
            
    def clean(self):
        if self.kind == FSNODE_FILE:
            self.delete()
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
        self.wasRebuilt = False
    
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
        
    def softRebuild(self):
        if self.kind == FSNODE_FILE:
            return
        if self.kind == FSNODE_FOLDER:
            self._softBuildAsFolder()
        elif self.kind == FSNODE_GENERATOR:
            self._softBuildAsGenerator()
        else:
            raise FLibFSError("Unknown kind")
        
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
    
FSNodeAttribute.node = Reference(FSNodeAttribute.node_id, FSNode.id)
    
FSNode.filters = ReferenceSet(  FSNode.id,
                                FSNodeFilter.node_id,
                                FSNodeFilter.filter_id,
                                FSFilter.id)

FSNode.attributes = ReferenceSet(   FSNode.id, FSNodeAttribute.node_id) 
