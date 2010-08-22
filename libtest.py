#!/usr/bin/python

from flibrary.library import Library
from flibrary.providers.taglib import TaglibProvider
from flibrary.providers.mimetype import MimeTypeProvider
from flibrary.providers.xattrprov import XAttrProvider
from flibrary.object import Object
from flibrary.attribute import Attribute
import flibrary.objects2attributes
import os.path

lib = Library("mysql://fuselib@localhost/fuselib", True)
lib.addProvider(MimeTypeProvider());
lib.addProvider(XAttrProvider());
lib.addProvider(TaglibProvider());
lib.scanDirectory(os.path.expanduser("~/Music/"))
