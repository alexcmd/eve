#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\trinity\__init__.py
import blue
import walk
import telemetry
import sys
import os
import log
if blue.pyos.packaged:
    DEFAULT_TRI_PLATFORM = 'dx9'
    VALID_TRI_PLATFORMS = ['dx9', 'dx11']
    DEFAULT_TRI_TYPE = 'deploy'
    VALID_TRI_TYPES = ['deploy']
else:
    DEFAULT_TRI_PLATFORM = 'dx9'
    VALID_TRI_PLATFORMS = ['dx9', 'dx11', 'gles2']
    DEFAULT_TRI_TYPE = 'internal'
    VALID_TRI_TYPES = ['deploy', 'internal', 'dev']

def GetEnumValueName(enumName, value):
    if enumName in globals():
        enum = globals()[enumName]
        result = ''
        for enumKeyName, (enumKeyValue, enumKeydocString) in enum.values.iteritems():
            if enumKeyValue == value:
                if result != '':
                    result += ' | '
                result += enumKeyName

        return result


def GetEnumValueNameAsBitMask(enumName, value):
    if enumName in globals():
        enum = globals()[enumName]
        result = ''
        for enumKeyName, (enumKeyValue, enumKeydocString) in enum.values.iteritems():
            if enumKeyValue & value == enumKeyValue:
                if result != '':
                    result += ' | '
                result += enumKeyName

        return result


def ConvertTriFileToGranny(path):
    helper = TriGeometryRes()
    return helper.ConvertTriFileToGranny(path)


def Load(path, nonCached = False):
    if nonCached:
        blue.resMan.loadObjectCache.Delete(path)
    obj = blue.resMan.LoadObject(path)
    return obj


def LoadDone(evt):
    evt.isDone = True


def WaitForResourceLoads():
    blue.resMan.Wait()


def WaitForUrgentResourceLoads():
    blue.resMan.WaitUrgent()


def LoadUrgent(path):
    blue.resMan.SetUrgentResourceLoads(True)
    obj = Load(path)
    blue.resMan.SetUrgentResourceLoads(False)
    return obj


def GetResourceUrgent(path, extra = ''):
    blue.resMan.SetUrgentResourceLoads(True)
    obj = blue.resMan.GetResource(path, extra)
    blue.resMan.SetUrgentResourceLoads(False)
    return obj


def Save(obj, path):
    blue.motherLode.Delete(path)
    return blue.resMan.SaveObject(obj, path)


def SaveRenderTarget(filename, rt = None):
    if rt is None:
        rt = renderContext.GetDefaultBackBuffer()
    if not rt.isReadable:
        readable = Tr2RenderTarget(rt.width, rt.height, 1, rt.format)
        rt.Resolve(readable)
        return Tr2HostBitmap(readable).Save(filename)
    else:
        return Tr2HostBitmap(rt).Save(filename)


def InstallSystemBinaries(fileName):
    installMsg = 'Executing %s ...' % fileName
    print installMsg
    log.general.Log(installMsg)
    oldDir = os.getcwdu()
    os.chdir(blue.paths.ResolvePath(u'bin:/'))
    exitStatus = os.system(fileName)
    os.chdir(oldDir)
    retString = 'Execution of ' + fileName
    if exitStatus:
        retString += ' failed (exit code %d)' % exitStatus
        log.general.Log(retString, log.LGERR)
    else:
        retString += ' succeeded'
        log.general.Log(retString)


def RobustImport(moduleName, moduleNameForFallback = None):
    try:
        mod = __import__(moduleName, fromlist=['*'])
    except ImportError:
        import imp
        if imp.get_suffixes()[0][0] == '_d.pyd':
            InstallSystemBinaries('DirectXRedistForDebug.exe')
        else:
            InstallSystemBinaries('DirectXRedist.exe')
        try:
            mod = __import__(moduleName, fromlist=['*'])
        except ImportError:
            if moduleNameForFallback:
                print 'Import failed on %s, falling back to %s ...' % (moduleName, moduleNameForFallback)
                mod = __import__(moduleNameForFallback, fromlist=['*'])
            else:
                log.Quit('Failed to import trinity DLL')

    for memberName in dir(mod):
        globals()[memberName] = getattr(mod, memberName)

    del mod


def _GetPreferredPlatform():
    hasPrefs = hasattr(__builtins__, 'prefs') or 'prefs' in __builtins__
    if hasPrefs:
        return prefs.GetValue('trinityPreferredPlatform', DEFAULT_TRI_PLATFORM)
    else:
        return DEFAULT_TRI_PLATFORM


def _SetPreferredPlatform(p):
    hasPrefs = hasattr(__builtins__, 'prefs') or 'prefs' in __builtins__
    if hasPrefs:
        prefs.SetValue('trinityPreferredPlatform', p)


def _ImportDll():
    args = blue.pyos.GetArg()
    hasboot = hasattr(__builtins__, 'boot') or 'boot' in __builtins__
    if hasboot and boot.role in ('server', 'proxy') and '/jessica' not in args and '/minime' not in args:
        raise RuntimeError("Don't import trinity on the proxy or server")
    triPlatform = _GetPreferredPlatform()
    triType = DEFAULT_TRI_TYPE
    rightHanded = False
    for arg in args:
        arg = arg.lower()
        if arg.startswith('/triplatform'):
            s = arg.split('=')
            triPlatform = s[1]
        elif arg.startswith('/tritype'):
            s = arg.split('=')
            triType = s[1]
        elif arg == '/righthanded':
            rightHanded = True

    if triType not in VALID_TRI_TYPES:
        log.Quit('Invalid Trinity dll type')
    if triPlatform not in VALID_TRI_PLATFORMS:
        log.Quit('Invalid Trinity platform')
    dllName = '_trinity_%s_%s' % (triPlatform, triType)
    print 'Starting up Trinity through %s ...' % dllName
    RobustImport(dllName)
    if rightHanded:
        SetRightHanded(True)
        settings.SetValue('geometryResNormalizeOnLoad', True)
        print 'Trinity is using a right-handed coordinate system'
    if hasattr(blue.memoryTracker, 'd3dHeap1'):
        if GetD3DCreatedHeapCount() > 0:
            blue.memoryTracker.d3dHeap1 = GetD3DCreatedHeap(0)
        if GetD3DCreatedHeapCount() > 1:
            blue.memoryTracker.d3dHeap2 = GetD3DCreatedHeap(1)
    return triPlatform


platform = _ImportDll()
adapters = blue.classes.CreateInstance('trinity.Tr2VideoAdapters')
try:
    adapterInfo = adapters.GetAdapterInfo(adapters.DEFAULT_ADAPTER)
    blue.SetCrashKeyValues(u'GPU_Description', adapterInfo.description)
    blue.SetCrashKeyValues(u'GPU_Driver', unicode(adapterInfo.driver))
    blue.SetCrashKeyValues(u'GPU_Driver_Version', unicode(adapterInfo.driverVersion))
    blue.SetCrashKeyValues(u'GPU_VendorId', unicode(adapterInfo.vendorID))
    blue.SetCrashKeyValues(u'GPU_DeviceId', unicode(adapterInfo.deviceID))
except RuntimeError:
    pass
except SystemError:
    if platform == 'dx11':
        _SetPreferredPlatform('dx9')
        log.Quit('Video card may not support DX11 - setting preferred platform to DX9')

device = blue.classes.CreateInstance('trinity.TriDevice')
renderContext = device.GetRenderContext()
app = blue.classes.CreateInstance('triui.App')
if hasattr(blue, 'CcpStatistics'):
    statistics = blue.CcpStatistics()
from trinity.renderJob import CreateRenderJob
from trinity.renderJobUtils import *
renderJobs = trinity.renderJob.RenderJobs()
device.SetRenderJobs(renderJobs)

def IsFpsEnabled():
    return bool('FPS' in (j.name for j in renderJobs.recurring))


def SetFpsEnabled(enable, viewPort = None):
    if enable:
        if IsFpsEnabled():
            return
        fpsJob = CreateRenderJob('FPS')
        fpsJob.SetViewport(viewPort)
        fpsJob.RenderFps()
        fpsJob.ScheduleRecurring(insertFront=False)
    else:
        trinity.renderJobs.UnscheduleByName('FPS')


def AddRenderJobText(text, x, y, renderJob, color = 4278255360L):
    steps = [ step for step in renderJob.steps if step.name == 'RenderDebug' ]
    step = None
    if len(steps) > 0:
        step = steps[0]
    else:
        return
    step.Print2D(x, y, color, text)
    return renderJob


def CreateDebugRenderJob(renderJobName, viewPort, renderJobIndex = -1):
    renderJob = trinity.CreateRenderJob(renderJobName)
    renderJob.SetViewport(viewPort)
    step = renderJob.RenderDebug()
    step.name = 'RenderDebug'
    step.autoClear = False
    if renderJobIndex is -1:
        renderJob.ScheduleRecurring()
    else:
        trinity.renderJobs.recurring.insert(renderJobIndex, renderJob)
    return renderJob


from trinity.GraphManager import GraphManager
graphs = GraphManager()

def SetupDefaultGraphs():
    graphs.Clear()
    graphs.AddGraph('frameTime')
    graphs.AddGraph('devicePresent')
    graphs.AddGraph('primitiveCount')
    graphs.AddGraph('batchCount')
    graphs.AddGraph('pendingLoads')
    graphs.AddGraph('pendingPrepares')
    graphs.AddGraph('textureResBytes')


def AddFrameTimeMarker(name):
    line = GetLineGraphFrameTime()
    if line is not None:
        line.AddMarker(name)


class FrameTimeMarkerStopwatch(object):

    def __init__(self, stopwatchName):
        self.started = blue.os.GetCycles()[0]
        self.stopwatchName = stopwatchName

    def __str__(self):
        return '%s %i ms' % (self.stopwatchName, int(1000 * ((blue.os.GetCycles()[0] - self.started) / float(blue.os.GetCycles()[1]))))

    def __del__(self):
        AddFrameTimeMarker(str(self))


def CreateBinding(cs, src, srcAttr, dst, dstAttr):
    binding = TriValueBinding()
    binding.sourceObject = src
    binding.sourceAttribute = srcAttr
    binding.destinationObject = dst
    binding.destinationAttribute = dstAttr
    if cs:
        cs.bindings.append(binding)
    return binding


def CreatePythonBinding(cs, src, srcAttr, dst, dstAttr):
    binding = Tr2PyValueBinding()
    binding.sourceObject = src
    binding.sourceAttribute = srcAttr
    binding.destinationObject = dst
    binding.destinationAttribute = dstAttr
    if cs:
        cs.bindings.append(binding)
    return binding


if not blue.pyos.packaged:
    SetFpsEnabled(True)
if blue.win32.IsTransgaming():
    settings.SetValue('strictShaderCompilation', True)
shaderManager = GetShaderManager()

@telemetry.ZONE_FUNCTION
def PopulateShaderLibrary():
    for path, dirs, files in walk.walk('res:/Graphics/Shaders/ShaderDescriptions'):
        for f in files:
            filepath = path + '/' + f
            if filepath.endswith('.red') or filepath.endswith('.black'):
                highLevelShader = Load(filepath)
                if highLevelShader is not None:
                    try:
                        shaderManager.shaderLibrary.append(highLevelShader)
                    except blue.error as e:
                        log.general.Log('Exception loading High Level Shader: %s' % filepath, log.LGERR)
                        log.LogException()
                        sys.exc_clear()

                else:
                    log.general.Log('Unable to find shader library object: %s' % filepath, log.LGERR)


PopulateShaderLibrary()