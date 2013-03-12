#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\autoexec_common.py
import os
import sys
import blue
import log
import logging
logging.root.setLevel(logging.INFO)
import carbon.logsetup
carbon.logsetup.Init()
try:
    import marshalstrings
except ImportError:
    pass

def ReturnFalse():
    return False


def LogStarting(mode):
    startedat = '%s %s version %s build %s starting %s %s' % (boot.appname,
     mode,
     boot.version,
     boot.build,
     blue.os.FormatUTC()[0],
     blue.os.FormatUTC()[2])
    print startedat
    log.general.Log(startedat, log.LGNOTICE)
    log.general.Log('Python version: ' + sys.version, log.LGNOTICE)
    if blue.win32.IsTransgaming():
        log.general.Log('Transgaming? yes')
        try:
            blue.win32.TGGetOS()
            blue.win32.TGGetSystemInfo()
        except NotImplementedError:
            log.general.Log('TG OS & TG SI: not implemented, pretending not to be TG')
            blue.win32.IsTransgaming = ReturnFalse

    else:
        log.general.Log('Transgaming? no')
    if blue.win32.IsTransgaming():
        log.general.Log('TG OS: ' + blue.win32.TGGetOS(), log.LGNOTICE)
        log.general.Log('TG SI: ' + repr(blue.win32.TGGetSystemInfo()), log.LGNOTICE)
    log.general.Log('Process bits: ' + repr(blue.win32.GetProcessBits()), log.LGNOTICE)
    log.general.Log('Wow64 process? ' + ('yes' if blue.win32.IsWow64Process() else 'no'), log.LGNOTICE)
    log.general.Log('System info: ' + repr(blue.win32.GetSystemInfo()), log.LGNOTICE)
    if blue.win32.IsWow64Process():
        log.general.Log('Native system info: ' + repr(blue.win32.GetNativeSystemInfo()), log.LGNOTICE)


def LogStarted(mode):
    startedat = '%s %s version %s build %s started %s %s' % (boot.appname,
     mode,
     boot.version,
     boot.build,
     blue.os.FormatUTC()[0],
     blue.os.FormatUTC()[2])
    print strx(startedat)
    log.general.Log(startedat, log.LGINFO)
    log.general.Log(startedat, log.LGNOTICE)
    log.general.Log(startedat, log.LGWARN)
    log.general.Log(startedat, log.LGERR)


try:
    blue.SetBreakpadBuildNumber(int(boot.build))
    if blue.win32.IsTransgaming():
        blue.SetCrashKeyValues(u'OS', u'Mac')
    else:
        import ctypes
        try:
            wine = ctypes.windll.ntdll.wine_get_version
            blue.SetCrashKeyValues(u'OS', u'Linux')
        except AttributeError:
            blue.SetCrashKeyValues(u'OS', u'Win')

except RuntimeError:
    pass

if not blue.pyos.packaged:
    import walk
    for root, subdirs, files in walk.walk('resBin:/python'):
        for f in files:
            if f.endswith('.zip'):
                sys.path.append(blue.paths.ResolvePath('/'.join([root, f])))

logdestination = prefs.ini.GetValue('networkLogging', '')
if logdestination:
    networklogport = prefs.ini.GetValue('networkLoggingPort', 12201)
    networklogThreshold = prefs.ini.GetValue('networkLoggingThreshold', 1)
    blue.EnableNetworkLogging(logdestination, networklogport, boot.role, networklogThreshold)
fileLoggingDirectory = prefs.ini.GetValue('fileLogDirectory', '')
if fileLoggingDirectory:
    if not hasattr(blue, 'EnableFileLogging'):
        print 'File Logging configured but not supported'
    else:
        fileLoggingDirectory = os.path.normpath(fileLoggingDirectory)
        fileLoggingThreshold = int(prefs.ini.GetValue('fileLoggingThreshold', 1))
        blue.EnableFileLogging(fileLoggingDirectory, boot.role, fileLoggingThreshold)