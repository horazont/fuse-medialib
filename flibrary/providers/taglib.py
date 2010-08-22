import tagpy
from provider import Provider
from flibrary.attributes import *


class TaglibProvider(Provider):
    def getAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        try:
            ref = tagpy.FileRef(fileName)
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
        data["class"] = "audio"
        
        if title is not None:
            data[ATTR_GENERIC_TITLE] = title
        if album is not None:
            data[ATTR_GENERIC_ALBUM] = album
        if artist is not None:
            data[ATTR_GENERIC_ARTIST] = artist
        if genre is not None:
            data["audio/genre"] = genre
        if track is not None:
            data["audio/trackno"] = track
        if year is not None:
            data[ATTR_GENERIC_YEAR] = year
            
        file = ref.file()
        if "xiphComment" in dir(file):
            xiph = file.xiphComment()
            fields = xiph.fieldListMap()
            if "DISCNUMBER" in fields:
                data["audio/discno"] = fields["DISCNUMBER"][0]
            if "TOTALDISCS" in fields:
                data["audio/totaldiscs"] = fields["TOTALDISCS"][0]
            if "TOTALTRACKS" in fields:
                data["audio/totaltracks"] = fields["TOTALTRACKS"][0]
            if "RATING:BANSHEE" in fields:
                data[ATTR_GENERIC_RATING] = float(fields["RATING:BANSHEE"][0])
        return data
