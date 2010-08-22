from storm.locals import *
import os
import stat as stathelper
from object import Object
from errors import *
from attributes import *

class Library(object):
    toCommitCount = 0
    
    def __init__(self, databaseURI, initdb = False):
        self.database = create_database(databaseURI)
        self.store = Store(self.database)
        
        if initdb:
            self.store.execute("""CREATE TABLE IF NOT EXISTS `attributes` (
                id INTEGER AUTO_INCREMENT PRIMARY KEY, 
                name VARCHAR(255) UNIQUE COMMENT 'attribute name'
            )""")
            self.store.execute("""CREATE TABLE IF NOT EXISTS `objects` (
                id INTEGER AUTO_INCREMENT PRIMARY KEY, 
                realFileName VARCHAR(2047) COMMENT 'where to find that on the file system', 
                mtime BIGINT COMMENT 'fs modification time',
                atime BIGINT COMMENT 'fs access time',
                ctime BIGINT COMMENT 'fs creation time',
                INDEX realFileName (realFileName), 
                FULLTEXT INDEX (realFileName)
            )""")
            self.store.execute("""CREATE TABLE IF NOT EXISTS `objects2attributes` (
                object_id INTEGER COMMENT 'reference to object' REFERENCES objects (id), 
                attribute_id INTEGER COMMENT 'reference to attribute' REFERENCES attributes (id), 
                value VARCHAR(2047) COMMENT 'value of that attribute for this object',
                INDEX value (value),
                FULLTEXT INDEX (value), 
                PRIMARY KEY (object_id, attribute_id)
            )""")
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
            )""")
            self.store.commit()
        
        self.providers = []
    
    def addProvider(self, provider):
        if not getattr(provider, "getAttributes", False):
            raise LibraryError("Given provider does not implement getAttributes.")
        self.providers += [provider]
        provider.library = self
        
    def _handleFile(self, fullPath, stat):
        attributes = {}
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
        if len(attributes)-genericAttributes > 0:
            self.updateFile(unicode(fullPath, "utf-8"), attributes, fileStat = stat)
        
    def _handleFSNode(self, stat, fullPath, recursively, followSymLinks):
        if stathelper.S_ISDIR(stat.st_mode):
            if recursively:
                self.scanDirectory(fullPath + "/")
        elif stathelper.S_ISLNK(stat.st_mode):
            if followSymLinks:
                statFollowed = os.stat(fullPath)
                self._handleFSNode(statFollowed, fullPath, recursively, followSymLinks)
        elif stathelper.S_ISREG(stat.st_mode):
            self._handleFile(fullPath, stat)
            
    
    def scanDirectory(self, path, recursively = True, followSymLinks = False):
        if len(self.providers) == 0:
            raise LibraryError("No provider assigned.")
        for fileName in os.listdir(path):
            fullPath = path + fileName
            stat = os.lstat(fullPath)
            self._handleFSNode(stat, fullPath, recursively, followSymLinks)
        if self.toCommitCount >= 100:
            self.store.commit()
            
    def updateFile(self, realFileName, attributes, fileStat = None):
        if fileStat is None:
            fileStat = os.stat(realFileName)
        fileObject = self.store.find(Object, Object.realFileName == realFileName)
        if fileObject.count() == 0:
            fileObject = Object(realFileName)
            self.store.add(fileObject)
        else:
            fileObject = fileObject[0]
        fileObject.mtime = fileStat.st_mtime
        fileObject.atime = fileStat.st_atime
        fileObject.ctime = fileStat.st_ctime
        for key, value in attributes.items():
            fileObject[key] = value
        self.toCommitCount += 1
        
