#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\csaaScreenshot.py
import trinity

def csaaScreenshot(useNVidiaAA, width, height, scene):
    try:
        csaaFmt = trinity.TRIMULTISAMPLE_8_SAMPLES if useNVidiaAA else trinity.TRIMULTISAMPLE_NONE
        csaaQty = 2 if useNVidiaAA else 0
        buffer = trinity.Tr2RenderTarget(width, height, 1, trinity.PIXEL_FORMAT.B8G8R8X8_UNORM, csaaFmt, csaaQty)
        depth = trinity.Tr2DepthStencil(width, height, trinity.DEPTH_STENCIL_FORMAT.D24S8, csaaFmt, csaaQty)
        job = trinity.CreateRenderJob('CSAA screenshot')
        job.SetRenderTarget(buffer)
        job.SetDepthStencil(depth)
        vp = trinity.TriViewport()
        vp.x = 0
        vp.y = 0
        vp.width = width
        vp.height = height
        job.SetViewport(vp)
        job.Clear((0, 0, 0, 0), 1.0)
        job.RenderScene(scene)
        trinity.SetPerspectiveProjection(trinity.GetFieldOfView(), trinity.GetFrontClip(), trinity.GetBackClip(), 1.0)
        job.ScheduleOnce()
        return (job, buffer)
    except Exception:
        return None