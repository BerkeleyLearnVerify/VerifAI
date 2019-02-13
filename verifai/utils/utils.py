"""Assorted utility functions"""

### Python conveniences

def cached(oldMethod):
    """Decorator for making a method with no arguments cache its result"""
    storageName = f'_cached_{oldMethod.__name__}'
    def newMethod(self):
        if not hasattr(self, storageName):
            setattr(self, storageName, oldMethod(self))
        return getattr(self, storageName)
    return newMethod

def cached_property(oldMethod):
    """Decorator for making a property which caches its value"""
    return property(cached(oldMethod))
