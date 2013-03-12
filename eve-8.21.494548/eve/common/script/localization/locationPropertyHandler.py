#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/common/script/localization/locationPropertyHandler.py
import eveLocalization
import localization
import log
import util

class LocationPropertyHandler(localization.BasePropertyHandler):
    __guid__ = 'localization.LocationPropertyHandler'
    PROPERTIES = {localization.CODE_UNIVERSAL: ('name', 'rawName')}

    def _GetName(self, locationID, languageID, *args, **kwargs):
        try:
            return cfg.evelocations.Get(locationID).locationName
        except KeyError:
            log.LogException()
            return '[no location: %d]' % locationID

    def _GetRawName(self, locationID, languageID, *args, **kwargs):
        try:
            return cfg.evelocations.Get(locationID).GetRawName(languageID)
        except KeyError:
            log.LogException()
            return '[no location: %d]' % locationID

    if boot.role != 'client':
        _GetName = _GetRawName

    def Linkify(self, locationID, linkText):
        if util.IsRegion(locationID):
            locationTypeID = const.typeRegion
        elif util.IsConstellation(locationID):
            locationTypeID = const.typeConstellation
        elif util.IsSolarSystem(locationID):
            locationTypeID = const.typeSolarSystem
        else:
            if util.IsCelestial(locationID):
                warnText = "LOCALIZATION ERROR: 'linkify' argument used for a location of type celestial."
                warnText += " This is not supported. Please use the 'linkinfo' tag with arguments instead. locID:"
                localization.LogWarn(warnText, locationID)
                return linkText
            if util.IsStation(locationID):
                try:
                    locationTypeID = cfg.stations.Get(locationID).stationTypeID
                except KeyError:
                    return '[no station: %d]' % locationID

            else:
                localization.LogInfo("LOCALIZATION LINK: The 'linkify' argument was used for a location whose type can not be identified.", locationID)
                return linkText
        return '<a href=showinfo:%d//%d>%s</a>' % (locationTypeID, locationID, linkText)


eveLocalization.RegisterPropertyHandler(eveLocalization.VARIABLE_TYPE.LOCATION, LocationPropertyHandler())