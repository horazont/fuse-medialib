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


class Mapper(object):
    def __init__(self, dataObj, providingMap):
        self.data = dataObj
        self.attrs = providingMap
        
    def assign(self, mapping, overwrite = True):
        data = self.data
        attrs = self.attrs
        for fileKey, ourKey in mapping.items():
            try:
                if (not overwrite) and (ourKey in data):
                    continue
                newValue = attrs[fileKey]
                if not isinstance(newValue, unicode):
                    newValue = unicode(newValue, "utf-8")
                data[ourKey] = newValue
            except IOError:
                pass
            except IndexError:
                pass
            except KeyError:
                pass
            except:
                raise
