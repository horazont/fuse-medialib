from flibrary.library import Library
from flibrary.object import Object
from flibrary.objects2attributes import AssociatedAttribute
from flibrary.attribute import Attribute
from storm.locals import *

lib = Library("mysql://fuselib@localhost/fuselib")
store = lib.store
