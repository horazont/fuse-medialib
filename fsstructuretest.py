from flibfs.structure import FSStructure
from flibfs.node import *

struct = FSStructure("mysql://fuselib@localhost/fuselib", True)
fs = struct.getFilesystem(u"test", True)

#rootDir = fs.getRootDir()
#artists = rootDir.createDirectory("Artist", False, False, False)
