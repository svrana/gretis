try:
    import tornado
    TORNADO_AVAILABLE = True
except ImportError:
    TORNADO_AVAILABLE = False

try:
    import greenlet
    GREENLET_AVAILABLE = True
except:
    GREENLET_AVAILABLE = False

