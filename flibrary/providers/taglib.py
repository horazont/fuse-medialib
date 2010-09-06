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
        
        if title is not None and len(title) > 0:
            data[ATTR_GENERIC_TITLE] = safeEncode(title)
        if album is not None and len(album) > 0:
            data[ATTR_GENERIC_ALBUM] = safeEncode(album)
        if artist is not None and len(artist) > 0:
            data[ATTR_GENERIC_ARTIST] = safeEncode(artist)
        if genre is not None and len(genre) > 0:
            data[ATTR_GENERIC_GENRE] = safeEncode(genre)
        if track is not None and track > 0:
            data[u"audio/trackno"] = safeEncode(track)
        if year is not None and year > 0:
            data[ATTR_GENERIC_YEAR] = safeEncode(year)
            
        file = ref.file()
        if "xiphComment" in dir(file):
            xiph = file.xiphComment()
            fields = xiph.fieldListMap()
            if "DISCNUMBER" in fields:
                value = safeEncode(fields["DISCNUMBER"][0])
                if len(value) > 0 and int(value) > 0:
                    data[u"audio/discno"] = value
            if "TOTALDISCS" in fields:
                value = safeEncode(fields["TOTALDISCS"][0])
                if len(value) > 0 and int(value) > 0:
                    data[u"audio/totaldiscs"] = value
            if "TOTALTRACKS" in fields:
                value = safeEncode(fields["TOTALTRACKS"][0])
                if len(value) > 0 and int(value) > 0:
                    data[u"audio/totaltracks"] = value
            if "RATING:BANSHEE" in fields:
                value = safeEncode(fields["RATING:BANSHEE"][0])
                if len(value) > 0:
                    data[ATTR_GENERIC_RATING] = value
        return data
