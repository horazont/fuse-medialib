from flibfs.structure import FSStructure
from flibfs.node import *

struct = FSStructure("mysql://fuselib@localhost/fuselib", True)

audioFs = struct.getFilesystem(u"audio")
root = audioFs.getRootDir()

store = struct.store

#rootDir = fs.getRootDir()
#artists = rootDir.createDirectory("Artist", False, False, False)
