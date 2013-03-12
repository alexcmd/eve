#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/ui/services/device.py
import service
import sys
import blue
import uthread
import trinity
import util
import log
import localization
import bluepy

class Const(object):

    def __init__(self, theDict):
        self._dict = theDict

    def __getattr__(self, attr):
        try:
            return self._dict[attr]
        except KeyError:
            raise AttributeError, 'our dict has no key ' + attr

    def __getitem__(self, key):
        return self._dict[key]


class AttribDict(dict):

    def __init__(self, other = {}):
        dict.__init__(self, other)

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, val):
        self[attr] = val


class Rect(object):
    __slots__ = ['width', 'height', 'aspect']

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.aspect = float(width) / float(height)

    def __lt__(self, other):
        return self.aspect < other.aspect or self.aspect == other.aspect and self.width < other.width

    def __eq__(self, other):
        return self.width == other.width and self.height == other.height


class DeviceMgr(service.Service):
    __guid__ = 'svc.device'
    __servicename__ = 'device'
    __displayname__ = 'Device Service'
    __startupdependencies__ = ['settings']
    __exportedcalls__ = {'SetDevice': [],
     'GetSettings': [],
     'GetSaveMode': [],
     'ResetMonitor': [],
     'ToggleWindowed': [],
     'CreateDevice': [],
     'PrepareMain': [],
     'CurrentAdapter': [],
     'GetAdapters': [],
     'GetWindowModes': [],
     'GetAdapterResolutionsAndRefreshRates': [],
     'GetBackbufferFormats': [],
     'GetStencilFormats': [],
     'GetPresentationIntervalOptions': []}
    __depthStencilFormatNameList__ = [trinity.DEPTH_STENCIL_FORMAT.D24S8,
     trinity.DEPTH_STENCIL_FORMAT.D24X4S4,
     trinity.DEPTH_STENCIL_FORMAT.D32,
     trinity.DEPTH_STENCIL_FORMAT.D24X8,
     trinity.DEPTH_STENCIL_FORMAT.D16,
     trinity.DEPTH_STENCIL_FORMAT.D15S1,
     trinity.DEPTH_STENCIL_FORMAT.D24FS8,
     trinity.DEPTH_STENCIL_FORMAT.D16_LOCKABLE,
     trinity.DEPTH_STENCIL_FORMAT.D32F_LOCKABLE]

    def Run(self, memStream = None):
        self.LogInfo('Starting DeviceMgr')
        self.cachedAdapterIdentifiers = []
        for adapter in range(trinity.adapters.GetAdapterCount()):
            adId = trinity.adapters.GetAdapterInfo(adapter)
            self.cachedAdapterIdentifiers.append(adId)

        if settings.public.device.Get('vsync', 1):
            self.defaultPresentationInterval = trinity.PRESENT_INTERVAL.ONE
        else:
            self.defaultPresentationInterval = trinity.PRESENT_INTERVAL.IMMEDIATE
        self.minimumSize = {'width': 1024,
         'height': 768}
        self.AppRun()

    def Initialize(self):
        self.validFormats = [trinity.PIXEL_FORMAT.R10G10B10A2_UNORM,
         trinity.PIXEL_FORMAT.B8G8R8X8_UNORM,
         trinity.PIXEL_FORMAT.B8G8R8A8_UNORM,
         trinity.PIXEL_FORMAT.B5G6R5_UNORM,
         trinity.PIXEL_FORMAT.B5G5R5A1_UNORM]
        self.depthStencilFormats = [ name for name in self.__depthStencilFormatNameList__ ]
        self.settingsBackup = None
        self.positionBackup = None
        self.resolutionBackup = None
        self.adapters = None
        while not self.adapters:
            self.adapters = self.FindDeviceTypeAdapters()
            if not self.adapters:
                trinity.adapters.Refresh()

        self.LogInfo('valid adapters: %s' % self.adapters)
        self.desktopMode = trinity.adapters.GetCurrentDisplayMode(trinity.adapters.DEFAULT_ADAPTER)
        self.preFullScreenPosition = None

    def Stop(self, memStream = None):
        self.LogInfo('Stopping DeviceMgr')
        service.Service.Stop(self)

    def HandleResizeEvent(self, *args):
        triapp = trinity.app
        clientRect = triapp.GetClientRect(triapp.hwnd)
        width = clientRect.right - clientRect.left
        height = clientRect.bottom - clientRect.top
        self.LogInfo('HandleResizeEvent ' + str(width) + ',' + str(height))
        if width < 1 or height < 1:
            self.LogWarn('HandleResizeEvent called with invalid width or height')
            return
        deviceSettings = self.GetSettings()
        deviceSettings.BackBufferWidth = width
        deviceSettings.BackBufferHeight = height
        keepSettings = deviceSettings.Windowed and not triapp.isMaximized
        uthread.new(self.SetDevice, deviceSettings, keepSettings=keepSettings, updateWindowPosition=False)

    def ForceSize(self, width = 512, height = 512):
        deviceSettings = self.GetSettings()
        deviceSettings.BackBufferWidth = width
        deviceSettings.BackBufferHeight = height
        deviceSettings.Windowed = True
        triapp = trinity.app
        triapp.minimumWidth = width
        triapp.minimumHeight = height
        uthread.new(self.SetDevice, deviceSettings, updateWindowPosition=False)

    def CreateDevice(self):
        self.LogInfo('CreateDevice')
        if '/safemode' in blue.pyos.GetArg():
            self.SetToSafeMode()
        triapp = trinity.app
        triapp.title = uicore.triappargs['title']
        triapp.hideTitle = 1
        triapp.fullscreen = 0
        triapp.Create()
        triapp.minimumWidth = self.minimumSize['width']
        triapp.minimumHeight = self.minimumSize['height']
        dev = trinity.device
        while not dev.DoesD3DDeviceExist():
            try:
                self.Initialize()
                triapp = trinity.app
                trinity.device.disableAsyncLoad = not bool(settings.public.generic.Get('asyncLoad', 1))
                if self.IsHDRSupported() and settings.public.device.Get('hdrEnabled', self.GetDefaultHDRState()):
                    dev.hdrEnable = True
                else:
                    dev.hdrEnable = False
                self.SetResourceCacheSize()
                blue.os.sleeptime = 0
                dev.mipLevelSkipCount = settings.public.device.Get('textureQuality', self.GetDefaultTextureQuality())
                trinity.SetShaderModel(self.GetAppShaderModel())
                self.PrepareMain(True)
                if trinity.adapters.SupportsDepthStencilFormat(trinity.adapters.DEFAULT_ADAPTER, trinity.adapters.GetCurrentDisplayMode(trinity.adapters.DEFAULT_ADAPTER).format, trinity.DEPTH_STENCIL_FORMAT.READABLE):
                    trinity.AddGlobalSituationFlags(['OPT_INTZ'])
                else:
                    trinity.RemoveGlobalSituationFlags(['OPT_INTZ'])
                try:
                    trinity.RebindAllShaderMaterials()
                except:
                    pass

            except trinity.D3DERR_NOTAVAILABLE as e:
                sys.exc_clear()
                trinity.adapters.Refresh()

        if not blue.win32.IsTransgaming():
            resizeEventHandler = blue.BlueEventToPython()
            resizeEventHandler.handler = self.HandleResizeEvent
            triapp.resizeEventListener = resizeEventHandler
        for k, v in self.GetAppSettings().iteritems():
            trinity.settings.SetValue(k, v)

        for dir in self.GetAppMipLevelSkipExclusionDirectories():
            trinity.AddMipLevelSkipExclusionDirectory(dir)

    def PrepareMain(self, muteExceptions = False):
        self.LogInfo('PrepareMain')
        safe = self.GetSaveMode().__dict__
        personal = settings.public.device.Get('DeviceSettings', safe).copy()
        if 'PresentationInterval' in personal and personal['PresentationInterval'] & 16 == 0:
            self.LogInfo('Upgrading PresentationInterval setting')
            if personal['PresentationInterval'] == -0x80000000:
                personal['PresentationInterval'] = trinity.PRESENT_INTERVAL.IMMEDIATE
            elif personal['PresentationInterval'] == 0:
                personal['PresentationInterval'] = trinity.PRESENT_INTERVAL.ONE
            else:
                personal['PresentationInterval'] = trinity.PRESENT_INTERVAL.ONE + personal['PresentationInterval'] - 1
        safe.update(personal)
        triapp = trinity.app
        set = util.KeyVal()
        set.__doc__ = 'Device set'
        set.__dict__ = safe
        set.hDeviceWindow = triapp.GetHwnd()
        self.SetDevice(set, hideTitle=not set.Windowed, keepSettings=False, muteExceptions=muteExceptions)

    def ResetMonitor(self, fallback = 1, *args):
        self.LogInfo('ResetMonitor')
        set = self.GetSaveMode()
        self.SetDevice(set, fallback=fallback, hideTitle=not set.Windowed)

    def FindDeviceTypeAdapters(self):
        result = []
        for adapter in range(len(self.cachedAdapterIdentifiers)):
            for format in self.validFormats:
                if trinity.adapters.SupportsBackBufferFormat(adapter, format, False):
                    result.append(adapter)
                    break

        return result

    def GetValidDepthStencilFormats(self, adapter, displayFormat):
        result = []
        for f in self.depthStencilFormats:
            if not trinity.adapters.SupportsDepthStencilFormat(adapter, displayFormat, f):
                continue
            result.append(f)

        return result

    def GetValidWindowedFormats(self, adapter = 0, displayFormat = None):
        if not displayFormat:
            displayFormat = self.desktopMode.format
        if displayFormat not in self.validFormats:
            return []
        result = []
        for bbFormat in self.validFormats:
            if not trinity.adapters.SupportsRenderTargetFormat(adapter, displayFormat, bbFormat):
                continue
            dsFormats = self.GetValidDepthStencilFormats(adapter, displayFormat)
            for dsFormat in dsFormats:
                result.append((bbFormat, dsFormat))

        return result

    def GetValidFullscreenModes(self, adapter = 0):
        result = []
        for format in self.validFormats:
            try:
                if not trinity.adapters.SupportsBackBufferFormat(adapter, format, False):
                    continue
            except:
                continue

            if not self.GetValidDepthStencilFormats(adapter, format):
                continue
            try:
                for m in range(trinity.adapters.GetDisplayModeCount(adapter, format)):
                    result.append(trinity.adapters.GetDisplayMode(adapter, format, m))

            except:
                pass

        result = [ mode for mode in result if mode.height > 0 and mode.width > 0 ]

        def Cmp(x, y):
            rx = Rect(x.width, x.height)
            ry = Rect(y.width, y.height)
            if rx < ry:
                return -1
            if rx > ry:
                return 1
            if x.format < y.format:
                return -1
            if x.format > y.format:
                return 1
            return 0

        result.sort(Cmp)
        for i in xrange(len(result)):
            if i >= len(result):
                break
            while i + 1 < len(result) and result[i].width == result[i + 1].width and result[i].height == result[i + 1].height and result[i].format == result[i + 1].format:
                del result[i + 1]

        if not result:
            raise RuntimeError('No valid fullscreen modes found')
        return result

    def GetDefaultWindowedMode(self, adapter = None, dim = None):
        self.LogInfo('GetDefaultWindowedMode')
        formats = self.GetValidWindowedFormats(adapter)
        self.LogInfo('Valid windowed formats:', formats)
        if not formats:
            return
        if dim:
            width, height = dim
        else:
            width, height = self.desktopMode.width, self.desktopMode.height
        if width > self.desktopMode.width or height > self.desktopMode.height:
            return
        displayFormat = self.desktopMode.format
        chosen = None
        for f in formats:
            if f[0] == displayFormat:
                chosen = f
                break

        if not chosen:
            chosen = formats[0]
        bbFormat, dsFormat = chosen
        self.LogInfo('Chosen format', bbFormat, dsFormat)
        result = {'Windowed': 1,
         'BackBufferFormat': bbFormat,
         'AutoDepthStencilFormat': dsFormat,
         'BackBufferWidth': width,
         'BackBufferHeight': height}
        return result

    def GetDefaultFullscreenMode(self, adapter, dim = None):
        self.LogInfo('GetDefaultFullscreenMode')
        modes = self.GetValidFullscreenModes(adapter)
        if dim:
            a = {}
            for mode in modes:
                aspect = float(mode.width) / float(mode.height)
                if aspect not in a:
                    a[aspect] = []
                a[aspect].append(mode)

            width, height = dim
            aspect = float(width) / float(height)
            closest = None
            for other in a.keys():
                if closest is None or abs(other - aspect) < abs(closest - aspect):
                    closest = other

            modes = a[closest]
            greater = [ mode for mode in modes if mode.height >= height and mode.width >= width ]
            if greater:
                modes = greater
            else:
                modes.reverse()
            width, height = modes[0].width, modes[0].height
        else:
            width, height = modes[-1].width, modes[-1].height
        modes = [ mode for mode in modes if mode.height == height and mode.width == width ]
        dsFormat = None
        for bbFormat in self.validFormats:
            m = None
            for mode in modes:
                if mode.format == bbFormat:
                    m = mode
                    break

            if not m:
                continue
            if not trinity.adapters.SupportsRenderTargetFormat(adapter, bbFormat, bbFormat):
                continue
            dsFormats = self.GetValidDepthStencilFormats(adapter, bbFormat)
            if not dsFormats:
                continue
            dsFormat = dsFormats[0]
            break

        if not dsFormat:
            raise RuntimeError('No Defautl Fullscreen mode found')
        result = {'Windowed': 0,
         'BackBufferFormat': bbFormat,
         'AutoDepthStencilFormat': dsFormat,
         'BackBufferWidth': width,
         'BackBufferHeight': height}
        return result

    def GetFailsafeMode(self, adapter, windowed, dimensions = None):
        desktopdim = (self.desktopMode.width, self.desktopMode.height)
        if not dimensions:
            dimensions = desktopdim
        mode = None
        if windowed:
            mode = self.GetDefaultWindowedMode(adapter, dimensions)
            if not mode:
                return
        else:
            mode = self.GetDefaultFullscreenMode(adapter, dimensions)
        if not mode:
            mode = self.GetDefaultFullscreenMode(adapter, None)
        mode = Const(mode)
        presentation = AttribDict()
        presentation.BackBufferWidth = mode.BackBufferWidth
        presentation.BackBufferHeight = mode.BackBufferHeight
        presentation.BackBufferFormat = mode.BackBufferFormat
        presentation.AutoDepthStencilFormat = mode.AutoDepthStencilFormat
        presentation.Windowed = mode.Windowed
        presentation.BackBufferCount = 1
        presentation.MultiSampleType = 1
        presentation.MultiSampleQuality = 0
        presentation.SwapEffect = trinity.SWAP_EFFECT.DISCARD
        presentation.hDeviceWindow = None
        presentation.EnableAutoDepthStencil = 1
        presentation.FullScreen_RefreshRateInHz = 0
        presentation.PresentationInterval = self.defaultPresentationInterval
        creation = AttribDict()
        creation.Adapter = adapter
        creation.PresentationParameters = presentation
        return creation

    def IsWindowed(self, devSettings = None):
        if devSettings is None:
            devSettings = self.GetSettings()
        return devSettings.Windowed

    def ValidatePresentation(self, adapter, pp):
        pp = Const(pp)
        if self.IsWindowed(pp):
            selected = (pp.BackBufferFormat, pp.AutoDepthStencilFormat)
            valid = self.GetValidWindowedFormats(adapter)
            if valid and selected in valid:
                return 1
        else:
            valid = self.GetValidFullscreenModes(adapter)
            valid = [ item for item in valid if item.format == pp.BackBufferFormat and item.width == pp.BackBufferWidth and item.height == pp.BackBufferHeight ]
            if valid:
                if pp.AutoDepthStencilFormat in self.GetValidDepthStencilFormats(adapter, pp.BackBufferFormat):
                    return 1
        return 0

    def FixupPresentation(self, adapter, pp):
        if self.ValidatePresentation(adapter, pp):
            return pp
        pp = AttribDict(pp)
        create = self.GetFailsafeMode(adapter, pp.Windowed, (pp.BackBufferWidth, pp.BackBufferHeight))
        if not create:
            create = self.GetFailsafeMode(adapter, 0, (pp.BackBufferWidth, pp.BackBufferHeight))
        return create.PresentationParameters

    def CreationToSettings(self, creation):
        set = util.KeyVal()
        set.__doc__ = 'Device set'
        for t in ['BackBufferFormat',
         'FullScreen_RefreshRateInHz',
         'Windowed',
         'BackBufferWidth',
         'BackBufferHeight',
         'BackBufferCount',
         'MultiSampleType',
         'MultiSampleQuality',
         'EnableAutoDepthStencil',
         'PresentationInterval',
         'hDeviceWindow',
         'SwapEffect',
         'AutoDepthStencilFormat']:
            set.__dict__[t] = creation.PresentationParameters[t]

        set.Adapter = creation.Adapter
        return set

    def GetSaveMode(self):
        self.LogInfo('GetSaveMode')
        set = self.GetSettings()
        windowed = 0
        adapter = self.adapters[0]
        create = self.GetFailsafeMode(adapter, windowed, (trinity.device.adapterWidth, trinity.device.adapterHeight))
        if not create:
            create = self.GetFailsafeMode(adapter, not windowed, (trinity.device.adapterWidth, trinity.device.adapterHeight))
        return self.CreationToSettings(create)

    def GetPreferedResolution(self, windowed):
        if windowed:
            lastWindowed = settings.public.device.Get('WindowedResolution', None)
            if lastWindowed is not None:
                return lastWindowed
            else:
                return (trinity.device.adapterWidth, trinity.device.adapterHeight)
        else:
            lastFullScreen = settings.public.device.Get('FullScreenResolution', None)
            if lastFullScreen is not None:
                return lastFullScreen
            return (trinity.device.adapterWidth, trinity.device.adapterHeight)

    def ToggleWindowed(self, *args):
        self.LogInfo('ToggleWindowed')
        triapp = trinity.app
        set = self.GetSettings()
        if set.Windowed:
            wr = triapp.GetWindowRect()
            self.preFullScreenPosition = (wr.left, wr.top)
        set.FullScreen_RefreshRateInHz = self.CurrentAdapter().refreshRateDenominator
        set.Windowed = not set.Windowed
        set.BackBufferWidth, set.BackBufferHeight = self.GetPreferedResolution(set.Windowed)
        self.SetDevice(set, hideTitle=not set.Windowed)

    def EnforceDeviceSettings(self, deviceSettings):
        advanced = settings.public.device.Get('advancedDevice', 0)
        deviceSettings.PresentationInterval = (self.defaultPresentationInterval, deviceSettings.PresentationInterval)[advanced]
        return deviceSettings

    def BackupSettings(self):
        self.resolutionBackup = (trinity.device.adapterWidth, trinity.device.adapterHeight)
        self.settingsBackup = self.GetSettings()
        if self.settingsBackup.Windowed:
            wr = trinity.app.GetWindowRect()
            self.positionBackup = (wr.left, wr.top)

    def SanitizeDeviceTypes(self, device):
        if type(device.PresentationInterval) == long:
            device.PresentationInterval = int(device.PresentationInterval)

    def SetDevice(self, device, tryAgain = 1, fallback = 0, keepSettings = 1, hideTitle = None, userModified = False, muteExceptions = False, updateWindowPosition = True):
        if hideTitle is None:
            hideTitle = not device.Windowed
        self.LogInfo('SetDevice: tryAgain', tryAgain, 'fallback', fallback, 'keepSettings', keepSettings, 'hideTitle', hideTitle, 'deviceDict', device.__dict__)
        if not fallback:
            device = self.EnforceDeviceSettings(device)
        self.SanitizeDeviceTypes(device)
        change = self.CheckDeviceDifference(device, getChange=1)
        dev = trinity.device
        if not change and tryAgain and dev.DoesD3DDeviceExist():
            return
        sm.ChainEvent('ProcessDeviceChange')
        self.LogInfo('SetDevice: Found a difference')
        pr = []
        for k, v in device.__dict__.items():
            pr.append((k, v))

        pr.sort()
        self.LogInfo(' ')
        self.LogInfo('-' * 100)
        self.LogInfo('SetDevice')
        self.LogInfo('-' * 100)
        for k, v in pr:
            extra = ''
            if k in change:
                extra = '   >> this one changed, it was ' + str(change[k][0])
            self.LogInfo('        ' + str(k) + ':    ' + str(v) + extra)

        self.LogInfo('-' * 100)
        triapp = trinity.app
        if tryAgain:
            self.BackupSettings()
        try:
            triapp.hideTitle = hideTitle
            triapp.AdjustWindowForChange(device.Windowed, settings.public.device.Get('FixedWindow', False))
            self.LogInfo('before')
            self.LogInfo(repr(device.__dict__))
            if device.Adapter not in self.adapters:
                device.Adapter = self.adapters[0]
            device.__dict__.update(self.FixupPresentation(device.Adapter, device.__dict__))
            self.LogInfo('apter')
            self.LogInfo(repr(device.__dict__))
            dev = trinity.device
            dev.viewport.width = device.BackBufferWidth
            dev.viewport.height = device.BackBufferHeight
            while True:
                try:
                    triapp.ChangeDevice(device.Adapter, 0, 0, device.__dict__)
                    break
                except trinity.D3DERR_DEVICELOST:
                    blue.pyos.synchro.SleepWallclock(1000)

        except Exception as e:
            import traceback
            self.LogInfo('*' * 100)
            self.LogInfo(traceback.format_exc())
            self.LogInfo('*' * 100)
            self.LogInfo(repr(device.__dict__))
            if trinity.device.GetRenderingPlatformID() == 2:
                if prefs.HasKey('trinityPreferredPlatform') and prefs.GetValue('trinityPreferredPlatform') == 'dx11':
                    prefs.SetValue('trinityPreferredPlatform', 'dx9')
                    log.Quit('Failed to create device under DX11 - setting preferred platform to DX9')
                else:
                    log.Quit('Failed to create device under DX11')
            if tryAgain and self.settingsBackup:
                sys.exc_clear()
                self.LogInfo('SetDevice failed, trying again with backup settings')
                self.SetDevice(self.settingsBackup, 0, keepSettings=keepSettings)
                return
            if not fallback:
                sys.exc_clear()
                self.LogInfo('SetDevice with backup settings failed, falling back to savemode')
                set = self.GetSaveMode()
                self.SetDevice(set, fallback=1, tryAgain=0, hideTitle=not set.Windowed, keepSettings=False)
                return
            if muteExceptions:
                log.LogException()
                sys.exc_clear()
            self.LogInfo('SetDevice failed completely')
            self.LogInfo('-' * 100)
            self.LogInfo(' ')
            return

        self.LogInfo(' ')
        self.SetBloom(dev)
        if updateWindowPosition:
            self.UpdateWindowPosition(device)
        else:
            wr = triapp.GetWindowRect()
            triapp.SetWindowPos(wr.left, wr.top)
        sm.ScatterEvent('OnSetDevice')
        if uicore.desktop:
            uicore.desktop.UpdateSize()
        if keepSettings:
            set = self.GetSettings()
            keep = set.__dict__
            del keep['hDeviceWindow']
            settings.public.device.Set('DeviceSettings', keep)
            self.settings.SaveSettings()
            self.LogInfo('Keeping device settings:', repr(keep))
            if self.IsWindowed(set):
                settings.public.device.Set('WindowedResolution', (set.BackBufferWidth, set.BackBufferHeight))
            else:
                settings.public.device.Set('FullScreenResolution', (set.BackBufferWidth, set.BackBufferHeight))
                if userModified and self.resolutionBackup and self.resolutionBackup != (set.BackBufferWidth, set.BackBufferHeight):
                    self.AskForConfirmation()
        sm.ScatterEvent('OnEndChangeDevice', change)
        unsupportedModels = ['SM_1_1', 'SM_2_0_LO', 'SM_2_0_HI']
        maxCardModel = trinity.GetMaxShaderModelSupported()
        if maxCardModel in unsupportedModels:
            message = localization.GetByLabel('/Carbon/UI/Service/Device/ShaderModelNotSupportedMessage')
            title = localization.GetByLabel('/Carbon/UI/Service/Device/ShaderModelNotSupportedTitle')
            ret = blue.win32.MessageBox(message, title, 48)
            bluepy.Terminate('Shader Model version check failed')

    def UpdateWindowPosition(self, set = None):
        if set is None:
            set = self.GetSettings()
        triapp = trinity.app
        x, y = (0, 0)
        if set.Windowed:
            currentAdapter = self.CurrentAdapter()
            if self.preFullScreenPosition:
                x, y = self.preFullScreenPosition
            else:
                x = (currentAdapter.width - set.BackBufferWidth) / 2
                y = (currentAdapter.height - set.BackBufferHeight) / 2 - 32
            x = max(0, min(x, currentAdapter.width - set.BackBufferWidth))
            y = max(0, min(y, currentAdapter.height - set.BackBufferHeight))
        triapp.SetWindowPos(x, y)

    def AskForConfirmation(self):
        loadingSvc = sm.GetService('loading')
        if hasattr(loadingSvc, 'CountDownWindow'):
            sm.GetService('loading').CountDownWindow(localization.GetByLabel('/Carbon/UI/Service/Device/KeepDisplayChanges'), 15000, self.KeepChanges, self.DiscardChanges, inModalLayer=1)

    def DiscardChanges(self, *args):
        if self.settingsBackup:
            self.SetDevice(self.settingsBackup)

    def KeepChanges(self, *args):
        pass

    def CheckDeviceDifference(self, set, getChange = 0):
        current = self.GetSettings()
        change = {}
        for k, v in set.__dict__.items():
            if k in ('FullScreen_RefreshRateInHz', 'hDeviceWindow', '__doc__'):
                continue
            initvalue = getattr(current, k, 'not set')
            if initvalue == 'not set' or initvalue != v:
                if not getChange:
                    return (k, initvalue, v)
                change[k] = (initvalue, v)

        if getChange:
            return change
        return 0

    def ForceSetup(self, device, z = 0):
        dev = trinity.device
        dev.viewport.width = device.BackBufferWidth
        dev.viewport.height = device.BackBufferHeight
        triapp = trinity.app
        triapp.ChangeDevice(device.Adapter, 0, 1, device.__dict__)

    def GetSettings(self, *args):
        current = trinity.device.GetPresentParameters()
        triapp = trinity.app
        set = util.KeyVal()
        set.__doc__ = 'Device set'
        set.__dict__ = current
        set.Adapter = trinity.device.adapter
        if set.Adapter not in self.adapters:
            set.Adapter = self.adapters[0]
        set.hDeviceWindow = triapp.GetHwnd()
        set.SwapEffect = trinity.SWAP_EFFECT.DISCARD
        return set

    def CurrentAdapter(self, set = None):
        self.LogInfo('CurrentAdapter')
        set = set or self.GetSettings()
        return trinity.adapters.GetCurrentDisplayMode(set.Adapter)

    def GetAdapters(self):
        self.LogInfo('GetAdapters')
        options = []
        for i in xrange(len(self.cachedAdapterIdentifiers)):
            identifier = self.cachedAdapterIdentifiers[i]
            options.append((str(identifier.description), i))

        return options

    def GetAdaptersEnumerated(self):
        self.LogInfo('GetAdapters')
        options = []
        for i in xrange(len(self.cachedAdapterIdentifiers)):
            identifier = self.cachedAdapterIdentifiers[i]
            identifierDesc = str(identifier.description)
            identifierDesc += ' ' + str(i + 1)
            options.append((identifierDesc, i))

        return options

    def GetWindowModes(self):
        self.LogInfo('GetWindowModes')
        adapter = self.CurrentAdapter()
        fullscreenModeLabel = localization.GetByLabel('/Carbon/UI/Service/Device/FullScreen')
        windowModeLabel = localization.GetByLabel('/Carbon/UI/Service/Device/WindowMode')
        if blue.win32.IsTransgaming() or adapter.format not in self.validFormats:
            return [(fullscreenModeLabel, 0)]
        else:
            return [(windowModeLabel, 1), (fullscreenModeLabel, 0)]

    def GetBackbufferFormats(self, set = None):
        self.LogInfo('GetBackbufferFormats')
        set = set or self.GetSettings()
        options = []
        for formatVal in self.validFormats:
            if set.Windowed:
                adapterFormatVal = self.CurrentAdapter().format
                if formatVal == trinity.PIXEL_FORMAT.R10G10B10A2_UNORM:
                    continue
            else:
                adapterFormatVal = formatVal
                if not trinity.adapters.SupportsBackBufferFormat(set.Adapter, adapterFormatVal, False):
                    continue
            if not trinity.adapters.GetDisplayModeCount(set.Adapter, adapterFormatVal):
                continue
            if not trinity.adapters.SupportsRenderTargetFormat(set.Adapter, adapterFormatVal, formatVal):
                continue
            options.append(formatVal)

        return options

    def DebugRes(self):
        currentAdapter = self.CurrentAdapter()
        set = self.GetSettings()
        if set.Windowed:
            set.FullScreen_RefreshRateInHz = 0
        elif not set.FullScreen_RefreshRateInHz:
            set.FullScreen_RefreshRateInHz = currentAdapter.refreshRateDenominator

    def GetAdapterResolutionsAndRefreshRates(self, set = None):
        self.LogInfo('GetAdapterResolutionsAndRefreshRates')
        currentAdapter = self.CurrentAdapter()
        set = set or self.GetSettings()
        if self.IsWindowed(set):
            set.FullScreen_RefreshRateInHz = 0
            checkFormat = currentAdapter.format
        else:
            checkFormat = set.BackBufferFormat
            if not set.FullScreen_RefreshRateInHz:
                set.FullScreen_RefreshRateInHz = currentAdapter.refreshRateDenominator
        options = []
        refresh = {}
        for modeIx in range(trinity.adapters.GetDisplayModeCount(set.Adapter, checkFormat)):
            ops = trinity.adapters.GetDisplayMode(set.Adapter, checkFormat, modeIx)
            if ops.width < self.minimumSize['width'] or ops.height < self.minimumSize['height']:
                continue
            if set.Windowed and ops.refreshRateDenominator - trinity.device.adapterRefreshRate > 1:
                continue
            option = (localization.GetByLabel('/Carbon/UI/Service/Device/ScreenSize', width=ops.width, height=ops.height), (ops.width, ops.height))
            if option not in options:
                options.append(option)
            if (ops.width, ops.height) not in refresh:
                refresh[ops.width, ops.height] = []
            if not set.Windowed and ops.refreshRateDenominator not in refresh[ops.width, ops.height]:
                refresh[ops.width, ops.height].append(ops.refreshRateDenominator)

        option = (localization.GetByLabel('/Carbon/UI/Service/Device/ScreenSize', width=currentAdapter.width, height=currentAdapter.height), (currentAdapter.width, currentAdapter.height))
        if option not in options:
            options.append(option)
        if (currentAdapter.width, currentAdapter.height) not in refresh:
            refresh[currentAdapter.width, currentAdapter.height] = [currentAdapter.refreshRateDenominator]
        resoptions = []
        if (set.BackBufferWidth, set.BackBufferHeight) in refresh:
            resoptions = [ (localization.GetByLabel('/Carbon/UI/Common/HertzShort', hertz=rr), rr) for rr in refresh[set.BackBufferWidth, set.BackBufferHeight] ]
        return (options, resoptions)

    def GetStencilFormats(self, set = None):
        self.LogInfo('GetStencilFormats')
        set = set or self.GetSettings()
        options = []
        for bbFormat in self.depthStencilFormats:
            if not trinity.adapters.SupportsDepthStencilFormat(set.Adapter, self.CurrentAdapter().format, bbFormat):
                continue
            options.append(bbFormat)

        return options

    def GetPresentationIntervalOptions(self, set = None):
        self.LogInfo('GetPresentationIntervalOptions')
        set = set or self.GetSettings()
        options = []
        presentintvals = {trinity.PRESENT_INTERVAL.IMMEDIATE: localization.GetByLabel('/Carbon/UI/Service/Device/PresentationIntervalImmediate'),
         trinity.PRESENT_INTERVAL.ONE: localization.GetByLabel('/Carbon/UI/Service/Device/PresentationIntervalOne')}
        if not set.Windowed:
            presentintvals[trinity.PRESENT_INTERVAL.TWO] = localization.GetByLabel('/Carbon/UI/Service/Device/PresentationIntervalTwo')
            presentintvals[trinity.PRESENT_INTERVAL.THREE] = localization.GetByLabel('/Carbon/UI/Service/Device/PresentationIntervalThree')
            presentintvals[trinity.PRESENT_INTERVAL.FOUR] = localization.GetByLabel('/Carbon/UI/Service/Device/PresentationIntervalFour')
        for key, value in presentintvals.iteritems():
            options.append((value, key))

        return options

    def SupportsSM3(self, adapter = 0):
        return trinity.adapters.GetShaderVersion(adapter) >= 3.0

    def SetBloom(self, dev = None):
        if not self.IsBloomSupported():
            return
        self.bloomType = settings.public.device.Get('bloomType', self.GetDefaultBloomType())

    def GetBloom(self):
        dev = trinity.device
        return getattr(self, 'bloomType', 0)

    def SetHdr(self, enabled):
        dev = trinity.device
        if self.IsHDRSupported():
            if dev.hdrEnable != enabled:
                dev.hdrEnable = enabled

    def IsHdrEnabled(self):
        dev = trinity.device
        return bool(dev.hdrEnable and dev.postProcess)

    def SetResourceCacheSize(self):
        cacheSize = 1
        if settings.public.device.Get('resourceCacheEnabled', self.GetDefaultResourceState()):
            textureQuality = settings.public.device.Get('textureQuality', self.GetDefaultTextureQuality())
            if textureQuality == 2:
                cacheSize = 1
            elif textureQuality == 1:
                cacheSize = 32
            else:
                cacheSize = 128
        self.LogInfo('Setting resource cache size to', cacheSize, 'MB')
        dev = trinity.device
        MEG = 1048576
        finalSize = cacheSize * MEG
        blue.motherLode.maxMemUsage = finalSize
        return finalSize

    def GetResourceCacheSize(self):
        dev = trinity.device
        return dev.GetResourceCacheSize()

    def ResetDevice(self):
        dev = trinity.device
        self.SetHdr(bool(settings.public.device.Get('hdrEnabled', self.GetDefaultHDRState())))
        dev.ResetDeviceResources()

    def SetToSafeMode(self):
        settings.public.device.Set('textureQuality', 2)
        settings.public.device.Set('shaderQuality', 1)
        settings.public.device.Set('hdrEnabled', 0)
        settings.public.device.Set('bloomType', 0)
        settings.public.device.Set('shadowsEnabled', 0)
        settings.public.device.Set('resourceCacheEnabled', 0)

    def GetVendorIDAndDeviceID(self):
        dev = trinity.device
        identifier = self.cachedAdapterIdentifiers[dev.adapter]
        vendorID = identifier.vendorID
        deviceID = identifier.deviceID
        return (vendorID, deviceID)

    def GetDefaultTextureQuality(self):
        if blue.win32.IsTransgaming():
            vID, dID = self.GetVendorIDAndDeviceID()
            if vID == 32902 and dID == 10146:
                return 2
            elif vID == 32902 and dID == 10754:
                return 2
            elif vID == 4098 and dID == 29063:
                return 1
            elif vID == 4098 and dID == 29125:
                return 1
            elif vID == 4318 and dID == 917:
                return 1
            elif vID == 4318 and dID == 913:
                return 1
            else:
                return 0
        else:
            return 0

    def GetDefaultShaderQuality(self):
        if blue.win32.IsTransgaming():
            vID, dID = self.GetVendorIDAndDeviceID()
            if vID == 32902 and dID == 10146:
                return 1
            elif vID == 32902 and dID == 10754:
                return 1
            elif vID == 4098 and dID == 29063:
                return 1
            elif vID == 4098 and dID == 29125:
                return 1
            elif vID == 4318 and dID == 917:
                return 1
            elif vID == 4318 and dID == 913:
                return 1
            else:
                return 3
        else:
            return 3

    def GetDefaultLodQuality(self):
        return 3

    def GetDefaultBloomType(self):
        return 0

    def GetDefaultHDRState(self):
        return 0

    def GetDefaultShadowState(self):
        if self.SupportsSM3():
            return 1
        else:
            return 0

    def GetDefaultResourceState(self):
        return 0

    def IsHDRSupported(self):
        if blue.win32.IsTransgaming():
            vID, dID = self.GetVendorIDAndDeviceID()
            if vID == 32902 and dID == 10146:
                return False
            if vID == 32902 and dID == 10754:
                return False
            if vID == 4098 and dID == 29063:
                return False
            if vID == 4098 and dID == 29125:
                return False
            if vID == 4098 and dID == 29257:
                return False
            if vID == 4318 and dID == 917:
                return False
            if vID == 4318 and dID == 913:
                return False
        if self.SupportsSM3():
            return True
        else:
            return False

    def IsShadowingSupported(self):
        if blue.win32.IsTransgaming():
            vID, dID = self.GetVendorIDAndDeviceID()
            if vID == 32902 and dID == 10146:
                return False
            if vID == 32902 and dID == 10754:
                return False
            if vID == 4098 and dID == 29063:
                return False
            if vID == 4098 and dID == 29125:
                return False
            if vID == 4098 and dID == 29257:
                return False
            if vID == 4318 and dID == 917:
                return False
            if vID == 4318 and dID == 913:
                return False
        if self.SupportsSM3():
            return True
        else:
            return False

    def IsBloomSupported(self):
        if blue.win32.IsTransgaming():
            vID, dID = self.GetVendorIDAndDeviceID()
            if vID == 32902 and dID == 10146:
                return False
            if vID == 32902 and dID == 10754:
                return False
            if vID == 4098 and dID == 29063:
                return False
            if vID == 4098 and dID == 29125:
                return False
            if vID == 4098 and dID == 29257:
                return False
            if vID == 4318 and dID == 917:
                return False
            if vID == 4318 and dID == 913:
                return False
        return True

    def AppRun(self):
        pass

    def GetAppShaderModel(self):
        sm = None
        if settings.public.device.Get('shaderModelLow', 0):
            sm = 'SM_3_0_LO'
        else:
            sm = 'SM_3_0_HI'
        return sm

    def GetAppSettings(self):
        return {}

    def GetAppMipLevelSkipExclusionDirectories(self):
        return []

    def GetAppFeatureState(self, featureName, featureDefault):
        return featureDefault