from providers import Provider

class MimeTypeProvider(Provider):
    def getAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        
