from storm.locals import *
import os
import os.path
import stat
from object import Object
from directory import Directory
from errors import *
from attributes import *
import time

UPDATE_INTERVAL = 86400

class Library(object):
    
    def __init__(self, databaseURI, initdb = False):
        self.database = create_database(databaseURI)
        self.store = Store(self.database)
        
        if initdb:
            self.store.execute("""CREATE TABLE IF NOT EXISTS `attributes` (
                id INTEGER AUTO_INCREMENT PRIMARY KEY, 
                name VARCHAR(255) NOT NULL UNIQUE COMMENT 'attribute name'
            ) COLLATE = utf8_bin""")
            self.store.execute("""CREATE TABLE IF NOT EXISTS `objects` (
                id INTEGER AUTO_INCREMENT PRIMARY KEY, 
                realFileName VARCHAR(2047) NOT NULL COMMENT 'where to find that on the file system', 
                mtime BIGINT NOT NULL DEFAULT 0 COMMENT 'fs modification time',
                ctime BIGINT NOT NULL DEFAULT 0 COMMENT 'fs creation time',
                lastScan BIGINT NOT NULL DEFAULT 0 COMMENT 'timestamp of last scan',
                INDEX realFileName (realFileName), 
                FULLTEXT INDEX (realFileName)
            ) COLLATE = utf8_bin""")
            self.store.execute("""CREATE TABLE IF NOT EXISTS `objects2attributes` (
                object_id INTEGER COMMENT 'reference to object' REFERENCES objects (id), 
                attribute_id INTEGER COMMENT 'reference to attribute' REFERENCES attributes (id), 
                value VARCHAR(2047) COMMENT 'value of that attribute for this object',
                INDEX value (value),
                FULLTEXT INDEX (value), 
                PRIMARY KEY (object_id, attribute_id)
            ) COLLATE = utf8_bin""")
            self.store.execute("""CREATE TABLE IF NOT EXISTS `jobqueue` (
                id INTEGER AUTO_INCREMENT PRIMARY KEY,
                notBefore BIGINT COMMENT 'the job must not be executed before this time',
                action ENUM(
                    'reindex-dir',
                    'update-file',
                    'assign-file'
                ) COMMENT 'which job to execute',
                pathData VARCHAR(2047) COMMENT 'fs object to operate on',
                additionalData1 VARCHAR(255) COMMENT 'e.g. attribute name',
                additionalData2 VARCHAR(2047) COMMENT 'e.g. attirbute value'
            ) COLLATE = utf8_bin""")
            self.store.execute("""CREATE TABLE IF NOT EXISTS `directories` (
                id INTEGER AUTO_INCREMENT PRIMARY KEY,
                path VARCHAR(2047) NOT NULL COMMENT 'path to the directory',
                mtime BIGINT NOT NULL DEFAULT 0 COMMENT 'fs modification time',
                ctime BIGINT NOT NULL DEFAULT 0 COMMENT 'fs creation time',
                lastScan BIGINT NOT NULL DEFAULT 0 COMMENT 'timestamp of last full scan',
                followSymLinks BOOL NOT NULL DEFAULT FALSE COMMENT 'will follow symlinks on autoscan',
                recursively BOOL NOT NULL DEFAULT TRUE COMMENT 'recurse into subdirectories on autoscan',
                INDEX path (path)
            ) COLLATE = utf8_bin""")
            self.store.commit()
        
        self.providers = []
    
    def addProvider(self, provider):
        if not getattr(provider, "getAttributes", False):
            raise LibraryError("Given provider does not implement getAttributes.")
        self.providers += [provider]
        provider.library = self
            
    def _getAttributesForFile(self, fullPath, stat):
        attributes = {
            ATTR_FILENAME: os.path.basename(fullPath)
        }
        try:
            file = open(fullPath, "rb")
        except:
            return
        for provider in self.providers:
            provider.getAttributes(fullPath, file, stat, attributes)
        genericAttributes = 0
        if ATTR_CLASS in attributes:
            genericAttributes += 1
        if ATTR_MIME_TYPE in attributes:
            genericAttributes += 1
        if ATTR_MIME_TYPE_FULL in attributes:
            genericAttributes += 1
        if ATTR_MIME_CLASS in attributes:
            genericAttributes += 1
        if ATTR_FILENAME in attributes:
            genericAttributes += 1
        return attributes, len(attributes) - genericAttributes
    
    def addDirectory(self, path, recursively = True, followSymLinks = False, forceUpdate = False):
        if path[-1] != u'/':
            path += u'/'
        dirObj = self.store.find(Directory, Directory.path == path).any()
        if dirObj is None:
            dirObj = Directory()
            dirObj.path = path
            dirObj.recursively = recursively
            dirObj.followSymLinks = followSymLinks
            self.store.add(dirObj)
            return dirObj, True
        else:
            dirObj.recursively = recursively
            dirObj.followSymLinks = followSymLinks
            if forceUpdate:
                dirObj.lastScan = 0
            return dirObj, False
    
    def _getFileAutocreate(self, realFileName):
        fileObj = self.store.find(Object, Object.realFileName == realFileName).any()
        if fileObj is None:
            fileObj = Object()
            fileObj.realFileName = realFileName
            self.store.add(fileObj)
            return fileObj
        else:
            return fileObj
    
    def _updateFile(self, fileObj, fileStat):
        attributes, count = self._getAttributesForFile(fileObj.realFileName, fileStat)
        if count == 0:
            fileObj._attributes.clear()
            self.store.remove(fileObj)
            return
        
        for key, value in attributes.items():
            fileObj[key] = value
        fileObj.mtime = fileStat.st_mtime
        fileObj.ctime = fileStat.st_ctime
        fileObj.lastScan = time.time()
        self.updatedFiles += 1
    
    def _updateDirNode(self, dirObj, fullPath, fileStat, force = False):
        if stat.S_ISDIR(fileStat.st_mode) and dirObj.recursively:
            subdirObj, created = self.addDirectory(fullPath + u'/', dirObj.recursively, dirObj.followSymLinks)
            if force or fileStat.st_mtime > subdirObj.mtime or fileStat.st_ctime > subdirObj.ctime:
                self._updateDir(subdirObj, os.stat(fullPath), force)
        elif stat.S_ISREG(fileStat.st_mode):
            if force:
                self._updateFile(self._getFileAutocreate(fullPath), fileStat)
            else:
                fileObj = self._getFileAutocreate(fullPath)
                if fileStat.st_mtime > fileObj.mtime or fileStat.st_ctime > fileObj.ctime:
                    self._updateFile(fileObj, fileStat)
        elif stat.S_ISLNK(fileStat.st_mode) and dirObj.followSymLinks:
            self._updateDirNode(dirObj, fullPath, os.stat(fullPath), force)
        
    def _updateDir(self, dirObj, dirStat, force = False):
        for file in os.listdir(dirObj.path):
            fullPath = dirObj.path + file
            fileStat = os.lstat(fullPath)
            self._updateDirNode(dirObj, fullPath, fileStat, force)
        dirObj.mtime = dirStat.st_mtime
        dirObj.ctime = dirStat.st_ctime
        dirObj.lastScan = time.time()
        self.updatedDirectories += 1
        
    def update(self, force = False):
        self.updatedFiles = 0
        self.updatedDirectories = 0
        self.removedFiles = 0
        self.removedDirectories = 0
        print "  Scanning for dirty / timed out directories..."
        directories = self.store.find(Directory)
        thisUpdate = time.time()
        if force:
            for dirObj in directories:
                self._updateDir(dirObj, True)
        else:
            for dirObj in directories:
                if not os.path.isdir(dirObj.path):
                    self.removedDirectories += 1
                    self.store.remove(dirObj)
                else:
                    dirStat = os.stat(dirObj.path)
                    if dirObj.lastScan + UPDATE_INTERVAL < thisUpdate:
                        self._updateDir(dirObj, dirStat, False)
                    else:
                        if int(dirStat.st_mtime) > dirObj.mtime or int(dirStat.st_ctime) > dirObj.ctime:
                            self._updateDir(dirObj, dirStat, False)
        
        print "  Scanning for dirty files in not updated files..."
        files = self.store.find(Object, Object.lastScan < int(thisUpdate))
        for fileObj in files:
            if not os.path.isfile(fileObj.realFileName):
                self.removedFiles += 1
                fileObj._attributes.clear()
                self.store.remove(fileObj)
            else:
                fileStat = os.stat(fileObj.realFileName)
                if int(fileStat.st_mtime) > fileObj.mtime or int(fileStat.st_ctime) > fileObj.ctime:
                    self._updateFile(fileObj, fileStat)
        return self.updatedFiles, self.updatedDirectories, self.removedFiles, self.removedDirectories
        
    def getUpdateStats(self):
        return self.updatedFiles, self.updatedDirectories, self.removedFiles, self.remvoedDirectories
