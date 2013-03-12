#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/common/script/localization/characterPropertyHandler.py
import eveLocalization
import localization
import log

class CharacterPropertyHandler(localization.BasePropertyHandler):
    __guid__ = 'localization.CharacterPropertyHandler'
    PROPERTIES = {localization.CODE_UNIVERSAL: ('name', 'rawName', 'gender'),
     localization.LOCALE_SHORT_ENGLISH: ('nameWithPossessive',),
     localization.LOCALE_SHORT_GERMAN: ('genitiveName',),
     localization.LOCALE_SHORT_RUSSIAN: ('genitiveName',)}
    GENDER_NORMALIZATION_MAPPING = {1: localization.GENDER_MALE,
     0: localization.GENDER_FEMALE}

    def _GetName(self, charID, languageID, *args, **kwargs):
        try:
            return cfg.eveowners.Get(charID).ownerName
        except KeyError:
            log.LogException()
            return '[no character: %d]' % charID

    def _GetRawName(self, charID, languageID, *args, **kwargs):
        try:
            return cfg.eveowners.Get(charID).GetRawName(languageID)
        except KeyError:
            log.LogException()
            return '[no character: %d]' % charID

    if boot.role != 'client':
        _GetName = _GetRawName

    def _GetGender(self, charID, languageID, *args, **kwargs):
        try:
            return self.GENDER_NORMALIZATION_MAPPING[cfg.eveowners.Get(charID).gender]
        except KeyError:
            log.LogException()
            return self.GENDER_NORMALIZATION_MAPPING[0]

    def _GetNameWithPossessiveEN_US(self, charID, *args, **kwargs):
        characterName = self._GetName(charID, languageID=localization.LOCALE_SHORT_ENGLISH)
        return self._PrepareLocalizationSafeString(characterName + "'s")

    def _GetGenitiveNameDE(self, charID, *args, **kwargs):
        characterName = self._GetName(charID, languageID=localization.LOCALE_SHORT_GERMAN)
        if characterName[-1:] not in 'sxz':
            characterName = characterName + 's'
        return self._PrepareLocalizationSafeString(characterName)

    def _GetGenitiveNameRU(self, charID, *args, **kwargs):
        characterName = self._GetName(charID, languageID=localization.LOCALE_SHORT_RUSSIAN)
        nameWithPossessive = self._PrepareLocalizationSafeString(characterName + '[possessive]')
        return nameWithPossessive

    def Linkify(self, charID, linkText):
        try:
            charInfo = cfg.eveowners.Get(charID)
        except KeyError:
            log.LogException()
            return '[no character: %d]' % charID

        if charInfo.typeID:
            return '<a href=showinfo:%d//%d>%s</a>' % (charInfo.typeID, charID, linkText)
        else:
            return linkText


eveLocalization.RegisterPropertyHandler(eveLocalization.VARIABLE_TYPE.CHARACTER, CharacterPropertyHandler())