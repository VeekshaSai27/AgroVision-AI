import traceback, sys, importlib
importlib.invalidate_caches()
try:
    import app
    print('imported app OK')
except Exception:
    traceback.print_exc()
    sys.exit(1)
