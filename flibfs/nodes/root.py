from node import NodeContainer, NodeRegistry
from folder import NodeFolder

class NodeRoot(NodeFolder):
    def __init__(self, parent, itemclass = None):
        NodeFolder.__init__(self, parent)
        self.itemclass = itemclass

NodeRegistry["root"] = NodeRoot


