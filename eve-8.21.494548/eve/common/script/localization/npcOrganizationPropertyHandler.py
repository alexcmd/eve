#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/common/script/localization/npcOrganizationPropertyHandler.py
import const
import eveLocalization
import localization
import log

class NpcOrganizationPropertyHandler(localization.BasePropertyHandler):
    __guid__ = 'localization.NpcOrganizationPropertyHandler'
    PROPERTIES = {localization.CODE_UNIVERSAL: ('name', 'rawName', 'nameWithArticle'),
     localization.LOCALE_SHORT_ENGLISH: ('nameWithArticle',),
     localization.LOCALE_SHORT_RUSSIAN: ('gender',),
     localization.LOCALE_SHORT_GERMAN: ('gender',)}

    def _GetName(self, npcOrganizationID, languageID, *args, **kwargs):
        if const.minFaction <= npcOrganizationID <= const.maxFaction or const.minNPCCorporation <= npcOrganizationID <= const.maxNPCCorporation:
            try:
                return cfg.eveowners.Get(npcOrganizationID).name
            except KeyError:
                log.LogException()
                return '[no npcOrganization: %d]' % npcOrganizationID

    def _GetRawName(self, npcOrganizationID, languageID, *args, **kwargs):
        if const.minFaction <= npcOrganizationID <= const.maxFaction or const.minNPCCorporation <= npcOrganizationID <= const.maxNPCCorporation:
            try:
                return cfg.eveowners.Get(npcOrganizationID).GetRawName(languageID)
            except KeyError:
                log.LogException()
                return '[no npcOrganization: %d]' % npcOrganizationID

    if boot.role != 'client':
        _GetName = _GetRawName

    def _GetArticleEN_US(self, npcOrganizationID, *args, **kwargs):
        try:
            messageID = cfg.eveowners.Get(npcOrganizationID).ownerNameID
        except KeyError:
            log.LogException()
            return '[no npcOrganization: %d]' % npcOrganizationID

        try:
            return localization.GetMetaData(messageID, 'article', languageID=localization.LOCALE_SHORT_ENGLISH)
        except:
            localization.LogWarn("npcOrganizationID %s does not have the requested metadata 'article' in language '%s. Returning empty string by default." % (itemID, localization.LOCALE_SHORT_ENGLISH))
            return ''

    def _GetNameWithArticle(self, npcOrganizationID, languageID, *args, **kwargs):
        return self._GetName(npcOrganizationID, languageID, args, kwargs)

    def _GetNameWithArticleEN_US(self, npcOrganizationID, *args, **kwargs):
        englishName = self._GetName(npcOrganizationID, localization.LOCALE_SHORT_ENGLISH) or 'None'
        if 'The ' in englishName:
            return englishName
        else:
            return self._PrepareLocalizationSafeString(' '.join(('the', englishName)))

    def _GetGenderDE(self, npcOrganizationID, *args, **kwargs):
        return localization.GENDER_MALE

    def _GetGenderRU(self, npcOrganizationID, *args, **kwargs):
        return localization.GENDER_MALE

    def GetShowInfoData(self, ownerID, *args, **kwargs):
        try:
            item = cfg.eveowners.Get(ownerID)
        except KeyError:
            log.LogException()
            return [0, 0]

        return [item.typeID, ownerID]


eveLocalization.RegisterPropertyHandler(eveLocalization.VARIABLE_TYPE.NPCORGANIZATION, NpcOrganizationPropertyHandler())