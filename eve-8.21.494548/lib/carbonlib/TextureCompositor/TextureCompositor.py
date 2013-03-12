#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\TextureCompositor\TextureCompositor.py
import trinity
import blue
import types
import os
import sys
import time
import log
import telemetry
import yaml
rm = blue.resMan
RUN_RENDER_JOB, RETURN_RENDER_JOB = range(2)
DIFFUSE_MAP, SPECULAR_MAP, NORMAL_MAP, MASK_MAP = range(4)
MAPS = (DIFFUSE_MAP,
 SPECULAR_MAP,
 NORMAL_MAP,
 MASK_MAP)
MAPNAMES = ('DiffuseMap',
 'SpecularMap',
 'NormalMap',
 'CutMaskMap')
EFFECT_LOCATION = 'res:/Graphics/Effect/Utility/Compositing'
COMPOSITE_SHADER_PATHS = ['AlphaFill.fx',
 'BlitIntoAlpha1.fx',
 'BlitIntoAlpha2.fx',
 'BlitIntoAlphaWithZones.fx',
 'BlitUVOffset.fx',
 'ColorCopyblit.fx',
 'ColorCopyblitToGamma.fx',
 'ColorFill.fx',
 'ColorizedBlit.fx',
 'ColorizedBlit_AlphaTest.fx',
 'ColorizedCopyBlit.fx',
 'Copyblit.fx',
 'ExpandOpaque.fx',
 'ExpandOpaqueNoMask.fx',
 'MaskedNormalBlit.fx',
 'PatternBlit.fx',
 'SimpleBlit.fx',
 'SphericalCircleBlit.fx',
 'TwistNormalBlit.fx']
COMPRESS_DXT1 = trinity.TR2DXT_COMPRESS_SQUISH_DXT1
COMPRESS_DXT5 = trinity.TR2DXT_COMPRESS_SQUISH_DXT5
COMPRESS_DXT5n = trinity.TR2DXT_COMPRESS_RT_DXT5N

def GetEffectsToCache():
    effects = []
    for each in COMPOSITE_SHADER_PATHS:
        effect = trinity.Tr2Effect()
        effect.effectFilePath = EFFECT_LOCATION + '/' + each
        effects.append(effect)

    return effects


ENABLE_RESOURCE_LOAD_COUNTER = False
RESOURCE_LOAD_COUNTER = {}

class TextureCompositor(object):
    __metaclass__ = telemetry.ZONE_PER_METHOD
    cachedEffects = None

    def __init__(self, renderTarget = None, resData = None, targetWidth = 0):
        self.renderJob = None
        self.renderTarget = renderTarget
        self.resourcesToLoad = []
        self.targetWidth = targetWidth
        self.resData = resData
        self.atlasData = None
        self.SetStartingState()
        if not TextureCompositor.cachedEffects:
            TextureCompositor.cachedEffects = GetEffectsToCache()

    def SetStartingState(self):
        self.isReady = False
        self.isDone = False
        self.texturesWithCutouts = []
        self.texturesByResourceID = {}
        self.resourcesToLoad = []

    def CreateResource(self, effect, paramName, resPath, cutoutName = None, paramType = None, mapType = ''):
        if paramType is None:
            paramType = trinity.TriTexture2DParameter()
        paramRes = None
        error = False
        skipLoad = False
        atlasUVs = None
        if not resPath:
            error = True
        elif type(resPath) in types.StringTypes:
            if type(resPath) == types.UnicodeType:
                resPath = str(resPath)
            if self.atlasData:
                paramRes, atlasUVs = self.atlasData.GetTexture(resPath)
            if not paramRes:
                if self.targetWidth > 0 and self.resData:
                    resDataEntry = self.resData.GetEntryByFullResPath(resPath)
                    if resDataEntry:
                        resPath = resDataEntry.GetMapResolutonMatch(resPath, self.targetWidth)
                paramRes = rm.GetResource(resPath)
                skipLoad = not paramRes.isLoading
        elif type(resPath) == trinity.TriTextureRes:
            paramRes = resPath
            skipLoad = True
        elif hasattr(resPath, 'resource'):
            paramRes = resPath.resource
        else:
            error = True
        if error or paramRes is None:
            raise Exception('Invalid resource passed to texture compositor!')
            sys.exc_clear()
        param = paramType
        param.name = paramName
        param.SetResource(paramRes)
        item = (paramRes,
         effect,
         cutoutName,
         mapType,
         atlasUVs)
        if cutoutName:
            self.texturesWithCutouts.append(item)
        if not skipLoad:
            self.texturesByResourceID[id(paramRes)] = item
            if paramRes not in self.resourcesToLoad:
                self.resourcesToLoad.append(paramRes)
        return param

    def AppendResource(self, effect, paramName, resPath, cutoutName = None, paramType = None, mapType = ''):
        effect.resources.append(self.CreateResource(effect, paramName, resPath, cutoutName, paramType, mapType))

    def CreateParameter(self, paramType, paramName, paramValue):
        param = paramType
        param.name = paramName
        if type(paramValue) == type([]):
            paramValue = tuple(paramValue)
        param.value = paramValue
        return param

    def AppendParameter(self, effect, paramType, paramName, paramValue):
        effect.parameters.append(self.CreateParameter(paramType, paramName, paramValue))

    def SetAtlasData(self, atlasData):
        self.atlasData = atlasData

    def MakeEffect(self, effectName):
        effect = trinity.Tr2Effect()
        effect.effectFilePath = '{0}/{1}.fx'.format(EFFECT_LOCATION, effectName)
        if effect.effectResource.isLoading:
            self.resourcesToLoad.append(effect.effectResource)
        return effect

    def Start(self, clear = True):
        self.renderJob = trinity.CreateRenderJob('Texture Compositing')
        self.renderJob.PushRenderTarget(self.renderTarget)
        self.renderJob.PushDepthStencil(None)
        if clear:
            cl = self.renderJob.Clear((0.0, 1.0, 0.0, 0.0), 1.0)
            cl.isDepthCleared = False
        self.renderJob.SetStdRndStates(trinity.RM_FULLSCREEN)

    def End(self):
        isDone = False
        while not isDone:
            isLoading = len(self.resourcesToLoad) > 0
            while isLoading:
                isLoading = False
                for each in iter(self.resourcesToLoad):
                    isLoading = each.isLoading
                    if isLoading:
                        blue.synchro.Yield()
                        break

            isDone = True
            for each in iter(self.resourcesToLoad):
                if each.isLoading:
                    isDone = False
                    break

        if ENABLE_RESOURCE_LOAD_COUNTER:
            for paramRes in self.resourcesToLoad:
                count = RESOURCE_LOAD_COUNTER.get(paramRes.path, 0)
                RESOURCE_LOAD_COUNTER[paramRes.path] = count + 1

        self.isReady = True

    def SetShaderPath(self, effect, newPath):
        if newPath.split('/')[-1] in COMPOSITE_SHADER_PATHS:
            effect.effectFilePath = newPath
            if effect.effectResource.isLoading:
                self.resourcesToLoad.append(effect.effectResource)

    def Finalize(self, format, w, h, generateMipmap = False, textureToCopyTo = None, compressionSettings = None, mapType = None):
        isPC = not blue.win32.IsTransgaming()
        doCompression = compressionSettings is not None and compressionSettings.compressTextures and compressionSettings.AllowCompress(mapType) and isPC
        if doCompression:
            textureToCopyTo = None
        if not self.isReady:
            raise AttributeError('isReady must be true when Finalize() is called.')
        newParams = []
        lastFx = None
        for r in iter(self.texturesWithCutouts):
            cutout = [r[0].cutoutX,
             r[0].cutoutY,
             r[0].cutoutWidth,
             r[0].cutoutHeight]
            if r[4]:
                cutout = r[4]
            if lastFx is not None and r[1] != lastFx:
                lastFx.StartUpdate()
                lastFx.parameters.extend(newParams)
                lastFx.EndUpdate()
                newParams = []
            lastFx = r[1]
            newParams.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), r[2], cutout))

        if lastFx is not None:
            lastFx.StartUpdate()
            lastFx.parameters.extend(newParams)
            lastFx.EndUpdate()

        def FindOrAddFloat(effect, name):
            for r in effect.parameters:
                if r.name == name:
                    return r

            p = trinity.Tr2FloatParameter()
            p.name = name
            effect.parameters.append(p)
            return p

        for step in iter(self.renderJob.steps):
            if type(step) == trinity.TriStepRenderEffect:
                for res in step.effect.resources:
                    mapFormat = res.resource.format
                    if mapFormat == trinity.PIXEL_FORMAT.R8_UNORM:
                        v = FindOrAddFloat(step.effect, res.name.lower() + '_L8')
                        v.value = 1.0
                    elif mapFormat == trinity.PIXEL_FORMAT.R8G8_UNORM:
                        v = FindOrAddFloat(step.effect, res.name.lower() + '_L8A8')
                        v.value = 1.0
                    r = self.texturesByResourceID.get(id(res.resource))
                    if r:
                        mapName = r[3]
                        if mapName == 'N' and mapFormat == trinity.PIXEL_FORMAT.R8G8_UNORM:
                            v = FindOrAddFloat(step.effect, res.name.lower() + '_blitAsNormal')
                            v.value = 1.0

        self.renderJob.PopDepthStencil()
        self.renderJob.PopRenderTarget()
        self.renderJob.GenerateMipMaps(self.renderTarget)
        if textureToCopyTo is not None:
            self.renderJob.CopyRenderTarget(textureToCopyTo, self.renderTarget)
        self.renderJob.ScheduleChained()
        try:
            self.renderJob.WaitForFinish()
        except Exception:
            self.renderJob.CancelChained()
            raise 

        self.texturesWithCutouts = []
        self.texturesByResourceID.clear()
        self.isDone = True
        if self.renderJob.status != trinity.RJ_DONE:
            return
        if not doCompression:
            if textureToCopyTo is not None:
                return textureToCopyTo
            tex = trinity.TriTextureRes()
            tex.CreateAndCopyFromRenderTarget(self.renderTarget)
            return tex
        hostBitmap = trinity.Tr2HostBitmap(self.renderTarget)
        tex = trinity.TriTextureRes()
        compressionFormat = COMPRESS_DXT5n if mapType is NORMAL_MAP else COMPRESS_DXT5
        hostBitmap.Compress(compressionFormat, compressionSettings.qualityLevel, tex)
        while not tex.isPrepared:
            blue.synchro.Yield()

        return tex

    def CompositeTexture(self, effect, subrect = None):
        if self.renderTarget:
            vp = trinity.TriViewport()
            if subrect:
                vp.x = subrect[0]
                vp.y = subrect[1]
                vp.width = subrect[2] - subrect[0]
                vp.height = subrect[3] - subrect[1]
            else:
                vp.x = 0
                vp.y = 0
                vp.width = self.renderTarget.width
                vp.height = self.renderTarget.height
            self.renderJob.SetViewport(vp)
            self.renderJob.RenderEffect(effect)

    def CopyBlitTexture(self, path, subrect = None, srcRect = None, isNormalMap = False, alphaMultiplier = 1.0):
        effect = self.MakeEffect('Copyblit')
        self.AppendResource(effect, 'Texture', path, 'TextureReverseUV', mapType='N' if isNormalMap else '')
        if srcRect:
            self.AppendParameter(effect, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
        self.AppendParameter(effect, trinity.Tr2FloatParameter(), 'AlphaMultiplier', alphaMultiplier)
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_ADD)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ZERO)
        self.CompositeTexture(effect, subrect)

    def MaskedNormalBlitTexture(self, path, strength, subrect = None, srcRect = None):
        effect = self.MakeEffect('MaskedNormalBlit')
        self.AppendResource(effect, 'Texture', path, 'TextureReverseUV')
        self.AppendParameter(effect, trinity.Tr2FloatParameter(), 'Strength', strength)
        if srcRect:
            self.AppendParameter(effect, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_ADD)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ZERO)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        self.CompositeTexture(effect, subrect)

    def TwistNormalBlitTexture(self, path, strength, subrect = None, srcRect = None):
        effect = self.MakeEffect('TwistNormalBlit')
        self.AppendResource(effect, 'Texture', path, 'TextureReverseUV')
        self.AppendParameter(effect, trinity.Tr2FloatParameter(), 'Strength', strength)
        if srcRect:
            self.AppendParameter(effect, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_ADD)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ZERO)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        self.CompositeTexture(effect, subrect)

    def FillColor(self, color, subrect = None, skipAlpha = False, addAlpha = False):
        effect = self.MakeEffect('ColorFill')
        self.AppendParameter(effect, trinity.Tr2Vector4Parameter(), 'color1', color)
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_ADD)
        if skipAlpha:
            self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ZERO)
        else:
            self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        if addAlpha:
            self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        else:
            self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ZERO)
        self.CompositeTexture(effect, subrect)

    def SubtractAlphaFromAlpha(self, path, subrect = None, srcRect = None):
        effect = self.MakeEffect('BlitIntoAlpha1')
        self.AppendResource(effect, 'Texture', path, 'TextureReverseUV')
        if srcRect:
            self.AppendParameter(effect, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_REVSUBTRACT)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        self.CompositeTexture(effect, subrect)

    def BlitTextureIntoAlpha(self, path, subrect = None, srcRect = None):
        effect = self.MakeEffect('BlitIntoAlpha1')
        effect2 = self.MakeEffect('BlitIntoAlpha2')
        self.AppendResource(effect, 'Texture', path, 'TextureReverseUV')
        self.AppendResource(effect2, 'Texture', path, 'TextureReverseUV')
        self.AppendResource(effect2, 'MaskMap', path, 'MaskReverseUV')
        if srcRect:
            self.AppendParameter(effect, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
            self.AppendParameter(effect2, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_REVSUBTRACT)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        self.CompositeTexture(effect, subrect)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_ADD)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        self.CompositeTexture(effect2, subrect)

    def BlitTextureIntoAlphaWithMask(self, path, mask, subrect = None, srcRect = None):
        effect = self.MakeEffect('BlitIntoAlpha1')
        effect2 = self.MakeEffect('BlitIntoAlpha2')
        self.AppendResource(effect, 'Texture', path, 'TextureReverseUV')
        self.AppendResource(effect2, 'Texture', path, 'TextureReverseUV')
        self.AppendResource(effect2, 'MaskMap', mask, 'MaskReverseUV')
        if srcRect:
            self.AppendParameter(effect, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
            self.AppendParameter(effect2, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_REVSUBTRACT)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        self.CompositeTexture(effect, subrect)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_ADD)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        self.CompositeTexture(effect2, subrect)

    def BlitAlphaIntoAlphaWithMask(self, path, mask, subrect = None, srcRect = None):
        effect = self.MakeEffect('BlitIntoAlpha1')
        effect2 = self.MakeEffect('BlitIntoAlpha2')
        self.AppendResource(effect, 'Texture', mask, 'TextureReverseUV')
        self.AppendResource(effect2, 'Texture', path, 'TextureReverseUV')
        self.AppendResource(effect2, 'MaskMap', mask, 'MaskReverseUV')
        if srcRect:
            self.AppendParameter(effect, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
            self.AppendParameter(effect2, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_REVSUBTRACT)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        self.CompositeTexture(effect, subrect)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_ADD)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        self.CompositeTexture(effect2, subrect)

    def BlitAlphaIntoAlphaWithMaskAndZones(self, path, mask, zone, values, subrect = None, srcRect = None):
        effect = self.MakeEffect('BlitIntoAlpha1')
        effect2 = self.MakeEffect('BlitIntoAlphaWithZones')
        self.AppendResource(effect, 'Texture', mask, 'TextureReverseUV')
        self.AppendResource(effect2, 'Texture', path, 'TextureReverseUV')
        self.AppendResource(effect2, 'MaskMap', mask, 'MaskReverseUV')
        self.AppendResource(effect2, 'ZoneMap', zone, 'ZoneReverseUV')
        if srcRect:
            self.AppendParameter(effect, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
            self.AppendParameter(effect2, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
        self.AppendParameter(effect2, trinity.Tr2Vector4Parameter(), 'Color1', values)
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_REVSUBTRACT)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        self.CompositeTexture(effect, subrect)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_ADD)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        self.CompositeTexture(effect2, subrect)

    def BlitTexture(self, path, maskPath, weight, subrect = None, addAlpha = False, skipAlpha = False, srcRect = None, multAlpha = False, isNormalMap = False):
        effect = self.MakeEffect('SimpleBlit')
        self.AppendResource(effect, 'Texture', path, 'TextureReverseUV', mapType='N' if isNormalMap else '')
        self.AppendResource(effect, 'MaskMap', maskPath, 'MaskReverseUV')
        self.AppendParameter(effect, trinity.Tr2FloatParameter(), 'Strength', weight)
        if multAlpha:
            self.AppendParameter(effect, trinity.Tr2FloatParameter(), 'MultAlpha', 1.0)
        if srcRect:
            self.AppendParameter(effect, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect)
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_ADD)
        if skipAlpha:
            self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ZERO)
        else:
            self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        if addAlpha:
            self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        else:
            self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ZERO)
        self.CompositeTexture(effect, subrect)

    def ColorizedBlitTexture(self, detail, zone, overlay, color1, color2, color3, subrect = None, addAlpha = False, skipAlpha = False, useAlphaTest = False, srcRect = None, weight = 1.0, mask = None):
        if useAlphaTest:
            effect = self.MakeEffect('ColorizedBlit_AlphaTest')
        else:
            effect = self.MakeEffect('ColorizedBlit')
        effect.StartUpdate()
        res = []
        res.append(self.CreateResource(effect, 'DetailMap', detail, 'DetailReverseUV'))
        res.append(self.CreateResource(effect, 'ZoneMap', zone, 'ZoneReverseUV'))
        res.append(self.CreateResource(effect, 'OverlayMap', overlay, 'OverlayReverseUV'))
        if mask:
            res.append(self.CreateResource(effect, 'MaskMap', mask, 'MaskReverseUV2'))
        effect.resources.extend(res)
        param = []
        param.append(self.CreateParameter(trinity.Tr2FloatParameter(), 'Strength', weight))
        param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'Color1', color1))
        param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'Color2', color2))
        param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'Color3', color3))
        if srcRect:
            param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect))
        if mask:
            param.append(self.CreateParameter(trinity.Tr2FloatParameter(), 'UseMask', 1.0))
        effect.parameters.extend(param)
        effect.EndUpdate()
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_ADD)
        if skipAlpha:
            self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ZERO)
        else:
            self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        if addAlpha:
            self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        else:
            self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ZERO)
        self.CompositeTexture(effect, subrect)

    def ColorizedCopyBlitTexture(self, detail, zone, overlay, color1, color2, color3, subrect = None, addAlpha = False, srcRect = None, weight = 1.0):
        effect = self.MakeEffect('ColorizedCopyBlit')
        effect.StartUpdate()
        res = []
        res.append(self.CreateResource(effect, 'DetailMap', detail, 'DetailReverseUV'))
        res.append(self.CreateResource(effect, 'ZoneMap', zone, 'ZoneReverseUV'))
        res.append(self.CreateResource(effect, 'OverlayMap', overlay, 'OverlayReverseUV'))
        effect.resources.extend(res)
        self.AppendParameter(effect, trinity.Tr2FloatParameter(), 'Strength', weight)
        param = []
        param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'Color1', color1))
        param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'Color2', color2))
        param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'Color3', color3))
        if srcRect:
            param.append(self.CreateParameter(effect, trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect))
        effect.parameters.extend(param)
        effect.EndUpdate()
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_ADD)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ZERO)
        self.CompositeTexture(effect, subrect)

    def PatternBlitTexture(self, pattern, detail, zone, overlay, patterncolor1, patterncolor2, patterncolor3, color2, color3, subrect = None, patternTransform = (0, 0, 8, 8), patternRotation = 0.0, addAlpha = False, skipAlpha = False, srcRect = None):
        effect = self.MakeEffect('PatternBlit')
        effect.StartUpdate()
        res = []
        res.append(self.CreateResource(effect, 'PatternMap', pattern, 'PatternReverseUV'))
        res.append(self.CreateResource(effect, 'DetailMap', detail, 'DetailReverseUV'))
        res.append(self.CreateResource(effect, 'ZoneMap', zone, 'ZoneReverseUV'))
        res.append(self.CreateResource(effect, 'OverlayMap', overlay, 'OverlayReverseUV'))
        effect.resources.extend(res)
        param = []
        param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'PatternColor1', patterncolor1))
        param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'PatternColor2', patterncolor2))
        param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'PatternColor3', patterncolor3))
        param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'PatternTransform', patternTransform))
        param.append(self.CreateParameter(trinity.Tr2FloatParameter(), 'PatternRotation', patternRotation))
        param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'Color2', color2))
        param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'Color3', color3))
        if srcRect:
            param.append(self.CreateParameter(trinity.Tr2Vector4Parameter(), 'SourceUVs', srcRect))
        effect.parameters.extend(param)
        effect.EndUpdate()
        self.renderJob.SetRenderState(trinity.D3DRS_SEPARATEALPHABLENDENABLE, 1)
        self.renderJob.SetRenderState(trinity.D3DRS_BLENDOPALPHA, trinity.TRIBLENDOP_ADD)
        self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        if skipAlpha:
            self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ZERO)
        else:
            self.renderJob.SetRenderState(trinity.D3DRS_SRCBLENDALPHA, trinity.TRIBLEND_ONE)
        if addAlpha:
            self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ONE)
        else:
            self.renderJob.SetRenderState(trinity.D3DRS_DESTBLENDALPHA, trinity.TRIBLEND_ZERO)
        self.CompositeTexture(effect, subrect)


class AtlasData(object):

    def __init__(self):
        self.atlasData = {}
        self.preloadedTextures = {}

    def AddAtlas(self, atlasPath):
        resFile = blue.ResFile()
        data = {}
        if resFile.FileExists(atlasPath):
            resFile.Open(atlasPath)
            yamlStr = resFile.Read()
            resFile.Close()
            data = yaml.load(yamlStr, Loader=yaml.CLoader)
        for entry in data:
            self.atlasData[entry] = (atlasPath.split('.')[0], data[entry])
            resPath = '%s_%s.dds' % (self.atlasData[entry][0], str(self.atlasData[entry][1][0]))
            if resPath not in self.preloadedTextures:
                resource = blue.resMan.GetResource(resPath)
                self.preloadedTextures[resPath] = resource

    def IsLoaded(self):
        return not any(map(lambda x: x.isLoading, self.preloadedTextures.itervalues()))

    def GetTexture(self, path):
        testPath = path.split('.')[0].split(':')[1].lower()
        if testPath in self.atlasData:
            data = self.atlasData[testPath]
            resPath = data[0] + '_' + str(data[1][0]) + '.dds'
            au = data[1][1]
            sizeU = au[2] - au[0]
            sizeV = au[3] - au[1]
            atlasUVs = (-au[0] / sizeU,
             -au[1] / sizeV,
             1.0 / sizeU,
             1.0 / sizeV)
            paramRes = rm.GetResource(resPath)
            return (paramRes, atlasUVs)
        else:
            log.LogWarn('Atlas texture miss: %s' % path)
            return (None, None)


def GetAsResource(resPath):
    paramRes = None
    error = False
    if not resPath:
        error = True
    elif type(resPath) in types.StringTypes:
        if type(resPath) == types.UnicodeType:
            resPath = str(resPath)
        paramRes = rm.GetResource(resPath)
    elif type(resPath) == trinity.TriTextureRes:
        paramRes = resPath
    elif hasattr(resPath, 'resource'):
        paramRes = resPath.resource
    else:
        error = True
    if error:
        raise Exception('Invalid resourced passed to texture compositor!')
    else:
        return paramRes