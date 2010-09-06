from flibfs.node import *

class FSStructure(object):
    
    def __init__(self, databaseURI, initdb = False):
        self.database = create_database(databaseURI)
        self.store = Store(self.database)
        
        if initdb:
            self.store.execute("""CREATE TABLE IF NOT EXISTS  `filesystems` (
                id 
                    INTEGER AUTO_INCREMENT 
                    PRIMARY KEY,
                refname 
                    VARCHAR(255) NOT NULL 
                    UNIQUE 
                    COMMENT 'name for CLI usage'
            ) COLLATE=utf8_bin""")
            
            self.store.execute("""CREATE TABLE IF NOT EXISTS `fsnode` (
                id 
                    INTEGER AUTO_INCREMENT 
                    PRIMARY KEY,
                fs_id 
                    INTEGER NOT NULL 
                    COMMENT 'reference to the file system'
                    REFERENCES filesystems (id),
                parent_id 
                    INTEGER NULL 
                    COMMENT 'reference to the parent node otherwise NULL'
                    REFERENCES fsnode (id),
                displayName 
                    VARCHAR(255) NOT NULL
                    COMMENT 'display name in dir listing; used as prefix for generators',
                fullPath 
                    VARCHAR(2047) NOT NULL
                    COMMENT 'full path for fast access, without trailing slash',
                kind 
                    INTEGER NOT NULL 
                    COMMENT '0 = folder, 1 = file, 2 = generator',
                hidden 
                    BOOL NOT NULL
                    DEFAULT FALSE 
                    COMMENT 'may be true for generators',
                showLeafs
                    BOOL NOT NULL
                    DEFAULT FALSE
                    COMMENT 'wether to put leaves in here',
                relative 
                    INTEGER NOT NULL 
                    COMMENT 'for generated folder: id of generator node; for file: id of library object',
                size 
                    BIGINT NOT NULL 
                    DEFAULT 0 
                    COMMENT 'size for stat result',
                atime 
                    BIGINT NOT NULL 
                    DEFAULT 0 
                    COMMENT 'atime for stat result',
                mtime 
                    BIGINT NOT NULL 
                    DEFAULT 0 
                    COMMENT 'mtime for stat result',
                ctime 
                    BIGINT NOT NULL 
                    DEFAULT 0 
                    COMMENT 'ctime for stat result',
                INDEX
                    (parent_id, displayName),
                INDEX
                    (fullPath),
                INDEX
                    (kind)
            ) COLLATE=utf8_bin""")
            
            self.store.execute("""CREATE TABLE IF NOT EXISTS `fsfilter` (
                id 
                    INTEGER AUTO_INCREMENT 
                    PRIMARY KEY,
                attributeName
                    VARCHAR(255) NOT NULL
                    COMMENT 'reference to the attribute to filter',
                kind 
                    INTEGER NOT NULL
                    COMMENT '0 = exact match; 1 = starts-with; 2 = ends-with; 3 = contains; 4 = like; 5 = regex; 6 = none (generator)',
                value 
                    VARCHAR(255) DEFAULT NULL 
                    COMMENT 'value to match against'
            ) COLLATE=utf8_bin""")
            
            self.store.execute("""CREATE TABLE IF NOT EXISTS `fsnodefilter` (
                node_id     
                    INTEGER NOT NULL 
                    COMMENT 'reference to the related node'
                    REFERENCES fsnode (id),
                filter_id 
                    INTEGER NOT NULL 
                    COMMENT 'reference to the related filter'
                    REFERENCES fsfilter (id),
                PRIMARY KEY 
                    (node_id, filter_id)
            ) COLLATE=utf8_bin""")
            
            self.store.execute("""CREATE TABLE IF NOT EXISTS `fsnodeattribute` (
                node_id
                    INTEGER NOT NULL
                    COMMENT 'reference to the node'
                    REFERENCES fsnode (id),
                attribute_id
                    INTEGER NOT NULL
                    COMMENT 'internal attribute id',
                value
                    VARCHAR(255) NOT NULL
                    COMMENT 'attribute value',
                PRIMARY KEY
                    (node_id, attribute_id)
            ) COLLATE=utf8_bin""")
            
            self.store.commit()
            
    def newFilesystem(self, name):
        if self.store.find(Filesystem, Filesystem.refName == name).any() is not None:
            raise FLibFSValidityError("There is already a filesystem with that name.")
        obj = Filesystem(self.store)
        obj.refName = name
        self.store.add(obj)
        return obj
        
    def getFilesystem(self, name, allowCreation = False):
        obj = self.store.find(Filesystem, Filesystem.refName == name).any()
        if obj is None:
            return self.newFilesystem(name)
        else:
            return obj
