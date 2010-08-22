import re

class Provider(object):
    def getFilteredAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        return self.getAttributes
    
    def getAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        return False

class RegExProvider(object):
    def __init__(self, expression):
        self.re = re.compile(expression)
        
    def getFilteredAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        if self.re.match(fileName):
            return self.getAttributes(fileName, fileObject, fileStat, fileAttributes)
        return False
