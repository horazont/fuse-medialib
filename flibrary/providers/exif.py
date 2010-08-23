from pyexiv2 import Image
from provider import Provider, Mapper
from flibrary.attributes import *

class ExifProvider(Provider):
    def getAttributes(self, fileName, fileObject, fileStat, fileAttributes):
        try:
            img = Image(fileName)
        except:
            return False
        
        fileAttributes[u"class"] = u"image"
        
        mapper = Mapper(fileAttributes, img)
        
        mapper.assign({
            'Exif.Image.Make': u"image/make",
            'Exif.Image.Model': u"image/make-model",
            'Exif.Image.DateTime': ATTR_GENERIC_DATETIME,
            'Exif.Image.XResolution': u"image/x-resolution",
            'Exif.Image.YResolution': u"image/y-resolution",
            'Exif.Photo.ExposureTime': u"photo/exposure-time",
            'Exif.Photo.FNumber': u"photo/f-number",
            'Exif.Photo.ISOSpeedRatings': u"photo/iso-speed-ratings",
            'Exif.Photo.ShutterSpeedValue': u"photo/shutter-speed-value",
            'Exif.Photo.ApertureValue': u"photo/aperture-value",
            'Exif.Photo.ExposureBiasValue': u"photo/exposure-bias-value",
            'Exif.Photo.MeteringMode': u"photo/metering-mode",
            'Exif.Photo.Flash': u"photo/flash",
            'Exif.Photo.FocalLength': u"photo/focal-length"
        })
