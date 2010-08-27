from flibrary.object import Object
import re

class FormattingNode(object):
    def __init__(self, failureSkip = 0):
        self.failureSkip = 0
    
    def resolve(self, obj):
        pass

class FormattingNodeStatic(FormattingNode):
    def __init__(self, value, **kwargs):
        super(FormattingNodeStatic, self).__init__(**kwargs)
        self.value = value
    
    def resolve(self, obj):
        return (self.value, 0)
        
class FormattingNodeAttribute(FormattingNode):
    def __init__(self, attribName, **kwargs):
        super(FormattingNodeAttribute, self).__init__(**kwargs)
        self.attribName = attribName
        
    def resolve(self, obj):
        if self.attribName in obj:
            return (obj[self.attribName], 0)
        else:
            return ("", self.failureSkip)

def buildFormattingChain(s):
    regexp = re.compile(u"%([^?]+/[^?]+)(\?+)?%")
    lastPos = 0
    result = []
    for match in regexp.finditer(s):
        start = match.start()
        if start <> lastPos:
            result += [FormattingNodeStatic(s[lastPos:start])]
        questionMarks = match.group(2)
        skipCount = 0
        if questionMarks is not None:
            skipCount = len(match.group(2))
        result += [FormattingNodeAttribute(match.group(1), failureSkip = skipCount)]
    return result

def resolveFormatting(fmtChain, obj):
    skip = 0
    result = ""
    for node in fmtChain:
        if skip > 0:
            skip -= 1
            if skip < node.failureSkip:
                skip = node.failureSkip
            continue
        thisNodeStr, skipCount = node.resolve(obj)
        skip = skipCount
        result += thisNodeStr
    return result
