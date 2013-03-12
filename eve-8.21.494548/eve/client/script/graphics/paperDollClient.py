#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/graphics/paperDollClient.py
import svc
import paperDollUtil
import telemetry
import paperDoll
from ccConst import TEXTURE_RESOLUTIONS

class EvePaperDollClient(svc.paperDollClient):
    __guid__ = 'svc.evePaperDollClient'
    __replaceservice__ = 'paperDollClient'
    __notifyevents__ = svc.paperDollClient.__notifyevents__ + ['OnGraphicSettingsChanged']
    __dependencies__ = svc.paperDollClient.__dependencies__ + ['info', 'character', 'device']

    def Run(self, *etc):
        svc.paperDollClient.Run(self, *etc)
        if settings.public.device.Get('loadstationenv2', 1):
            self.LogInfo('Early loading of paperDoll asset data, station environments enabled')
            kicker = self.dollFactory

    def _AppPerformanceOptions(self):
        paperDoll.PerformanceOptions.EnableEveOptimizations()

    @telemetry.ZONE_METHOD
    def GetDollDNA(self, scene, entity, dollGender, dollDnaInfo, typeID):
        bloodlineID = self.info.GetBloodlineByTypeID(typeID).bloodlineID
        return self.character.GetDNAFromDBRowsForEntity(entity.entityID, dollDnaInfo, dollGender, bloodlineID)

    def SetupComponent(self, entity, component):
        svc.paperDollClient.SetupComponent(self, entity, component)
        doll = component.doll.doll
        if session.charid == entity.entityID:
            cs = paperDoll.CompressionSettings(compressTextures=True, generateMipmap=False)
            cs.compressNormalMap = False
            doll.compressionSettings = cs
        doll.usePrepassAlphaTestHair = settings.public.device.Get('interiorShaderQuality', self.device.GetDefaultInteriorShaderQuality()) == 0
        self.SetBoneOffsets(entity, component)

        def UpdateDoneCallback():
            if component.doll and component.doll.avatar:
                for curveSet in component.doll.avatar.curveSets:
                    if curveSet.name == 'HeadMatrixCurves':
                        trinityScene = sm.GetService('graphicClient').GetScene(entity.scene.sceneID)
                        if trinityScene:
                            for each in trinityScene.curveSets:
                                if each.name == 'HeadMatrixCurves':
                                    trinityScene.curveSets.remove(each)

                            trinityScene.curveSets.append(curveSet)
                            component.doll.avatar.curveSets.remove(curveSet)

        component.doll.doll.AddUpdateDoneListener(UpdateDoneCallback)

    def SetBoneOffsets(self, entity, component):
        avatar = self.GetPaperDollByEntityID(entity.entityID).avatar
        gender = self.GetDBGenderToPaperDollGender(component.gender)
        bloodlineID = self.info.GetBloodlineByTypeID(component.typeID).bloodlineID
        bloodline = paperDollUtil.bloodlineAssets[bloodlineID]
        self.character.AdaptDollAnimationData(bloodline, avatar, gender)

    def GetInitialTextureResolution(self):
        textureQuality = settings.public.device.Get('charTextureQuality', self.device.GetDefaultCharTextureQuality())
        return TEXTURE_RESOLUTIONS[textureQuality]

    @telemetry.ZONE_METHOD
    def OnGraphicSettingsChanged(self, changes):
        if 'charTextureQuality' in changes:
            textureQuality = settings.public.device.Get('charTextureQuality', self.device.GetDefaultCharTextureQuality())
            resolution = TEXTURE_RESOLUTIONS[textureQuality]
            for character in self.paperDollManager:
                character.doll.SetTextureSize(resolution)
                character.doll.buildDataManager.SetAllAsDirty()
                character.Update()

        if 'interiorShaderQuality' in changes:
            for character in self.paperDollManager:
                character.doll.usePrepassAlphaTestHair = settings.public.device.Get('interiorShaderQuality', self.device.GetDefaultInteriorShaderQuality()) == 0
                if character.doll.usePrepass:
                    character.doll.buildDataManager.SetAllAsDirty(True)
                    character.Update()