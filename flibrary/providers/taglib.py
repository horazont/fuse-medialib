import tagpy
from provider import Provider

class TaglibProvider(Provider):
    def getAttributes(self, fileName, fileObject):
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
        
        data = {}
        data["class"] = "audio"
        
        if title is not None:
            data["generic/title"] = title
        if album is not None:
            data["generic/album"] = album
        if artist is not None:
            data["generic/artist"] = artist
        if genre is not None:
            data["audio/genre"] = genre
        if track is not None:
            data["audio/trackno"] = track
        if year is not None:
            data["audio/year"] = year
            
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
                data["generic/rating"] = float(fields["RATING:BANSHEE"][0])
        return data
