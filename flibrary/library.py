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
            #self.store.execute("""CREATE TABLE IF NOT EXISTS `attributes` (
            #    id INTEGER AUTO_INCREMENT PRIMARY KEY,
            #    name VARCHAR(255) UNIQUE
            #)""")
            #self.store.execute("""CREATE TABLE IF NOT EXISTS `attributevalues` (
            #    id INTEGER AUTO_INCREMENT PRIMARY KEY,
            #    attribute_id INTEGER REFERENCES attributes (id),
            #    value VARCHAR(2047),
            #    INDEX value (value),
            #    INDEX attribvalue (attribute_id, value),
            #    FULLTEXT INDEX (value)
            #)""")
            #self.store.execute("""CREATER TABLE IF NOT EXISTS `objects` (
            #    id INTEGER AUTO_INCREMENT PRIMARY KEY,
            #    realFileName VARCHAR(2047),
            #    INDEX realFileName (realFileName), 
            #    FULLTEXT INDEX (realFileName)
            #)""")
            #self.store.execute("""CREATE TABLE IF NOT EXISTS `objectattributes` (
            #    object_id INTEGER REFERENCES objects (id),
            #    value_id INTEGER REFERENCES attributevalues (id),
            #    PRIMARY KEY (object_id, value_id)
            #)""")
            self.store.execute("CREATE TABLE IF NOT EXISTS `attributes` ("
                "id INTEGER AUTO_INCREMENT PRIMARY KEY, "
                "name VARCHAR(255) UNIQUE"
                ")");
            self.store.execute("CREATE TABLE IF NOT EXISTS `objects` ("
                "id INTEGER AUTO_INCREMENT PRIMARY KEY, "
                "realFileName VARCHAR(2047), "
                "INDEX realFileName (realFileName), "
                "FULLTEXT INDEX (realFileName)"
                ")");
            self.store.execute("CREATE TABLE IF NOT EXISTS `objects2attributes` ("
                "object_id INTEGER REFERENCES objects (id), "
                "attribute_id INTEGER REFERENCES attributes (id), "
                "value VARCHAR(2047), "
                "INDEX value (value), "
                "PRIMARY KEY (object_id, attribute_id)"
                ")");
            self.store.commit()
        
        self.providers = []
    
    def addProvider(self, provider):
        if not getattr(provider, "getAttributes", False):
            raise LibraryError("Given provider does not implement getAttributes.")
        self.providers += [provider]
        provider.library = self
        
    def _handleFile(self, fullPath):
        attributes = {}
        try:
            file = open(fullPath, "rb")
        except:
            return
        for provider in self.providers:
            data = provider.getAttributes(fullPath, file)
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
            self._handleFile(fullPath)
            
    
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
        
