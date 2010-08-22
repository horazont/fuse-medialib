from provider import Provider
from subprocess import Popen, PIPE
import re
from flibrary.attributes import *

class MimeTypeProvider(Provider):
    def __init__(self):
        self.re = re.compile("([^/\n]+)/([^/\n]+)")
    
    def getAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        process = Popen(['file', '-b', '--mime-type', fileName], stdout=PIPE)
        stdout = process.communicate()[0]
        
        match = self.re.match(stdout)
        if match is not None:
            cls = unicode(match.group(1), 'ascii')
            if cls in ['audio', 'video', 'image', 'text', 'application']:
                fileAttributes[ATTR_CLASS] = cls
            fileAttributes[ATTR_MIME_CLASS] = cls
            fileAttributes[ATTR_MIME_TYPE] = unicode(match.group(2), 'ascii')
            fileAttributes[ATTR_MIME_TYPE_FULL] = unicode(stdout, 'ascii')
