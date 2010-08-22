#!/usr/bin/python

from flibrary.library import Library
from flibrary.providers.taglib import TaglibProvider
from flibrary.providers.mimetype import MimeTypeProvider
from flibrary.providers.xattrprov import XAttrProvider, XAttrProviderInheriting
from flibrary.providers.exif import ExifProvider
from flibrary.object import Object
from flibrary.attribute import Attribute
import flibrary.objects2attributes
import os.path
import sys

lib = Library("mysql://fuselib@localhost/fuselib", True)
lib.addProvider(MimeTypeProvider())
lib.addProvider(XAttrProviderInheriting())
lib.addProvider(ExifProvider())
lib.addProvider(TaglibProvider())
lib.addDirectory(os.path.expanduser(u"~/Music/"), True, False)
lib.addDirectory(os.path.expanduser(u"~/Pictures/DigiREF/"), True, False)
print "Updating library..."
updatedFiles, updatedDirectories, removedFiles, removedDirectories = lib.update()
print "done."
print "Updated files       : %d" % updatedFiles
print "Removed files       : %d" % removedFiles
print "Updated directories : %d" % updatedDirectories
print "Removed directories : %d" % removedDirectories

# lib.scanDirectory(os.path.expanduser("~/Pictures/DigiREF/"))
