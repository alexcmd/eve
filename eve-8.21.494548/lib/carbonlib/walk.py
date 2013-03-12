#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\walk.py
import blue

def walk(top, topdown = True, onerror = None):
    try:
        names = blue.paths.listdir(top)
    except blue.error as err:
        if onerror is not None:
            onerror(err)
        return

    dirs, nondirs = [], []
    for name in names:
        if blue.paths.isdir(u'/'.join((top, name))):
            dirs.append(name)
        else:
            nondirs.append(name)

    if topdown:
        yield (top, dirs, nondirs)
    for name in dirs:
        new_path = u'/'.join((top, name))
        for x in walk(new_path, topdown, onerror):
            yield x

    if not topdown:
        yield (top, dirs, nondirs)