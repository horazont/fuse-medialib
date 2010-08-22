import re

class Provider(object):
    def getFilteredAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        return self.getAttributes
    
    def getAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        return False
        
class FakeRegEx(object):
    def match(s):
        return True

class RegExProvider(object):
    def __init__(self, expression = None):
        if expression is None:
            self.re = FakeRegEx()
        else:
            self.re = re.compile(expression)
        
    def getFilteredAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        if self.re.match(fileName) is not None:
            return self.getAttributes(fileName, fileObject, fileStat, fileAttributes)
        return False
