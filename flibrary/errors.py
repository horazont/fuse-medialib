

class LibraryError(Exception):
    pass

class LibraryStoreError(LibraryError):
    pass

class LibraryIntegrityError(LibraryError):
    pass
