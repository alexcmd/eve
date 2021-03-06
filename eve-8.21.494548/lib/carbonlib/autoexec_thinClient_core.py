#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\autoexec_thinClient_core.py
import autoexec_common
import blue
import sys
import os
import log
import bluepy
import localization
Done = False

def Startup(servicesToRun, builtinSetupHook, startInline = [], serviceManagerClass = 'ServiceManager'):
    global Done
    args = blue.pyos.GetArg()[1:]
    autoexec_common.LogStarting('ThinClient')
    additionalScriptDirs = ['script:/../../../client/script/',
     'script:/../../../../carbon/client/script/',
     'script:/../../../../carbon/tools/thinClient/script/',
     'script:/../../../devtools/script/']
    for argument in args:
        if argument.startswith('/cache='):
            cachepath = argument[len('/cache='):]
            blue.paths.SetSearchPath('cache:', cachepath + os.sep)
            log.general.Log('Cache directory set to: ' + blue.paths.ResolvePath(u'cache:/'), log.LGNOTICE)
        elif argument.startswith('/randomcache'):
            import tempfile
            cachepath = tempfile.mkdtemp()
            blue.paths.SetSearchPath('cache:', u'%s' % cachepath + os.sep)
            log.general.Log('Cache directory set to: ' + blue.paths.ResolvePath(u'cache:/'), log.LGNOTICE)

    if '/automaton' in args:
        additionalScriptDirs.extend(['script:/../../../../carbon/backend/script/', 'script:/../../../backend/script/'])
    if not blue.pyos.packaged and '/jessica' in args:
        additionalScriptDirs.extend(['script:/../../../../carbon/tools/jessica/script/', 'script:/../../../../carbon/backend/script/', 'script:/../../../backend/script/'])
        useExtensions = '/noJessicaExtensions' not in args
        if useExtensions:
            additionalScriptDirs.extend(['script:/../../../../carbon/tools/jessicaExtensions/script/', 'script:/../../../tools/jessicaExtensions/script/', 'script:/../tools/jessicaExtensions/script/'])
    import nasty
    nasty.Startup(additionalScriptDirs)
    errorMsg = {'resetsettings': ['The application is unable to clear the settings. If you are running other instances of Eve Online, please exit them. If the problem persists you should restart your system.', 'Cannot clear settings!', 'Cannot clear settings'],
     'clearcache': ['The application is unable to clear the cache. If you are running other instances of Eve Online, please exit them. If the problem persists you should restart your system.', 'Cannot clear cache!', 'Cannot clear cache']}
    for clearType, clearPath in [('resetsettings', blue.paths.ResolvePath(u'settings:/')), ('clearcache', blue.paths.ResolvePath(u'cache:/'))]:
        if getattr(prefs, clearType, 0):
            if clearType == 'resetsettings':
                prefs.DeleteValue(clearType)
            if os.path.exists(clearPath):
                i = 0
                while 1:
                    newDir = clearPath[:-1] + '_backup%s' % i
                    if not os.path.isdir(newDir):
                        try:
                            os.makedirs(newDir)
                        except:
                            blue.win32.MessageBox(errorMsg[clearType][0], errorMsg[clearType][1], 272)
                            bluepy.Terminate(errorMsg[clearType][2])
                            return False

                        break
                    i += 1

                for filename in os.listdir(clearPath):
                    if filename != 'Settings':
                        try:
                            os.rename(clearPath + filename, '%s_backup%s/%s' % (clearPath[:-1], i, filename))
                        except:
                            blue.win32.MessageBox(errorMsg[clearType][0], errorMsg[clearType][1], 272)
                            bluepy.Terminate(errorMsg[clearType][2])
                            return False

                prefs.DeleteValue(clearType)

    mydocs = blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL)
    paths = [blue.paths.ResolvePath(u'cache:/')]
    for path in paths:
        try:
            os.makedirs(path)
        except OSError as e:
            sys.exc_clear()

    import __builtin__, base
    session = base.CreateSession(None, const.session.SESSION_TYPE_GAME)
    __builtin__.session = session
    __builtin__.charsession = session
    builtinSetupHook()
    autoexec_common.LogStarted('ThinClient')
    import numerical
    bluepy.frameClock = numerical.FrameClock()
    blue.os.frameClock = bluepy.frameClock
    import service
    smClass = getattr(service, serviceManagerClass)
    srvMng = smClass(startInline=['DB2', 'machoNet'] + startInline)
    if hasattr(prefs, 'http') and prefs.http:
        print 'http'
        srvMng.Run(('http',))
    srvMng.Run(servicesToRun)
    title = '[%s] %s %s %s.%s pid=%s' % (boot.region.upper(),
     boot.codename,
     boot.role,
     boot.version,
     boot.build,
     blue.os.pid)
    blue.os.SetAppTitle(title)
    Done = True
    if bluepy.IsRunningStartupTest():
        bluepy.TerminateStartupTest()

    def f(*args, **kwargs):
        return 'Malkovich'

    localization.GetByMessageID = f
    localization.GetByLabel = f
    localization.GetImportantByMessageID = f
    localization.GetImportantByLabel = f
    localization._GetRawByMessageID = f
    localization.FormatImportantString = f


def StartClient(servicesToRun, builtinSetupHook, startInline = [], serviceManagerClass = 'ServiceManager'):
    boot.role = 'client'
    t = blue.pyos.CreateTasklet(Startup, (servicesToRun,
     builtinSetupHook,
     startInline,
     serviceManagerClass), {})
    t.context = '^boot::autoexec_thinClient'