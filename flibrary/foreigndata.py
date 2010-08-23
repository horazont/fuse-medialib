
def safeEncode(s):
    if isinstance(s, unicode):
        return s
    else:
        try:
            return unicode(s, "utf-8")
        except:
            pass
        try:
            return unicode(s, "latin-1")
        except:
            pass
        return unicode(s)
