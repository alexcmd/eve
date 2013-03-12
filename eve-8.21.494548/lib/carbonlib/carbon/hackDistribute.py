#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\carbon\hackDistribute.py
try:
    import blue
    blueContext = True
except ImportError:
    blueContext = False
    import shutil, os, platform, sys, stat
    relativeBranchRoot = '../../../../..'
    version = {'2.7': 'python_27',
     '2.6': 'python_26'}['.'.join(platform.python_version_tuple()[:2])]
    is_64bits = sys.maxsize > 4294967296L
    platformString = 'x64' if is_64bits else 'win32'

loadedDLLs = {}

def TimestampDoesNotMatch(f1, f2):
    a = os.stat(f1).st_mtime
    b = os.stat(f2).st_mtime
    return abs(a - b) > 0.1


def GetModuleJit(app, module):
    if not blueContext:
        moduleFolder = '%(app)s/autobuild/%(module)s/%(pythonVersion)s/%(platform)s/' % {'app': app,
         'module': module,
         'pythonVersion': version,
         'platform': platformString}
        localPython = sys.executable
        buildFolderLocation = os.path.abspath(os.path.join(__file__, relativeBranchRoot, moduleFolder))
        if buildFolderLocation not in sys.path:
            print 'Extending sys.path with "%s" to load %s' % (buildFolderLocation, module)
            sys.path.append(buildFolderLocation)
        localVersion = os.path.abspath(os.path.join(sys.executable, '../DLLs/%s.pyd' % module))
        if os.path.exists(localVersion):
            print 'Removing local version from "%s"' % localVersion
            os.remove(localVersion)


def GetDLLJit(app, module, dllsFor32Bit, dllsFor64bit):
    if not blueContext:
        moduleLocation = '%(app)s/bin/%(module)s/%(platform)s' % {'app': app,
         'module': module,
         'pythonVersion': version,
         'platform': platformString}
        localPython = sys.executable
        dllsToCopy = dllsFor64bit if is_64bits else dllsFor32Bit
        import ctypes
        for dll in dllsToCopy:
            if dll in loadedDLLs:
                continue
            autobuildVersion = os.path.abspath(os.path.join(__file__, relativeBranchRoot, moduleLocation, dll))
            print 'Loading DLL explicitly from %s' % autobuildVersion
            loadedDLL = ctypes.WinDLL(autobuildVersion)
            loadedDLLs[dll] = loadedDLL
            localVersion = os.path.abspath(os.path.join(sys.executable, '../DLLs/%s' % dll))
            if os.path.exists(localVersion):
                print 'Removing local version from "%s"' % localVersion
                os.remove(localVersion)