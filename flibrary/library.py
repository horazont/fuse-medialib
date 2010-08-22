from storm.locals import *
import os
import stat as stathelper
from object import Object
from errors import *

class Library(object):
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
                object_id INTEGER REFERENCES objects (id) COMMENT 'reference to object', 
                attribute_id INTEGER REFERENCES attributes (id) COMMENT 'reference to attribute', 
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
            data = provider.getAttributes(fullPath, file, stat)
            if data is not None:
                attributes.update(data)
                break
        if len(attributes) > 0:
            self.updateFile(unicode(fullPath, "utf-8"), attributes)
        
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
        self.store.commit()
            
    def updateFile(self, realFileName, attributes):
        fileObject = self.store.find(Object, Object.realFileName == realFileName)
        if fileObject.count() == 0:
            fileObject = Object(realFileName)
            self.store.add(fileObject)
        else:
            fileObject = fileObject[0]
        for key, value in attributes.items():
            fileObject[key] = value
        
