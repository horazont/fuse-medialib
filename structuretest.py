#!/usr/bin/python

from flibfs.structure import Structure
from flibrary.library import Library
from flibrary.object import Object

lib = Library("mysql://fuselib@localhost/fuselib")

structure = Structure(open("music.xml"), lib)

def printTree(parent, prefix = u""):
    for node in parent:
        print prefix+node.getName()
        if not node.isLeaf():
            printTree(node, prefix+u"  ")
            
def test(node):
    selection = node.select()
    for obj in selection:
        print obj.realFileName

print structure[("")].getDir()
