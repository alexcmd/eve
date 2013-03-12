#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\trinity\renderJobUtils.py
import trinity
import blue

class RenderTargetManager(object):

    def __init__(self):
        trinity.device.RegisterResource(self)
        self.targets = {}

    def OnCreate(self, device):
        pass

    def OnInvalidate(self, level):
        self.targets = {}

    def _Get(self, key, function, *args):
        if self.targets.has_key(key) and self.targets[key].object is not None:
            return self.targets[key].object

        def DeleteObject():
            self.targets.pop(key)

        rt = function(*args)
        self.targets[key] = blue.BluePythonWeakRef(rt)
        self.targets[key].callback = DeleteObject
        return rt

    @staticmethod
    def _CreateDepthStencilAL(width, height, format, msaaType, msaaQuality):
        ds = trinity.Tr2DepthStencil()
        ds.Create(width, height, format, msaaType, msaaQuality)
        return ds

    def GetDepthStencilAL(self, width, height, format, msaaType = 1, msaaQuality = 0, index = 0):
        key = (RenderTargetManager._CreateDepthStencilAL,
         index,
         width,
         height,
         format,
         msaaType,
         msaaQuality)
        return self._Get(key, RenderTargetManager._CreateDepthStencilAL, width, height, format, msaaType, msaaQuality)

    @staticmethod
    def _CreateRenderTargetAL(width, height, mipLevels, format):
        rt = trinity.Tr2RenderTarget()
        rt.Create(width, height, mipLevels, format)
        return rt

    @staticmethod
    def _CreateRenderTargetMsaaAL(width, height, format, msaaType, msaaQuality):
        rt = trinity.Tr2RenderTarget()
        rt.CreateMsaa(width, height, format, msaaType, msaaQuality)
        return rt

    def GetRenderTargetAL(self, width, height, mipLevels, format, index = 0):
        key = (RenderTargetManager._CreateRenderTargetAL,
         index,
         width,
         height,
         mipLevels,
         format)
        return self._Get(key, RenderTargetManager._CreateRenderTargetAL, width, height, mipLevels, format)

    def GetRenderTargetMsaaAL(self, width, height, format, msaaType, msaaQuality, index = 0):
        key = (RenderTargetManager._CreateRenderTargetMsaaAL,
         index,
         width,
         height,
         format,
         msaaType,
         msaaQuality)
        return self._Get(key, RenderTargetManager._CreateRenderTargetMsaaAL, width, height, format, msaaType, msaaQuality)

    def CheckRenderTarget(self, target, width, height, format):
        return target.width == width and target.height == height and target.format == format


renderTargetManager = RenderTargetManager()

def DeviceSupportsIntZ():
    adapters = trinity.adapters
    return adapters.SupportsDepthStencilFormat(adapters.DEFAULT_ADAPTER, adapters.GetCurrentDisplayMode(adapters.DEFAULT_ADAPTER).format, trinity.DEPTH_STENCIL_FORMAT.READABLE)


def DeviceSupportsRenderTargetFormat(format):
    adapters = trinity.adapters
    return adapters.GetDepthStencilMsaaSupport(adapters.DEFAULT_ADAPTER, adapters.GetCurrentDisplayMode(adapters.DEFAULT_ADAPTER).format, format)


def ConvertDepthFormatToALFormat(format):
    td = trinity.DEPTH_STENCIL_FORMAT
    dsLookup = {trinity.TRIFMT_D24S8: td.D24S8,
     trinity.TRIFMT_D24X8: td.D24X8,
     trinity.TRIFMT_D24FS8: td.D24FS8,
     trinity.TRIFMT_D32: td.D32,
     trinity.TRIFMT_INTZ: td.READABLE,
     trinity.TRIFMT_D16_LOCKABLE: td.D16_LOCKABLE,
     trinity.TRIFMT_D15S1: td.D15S1,
     trinity.TRIFMT_D24X4S4: td.D24X4S4,
     trinity.TRIFMT_D16: td.D16,
     trinity.TRIFMT_D32F_LOCKABLE: td.D32F_LOCKABLE,
     trinity.TRIFMT_D24FS8: td.D24FS8}
    dsFormatAL = dsLookup.get(format, td.AUTO)
    return dsFormatAL