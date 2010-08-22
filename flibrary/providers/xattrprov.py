from provider import RegExProvider
from xattr import xattr as XAttr
from flibrary.attributes import *

class XAttrMapper(object):
    def __init__(self, dataObj, attrProvider):
        self.data = dataObj
        self.attrs = attrProvider
        
    def assign(mapping):
        data = self.data
        attrs = self.attrs
        for fileKey, ourKey in mapping.items():
            try:
                data[ourKey] = attrs[fileKey]
            except IOError:
                pass
            except:
                raise

class XAttrProvider(RegExProvider):
    def getAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        attrs = XAttr(fileObject)
        data = fileAttributes
        mapper = XAttrMapper(data, attrs)
        
        try:
            mapper.assign({
                'user.author': ATTR_GENERIC_AUTHOR,
                'user.title': ATTR_GENERIC_TITLE,
                'user.year': ATTR_GENERIC_YEAR,
                'user.rating': ATTR_GENERIC_RATING,
                'user.album': ATTR_GENERIC_ALBUM
            })
        except:
            return False
