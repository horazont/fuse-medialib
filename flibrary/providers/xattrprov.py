from provider import RegExProvider, Mapper
from xattr import xattr as XAttr
from flibrary.attributes import *
import os.path

class XAttrProvider(RegExProvider):
    def getAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        attrs = XAttr(fileObject)
        data = fileAttributes
        mapper = Mapper(data, attrs)
        
        try:
            mapper.assign({
                'user.author': ATTR_GENERIC_AUTHOR,
                'user.title': ATTR_GENERIC_TITLE,
                'user.year': ATTR_GENERIC_YEAR,
                'user.rating': ATTR_GENERIC_RATING,
                'user.album': ATTR_GENERIC_ALBUM,
                'user.geo.location': ATTR_GENERIC_LOCATION,
                'user.date': ATTR_GENERIC_DATE,
                'user.datetime': ATTR_GENERIC_DATETIME
            })
        except:
            return False

class XAttrProviderInheriting(RegExProvider):
    def _getAttributesInheriting(self, fileName, fileAttributes, missing):
        if fileName == '/':
            return
        attrs = XAttr(fileName)
        mapper = Mapper(fileAttributes, attrs)
        
        mapper.assign({
            'user.author': ATTR_GENERIC_AUTHOR,
            'user.title': ATTR_GENERIC_TITLE,
            'user.year': ATTR_GENERIC_YEAR,
            'user.rating': ATTR_GENERIC_RATING,
            'user.album': ATTR_GENERIC_ALBUM,
            'user.geo.location': ATTR_GENERIC_LOCATION,
            'user.date': ATTR_GENERIC_DATE,
            'user.datetime': ATTR_GENERIC_DATETIME
        }, False)
        if 'user.x-stop-inheritance' in attrs:
            return False
        else:
            newMissing = {}
            for key in missing:
                if not key in fileAttributes:
                    newMissing[key] = True
            missing = newMissing
            if len(missing) == 0:
                return False
            self._getAttributesInheriting(os.path.dirname(fileName), fileAttributes, missing)
    
    def getAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        missing = {}
        for genericAttrib in [ATTR_GENERIC_AUTHOR, ATTR_GENERIC_TITLE, ATTR_GENERIC_YEAR, ATTR_GENERIC_RATING, ATTR_GENERIC_ALBUM, ATTR_GENERIC_DATETIME, ATTR_GENERIC_LOCATION, ATTR_GENERIC_DATE]:
            missing[genericAttrib] = genericAttrib in fileAttributes
        if len(missing) == 0:
            return False
        
        self._getAttributesInheriting(fileName, fileAttributes, missing)
        
