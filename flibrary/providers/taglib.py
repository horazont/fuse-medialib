import tagpy
from provider import Provider
from flibrary.attributes import *
from flibrary.foreigndata import safeEncode

class TaglibProvider(Provider):
    def getAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        try:
            useFileName = fileName
            if isinstance(fileName, unicode):
                useFileName = fileName.encode("utf-8")
            ref = tagpy.FileRef(useFileName)
        except ValueError:
            return None
            
        tags = ref.tag()
        
        title = tags.title
        album = tags.album
        artist = tags.artist
        genre = tags.genre
        track = tags.track
        year = tags.year
        
        data = fileAttributes
        data[u"class"] = u"audio"
        
        if title is not None:
            data[ATTR_GENERIC_TITLE] = safeEncode(title)
        if album is not None:
            data[ATTR_GENERIC_ALBUM] = safeEncode(album)
        if artist is not None:
            data[ATTR_GENERIC_ARTIST] = safeEncode(artist)
        if genre is not None:
            data[u"audio/genre"] = safeEncode(genre)
        if track is not None:
            data[u"audio/trackno"] = safeEncode(track)
        if year is not None:
            data[ATTR_GENERIC_YEAR] = safeEncode(year)
            
        file = ref.file()
        if "xiphComment" in dir(file):
            xiph = file.xiphComment()
            fields = xiph.fieldListMap()
            if "DISCNUMBER" in fields:
                data[u"audio/discno"] = safeEncode(fields["DISCNUMBER"][0])
            if "TOTALDISCS" in fields:
                data[u"audio/totaldiscs"] = safeEncode(fields["TOTALDISCS"][0])
            if "TOTALTRACKS" in fields:
                data[u"audio/totaltracks"] = safeEncode(fields["TOTALTRACKS"][0])
            if "RATING:BANSHEE" in fields:
                data[ATTR_GENERIC_RATING] = safeEncode(fields["RATING:BANSHEE"][0])
        return data
