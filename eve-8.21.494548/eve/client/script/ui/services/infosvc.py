#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/services/infosvc.py
import sys
import service
import blue
import telemetry
import uthread
import uix
import uiutil
import xtriui
import form
import util
import copy
import base
import random
import types
import state
import listentry
import uiconst
import uicls
import log
import localization
import localizationUtil
import moniker
import maputils
import skillUtil
import math
import bountyUtil
from collections import defaultdict
MINWIDTH = 325
MINHEIGHTREGULAR = 280
MINHEIGHTMEDAL = 480

def ReturnNone():
    return None


def ReturnArg(arg):
    return arg


class BadArgs(RuntimeError):

    def __init__(self, msgID, dict = None):
        RuntimeError.__init__(self, msgID, dict or {})


class Info(service.Service):
    __exportedcalls__ = {'ShowInfo': [],
     'GetAttrTypeInfo': [],
     'GetAttrItemInfo': [],
     'GetSolarSystemReport': [],
     'FormatUnit': [],
     'FormatValue': [],
     'GetFormatAndValue': [],
     'GetKillsRecentKills': [],
     'GetKillsRecentLosses': [],
     'GetEmploymentHistorySubContent': [],
     'GetAllianceMembersSubContent': []}
    __guid__ = 'svc.info'
    __notifyevents__ = ['DoSessionChanging',
     'OnItemChange',
     'OnAllianceRelationshipChanged',
     'OnContactChange']
    __update_on_reload__ = 0
    __servicename__ = 'info'
    __displayname__ = 'Information Service'
    __dependencies__ = ['dataconfig']
    __startupdependencies__ = ['settings']

    def __init__(self):
        service.Service.__init__(self)

    def Run(self, memStream = None):
        self.LogInfo('Starting InfoSvc')
        self.wnds = []
        self.lastActive = None
        self.moniker = None
        self.attributesByName = None
        self.ClearWnds()

    def OnItemChange(self, item, change):
        if item.categoryID != const.categoryCharge and (item.locationID == eve.session.shipid or const.ixLocationID in change and change[const.ixLocationID] == eve.session.shipid):
            self.itemchangeTimer = base.AutoTimer(1000, self.DelayOnItemChange, item, change)
        itemGone = False
        if const.ixLocationID in change and util.IsJunkLocation(item.locationID):
            itemGone = True
        if const.ixQuantity in change and item.stacksize == 0:
            log.LogTraceback('infoSvc processing ixQuantity change')
            itemGone = True
        if const.ixStackSize in change and item.stacksize == 0:
            itemGone = True
        if itemGone:
            for each in self.wnds:
                if each is None or each.destroyed:
                    self.wnds.remove(each)
                    continue
                if each.sr.itemID == item.itemID:
                    each.LoadData(each.sr.typeID)

    def DelayOnItemChange(self, item, change):
        self.itemchangeTimer = None
        for each in self.wnds:
            if each is None or each.destroyed:
                self.wnds.remove(each)
                continue
            if each.sr.itemID == eve.session.shipid and not each.IsMinimized():
                each.LoadData(each.sr.typeID, each.sr.itemID, each.sr.rec)

    def OnContactChange(self, contactIDs, contactType = None):
        for contactID in contactIDs:
            self.UpdateWnd(contactID)

    def OnAllianceRelationshipChanged(self, *args):
        for allianceid in (args[0], args[1]):
            self.UpdateWnd(allianceid)

    def GetShipAttributes(self):
        if not hasattr(self, 'shipAttributes'):
            self.shipAttributes = [(localization.GetByLabel('UI/Fitting/Structure'), [const.attributeHp,
               const.attributeCapacity,
               const.attributeDroneCapacity,
               const.attributeDroneBandwidth,
               const.attributeMass,
               const.attributeVolume,
               const.attributeAgility,
               const.attributeEmDamageResonance,
               const.attributeExplosiveDamageResonance,
               const.attributeKineticDamageResonance,
               const.attributeThermalDamageResonance,
               const.attributeSpecialAmmoHoldCapacity,
               const.attributeSpecialGasHoldCapacity,
               const.attributeSpecialIndustrialShipHoldCapacity,
               const.attributeSpecialLargeShipHoldCapacity,
               const.attributeSpecialMediumShipHoldCapacity,
               const.attributeSpecialMineralHoldCapacity,
               const.attributeSpecialOreHoldCapacity,
               const.attributeSpecialSalvageHoldCapacity,
               const.attributeSpecialShipHoldCapacity,
               const.attributeSpecialSmallShipHoldCapacity,
               const.attributeSpecialCommandCenterHoldCapacity,
               const.attributeSpecialPlanetaryCommoditiesHoldCapacity]),
             (localization.GetByLabel('UI/Common/Armor'), [const.attributeArmorHP,
               const.attributeArmorEmDamageResonance,
               const.attributeArmorExplosiveDamageResonance,
               const.attributeArmorKineticDamageResonance,
               const.attributeArmorThermalDamageResonance]),
             (localization.GetByLabel('UI/Common/Shield'), [const.attributeShieldCapacity,
               const.attributeShieldRechargeRate,
               const.attributeShieldEmDamageResonance,
               const.attributeShieldExplosiveDamageResonance,
               const.attributeShieldKineticDamageResonance,
               const.attributeShieldThermalDamageResonance]),
             (localization.GetByLabel('UI/Fitting/FittingWindow/Capacitor'), [const.attributeCapacitorCapacity, const.attributeRechargeRate]),
             (localization.GetByLabel('UI/Fitting/FittingWindow/Targeting'), [const.attributeMaxTargetRange,
               const.attributeMaxLockedTargets,
               const.attributeScanResolution,
               const.attributeScanLadarStrength,
               const.attributeScanMagnetometricStrength,
               const.attributeScanRadarStrength,
               const.attributeScanGravimetricStrength,
               const.attributeSignatureRadius]),
             (localization.GetByLabel('UI/InfoWindow/SharedFacilities'), [const.attributeFleetHangarCapacity, const.attributeShipMaintenanceBayCapacity, const.attributeMaxJumpClones]),
             (localization.GetByLabel('UI/InfoWindow/JumpDriveSystems'), [const.attributeJumpDriveCapacitorNeed,
               const.attributeJumpDriveRange,
               const.attributeJumpDriveConsumptionType,
               const.attributeJumpDriveConsumptionAmount,
               const.attributeJumpDriveDuration,
               const.attributeJumpPortalCapacitorNeed,
               const.attributeJumpPortalConsumptionMassFactor,
               const.attributeJumpPortalDuration,
               const.attributeSpecialFuelBayCapacity]),
             (localization.GetByLabel('UI/Compare/Propulsion'), [const.attributeMaxVelocity])]
        return self.shipAttributes

    def GetBlueprintAttributes(self):
        self.blueprintAttributes = [(localization.GetByLabel('UI/InfoWindow/ProducesHeader'), ['productTypeID']),
         (localization.GetByLabel('UI/InfoWindow/GeneralInfoHeader'), ['materialLevel',
           'wastageFactor',
           'copy',
           'productivityLevel',
           'licensedProductionRunsRemaining',
           'maxProductionLimit']),
         (localization.GetByLabel('UI/InfoWindow/ManufacturingHeader'), ['manufacturingTime']),
         (localization.GetByLabel('UI/InfoWindow/ResearchingHeader'), ['researchMaterialTime',
           'researchCopyTime',
           'researchProductivityTime',
           'researchTechTime'])]
        return self.blueprintAttributes

    def GetAttributeOrder(self):
        if not hasattr(self, 'attributeOrder'):
            self.attributeOrder = [const.attributePrimaryAttribute,
             const.attributeSecondaryAttribute,
             const.attributeRequiredSkill1,
             const.attributeRequiredSkill2,
             const.attributeRequiredSkill3,
             const.attributeRequiredSkill4,
             const.attributeRequiredSkill5,
             const.attributeRequiredSkill6]
        return self.attributeOrder

    def Stop(self, memStream = None):
        self.ClearWnds()
        self.lastActive = None
        self.moniker = None
        self.attributesByName = None
        self.wnds = []

    def ClearWnds(self):
        self.wnds = []
        if getattr(uicore, 'registry', None):
            for each in uicore.registry.GetWindows()[:]:
                if each is not None and not each.destroyed and each.windowID and each.windowID[0] == 'infowindow':
                    each.Close()

    def DoSessionChanging(self, isremote, session, change):
        self.moniker = None
        if session.charid is None:
            self.ClearWnds()

    def GetSolarSystemReport(self, solarsystemID = None):
        solarsystemID = solarsystemID or eve.session.solarsystemid or eve.session.solarsystemid2
        if solarsystemID is None:
            return
        items = sm.GetService('map').GetSolarsystemItems(solarsystemID)
        types = {}
        for celestial in items:
            types.setdefault(celestial.groupID, []).append(celestial)

        for groupID in types.iterkeys():
            if groupID == const.groupStation:
                continue

    def ShowInfo(self, typeID, itemID = None, new = 0, rec = None, parentID = None, headerOnly = 0, abstractinfo = None):
        if itemID == const.factionUnknown:
            eve.Message('KillerOfUnknownFaction')
            return
        modal = uicore.registry.GetModalWindow()
        ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
        createNew = new or not settings.user.ui.Get('useexistinginfownd', 1) or uicore.uilib.Key(uiconst.VK_SHIFT)
        if len(self.wnds):
            for each in self.wnds:
                if each is None or each.destroyed:
                    self.wnds.remove(each)

        useWnd = None
        if len(self.wnds) and not createNew:
            if self.lastActive is not None and self.lastActive in self.wnds:
                self.lastActive.SaveNote(closing=1)
                if not self.lastActive.destroyed:
                    useWnd = self.lastActive
            wnd = self.wnds[-1]
            if not modal or modal and modal.parent == wnd.parent:
                wnd.SaveNote(closing=1)
                if not wnd.destroyed:
                    useWnd = wnd
        if useWnd:
            useWnd.LoadData(typeID, itemID, rec=rec, parentID=parentID, headerOnly=headerOnly, abstractinfo=abstractinfo)
            useWnd.Maximize()
        else:
            useWnd = form.infowindow.Open(windowID=('infowindow', blue.os.GetWallclockTime()), typeID=typeID, itemID=itemID, rec=rec, parentID=parentID, headerOnly=headerOnly, abstractinfo=abstractinfo)
            self.wnds.append(useWnd)
        if modal and not modal.destroyed and modal.windowID != 'progresswindow':
            if useWnd.InStack():
                useWnd.sr.stack.ShowModal()
            else:
                useWnd.ShowModal()
        return useWnd

    def UpdateWnd(self, itemID, maximize = 0):
        for wnd in self.wnds:
            if wnd.sr.itemID == itemID or getattr(wnd.sr, 'corpID', None) == itemID or getattr(wnd.sr, 'allianceID', None) == itemID:
                wnd.LoadData(wnd.sr.typeID, wnd.sr.itemID)
                if maximize:
                    wnd.Maximize()
                break

    def FindInfoWindow(self):
        for wnd in uicore.registry.GetWindows():
            if wnd.windowID and wnd.windowID[0] == 'infowindow':
                return wnd

    def CloseWnd(self, wnd, *args):
        if wnd in self.wnds:
            self.wnds.remove(wnd)
        if self.lastActive == wnd:
            self.lastActive = None

    def OnActivateWnd(self, wnd):
        self.lastActive = wnd

    def GetRankEntry(self, rank, hilite = False):
        facwarcurrrank = getattr(rank, 'currentRank', 1)
        facwarhighrank = getattr(rank, 'highestRank', 1)
        facwarfaction = getattr(rank, 'factionID', None)
        if rank and facwarfaction is not None:
            lbl, desc = sm.GetService('facwar').GetRankLabel(facwarfaction, facwarcurrrank)
            if hilite:
                lbl = localization.GetByLabel('UI/FactionWarfare/CurrentRank', currentRankName=lbl)
            entry = listentry.Get('RankEntry', {'label': cfg.factions.Get(facwarfaction).factionName,
             'text': lbl,
             'rank': facwarcurrrank,
             'warFactionID': facwarfaction,
             'selected': False,
             'typeID': const.typeRank,
             'showinfo': 1,
             'line': 1})
            return entry

    def GetMedalEntry(self, wnd, info, details, *args):
        d = details
        numAwarded = 0
        if type(info) == list:
            m = info[0]
            numAwarded = len(info)
        else:
            m = info
        sublevel = 1
        if args:
            sublevel = args[0]
        medalribbondata = uix.FormatMedalData(d)
        medalid = m.medalID
        title = m.title
        if numAwarded > 0:
            title = localization.GetByLabel('UI/InfoWindow/MedalAwardedNumTimes', medalName=title, numTimes=numAwarded)
        description = m.description
        createdate = m.date
        medalTitleText = localization.GetByLabel('UI/InfoWindow/MedalTitle')
        data = {'label': title,
         'text': description,
         'sublevel': sublevel,
         'id': m.medalID,
         'line': 1,
         'abstractinfo': medalribbondata,
         'typeID': const.typeMedal,
         'itemID': m.medalID,
         'icon': 'ui_51_64_4',
         'showinfo': True,
         'sort_%s' % medalTitleText: '_%s' % title.lower(),
         'iconsize': 26}
        entry = listentry.Get('MedalRibbonEntry', data)
        if wnd is None:
            return entry
        return wnd.sr.data[C_RANKSTAB]['items'].append(entry)

    def EditContact(self, wnd, itemID, edit):
        wnd.SaveNote(1)
        addressBookSvc = sm.GetService('addressbook')
        addressBookSvc.AddToPersonalMulti(itemID, 'contact', edit)

    def GetWndData(self, wnd, typeID, itemID, parentID = None):
        moonOrPlanet = 0
        title = None
        invtype = cfg.invtypes.Get(typeID)
        invgroup = invtype.Group()
        noShowCatergories = (const.categoryEntity, const.categoryStation)
        noShowGroups = (const.groupMoon,
         const.groupPlanet,
         const.groupConstellation,
         const.groupSolarSystem,
         const.groupRegion,
         const.groupLargeCollidableObject)
        noShowTypes = ()
        showAttrs = invtype.id not in noShowTypes and invgroup.Category().id not in noShowCatergories and invgroup.id not in noShowGroups
        if invgroup.categoryID == const.categoryEntity:
            tmp = [ each for each in sm.GetService('godma').GetType(typeID).displayAttributes if each.attributeID == const.attributeEntityKillBounty ]
            if tmp:
                wnd.Wanted(tmp[0].value, False, True, isNPC=True)
        if itemID is not None and itemID < 0:
            pass
        if typeID and cfg.invtypes.Get(typeID).marketGroupID:
            wnd.sr.data['buttons'] += [(localization.GetByLabel('UI/Inventory/ItemActions/ViewTypesMarketDetails'),
              self.ShowMarketDetails,
              typeID,
              81)]
        elif typeID and cfg.invtypes.Get(typeID).published:
            wnd.sr.data['buttons'] += [(localization.GetByLabel('UI/Inventory/ItemActions/FindInContracts'),
              self.FindInContracts,
              typeID,
              81)]
        if wnd.sr.isCharacter or wnd.sr.isCorporation or wnd.sr.isAlliance:
            showAttrs = 0
            if not util.IsNPC(itemID):
                if eve.session.charid != itemID:
                    addressBookSvc = sm.GetService('addressbook')
                    if not addressBookSvc.IsInAddressBook(itemID, 'contact'):
                        wnd.sr.data['buttons'] += [(localization.GetByLabel('UI/PeopleAndPlaces/AddContact'),
                          self.EditContact,
                          (wnd, itemID, False),
                          81)]
                    else:
                        wnd.sr.data['buttons'] += [(localization.GetByLabel('UI/PeopleAndPlaces/EditContact'),
                          self.EditContact,
                          (wnd, itemID, True),
                          81)]
                if wnd.sr.isCorporation:
                    wnd.sr.dynamicTabs.append((C_ALLIANCEHISTORYTAB, 'AllianceHistory', localization.GetByLabel('UI/InfoWindow/TabNames/AllianceHistory')))
                if wnd.sr.isCharacter:
                    wnd.sr.dynamicTabs.append((C_EMPLOYMENTHISTORYTAB, 'EmploymentHistory', localization.GetByLabel('UI/InfoWindow/TabNames/EmploymentHistory')))
                    if not util.IsDustCharacter(itemID):
                        wnd.sr.dynamicTabs.append((C_DECORATIONSTAB, 'Decorations', localization.GetByLabel('UI/InfoWindow/TabNames/Decorations')))
                else:
                    wnd.sr.dynamicTabs.append((C_WARHISTORYTAB, 'WarHistory', localization.GetByLabel('UI/InfoWindow/TabNames/WarHistory')))
        if wnd.sr.isShip:
            try:
                shipinfo = sm.GetService('godma').GetItem(itemID)
            except:
                shipinfo = None
                sys.exc_clear()

            info = shipinfo or sm.GetService('godma').GetStateManager().GetShipType(typeID)
            attrDict = self.GetAttrDict(typeID)
            for caption, attrs in self.GetShipAttributes():
                shipAttr = [ each for each in attrs if each in attrDict ]
                if shipAttr:
                    wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('Header', {'label': caption}))
                    self.GetAttrItemInfo(itemID, typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'], attrList=shipAttr)

            baseWarpSpeed = self.GetBaseWarpSpeed(typeID, shipinfo)
            if baseWarpSpeed:
                bwsAttr = cfg.dgmattribs.Get(const.attributeBaseWarpSpeed)
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': bwsAttr.displayName,
                 'text': baseWarpSpeed,
                 'iconID': bwsAttr.iconID}))
            GAV = self.GetGAVFunc(itemID, info)
            for label, loadAttributeID, outputAttributeID in ((localization.GetByLabel('UI/Common/Cpu'), const.attributeCpuLoad, const.attributeCpuOutput), (localization.GetByLabel('UI/Common/Powergrid'), const.attributePowerLoad, const.attributePowerOutput), (localization.GetByLabel('UI/Common/Calibration'), const.attributeUpgradeLoad, const.attributeUpgradeCapacity)):
                wnd.sr.data[C_FITTINGTAB]['items'].append(listentry.Get('StatusBar', {'label': label,
                 'status': GAV(loadAttributeID),
                 'total': GAV(outputAttributeID)}))

            recommendedCerts = sm.StartService('certificates').GetCertificateRecommendationsByShipTypeID(typeID)
            tempList = []
            for cert in recommendedCerts:
                entry = self.GetCertEntry(cert)
                tempList.append((entry.get('level', ''), listentry.Get('CertEntry', entry)))

            sortedList = uiutil.SortListOfTuples(tempList)
            previousLevel = -1
            for each in sortedList:
                if each.level != previousLevel:
                    caption = localization.GetByLabel('UI/Certificates/RecommendationLevel', level=each.level)
                    if previousLevel != -1:
                        wnd.sr.data[C_CERTRECOMMENDEDTAB]['items'].append(listentry.Get('Divider'))
                    wnd.sr.data[C_CERTRECOMMENDEDTAB]['items'].append(listentry.Get('Header', {'label': caption}))
                    previousLevel = each.level
                wnd.sr.data[C_CERTRECOMMENDEDTAB]['items'].append(each)

            if attrDict.has_key(const.attributeMaxJumpClones) and info.maxJumpClones > 0:
                currentClones = []
                if eve.session.shipid:
                    currentClones = sm.GetService('clonejump').GetShipClones()
                wnd.sr.data[C_FITTINGTAB]['items'].append(listentry.Get('StatusBar', {'label': localization.GetByLabel('UI/InfoWindow/JumpClonesStatusBar'),
                 'status': len(currentClones),
                 'total': info.maxJumpClones}))
            self.GetAttrTypeInfo(typeID, wnd.sr.data[C_FITTINGTAB]['items'], [const.attributeLowSlots,
             const.attributeMedSlots,
             const.attributeHiSlots,
             const.attributeLauncherSlotsLeft,
             const.attributeTurretSlotsLeft,
             const.attributeUpgradeSlotsLeft,
             const.attributeMaxSubSystems,
             const.attributeRigSize], shipinfo)
            fmHeaderDone = 0
            consideredEffects = [const.effectHiPower,
             const.effectMedPower,
             const.effectLoPower,
             const.effectRigSlot,
             const.effectSubSystem]
            if shipinfo is not None:
                moduleData = {}
                for each in shipinfo.modules:
                    for effect in cfg.dgmtypeeffects.get(each.typeID, []):
                        if effect.effectID in consideredEffects:
                            powerEffect = cfg.dgmeffects.Get(effect.effectID)
                            if moduleData.has_key(effect.effectID):
                                moduleData[effect.effectID] += [[powerEffect, each]]
                            else:
                                moduleData[effect.effectID] = [[powerEffect, each]]

                fitHeader = 0
                if moduleData:
                    for effect in consideredEffects:
                        if not fitHeader:
                            wnd.sr.data[C_MODULESTAB]['items'].append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/FittedModules')}))
                            fitHeader = 1
                        if moduleData.has_key(effect):
                            fitSubheader = 0
                            for each in moduleData[effect]:
                                if not fitSubheader:
                                    wnd.sr.data[C_MODULESTAB]['items'].append(listentry.Get('Subheader', {'label': each[0].displayName}))
                                    fitSubheader = 1
                                wnd.sr.data[C_MODULESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                                 'label': localization.GetByLabel('UI/Common/ItemTypes/Module'),
                                 'text': each[1].name,
                                 'itemID': each[1].itemID,
                                 'typeID': each[1].typeID,
                                 'iconID': cfg.invtypes.Get(each[1].typeID).iconID}))

                    if fitHeader:
                        wnd.sr.data[C_MODULESTAB]['items'].append(listentry.Get('Divider'))
                fitHeader = 0
                if shipinfo.sublocations:
                    for each in shipinfo.sublocations:
                        if not fitHeader:
                            wnd.sr.data[C_MODULESTAB]['items'].append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/FittedCharges')}))
                            fitHeader = 1
                        wnd.sr.data[C_MODULESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': localization.GetByLabel('UI/Common/ItemTypes/Charge'),
                         'text': each.name,
                         'itemID': each.itemID,
                         'typeID': each.typeID,
                         'iconID': cfg.invtypes.Get(each.typeID).iconID}))

            else:
                shiptypeinfo = cfg.shiptypes.Get(typeID)
                fmHeaderDone = 1
                for key in ['weaponTypeID', 'miningTypeID']:
                    moduleTypeID = getattr(shiptypeinfo, key, None)
                    if moduleTypeID:
                        invtype = cfg.invtypes.Get(moduleTypeID)
                        wnd.sr.data[C_MODULESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': localization.GetByLabel('UI/Common/ItemTypes/Module'),
                         'text': invtype.name,
                         'typeID': moduleTypeID,
                         'iconID': invtype.iconID}))

            shiptypeinfo = cfg.shiptypes.Get(typeID)
            self.GetReqSkillInfo(typeID, wnd.sr.data[C_SKILLSTAB]['items'])
            self.GetMetaTypeInfo(typeID, wnd.sr.data[C_VARIATIONSTAB]['items'], wnd)
            self.InitVariationBottom(wnd)
            if itemID:
                insuranceCont = uicls.Container(parent=wnd.sr.therestcontainer, align=uiconst.TOBOTTOM, height=32)
                insuranceLabel = uicls.EveLabelMedium(text='', parent=insuranceCont, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
                timeLabel = uicls.EveLabelMedium(text='', parent=insuranceCont, align=uiconst.TOTOP)
                bp = sm.GetService('michelle').GetBallpark()
                isMine = False
                if bp is not None:
                    slimItem = bp.GetInvItem(itemID)
                    if slimItem is not None:
                        if slimItem.ownerID in (session.corpid, session.charid):
                            isMine = True
                    elif not session.solarsystemid:
                        isMine = True
                if isMine or bp is None:
                    contract = sm.RemoteSvc('insuranceSvc').GetContractForShip(itemID)
                    price = sm.GetService('insurance').GetInsurancePrice(typeID)
                    groupID = cfg.invtypes.Get(typeID).groupID
                    if groupID in (const.groupTitan, const.groupSupercarrier) or price <= 0:
                        insuranceLabel.text = ''
                    elif contract and contract.ownerID in (session.corpid, session.charid):
                        insuranceName = self.GetInsuranceName(contract.fraction)
                        insuranceLabel.text = insuranceName
                        payout = price * contract.fraction
                        insuranceLabel.hint = util.FmtISK(payout)
                        timeDiff = contract.endDate - blue.os.GetWallclockTime()
                        days = timeDiff / const.DAY
                        text = localization.GetByLabel('UI/Insurance/TimeLeft', time=timeDiff)
                        if days < 5:
                            timeLabel.color = util.Color.RED
                        timeLabel.text = text
                    else:
                        insuranceLabel.text = localization.GetByLabel('UI/Insurance/ShipUninsured')
                        insuranceLabel.color = util.Color.RED
        elif wnd.sr.isModule or wnd.sr.isStructure or wnd.sr.isDrone or wnd.sr.isAnchorable or wnd.sr.isConstructionPF or wnd.sr.isStructureUpgrade or wnd.sr.isApparel:
            self.GetInvTypeInfo(typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'], self.FilterZero, [const.attributeCapacity, const.attributeVolume, const.attributeMass])
            if not itemID:
                ammoLoadeds = [ x for x in cfg.dgmtypeattribs.get(typeID, []) if x.attributeID == const.attributeAmmoLoaded ]
                if len(ammoLoadeds):
                    self.GetAttrTypeInfo(ammoLoadeds[0].value, wnd.sr.data[C_ATTIBUTESTAB]['items'], [const.attributeEmDamage,
                     const.attributeThermalDamage,
                     const.attributeKineticDamage,
                     const.attributeExplosiveDamage])
            self.GetEffectTypeInfo(typeID, wnd.sr.data[C_FITTINGTAB]['items'], [const.effectHiPower,
             const.effectMedPower,
             const.effectLoPower,
             const.effectRigSlot,
             const.effectSubSystem])
            self.GetAttrItemInfo(itemID, typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'], banAttrs=[const.attributeCpu,
             const.attributePower,
             const.attributeRigSize,
             const.attributeCapacity,
             const.attributeVolume,
             const.attributeMass] + self.GetSkillAttrs())
            self.GetAttrItemInfo(itemID, typeID, wnd.sr.data[C_FITTINGTAB]['items'], (const.attributeCpu, const.attributePower, const.attributeRigSize))
            self.GetReqSkillInfo(typeID, wnd.sr.data[C_SKILLSTAB]['items'])
            self.GetMetaTypeInfo(typeID, wnd.sr.data[C_VARIATIONSTAB]['items'], wnd)
            self.InitVariationBottom(wnd)
        if invgroup.id in [const.groupSecureCargoContainer, const.groupAuditLogSecureContainer]:
            bp = sm.GetService('michelle').GetBallpark()
            if bp:
                ball = bp.GetBall(itemID)
            if bp and ball and not ball.isFree:
                bpr = sm.GetService('michelle').GetRemotePark()
                if bpr:
                    expiry = bpr.GetContainerExpiryDate(itemID)
                    daysLeft = max(0, (expiry - blue.os.GetWallclockTime()) / DAY)
                    expiryText = localization.GetByLabel('UI/Common/NumDays', numDays=daysLeft)
                    expiryLabel = listentry.Get('LabelTextTop', {'line': 1,
                     'label': localization.GetByLabel('UI/Common/Expires'),
                     'text': expiryText,
                     'iconID': const.iconDuration})
                    wnd.sr.data[C_ATTIBUTESTAB]['items'].append(expiryLabel)
        elif wnd.sr.isCharge:
            self.GetInvTypeInfo(typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'], self.FilterZero, [const.attributeCapacity, const.attributeVolume])
            if itemID:
                self.GetAttrItemInfo(itemID, typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'], banAttrs=[const.attributeCapacity, const.attributeVolume] + self.GetSkillAttrs())
            else:
                self.GetAttrTypeInfo(typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'], banAttrs=[const.attributeCapacity, const.attributeVolume] + self.GetSkillAttrs())
            bsd, bad = self.GetBaseDamageValue(typeID)
            if bad is not None and bsd is not None:
                text = localizationUtil.FormatNumeric(bsd[0], useGrouping=True, decimalPlaces=1)
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/InfoWindow/BaseShieldDamageLabel'),
                 'text': text,
                 'iconID': bsd[1]}))
                text = localizationUtil.FormatNumeric(bad[0], useGrouping=True, decimalPlaces=1)
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/InfoWindow/BaseArmorDamageLabel'),
                 'text': text,
                 'iconID': bad[1]}))
            self.GetReqSkillInfo(typeID, wnd.sr.data[C_SKILLSTAB]['items'])
            self.GetMetaTypeInfo(typeID, wnd.sr.data[C_VARIATIONSTAB]['items'], wnd)
            self.InitVariationBottom(wnd)
        elif wnd.sr.isCorporation:
            parallelCalls = []
            parallelCalls.append((sm.RemoteSvc('config').GetStationSolarSystemsByOwner, (itemID,)))
            if util.IsNPC(itemID):
                parallelCalls.append((sm.GetService('agents').GetAgentsByCorpID, (itemID,)))
                parallelCalls.append((sm.RemoteSvc('corporationSvc').GetCorpInfo, (itemID,)))
            else:
                parallelCalls.append((ReturnNone, ()))
                parallelCalls.append((ReturnNone, ()))
            parallelCalls.append((sm.GetService('faction').GetNPCCorpInfo, (itemID,)))
            systems, agents, corpmktinfo, npcCorpInfo = uthread.parallel(parallelCalls)
            founderdone = 0
            if cfg.invtypes.Get(cfg.eveowners.Get(wnd.sr.corpinfo.ceoID).typeID).groupID == const.groupCharacter:
                if wnd.sr.corpinfo.creatorID == wnd.sr.corpinfo.ceoID:
                    ceoLabel = localization.GetByLabel('UI/Corporations/CorpUIHome/CeoAndFounder')
                    founderdone = 1
                else:
                    ceoLabel = localization.GetByLabel('UI/Corporations/Common/CEO')
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': ceoLabel,
                 'text': cfg.eveowners.Get(wnd.sr.corpinfo.ceoID).name,
                 'typeID': cfg.eveowners.Get(wnd.sr.corpinfo.ceoID).typeID,
                 'itemID': wnd.sr.corpinfo.ceoID}))
            if not founderdone and cfg.invtypes.Get(cfg.eveowners.Get(wnd.sr.corpinfo.creatorID).typeID).groupID == const.groupCharacter:
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/Corporations/Common/Founder'),
                 'text': cfg.eveowners.Get(wnd.sr.corpinfo.creatorID).name,
                 'typeID': cfg.eveowners.Get(wnd.sr.corpinfo.creatorID).typeID,
                 'itemID': wnd.sr.corpinfo.creatorID}))
            if wnd.sr.corpinfo.allianceID:
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/Common/Alliance'),
                 'text': cfg.eveowners.Get(wnd.sr.corpinfo.allianceID).name,
                 'typeID': const.typeAlliance,
                 'itemID': wnd.sr.corpinfo.allianceID}))
            for configName, label in [('tickerName', localization.GetByLabel('UI/Corporations/CorpUIHome/TickerName')),
             ('shares', localization.GetByLabel('UI/Corporations/CorpUIHome/Shares')),
             ('memberCount', localization.GetByLabel('UI/Corporations/CorpUIHome/MemberCount')),
             ('taxRate', localization.GetByLabel('UI/Corporations/CorpUIHome/TaxRate'))]:
                if configName == 'memberCount' and util.IsNPC(itemID):
                    continue
                val = getattr(wnd.sr.corpinfo, configName, 0.0)
                if configName == 'taxRate':
                    val = localization.GetByLabel('UI/Common/Percentage', percentage=val * 100)
                elif isinstance(val, int):
                    val = localizationUtil.FormatNumeric(val, useGrouping=True, decimalPlaces=0)
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': label,
                 'text': val}))

            if wnd.sr.corpinfo.url:
                linkTag = '<url=%s>' % wnd.sr.corpinfo.url
                url = localization.GetByLabel('UI/Corporations/CorpUIHome/URLPlaceholder', linkTag=linkTag, url=wnd.sr.corpinfo.url)
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/Corporations/CorpUIHome/URL'),
                 'text': url}))
            if npcCorpInfo is not None and util.IsNPC(itemID):
                sizeDict = {'T': localization.GetByLabel('UI/Corporations/TinyCorp'),
                 'S': localization.GetByLabel('UI/Corporations/SmallCorp'),
                 'M': localization.GetByLabel('UI/Corporations/MediumCorp'),
                 'L': localization.GetByLabel('UI/Corporations/LargeCorp'),
                 'H': localization.GetByLabel('UI/Corporations/HugeCorp')}
                txt = sizeDict[npcCorpInfo.size]
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/Corporations/CorpSize'),
                 'text': txt}))
                extentDict = {'N': localization.GetByLabel('UI/Corporations/NationalCrop'),
                 'G': localization.GetByLabel('UI/Corporations/GlobalCorp'),
                 'R': localization.GetByLabel('UI/Corporations/RegionalCorp'),
                 'L': localization.GetByLabel('UI/Corporations/LocalCorp'),
                 'C': localization.GetByLabel('UI/Corporations/ConstellationCorp')}
                txt = extentDict[npcCorpInfo.extent]
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/Corporations/CorpExtent'),
                 'text': txt}))
            if itemID == session.corpid:
                for charinfo in sm.GetService('corp').GetMembersAsEveOwners():
                    if not util.IsNPC(charinfo.ownerID):
                        wnd.sr.data[C_CORPMEMBERSTAB]['items'].append(listentry.Get('User', {'info': charinfo,
                         'charID': charinfo.ownerID}))

                wnd.sr.data[C_CORPMEMBERSTAB]['headers'].append(localization.GetByLabel('UI/Common/NameCharacter'))
            solarSystemDict = {}
            corpName = cfg.eveowners.Get(itemID).name
            mapHintCallback = lambda : localization.GetByLabel('UI/InfoWindow/SystemSettledByCorp', corpName=corpName)
            for solarSys in systems:
                solarSystemDict[solarSys.solarSystemID] = (2.0,
                 1.0,
                 (mapHintCallback, ()),
                 None)

            mapSvc = sm.GetService('map')
            for solarSys in systems:
                parentConstellation = mapSvc.GetParent(solarSys.solarSystemID)
                parentRegion = mapSvc.GetParent(parentConstellation)
                name_with_path = ' / '.join([ mapSvc.GetItem(each).itemName for each in (parentRegion, parentConstellation, solarSys.solarSystemID) ])
                wnd.sr.data[C_SYSTEMSTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/Common/SolarSystem'),
                 'text': name_with_path,
                 'typeID': const.typeSolarSystem,
                 'itemID': solarSys.solarSystemID}))

            wnd.sr.data[C_SYSTEMSTAB]['name'] = localization.GetByLabel('UI/InfoWindow/SettledSystems')

            def ShowMap(*args):
                sm.GetService('viewState').ActivateView('starmap', hightlightedSolarSystems=solarSystemDict)

            wnd.sr.data['buttons'] += [(localization.GetByLabel('UI/Commands/ShowLocationOnMap'),
              ShowMap,
              (),
              66)]
            if not util.IsNPC(itemID):
                if sm.GetService('corp').GetActiveApplication(itemID) is not None:
                    buttonLabel = localization.GetByLabel('UI/Corporations/CorpApplications/ViewApplication')
                else:
                    buttonLabel = localization.GetByLabel('UI/Corporations/CorporationWindow/Alliances/Rankings/ApplyToJoin')
                wnd.sr.data['buttons'] += [(buttonLabel, sm.GetService('corp').ApplyForMembership, (itemID,))]
            else:
                wnd.sr.data['buttons'] += [(localization.GetByLabel('UI/AgentFinder/AgentFinder'),
                  uicore.cmd.OpenAgentFinder,
                  (),
                  66)]

            def SortStuff(a, b):
                for i in xrange(3):
                    x, y = a[i], b[i]
                    if x.name < y.name:
                        return -1
                    if x.name > y.name:
                        return 1

                return 0

            if corpmktinfo is not None:
                sellStuff = []
                buyStuff = []
                for each in corpmktinfo:
                    t = cfg.invtypes.GetIfExists(each.typeID)
                    if t:
                        g = cfg.invgroups.Get(t.groupID)
                        c = cfg.invcategories.Get(g.categoryID)
                        if each.sellPrice is not None:
                            sellStuff.append((c,
                             g,
                             t,
                             each.sellPrice,
                             each.sellQuantity,
                             each.sellDate,
                             each.sellStationID))
                        if each.buyPrice is not None:
                            buyStuff.append((c,
                             g,
                             t,
                             each.buyPrice,
                             each.buyQuantity,
                             each.buyDate,
                             each.buyStationID))

                sellStuff.sort(SortStuff)
                buyStuff.sort(SortStuff)
                for stuff, label in ((sellStuff, localization.GetByLabel('UI/InfoWindow/Supply')), (buyStuff, localization.GetByLabel('UI/InfoWindow/Demand'))):
                    if stuff:
                        wnd.sr.data[C_MARKETACTIVITYTAB]['items'].append(listentry.Get('Header', {'label': label}))
                        for each in stuff:
                            c, g, t, price, quantity, lastActivity, station = each
                            if lastActivity:
                                txt = localization.GetByLabel('UI/InfoWindow/CategoryGroupTypeForPrice', categoryName=c.name, groupName=g.name, typeName=t.name, price=price)
                            else:
                                txt = localization.GetByLabel('UI/InfoWindow/CategoryGroupTypeForPriceAndLastTransaction', categoryName=c.name, groupName=g.name, typeName=t.name, price=price, date=util.FmtDate(lastActivity, 'ls'), amount=quantity, location=station)
                            wnd.sr.data[C_MARKETACTIVITYTAB]['items'].append(listentry.Get('Text', {'line': 1,
                             'typeID': t.typeID,
                             'text': txt}))

            if util.IsNPC(itemID):
                agentCopy = agents[:]
                header = agentCopy.header
                acopy2 = util.Rowset(header)
                for i, agent in enumerate(agentCopy):
                    if agent.agentTypeID in (const.agentTypeResearchAgent, const.agentTypeBasicAgent, const.agentTypeFactionalWarfareAgent):
                        acopy2.append(agent)

                agentCopy = acopy2
                self.GetAgentScrollGroups(agentCopy, wnd.sr.data[C_AGENTSTAB]['items'])
        elif wnd.sr.isAlliance:
            rec = wnd.sr.allianceinfo
            executor = cfg.eveowners.Get(rec.executorCorpID)
            label = localization.GetByLabel('UI/Corporations/CorporationWindow/Alliances/Home/Executor')
            params = {'line': 1,
             'label': label,
             'text': executor.ownerName,
             'typeID': const.typeCorporation,
             'itemID': rec.executorCorpID}
            wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', params))
            label = localization.GetByLabel('UI/Corporations/CorporationWindow/Alliances/Home/ShortName')
            params = {'line': 1,
             'label': label,
             'text': rec.shortName}
            wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', params))
            label = localization.GetByLabel('UI/InfoWindow/CreatedByCorp')
            params = {'line': 1,
             'label': label,
             'text': cfg.eveowners.Get(rec.creatorCorpID).ownerName,
             'typeID': const.typeCorporation,
             'itemID': rec.creatorCorpID}
            wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', params))
            label = localization.GetByLabel('UI/Corporations/CorporationWindow/Alliances/Home/CreatedBy')
            params = {'line': 1,
             'label': label,
             'text': cfg.eveowners.Get(rec.creatorCharID).ownerName,
             'typeID': const.typeCharacterAmarr,
             'itemID': rec.creatorCharID}
            wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', params))
            label = localization.GetByLabel('UI/InfoWindow/StartDate')
            params = {'line': 1,
             'label': label,
             'text': util.FmtDate(rec.startDate, 'ls'),
             'typeID': None,
             'itemID': None}
            wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', params))
            if rec.url:
                linkTag = '<url=%s>' % rec.url
                url = localization.GetByLabel('UI/Corporations/CorpUIHome/URLPlaceholder', linkTag=linkTag, url=rec.url)
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/Common/URL'),
                 'text': url}))
        elif wnd.sr.isBlueprint:
            blueprintType = cfg.invbptypes.Get(typeID)
            isCopy = None
            if wnd.sr.blueprintInfo:
                bpi = wnd.sr.blueprintInfo
                wnd.sr.blueprintInfo = None
            elif wnd.sr.abstractinfo is not None:
                bpi = {'manufacturingTime': blueprintType.productionTime,
                 'productivityLevel': getattr(wnd.sr.abstractinfo, 'productivityLevel', 0),
                 'materialLevel': getattr(wnd.sr.abstractinfo, 'materialLevel', 0),
                 'maxProductionLimit': blueprintType.maxProductionLimit,
                 'researchMaterialTime': blueprintType.researchMaterialTime,
                 'researchCopyTime': blueprintType.researchCopyTime,
                 'researchProductivityTime': blueprintType.researchProductivityTime,
                 'researchTechTime': blueprintType.researchTechTime,
                 'wastageFactor': blueprintType.wasteFactor / 100.0,
                 'productTypeID': blueprintType.productTypeID}
                if wnd.sr.abstractinfo.isCopy:
                    bpi['copy'] = True
                    runs = wnd.sr.abstractinfo.Get('runs', None)
                    if runs is not None:
                        bpi['licensedProductionRunsRemaining'] = runs
            else:
                bpi = {'manufacturingTime': blueprintType.productionTime,
                 'productivityLevel': 0,
                 'materialLevel': 0,
                 'maxProductionLimit': blueprintType.maxProductionLimit,
                 'researchMaterialTime': blueprintType.researchMaterialTime,
                 'researchCopyTime': blueprintType.researchCopyTime,
                 'researchProductivityTime': blueprintType.researchProductivityTime,
                 'researchTechTime': blueprintType.researchTechTime,
                 'wastageFactor': blueprintType.wasteFactor / 100.0,
                 'productTypeID': blueprintType.productTypeID}
            for caption, attrs in self.GetBlueprintAttributes():
                bpAttr = [ each for each in attrs if each in bpi ]
                if bpAttr:
                    for each in bpAttr:
                        if each == 'copy':
                            isCopy = bpi[each] > 0
                            break

                    if isCopy is not None:
                        break

            typeOb = cfg.invtypes.Get(typeID)
            groupID = typeOb.groupID
            categoryID = typeOb.categoryID
            if categoryID != const.categoryAncientRelic:
                if isCopy == True:
                    label = localization.GetByLabel('UI/InfoWindow/BlueprintCopy', color='0xff999999')
                    wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('Item', {'itemID': None,
                     'isCopy': True,
                     'typeID': typeID,
                     'label': label,
                     'getIcon': 1}))
                elif isCopy == False:
                    label = localization.GetByLabel('UI/InfoWindow/BlueprintOriginal', color='0xff55bb55')
                    wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('Item', {'itemID': None,
                     'typeID': typeID,
                     'label': label,
                     'getIcon': 1}))
            godmaChar = sm.GetService('godma').GetItem(session.charid)
            if categoryID == const.categoryAncientRelic:
                attrTypeInfo = cfg.dgmattribs.Get(const.attributeVolume)
                formatedValue = localizationUtil.FormatNumeric(invtype.volume, useGrouping=True)
                text = localization.GetByLabel('UI/InfoWindow/ValueAndUnit', value=formatedValue, unit=self.FormatUnit(attrTypeInfo.unitID))
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': attrTypeInfo.displayName,
                 'text': text,
                 'iconID': attrTypeInfo.iconID}))
                propertyName = 'researchTechTime'
                propertyValue = bpi[propertyName]
                propertyName = localization.GetByLabel('UI/InfoWindow/ResearchTechTime')
                propertyValue = self.FormatAsFactoryTime(propertyValue)
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('Header', {'line': 1,
                 'label': localization.GetByLabel('UI/ScienceAndIndustry/ReverseEngineering')}))
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': propertyName,
                 'text': propertyValue,
                 'iconID': const.iconDuration}))
            else:
                for caption, attrs in self.GetBlueprintAttributes():
                    bpAttr = [ each for each in attrs if each in bpi ]
                    if bpAttr:
                        if 'researchTechTime' in bpAttr or not isCopy or caption not in [localization.GetByLabel('UI/InfoWindow/ResearchingHeader')]:
                            wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('Header', {'line': 1,
                             'label': caption}))
                        for each in bpAttr:
                            propertyName = each
                            propertyValue = bpi[each]

                            def AddData(label, text):
                                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                                 'label': label,
                                 'text': text,
                                 'iconID': const.iconDuration}))

                            if propertyName in ('researchMaterialTime', 'researchCopyTime', 'researchProductivityTime'):
                                if isCopy:
                                    continue
                            if propertyName == 'manufacturingTime':
                                propertyName = localization.GetByLabel('UI/InfoWindow/ManufacturingTime')
                                batchTime = blueprintType.productionTime
                                pl = bpi['productivityLevel']
                                if pl > 0:
                                    batchTime = batchTime - (1.0 - 1.0 / (1 + pl)) * blueprintType.productivityModifier
                                elif pl < 0:
                                    batchTime = batchTime + (1.0 - pl) * blueprintType.productivityModifier
                                batchTime = int(batchTime)
                                propertyValue = self.FormatAsFactoryTime(batchTime)
                                AddData(propertyName, propertyValue)
                                if godmaChar:
                                    timeMultiplier = godmaChar.manufactureTimeMultiplier
                                    batchTime = long(float(batchTime) * timeMultiplier)
                                    propertyName = localization.GetByLabel('UI/InfoWindow/ManufacturingTimeForYou')
                                    propertyValue = self.FormatAsFactoryTime(batchTime)
                                    AddData(propertyName, propertyValue)
                                continue
                            elif propertyName == 'researchMaterialTime':
                                propertyName = localization.GetByLabel('UI/InfoWindow/ResearchMaterialTime')
                                propertyValue = self.FormatAsFactoryTime(propertyValue)
                                AddData(propertyName, propertyValue)
                                if godmaChar:
                                    timeMultiplier = godmaChar.mineralNeedResearchSpeed
                                    batchTime = blueprintType.researchMaterialTime
                                    batchTime = long(float(batchTime) * timeMultiplier)
                                    propertyName = localization.GetByLabel('UI/InfoWindow/ResearchMaterialTimeYou')
                                    propertyValue = self.FormatAsFactoryTime(batchTime)
                                    AddData(propertyName, propertyValue)
                                continue
                            elif propertyName == 'researchCopyTime':
                                if godmaChar:
                                    timeMultiplier = sm.GetService('godma').GetType(cfg.eveowners.Get(session.charid).typeID).copySpeedPercent
                                else:
                                    timeMultiplier = 1.0
                                propertyName = localization.GetByLabel('UI/InfoWindow/ResearchCopyTime')
                                propertyValue = self.FormatAsFactoryTime(long(float(propertyValue) * timeMultiplier))
                                AddData(propertyName, propertyValue)
                                if godmaChar:
                                    timeMultiplier = godmaChar.copySpeedPercent
                                    percent = float(1) / float(blueprintType.maxProductionLimit)
                                    batchTime = long(float(blueprintType.researchCopyTime) * percent)
                                    batchTime = long(float(batchTime) * timeMultiplier)
                                    propertyName = localization.GetByLabel('UI/InfoWindow/ResearchCopyTimeYou')
                                    propertyValue = self.FormatAsFactoryTime(batchTime)
                                    AddData(propertyName, propertyValue)
                                continue
                            elif propertyName == 'researchProductivityTime':
                                propertyName = localization.GetByLabel('UI/InfoWindow/ResearchProductivityTime')
                                propertyValue = self.FormatAsFactoryTime(propertyValue)
                                AddData(propertyName, propertyValue)
                                if godmaChar:
                                    timeMultiplier = godmaChar.manufacturingTimeResearchSpeed
                                    batchTime = blueprintType.researchProductivityTime
                                    batchTime = long(float(batchTime) * timeMultiplier)
                                    propertyName = localization.GetByLabel('UI/InfoWindow/ResearchProductivityTimeYou')
                                    propertyValue = self.FormatAsFactoryTime(batchTime)
                                    AddData(propertyName, propertyValue)
                                continue
                            elif propertyName == 'researchTechTime':
                                if not isCopy:
                                    continue
                                propertyName = localization.GetByLabel('UI/InfoWindow/ResearchTechTime')
                                propertyValue = self.FormatAsFactoryTime(propertyValue)
                                AddData(propertyName, propertyValue)
                                continue
                            elif propertyName in ('materialLevel', 'maxProductionLimit', 'productivityLevel'):
                                propertyDict = {'materialLevel': localization.GetByLabel('UI/InfoWindow/MaterialLevel'),
                                 'maxProductionLimit': localization.GetByLabel('UI/InfoWindow/MaxRunsPerBlueprintCopy'),
                                 'productivityLevel': localization.GetByLabel('UI/InfoWindow/ProductivityLevel')}
                                propertyName = propertyDict.get(propertyName)
                                propertyValue = localizationUtil.FormatNumeric(propertyValue, useGrouping=True, decimalPlaces=0)
                            elif propertyName == 'wastageFactor':
                                propertyName = localization.GetByLabel('UI/InfoWindow/WastageFactor')
                                propertyValue = localization.GetByLabel('UI/Common/Percentage', percentage=propertyValue * 100)
                            elif propertyName == 'productTypeID':
                                typeInfo = cfg.invtypes.Get(propertyValue)
                                typeDescription = localization.GetByLabel('UI/InfoWindow/Produces', invType=propertyValue, portion=typeInfo.portionSize)
                                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('Item', {'itemID': None,
                                 'typeID': propertyValue,
                                 'label': typeDescription,
                                 'getIcon': 1}))
                                continue
                            elif propertyName == 'copy':
                                propertyName = localization.GetByLabel('UI/InfoWindow/IsCopyBlueprint')
                                if propertyValue:
                                    propertyValue = localization.GetByLabel('UI/Common/Yes')
                                else:
                                    propertyValue = localization.GetByLabel('UI/Common/No')
                            elif propertyName == 'licensedProductionRunsRemaining':
                                propertyName = localization.GetByLabel('UI/InfoWindow/LicensedRunsRemaining')
                                if propertyValue == -1:
                                    propertyValue = localization.GetByLabel('UI/InfoWindow/InfiniteRunsRemaining')
                            AddData(propertyName, propertyValue)

            bomByActivity = sm.RemoteSvc('factory').GetMaterialsForTypeWithActivity(typeID)
            activities = {const.activityManufacturing: C_MANUFACTURINGTAB,
             const.activityCopying: C_COPYINGTAB,
             const.activityResearchingMaterialProductivity: C_RESEARCHINGMATERIALEFFTAB,
             const.activityResearchingTimeProductivity: C_RESEARCHTIMEPRODTAB,
             const.activityDuplicating: C_DUPLICATINGTAB,
             const.activityReverseEngineering: C_REVERSEENGINEERINGTAB,
             const.activityInvention: C_INVENTIONTAB}
            blueprintMaterialMultiplier = 0.0
            characterMaterialMultiplier = max(1.0, godmaChar.manufactureCostMultiplier) if godmaChar else 1.0
            if 'wastageFactor' in bpi:
                blueprintMaterialMultiplier = bpi['wastageFactor']
            for activity in activities:
                if activity not in bomByActivity:
                    continue
                activityName = activities[activity]
                skills = []
                materials = []
                commands = []
                extraMaterials = []
                extraCommands = []
                indexedExtras = copy.deepcopy(bomByActivity[activity].extras).Index('requiredTypeID')
                for skill in bomByActivity[activity].skills:
                    propertyInfo = cfg.invtypes.Get(skill.requiredTypeID)
                    propertyName = propertyInfo.typeName
                    propertyValue = localization.GetByLabel('UI/InfoWindow/SkillAndLevel', skill=skill.requiredTypeID, skillLevel=skill.quantity)
                    skills.append((propertyName,
                     propertyValue,
                     skill.requiredTypeID,
                     skill.quantity))

                for material in bomByActivity[activity].rawMaterials:
                    if material.quantity <= 0:
                        continue
                    propertyInfo = cfg.invtypes.Get(material.requiredTypeID)
                    propertyName = propertyInfo.typeName
                    amountRequired = amountRequiredByPlayer = material.quantity
                    blueprintWaste = characterWaste = 0.0
                    if activity in (const.activityManufacturing, const.activityDuplicating):
                        if activity == const.activityManufacturing:
                            blueprintWaste = float(amountRequired) * float(blueprintMaterialMultiplier)
                        characterWaste = float(amountRequired) * float(characterMaterialMultiplier) - float(amountRequired)
                        amountRequired = amountRequired + blueprintWaste
                        amountRequiredByPlayer = int(round(amountRequired + characterWaste))
                        amountRequired = int(round(amountRequired))
                    if amountRequiredByPlayer == amountRequired:
                        propertyValue = localization.GetByLabel('UI/InfoWindow/MaterialsRequired', invType=material.requiredTypeID, amountRequiredByPlayer=amountRequiredByPlayer)
                    else:
                        propertyValue = localization.GetByLabel('UI/InfoWindow/MaterialsRequiredYou', invType=material.requiredTypeID, amountRequiredByYou=amountRequiredByPlayer, amountRequiredPerfect=amountRequired)
                    if amountRequiredByPlayer >= 0.0:
                        commands.append((material.requiredTypeID, amountRequiredByPlayer))
                    materials.append((propertyName, propertyValue, material.requiredTypeID))

                for key, extra in indexedExtras.iteritems():
                    if extra.quantity <= 0:
                        continue
                    propertyInfo = cfg.invtypes.Get(extra.requiredTypeID)
                    propertyName = propertyInfo.typeName
                    if extra.damagePerJob < 1.0:
                        propertyValue = localization.GetByLabel('UI/InfoWindow/DamagePerRun', invType=extra.requiredTypeID, amountRequiredByPlayer=extra.quantity, percentage=extra.damagePerJob * 100)
                    else:
                        propertyValue = localization.GetByLabel('UI/InfoWindow/MaterialsRequired', invType=extra.requiredTypeID, amountRequiredByPlayer=extra.quantity)
                    extraMaterials.append((propertyName, propertyValue, extra.requiredTypeID))
                    extraCommands.append((extra.requiredTypeID, extra.quantity))

                wnd.sr.data[activityName]['items'].append(listentry.Get('Text', {'line': 1,
                 'text': localization.GetByLabel('UI/InfoWindow/BillOfMaterialHint1')}))
                wnd.sr.data[activityName]['items'].append(listentry.Get('Divider'))
                for label, content, cmds in ((localization.GetByLabel('UI/Common/Skills'), skills, None), (localization.GetByLabel('UI/ScienceAndIndustry/Materials'), materials, commands), (localization.GetByLabel('UI/ScienceAndIndustry/ExtraMaterials'), extraMaterials, extraCommands)):
                    data = {'GetSubContent': self.GetBOMSubContent,
                     'label': label,
                     'groupItems': content,
                     'id': ('BOM', label),
                     'tabs': [],
                     'state': 'locked',
                     'showicon': 'hide',
                     'commands': cmds}
                    wnd.sr.data[activityName]['items'].append(listentry.Get('Group', data))

        elif wnd.sr.isStargate:
            bp = sm.GetService('michelle').GetBallpark()
            if bp is not None:
                slimItem = bp.GetInvItem(itemID)
                if slimItem is not None:
                    locs = []
                    for each in slimItem.jumps:
                        if each.locationID not in locs:
                            locs.append(each.locationID)
                        if each.toCelestialID not in locs:
                            locs.append(each.toCelestialID)

                    if len(locs):
                        cfg.evelocations.Prime(locs)
                    for each in slimItem.jumps:
                        destLabel = localization.GetByLabel('UI/InfoWindow/DestinationInSolarsystem', destination=each.toCelestialID, solarsystem=each.locationID)
                        wnd.sr.data[C_JUMPSTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': localization.GetByLabel('UI/Common/Jump'),
                         'text': destLabel,
                         'typeID': const.groupSolarSystem,
                         'itemID': each.locationID}))

        elif wnd.sr.isCelestial:
            if 40000000 < itemID < 50000000:
                celestialinfo = sm.RemoteSvc('config').GetCelestialStatistic(itemID)
                if len(celestialinfo):
                    for key in celestialinfo.columns:
                        if key not in 'celestialID':
                            val = celestialinfo[0][key]
                            text = val
                            if invgroup.id not in [const.groupSun] and key in ('spectralClass', 'luminosity', 'age'):
                                pass
                            elif invgroup.id in [const.groupSun] and key in ('orbitRadius', 'eccentricity', 'massDust', 'density', 'surfaceGravity', 'escapeVelocity', 'orbitPeriod', 'pressure'):
                                pass
                            elif key in ('fragmented', 'locked', 'rotationRate', 'mass', 'massGas', 'life'):
                                pass
                            elif invgroup.id in [const.groupAsteroidBelt] and key in ('surfaceGravity', 'escapeVelocity', 'pressure', 'radius', 'temperature'):
                                pass
                            elif invgroup.id in [const.groupMoon] and key in ('eccentricity',):
                                pass
                            else:
                                label, value = util.FmtPlanetAttributeKeyVal(key, val)
                                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                                 'label': label,
                                 'text': value}))

            universeID, regionID, constellationID, solarsystemID, _itemID = sm.GetService('map').GetParentLocationID(itemID, 1)
            if solarsystemID is None and moonOrPlanet:
                solarsystemID = parentID
            if solarsystemID is not None:
                solarsystem = sm.GetService('map').GetSolarsystemItems(solarsystemID)
                sun = None
                if cfg.invtypes.Get(typeID).groupID == const.groupSolarSystem:
                    for each in solarsystem:
                        if cfg.invtypes.Get(each.typeID).groupID == const.groupSun:
                            sun = each.itemID

                    if sun:
                        itemID = sun
                orbitItems = []
                indent = 0
                if solarsystemID == itemID and sun:
                    rootID = [ each for each in solarsystem if cfg.invtypes.Get(each.typeID).groupID == const.groupSun ][0].itemID
                else:
                    rootID = itemID
                groupSort = {const.groupStation: -2,
                 const.groupStargate: -1,
                 const.groupAsteroidBelt: 1,
                 const.groupMoon: 2,
                 const.groupPlanet: 3}

                def DrawOrbitItems(rootID, indent):
                    tmp = [ each for each in solarsystem if each.orbitID == rootID ]
                    tmp.sort(lambda a, b: cmp(*[ groupSort.get(cfg.invtypes.Get(each.typeID).groupID, 0) for each in (a, b) ]) or cmp(a.celestialIndex, b.celestialIndex) or cmp(a.orbitIndex, b.orbitIndex))
                    for each in tmp:
                        name = cfg.evelocations.Get(each.itemID).name
                        planet = False
                        if util.IsStation(each.itemID):
                            name = '<b>' + name + '</b>'
                        elif each.groupID == const.groupMoon:
                            name = '<color=0xff666666>' + name + '</color>'
                        elif each.groupID == const.groupPlanet:
                            planet = True
                        if planet:
                            wnd.sr.data[C_ORBITALBODIESTAB]['items'].append(listentry.Get('LabelPlanetTextTop', {'line': 1,
                             'label': indent * '    ' + cfg.invtypes.Get(each.typeID).name,
                             'text': indent * '    ' + name,
                             'typeID': each.typeID,
                             'itemID': each.itemID,
                             'locationID': solarsystemID}))
                        else:
                            wnd.sr.data[C_ORBITALBODIESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                             'label': indent * '    ' + cfg.invtypes.Get(each.typeID).name,
                             'text': indent * '    ' + name,
                             'typeID': each.typeID,
                             'itemID': each.itemID}))
                        DrawOrbitItems(each.itemID, indent + 1)

                if sun:
                    DrawOrbitItems(rootID, 0)
                itemID = solarsystemID
            typeGroupID = cfg.invtypes.Get(typeID).groupID
            neighborGrouping = {const.groupConstellation: localization.GetByLabel('UI/InfoWindow/AdjacentConstellations'),
             const.groupRegion: localization.GetByLabel('UI/InfoWindow/AdjacentRegions'),
             const.groupSolarSystem: localization.GetByLabel('UI/InfoWindow/AdjacentSolarSystem')}
            childGrouping = {const.groupRegion: localization.GetByLabel('UI/InfoWindow/RelatedConstellation'),
             const.groupConstellation: localization.GetByLabel('UI/InfoWindow/RelatedSolarSystem')}
            if typeGroupID == const.groupConstellation:
                children = sm.GetService('map').GetChildren(itemID)
                for childID in children:
                    childItem = sm.GetService('map').GetItem(childID)
                    if childItem is not None:
                        text = self.GetColorCodedSecurityStringForSystem(childItem.itemID, childItem.itemName)
                        wnd.sr.data[C_CHILDRENTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': cfg.invtypes.Get(childItem.typeID).name,
                         'text': text,
                         'typeID': childItem.typeID,
                         'itemID': childItem.itemID,
                         'tabs': [35],
                         'tabMargin': -2}))

                wnd.sr.data[C_CHILDRENTAB]['name'] = childGrouping.get(const.groupConstellation, localization.GetByLabel('UI/InfoWindow/UnknownTabName'))
            elif typeGroupID == const.groupRegion:
                children = sm.GetService('map').GetChildren(itemID)
                for childID in children:
                    childItem = sm.GetService('map').GetItem(childID)
                    if childItem is not None:
                        wnd.sr.data[C_CHILDRENTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': cfg.invtypes.Get(childItem.typeID).name,
                         'text': childItem.itemName,
                         'typeID': childItem.typeID,
                         'itemID': childItem.itemID}))

                wnd.sr.data[C_CHILDRENTAB]['name'] = childGrouping.get(const.groupRegion, localization.GetByLabel('UI/InfoWindow/UnknownTabName'))
            if typeGroupID in [const.groupConstellation, const.groupRegion, const.groupSolarSystem]:
                neigbors = sm.GetService('map').GetNeighbors(itemID)
                for childID in neigbors:
                    childItem = sm.GetService('map').GetItem(childID)
                    if childItem is not None:
                        if childItem.typeID == const.groupSolarSystem:
                            text = self.GetColorCodedSecurityStringForSystem(childID, childItem.itemName)
                        else:
                            text = childItem.itemName
                        wnd.sr.data[C_NEIGHBORSTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': cfg.invtypes.Get(childItem.typeID).name,
                         'text': text,
                         'typeID': childItem.typeID,
                         'itemID': childItem.itemID,
                         'tabs': [35],
                         'tabMargin': -2}))

                wnd.sr.data[C_NEIGHBORSTAB]['name'] = neighborGrouping.get(typeGroupID, localization.GetByLabel('UI/InfoWindow/UnknownTabName'))
            if cfg.invtypes.Get(typeID).groupID in [const.groupConstellation, const.groupSolarSystem]:
                mapSvc = sm.GetService('map')
                shortestRoute = sm.GetService('starmap').ShortestGeneralPath(itemID)
                shortestRoute = shortestRoute[1:]
                wasRegion = None
                wasConstellation = None
                if len(shortestRoute) > 0:
                    wnd.sr.data[C_ROUTETAB]['items'].append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Market/MarketQuote/NumberOfJumps', num=len(shortestRoute))}))
                for i in range(len(shortestRoute)):
                    childID = shortestRoute[i]
                    childItem = sm.GetService('map').GetItem(childID)
                    parentConstellation = mapSvc.GetParent(childID)
                    parentRegion = mapSvc.GetParent(parentConstellation)
                    nameWithPath = localization.GetByLabel('UI/InfoWindow/SolarsystemLocation', region=parentRegion, constellation=parentConstellation, solarsystem=childID)
                    nameWithPath = self.GetColorCodedSecurityStringForSystem(childID, nameWithPath)
                    jumpDescription = localization.GetByLabel('UI/InfoWindow/RegularJump', numJumps=i + 1)
                    if i > 0:
                        if wasRegion != parentRegion:
                            jumpDescription = localization.GetByLabel('UI/InfoWindow/RegionJump', numJumps=i + 1)
                        elif wasConstellation != parentConstellation:
                            jumpDescription = localization.GetByLabel('UI/InfoWindow/ConstellationJump', numJumps=i + 1)
                    wasRegion = parentRegion
                    wasConstellation = parentConstellation
                    if childItem is not None:
                        wnd.sr.data[C_ROUTETAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': jumpDescription,
                         'text': nameWithPath,
                         'typeID': childItem.typeID,
                         'itemID': childItem.itemID,
                         'tabs': [35],
                         'tabMargin': -2}))

            groupID = cfg.invtypes.Get(typeID).groupID

            def ShowMap(idx, *args):
                sm.GetService('viewState').ActivateView('starmap', interestID=itemID)

            if groupID in [const.groupSolarSystem, const.groupConstellation, const.groupRegion]:
                loc = (None, None, None)
                if groupID == const.groupSolarSystem:
                    systemID = itemID
                    constellationID = sm.GetService('map').GetParent(itemID)
                    regionID = sm.GetService('map').GetParent(constellationID)
                    loc = (systemID, constellationID, regionID)
                elif groupID == const.groupConstellation:
                    constellationID = itemID
                    regionID = sm.GetService('map').GetParent(constellationID)
                    loc = (None, constellationID, regionID)
                elif groupID == const.groupRegion:
                    regionID = itemID
                    loc = (None, None, regionID)
                wnd.sr.data['buttons'] = [(localization.GetByLabel('UI/Inflight/BookmarkLocation'),
                  self.Bookmark,
                  (itemID, typeID, parentID),
                  81), (localization.GetByLabel('UI/Commands/ShowLocationOnMap'),
                  ShowMap,
                  [const.groupSolarSystem, const.groupConstellation, const.groupRegion].index(groupID),
                  81), (localization.GetByLabel('UI/Sovereignty/Sovereignty'), self.DrillToLocation, loc)]
            elif itemID and groupID == const.groupStation:
                wnd.sr.data['buttons'] = [(localization.GetByLabel('UI/Inflight/SetDestination'),
                  self.SetDestination,
                  (itemID,),
                  81)]
            invtype = cfg.invtypes.Get(typeID)
            if invtype.categoryID == const.categoryAsteroid or invtype.groupID == const.groupHarvestableCloud:
                formatedValue = localizationUtil.FormatNumeric(invtype.volume, useGrouping=True)
                value = localization.GetByLabel('UI/InfoWindow/ValueAndUnit', value=formatedValue, unit=self.FormatUnit(const.unitVolume))
                fields = [(localization.GetByLabel('UI/Common/Volume'), value), (localization.GetByLabel('UI/InfoWindow/UnitsToRefine'), localizationUtil.FormatNumeric(int(invtype.portionSize), useGrouping=True))]
                try:
                    fields.append((localization.GetByLabel('UI/Generic/FormatPlanetAttributes/attributeRadius'), self.FormatValue(sm.GetService('michelle').GetBallpark().GetBall(itemID).radius, const.unitLength)))
                except:
                    sys.exc_clear()

                for header, text in fields:
                    wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                     'label': header,
                     'text': text}))

        showChar = False
        if session.stationid:
            shipID = util.GetActiveShip()
            if shipID == itemID:
                showChar = True
                ownerID = session.charid
        if wnd.sr.isOwned:
            if eve.session.solarsystemid is not None:
                slimitem = sm.GetService('michelle').GetBallpark().GetInvItem(itemID)
                if slimitem is not None:
                    showChar = True
                    ownerID = slimitem.ownerID
        if showChar:
            ownerOb = cfg.eveowners.Get(ownerID)
            if ownerOb.groupID == const.groupCharacter:
                btn = uix.GetBigButton(42, wnd.sr.subinfolinkcontainer, left=0, top=0, iconMargin=2)
                btn.OnClick = (wnd.LoadData, ownerOb.typeID, ownerID)
                btn.hint = localization.GetByLabel('UI/InfoWindow/ClickForPilotInfo')
                btn.sr.icon.LoadIconByTypeID(ownerOb.typeID, itemID=ownerID, ignoreSize=True)
                btn.sr.icon.SetSize(0, 0)
                wnd.sr.subinfolinkcontainer.height = 42
            if ownerOb.groupID == const.groupCorporation:
                wnd.GetCorpLogo(ownerID, parent=wnd.sr.subinfolinkcontainer)
                wnd.sr.subinfolinkcontainer.height = 64
        if wnd.sr.isFaction:
            races, stations, systems = sm.GetService('faction').GetFactionInfo(itemID)
            memberRaceList = []
            for race in cfg.races:
                if race.raceID in races:
                    memberRaceList.append(race.raceName)

            if len(memberRaceList) > 0:
                memberRaceText = localizationUtil.FormatGenericList(memberRaceList)
                wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/InfoWindow/MemberRaces'),
                 'text': memberRaceText}))
            text = localizationUtil.FormatNumeric(systems, useGrouping=True)
            wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
             'label': localization.GetByLabel('UI/InfoWindow/SettledSystems'),
             'text': text}))
            text = localizationUtil.FormatNumeric(stations, useGrouping=True)
            wnd.sr.data[C_ATTIBUTESTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
             'label': localization.GetByLabel('UI/Common/Stations'),
             'text': text}))
            wnd.sr.data[C_ATTIBUTESTAB]['name'] = localization.GetByLabel('UI/InfoWindow/TabNames/Statistics')

            def SortFunc(x, y):
                xname = cfg.eveowners.Get(x).name
                if xname.startswith('The '):
                    xname = xname[4:]
                yname = cfg.eveowners.Get(y).name
                if yname.startswith('The '):
                    yname = yname[4:]
                if xname < yname:
                    return -1
                if xname > yname:
                    return 1
                return 0

            corpsOfFaction = sm.GetService('faction').GetCorpsOfFaction(itemID)
            corpsOfFaction = copy.copy(corpsOfFaction)
            corpsOfFaction.sort(SortFunc)
            for corpID in corpsOfFaction:
                corp = cfg.eveowners.Get(corpID)
                wnd.sr.data[C_MEMBEROFCORPSTAB]['items'].append(listentry.Get('Text', {'line': 1,
                 'typeID': corp.typeID,
                 'itemID': corp.ownerID,
                 'text': corp.name}))

            mapSvc = sm.GetService('map')
            regions, constellations, solarsystems = sm.GetService('faction').GetFactionLocations(itemID)
            for regionID in regions:
                nameWithPath = mapSvc.GetItem(regionID).itemName
                wnd.sr.data[C_SYSTEMSTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/Common/LocationTypes/Region'),
                 'text': nameWithPath,
                 'typeID': const.typeRegion,
                 'itemID': regionID}))

            for constellationID in constellations:
                regionID = mapSvc.GetParent(constellationID)
                nameWithPath = localization.GetByLabel('UI/InfoWindow/ConstellationLocation', region=regionID, constellation=constellationID)
                wnd.sr.data[C_SYSTEMSTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/Corporations/ConstellationCorp'),
                 'text': nameWithPath,
                 'typeID': const.typeConstellation,
                 'itemID': constellationID}))

            for solarsystemID in solarsystems:
                constellationID = mapSvc.GetParent(solarsystemID)
                regionID = mapSvc.GetParent(constellationID)
                nameWithPath = localization.GetByLabel('UI/InfoWindow/SolarsystemLocation', region=regionID, constellation=constellationID, solarsystem=solarsystemID)
                wnd.sr.data[C_SYSTEMSTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': localization.GetByLabel('UI/Common/LocationTypes/SolarSystem'),
                 'text': nameWithPath,
                 'typeID': const.typeSolarSystem,
                 'itemID': solarsystemID}))

            wnd.sr.data[C_SYSTEMSTAB]['name'] = localization.GetByLabel('UI/InfoWindow/ControlledTerritory')
            illegalities = cfg.invcontrabandTypesByFaction.get(itemID, {})
            for tmpTypeID, illegality in illegalities.iteritems():
                txt = self.__GetIllegalityString(illegality)
                illegalityText = localization.GetByLabel('UI/InfoWindow/IllegalTypeString', item=tmpTypeID, implications=txt)
                wnd.sr.data[C_LEGALITYTAB]['items'].append(listentry.Get('Text', {'line': 1,
                 'text': illegalityText,
                 'typeID': tmpTypeID}))

            wnd.sr.data[C_LEGALITYTAB]['items'] = localizationUtil.Sort(wnd.sr.data[C_LEGALITYTAB]['items'], key=lambda x: x['text'])
            if illegalities:
                wnd.sr.data[C_LEGALITYTAB]['items'].insert(0, listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/IllegalTypes')}))
        if wnd.sr.isCharacter and util.IsNPC(itemID) or invgroup == const.groupAgentsinSpace and sm.GetService('godma').GetType(typeID).agentID:
            agentID = itemID or sm.GetService('godma').GetType(typeID).agentID
            try:
                details = sm.GetService('agents').GetAgentMoniker(agentID).GetInfoServiceDetails()
                if details is not None:
                    npcDivisions = sm.GetService('agents').GetDivisions()
                    agentInfo = sm.GetService('agents').GetAgentByID(agentID)
                    if agentInfo:
                        typeDict = {const.agentTypeGenericStorylineMissionAgent: localization.GetByLabel('UI/InfoWindow/AgentTypeStorylineImportant'),
                         const.agentTypeStorylineMissionAgent: localization.GetByLabel('UI/InfoWindow/AgentTypeStorylineImportant'),
                         const.agentTypeEventMissionAgent: localization.GetByLabel('UI/InfoWindow/AgentTypeEvent'),
                         const.agentTypeCareerAgent: localization.GetByLabel('UI/InfoWindow/AgentTypeCareer')}
                        t = typeDict.get(agentInfo.agentTypeID, None)
                        if t:
                            wnd.sr.data[C_AGENTINFOTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                             'label': localization.GetByLabel('UI/InfoWindow/AgentType'),
                             'text': t}))
                    if agentInfo and agentInfo.agentTypeID not in (const.agentTypeGenericStorylineMissionAgent, const.agentTypeStorylineMissionAgent):
                        wnd.sr.data[C_AGENTINFOTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': localization.GetByLabel('UI/InfoWindow/AgentDivision'),
                         'text': npcDivisions[agentInfo.divisionID].divisionName.replace('&', '&amp;')}))
                    if details.stationID:
                        stationinfo = sm.RemoteSvc('stationSvc').GetStation(details.stationID)
                        wnd.sr.data[C_AGENTINFOTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': localization.GetByLabel('UI/InfoWindow/AgentLocation'),
                         'text': cfg.evelocations.Get(details.stationID).name,
                         'typeID': stationinfo.stationTypeID,
                         'itemID': details.stationID}))
                    else:
                        agentSolarSystemID = sm.GetService('agents').GetSolarSystemOfAgent(agentID)
                        wnd.sr.data[C_AGENTINFOTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': localization.GetByLabel('UI/InfoWindow/AgentLocation'),
                         'text': cfg.evelocations.Get(agentSolarSystemID).name,
                         'typeID': const.typeSolarSystem,
                         'itemID': agentSolarSystemID}))
                    if agentInfo and agentInfo.agentTypeID not in (const.agentTypeGenericStorylineMissionAgent, const.agentTypeStorylineMissionAgent):
                        level = localizationUtil.FormatNumeric(details.level, decimalPlaces=0)
                        wnd.sr.data[C_AGENTINFOTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': localization.GetByLabel('UI/InfoWindow/AgentLevel'),
                         'text': level}))
                    for data in details.services:
                        serviceInfo = sm.GetService('agents').ProcessAgentInfoKeyVal(data)
                        for entry in serviceInfo:
                            wnd.sr.data[C_AGENTINFOTAB]['items'].append(listentry.Get('Header', {'label': entry[0]}))
                            for entryDetails in entry[1]:
                                wnd.sr.data[C_AGENTINFOTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                                 'label': entryDetails[0],
                                 'text': entryDetails[1]}))

                    if details.incompatible:
                        if type(details.incompatible) is tuple:
                            incText = localization.GetByLabel(details.incompatible[0], **details.incompatible[1])
                        else:
                            incText = details.incompatible
                        wnd.sr.data[C_AGENTINFOTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                         'label': localization.GetByLabel('UI/InfoWindow/AgentCompatibility'),
                         'text': incText}))
            except UserError as e:
                sys.exc_clear()

        if wnd.sr.isControlTower:
            wnd.sr.dynamicTabs.append((C_FUELREQTAB, 'FuelRequirements', localization.GetByLabel('UI/InfoWindow/TabNames/FuelRequirements')))
        if wnd.sr.isUpgradeable:
            wnd.sr.dynamicTabs.append((C_UPGRADEMATERIALREQTAB, 'UpgradeMaterialRequirements', localization.GetByLabel('UI/InfoWindow/TabNames/UpgradeRequirements')))
        if wnd.sr.isConstructionPF:
            wnd.sr.dynamicTabs.append((C_MATERIALREQTAB, 'MaterialRequirements', localization.GetByLabel('UI/InfoWindow/TabNames/MaterialRequirements')))
        if wnd.sr.isReaction:
            wnd.sr.dynamicTabs.append((C_REACTIONTAB, 'Reaction', localization.GetByLabel('UI/InfoWindow/TabNames/Reaction')))
        if util.IsOrbital(cfg.invtypes.Get(typeID).categoryID):

            def FetchDynamicAttributes(wnd, data, itemID):
                if sm.GetService('michelle').GetBallpark().GetBall(itemID) is not None:
                    taxRate = moniker.GetPlanetOrbitalRegistry(session.solarsystemid).GetTaxRate(itemID)
                    if taxRate is not None:
                        text = localization.GetByLabel('UI/Common/Percentage', percentage=taxRate * 100)
                    else:
                        text = localization.GetByLabel('UI/PI/Common/CustomsOfficeAccessDenied')
                    data['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                     'label': localization.GetByLabel('UI/PI/Common/CustomsOfficeTaxRateLabel'),
                     'text': text,
                     'icon': 'ui_77_32_46'}))
                    wnd.sr.maintabs.ReloadVisible()
                else:
                    log.LogInfo('Unable to fetch tax rate for customs office in a different system')

            uthread.new(FetchDynamicAttributes, wnd, wnd.sr.data[C_ATTIBUTESTAB], itemID)
        if typeID not in (const.typeFaction,):
            illegalities = cfg.invtypes.Get(typeID).Illegality()
            if illegalities:
                wnd.sr.data[C_LEGALITYTAB]['items'].append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/LegalImplications')}))
            for tmpFactionID, illegality in illegalities.iteritems():
                txt = self.__GetIllegalityString(illegality)
                illegalityText = localization.GetByLabel('UI/InfoWindow/IllegalWithFactionString', factionName=cfg.eveowners.Get(tmpFactionID).name, implications=txt)
                wnd.sr.data[C_LEGALITYTAB]['items'].append(listentry.Get('Text', {'line': 1,
                 'text': illegalityText,
                 'typeID': const.typeFaction,
                 'itemID': tmpFactionID}))

        if (wnd.sr.isFaction or wnd.sr.isCorporation or wnd.sr.isCharacter or wnd.sr.isAlliance) and not util.IsDustCharacter(itemID):
            wnd.sr.dynamicTabs.append((C_STANDINGSTAB, 'Standings', localization.GetByLabel('UI/InfoWindow/TabNames/Standings')))
        if wnd.sr.isAlliance:
            wnd.sr.dynamicTabs.append((C_MEMBERSTAB, 'AllianceMembers', localization.GetByLabel('UI/InfoWindow/TabNames/Members')))
        if typeID == const.typePlasticWrap:
            self.GetAttrItemInfo(itemID, typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'])
        elif wnd.sr.isGenericItem and not moonOrPlanet:
            if itemID is not None and sm.GetService('godma').GetItem(itemID) is not None:
                self.GetAttrItemInfo(itemID, typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'], banAttrs=self.GetSkillAttrs())
            else:
                self.GetAttrTypeInfo(typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'], banAttrs=self.GetSkillAttrs())
            self.GetReqSkillInfo(typeID, wnd.sr.data[C_SKILLSTAB]['items'])
            if wnd.sr.isSkill and len(cfg.GetTypesRequiredBySkill(typeID)) > 0:
                wnd.sr.dynamicTabs.append((C_REQUIREDFORTAB, 'RequiredFor', localization.GetByLabel('UI/InfoWindow/TabNames/RequiredFor')))
        if wnd.sr.isStation and itemID is not None:
            sortServices = []
            stationInfo = sm.GetService('map').GetStation(itemID)
            mask = stationInfo.serviceMask
            for info in sm.GetService('station').GetStationServiceInfo(stationInfo=stationInfo):
                if info.name == 'navyoffices':
                    faction = sm.GetService('faction').GetFaction(stationInfo.ownerID)
                    if faction and faction in [const.factionAmarrEmpire,
                     const.factionCaldariState,
                     const.factionGallenteFederation,
                     const.factionMinmatarRepublic]:
                        sortServices.append((info.label, (info.label, info.iconID)))
                        break
                else:
                    for bit in info.serviceIDs:
                        if mask & bit:
                            sortServices.append((info.label, (info.label, info.iconID)))
                            break

            if sortServices:
                sortServices = uiutil.SortListOfTuples(sortServices)
                for displayName, iconpath in sortServices:
                    wnd.sr.data[C_SERVICESTAB]['items'].append(listentry.Get('IconEntry', {'line': 1,
                     'label': displayName,
                     'selectable': 0,
                     'iconoffset': 4,
                     'icon': iconpath}))

            for locID in [stationInfo.regionID, stationInfo.constellationID, stationInfo.solarSystemID]:
                mapItem = sm.GetService('map').GetItem(locID)
                if mapItem is not None:
                    if mapItem.typeID == const.typeSolarSystem:
                        text = self.GetColorCodedSecurityStringForSystem(mapItem.itemID, mapItem.itemName)
                        text = text.replace('<t>', ' ')
                    else:
                        text = mapItem.itemName
                    wnd.sr.data[C_LOCATIONTAB]['items'].append(listentry.Get('LabelTextTop', {'line': 1,
                     'label': cfg.invtypes.Get(mapItem.typeID).name,
                     'text': text,
                     'typeID': mapItem.typeID,
                     'itemID': mapItem.itemID}))

            stationOwnerID = None
            if eve.session.solarsystemid is not None:
                slimitem = sm.GetService('michelle').GetBallpark().GetInvItem(itemID)
                if slimitem is not None:
                    stationOwnerID = slimitem.ownerID
            if stationOwnerID is None and stationInfo and stationInfo.ownerID:
                stationOwnerID = stationInfo.ownerID
            if stationOwnerID is not None:
                wnd.GetCorpLogo(stationOwnerID, parent=wnd.sr.subinfolinkcontainer)
                wnd.sr.subinfolinkcontainer.height = 64
            wnd.sr.data['buttons'] = [(localization.GetByLabel('UI/Inflight/SetDestination'),
              self.SetDestination,
              (itemID,),
              81)]
        if wnd.sr.isAbstract:
            if wnd.sr.abstractinfo is not None:
                if wnd.sr.isRank:
                    characterRanks = sm.StartService('facwar').GetCharacterRankOverview(session.charid)
                    characterRanks = [ each for each in characterRanks if each.factionID == wnd.sr.abstractinfo.warFactionID ]
                    for x in range(9, -1, -1):
                        hilite = False
                        if characterRanks:
                            if characterRanks[0].currentRank == x:
                                hilite = True
                        rank = util.KeyVal(currentRank=x, factionID=wnd.sr.abstractinfo.warFactionID)
                        wnd.sr.data[C_HIERARCHYTAB]['items'].append(self.GetRankEntry(rank, hilite=hilite))

                elif wnd.sr.isCertificate:
                    self.GetReqSkillInfo(None, wnd.sr.data[C_SKILLSTAB]['items'], sm.StartService('certificates').GetParentSkills(wnd.sr.abstractinfo.certificateID), True)
                    self.GetReqCertInfo(None, wnd.sr.data[C_CERTIFICATETAB]['items'], sm.StartService('certificates').GetParentCertificates(wnd.sr.abstractinfo.certificateID))
                    if not len(wnd.sr.data[C_SKILLSTAB]['items']):
                        wnd.sr.data[C_SKILLSTAB]['items'].append(listentry.Get('Text', {'line': 0,
                         'text': localization.GetByLabel('UI/Certificates/NoSkillRequirements')}))
                    if not len(wnd.sr.data[C_CERTIFICATETAB]['items']):
                        wnd.sr.data[C_CERTIFICATETAB]['items'].append(listentry.Get('Text', {'line': 0,
                         'text': localization.GetByLabel('UI/Certificates/NoCertificateRequirements')}))
                    self.GetRecommendedFor(wnd.sr.abstractinfo.certificateID, wnd.sr.data[C_CERTRECOMMENDEDFORTAB]['items'])
                elif wnd.sr.isSchematic:
                    self.GetSchematicTypeScrollList(wnd.sr.abstractinfo.schematicID, wnd.sr.data[C_PRODUCTIONINFO]['items'])
                    self.GetSchematicAttributes(wnd.sr.abstractinfo.schematicID, wnd.sr.abstractinfo.cycleTime, wnd.sr.data[C_ATTIBUTESTAB]['items'])
        if wnd.sr.isPin:
            banAttrs = self.GetSkillAttrs()
            if cfg.invtypes.Get(typeID).groupID == const.groupExtractorPins:
                banAttrs.extend([const.attributePinCycleTime, const.attributePinExtractionQuantity])
            if itemID is not None and sm.GetService('godma').GetItem(itemID) is not None:
                self.GetAttrItemInfo(itemID, typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'], banAttrs=banAttrs)
            else:
                self.GetAttrTypeInfo(typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'], banAttrs=banAttrs)
            self.GetReqSkillInfo(typeID, wnd.sr.data[C_SKILLSTAB]['items'])
            if cfg.invtypes.Get(typeID).groupID == const.groupProcessPins:
                wnd.sr.dynamicTabs.append((C_SCHEMATICSTAB, 'ProcessPinSchematics', localization.GetByLabel('UI/InfoWindow/TabNames/Schematics')))
        if wnd.sr.isPICommodity:
            wnd.sr.dynamicTabs.append((C_PRODUCTIONINFO, 'CommodityProductionInfo', localization.GetByLabel('UI/InfoWindow/TabNames/ProductionInfo')))
        if wnd.sr.isPlanet:
            if sm.GetService('machoNet').GetGlobalConfig().get('enableDustLink'):
                if eve.session.solarsystemid is not None:
                    slimitem = sm.GetService('michelle').GetBallpark().GetInvItem(itemID)
                    if slimitem is not None:
                        if slimitem.corpID is not None:
                            wnd.sr.dynamicTabs.append((C_PLANETCONTROLTAB, 'PlanetControlInfo', localization.GetByLabel('UI/InfoWindow/TabNames/PlanetControl')))
        if showAttrs and not wnd.sr.data[C_ATTIBUTESTAB]['items']:
            for a in cfg.dgmattribs:
                try:
                    self.GetInvTypeInfo(typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'], self.FilterZero, [a.attributeID])
                except:
                    sys.exc_clear()

            for e in cfg.dgmeffects:
                try:
                    self.GetEffectTypeInfo(typeID, wnd.sr.data[C_ATTIBUTESTAB]['items'], [e.effectID])
                except:
                    sys.exc_clear()

        if prefs.GetValue('showdogmatab', 0) == 1:
            container = wnd.sr.data[C_DOGMATAB]['items']
            container.append(listentry.Get('Header', {'label': 'Type Attributes'}))
            typeattribs = cfg.dgmtypeattribs.get(typeID, [])
            tattribs = []
            for ta in typeattribs:
                v = ta.value
                a = cfg.dgmattribs.Get(ta.attributeID)
                if v is None:
                    v = a.defaultValue
                tattribs.append([a.attributeID,
                 a.attributeName,
                 v,
                 a.attributeCategory,
                 a.description])

            tattribs.sort(lambda x, y: cmp(x[1], y[1]))
            for ta in tattribs:
                attributeID = ta[0]
                attributeName = ta[1]
                v = ta[2]
                attributeCategory = ta[3]
                description = ta[4]
                if attributeCategory == 7:
                    v = hex(int(v))
                entryData = {'line': 1,
                 'label': attributeName,
                 'text': '%s<br>%s' % (v, description)}
                entry = listentry.Get('LabelTextTop', entryData)
                container.append(entry)

            container.append(listentry.Get('Header', {'label': 'Effects'}))
            teffects = []
            for te in cfg.dgmtypeeffects.get(typeID, []):
                e = cfg.dgmeffects.Get(te.effectID)
                teffects.append([e, e.effectName])

            teffects.sort(lambda x, y: cmp(x[1], y[1]))
            for e, effectName in teffects:
                entryData = {'label': effectName}
                entry = listentry.Get('Subheader', entryData)
                container.append(entry)
                for columnName in e.header:
                    entryData = {'line': 1,
                     'label': columnName,
                     'text': '%s' % getattr(e, columnName)}
                    entry = listentry.Get('LabelTextTop', entryData)
                    container.append(entry)

    def GetInsuranceName(self, fraction):
        fraction = '%.1f' % fraction
        label = {'0.5': 'UI/Insurance/BasicInsurance',
         '0.6': 'UI/Insurance/StandardInsurance',
         '0.7': 'UI/Insurance/BronzeInsurance',
         '0.8': 'UI/Insurance/SilverInsurance',
         '0.9': 'UI/Insurance/GoldInsurance',
         '1.0': 'UI/Insurance/PlatinumInsurance'}.get(fraction, fraction)
        return localization.GetByLabel(label)

    @telemetry.ZONE_METHOD
    def GetBloodlineByTypeID(self, typeID):
        if not hasattr(self, 'bloodlines'):
            bls = {}
            for each in cfg.bloodlines:
                bls[util.LookupConstValue('bloodline%dType' % each.bloodlineID)] = each.bloodlineID

            self.bloodlines = bls
        return cfg.bloodlines.Get(self.bloodlines[typeID])

    def GetGAVFunc(self, itemID, info):
        GAV = None
        if info.itemID is not None:
            GAV = lambda attributeID: getattr(info, cfg.dgmattribs.Get(attributeID).attributeName)
        elif itemID:
            dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
            if dogmaLocation.IsItemLoaded(itemID):
                GAV = lambda attributeID: dogmaLocation.GetAttributeValue(itemID, attributeID)
        if GAV is None:
            GAV = lambda attributeID: getattr(info, cfg.dgmattribs.Get(attributeID).attributeName)
        return GAV

    def GetCertEntry(self, cert):
        certID = cert.certificateID
        level = getattr(cert, 'recommendationLevel', None)
        certInfo = cfg.certificates.Get(certID)
        label, grade, descr = sm.GetService('certificates').GetCertificateLabel(certID)
        entry = {'line': 1,
         'label': label,
         'grade': certInfo.grade,
         'certID': certID,
         'icon': 'ui_79_64_%s' % (certInfo.grade + 1),
         'level': level,
         'hideBar': 1}
        return entry

    def DrillToLocation(self, systemID, constellationID, regionID):
        location = (systemID, constellationID, regionID)
        sm.GetService('sov').GetSovOverview(location)

    def GetAgentScrollGroups(self, agents, scroll):
        dudesToPrime = []
        locationsToPrime = []
        for each in agents:
            dudesToPrime.append(each.agentID)
            if each.stationID:
                locationsToPrime.append(each.stationID)
            locationsToPrime.append(each.solarsystemID)

        cfg.eveowners.Prime(dudesToPrime)
        cfg.evelocations.Prime(locationsToPrime)

        def SortFunc(level, agentID, x, y):
            if x[level] < y[level]:
                return -1
            if x[level] > y[level]:
                return 1
            xname = cfg.eveowners.Get(x[agentID]).name
            yname = cfg.eveowners.Get(y[agentID]).name
            if xname < yname:
                return -1
            if xname > yname:
                return 1
            return 0

        agents.sort(lambda x, y: SortFunc(agents.header.index('level'), agents.header.index('agentID'), x, y))
        allAgents = sm.RemoteSvc('agentMgr').GetAgents().Index('agentID')
        divisions = {}
        for each in agents:
            if allAgents[each[0]].divisionID not in divisions:
                divisions[allAgents[each[0]].divisionID] = 1

        npcDivisions = sm.GetService('agents').GetDivisions()

        def SortDivisions(npcDivisions, x, y):
            x = npcDivisions[x].divisionName.lower()
            y = npcDivisions[y].divisionName.lower()
            if x < y:
                return -1
            elif x > y:
                return 1
            else:
                return 0

        divisions = divisions.keys()
        divisions.sort(lambda x, y, npcDivisions = npcDivisions: SortDivisions(npcDivisions, x, y))
        for divisionID in divisions:
            amt = 0
            for agent in agents:
                if agent.divisionID == divisionID:
                    amt += 1

            label = localization.GetByLabel('UI/InfoWindow/AgentDivisionWithCount', divisionName=npcDivisions[divisionID].divisionName.replace('&', '&amp;'), numAgents=amt)
            data = {'GetSubContent': self.GetCorpAgentListSubContent,
             'label': label,
             'agentdata': (divisionID, agents),
             'id': ('AGENTDIVISIONS', divisionID),
             'tabs': [],
             'state': 'locked',
             'showicon': 'hide',
             'showlen': 0}
            scroll.append(listentry.Get('Group', data))

    def InitVariationBottom(self, wnd):
        btns = [localization.GetByLabel('UI/Compare/CompareButton'),
         self.CompareTypes,
         wnd,
         81,
         uiconst.ID_OK,
         0,
         0]
        btns = uicls.ButtonGroup(btns=[btns], parent=wnd.sr.subcontainer, idx=0)
        wnd.sr.variationbtm = btns
        wnd.sr.variationbtm.state = uiconst.UI_HIDDEN

    def CompareTypes(self, wnd):
        typeWnd = form.TypeCompare.Open()
        typeWnd.AddEntry(wnd.sr.variationTypeDict)

    def GetBaseWarpSpeed(self, typeID, shipinfo = None):
        defaultWSM = 1.0
        defaultBWS = 3.0
        if shipinfo:
            wsm = getattr(shipinfo, 'warpSpeedMultiplier', defaultWSM)
            bws = getattr(shipinfo, 'baseWarpSpeed', defaultBWS)
        else:
            attrTypeInfo = util.IndexedRows(cfg.dgmtypeattribs.get(typeID, []), ('attributeID',))
            wsm = attrTypeInfo.get(const.attributeWarpSpeedMultiplier) or util.KeyVal(value=defaultWSM)
            bws = attrTypeInfo.get(const.attributeBaseWarpSpeed) or util.KeyVal(value=defaultBWS)
            wsm = wsm.value
            bws = bws.value
        return localization.GetByLabel('UI/Fitting/FittingWindow/WarpSpeed', distText=util.FmtDist(max(1.0, bws) * wsm * 3 * const.AU, 2))

    def GetBaseDamageValue(self, typeID):
        bsd = None
        bad = None
        attrTypeInfo = util.IndexedRows(cfg.dgmtypeattribs.get(typeID, []), ('attributeID',))
        vals = []
        for attrID in [const.attributeEmDamage,
         const.attributeThermalDamage,
         const.attributeKineticDamage,
         const.attributeExplosiveDamage]:
            if attrID in attrTypeInfo:
                vals.append(attrTypeInfo[attrID].value)

        if len(vals) == 4:
            bsd = (vals[0] * 1.0 + vals[1] * 0.8 + vals[2] * 0.6 + vals[3] * 0.4, 69)
            bad = (vals[0] * 0.4 + vals[1] * 0.65 + vals[2] * 0.75 + vals[3] * 0.9, 68)
        return (bsd, bad)

    def FormatAsFactoryTime(self, value):
        valueInBlueTimes = long(10000000L * value)
        return util.FmtTimeInterval(valueInBlueTimes, breakAt='min')

    def GetBOMSubContent(self, nodedata, *args):
        scrolllist = []
        if localization.GetByLabel('UI/Common/Skills') in [nodedata.label, nodedata.Get('cleanLabel', None)]:
            skills = []
            for each in nodedata.groupItems:
                skills.append((each[0], (each[2], each[3])))

            if skills:
                skills = uiutil.SortListOfTuples(skills)
                self.GetReqSkillInfo(None, scrolllist, skills)
        else:
            for each in nodedata.groupItems:
                entry = listentry.Get('Item', {'itemID': None,
                 'typeID': each[2],
                 'label': each[1],
                 'getIcon': 1})
                scrolllist.append((each[0], entry))

            scrolllist = uiutil.SortListOfTuples(scrolllist)
            if eve.session.role & service.ROLE_GML == service.ROLE_GML:
                scrolllist.append(listentry.Get('Divider'))
                scrolllist.append(listentry.Get('Button', {'label': 'GML: Create in cargo',
                 'caption': 'Create',
                 'OnClick': self.DoCreateMaterials,
                 'args': (nodedata.Get('commands', None), '', 10)}))
        return scrolllist

    def GetKillsRecentKills(self, num, startIndex):
        shipKills = sm.RemoteSvc('charMgr').GetRecentShipKillsAndLosses(num, startIndex)
        return [ k for k in shipKills if k.finalCharacterID == eve.session.charid ]

    def GetKillsRecentLosses(self, num, startIndex):
        shipKills = sm.RemoteSvc('charMgr').GetRecentShipKillsAndLosses(num, startIndex)
        return [ k for k in shipKills if k.victimCharacterID == eve.session.charid ]

    def FindInContracts(self, typeID):
        sm.GetService('contracts').FindRelated(typeID, None, None, None, None, None)

    def ShowMarketDetails(self, typeID):
        uthread.new(sm.StartService('marketutils').ShowMarketDetails, typeID, None)

    def GetAllianceHistorySubContent(self, itemID):
        scrolllist = []
        allianceHistory = sm.RemoteSvc('allianceRegistry').GetEmploymentRecord(itemID)

        def AddToScroll(**data):
            scrolllist.append(listentry.Get('LabelTextTop', data))

        if len(allianceHistory) == 0:
            AddToScroll(line=True, text='', label=localization.GetByLabel('UI/InfoWindow/NoRecordsFound'), typeID=None, itemID=None)
        lastQuit = None
        for allianceRec in allianceHistory[:-1]:
            if allianceRec.allianceID is None:
                lastQuit = allianceRec.startDate
            else:
                alliance = cfg.eveowners.Get(allianceRec.allianceID)
                if allianceRec.startDate:
                    sd = util.FmtDate(allianceRec.startDate, 'ln')
                else:
                    sd = localization.GetByLabel('UI/InfoWindow/UnknownAllianceStartDate')
                if allianceRec.deleted:
                    nameTxt = localization.GetByLabel('UI/InfoWindow/AllianceClosed', allianceName=alliance.name)
                else:
                    nameTxt = alliance.name
                if lastQuit:
                    ed = util.FmtDate(lastQuit, 'ln')
                    text = localization.GetByLabel('UI/InfoWindow/InAllianceFromAndTo', allianceName=nameTxt, fromDate=sd, toDate=ed)
                else:
                    text = localization.GetByLabel('UI/InfoWindow/InAllianceFromAndToThisDay', allianceName=nameTxt, fromDate=sd)
                AddToScroll(line=True, label=localization.GetByLabel('UI/Common/Alliance'), text=text, typeID=alliance.typeID, itemID=allianceRec.allianceID)
                lastQuit = None

        if len(allianceHistory) > 1:
            scrolllist.append(listentry.Get('Divider'))
        if len(allianceHistory) >= 1:
            AddToScroll(line=True, label=localization.GetByLabel('UI/InfoWindow/CorporationFounded'), text=util.FmtDate(allianceHistory[-1].startDate, 'ln'), typeID=None, itemID=None)
        return scrolllist

    def GetWarHistorySubContent(self, itemID):
        regwars = sm.RemoteSvc('warsInfoMgr').GetWarsByOwnerID(itemID)
        facwars = []
        owners = []
        scrolllist = []
        if not util.IsAlliance(itemID) and util.IsCorporation(itemID) and sm.StartService('facwar').GetCorporationWarFactionID(itemID):
            facwars = sm.GetService('facwar').GetFactionWars(itemID).values()
        for wars in (facwars, regwars):
            for war in wars:
                if war.declaredByID not in owners:
                    owners.append(war.declaredByID)
                if war.againstID not in owners:
                    owners.append(war.againstID)

        if len(owners):
            cfg.eveowners.Prime(owners)
        notStartedWars = []
        ongoingWars = []
        finishedWars = []
        for war in regwars:
            currentTime = blue.os.GetWallclockTime()
            warFinished = war.timeFinished
            timeStarted = war.timeStarted if hasattr(war, 'timeStarted') else 0
            if warFinished:
                if currentTime >= warFinished:
                    finishedWars.append(war)
            elif timeStarted:
                if currentTime <= timeStarted:
                    notStartedWars.append(war)
                else:
                    ongoingWars.append(war)

        if len(ongoingWars):
            myLabel = localization.GetByLabel('UI/Corporations/Wars/ActiveWars')
            warGroup = self.GetWarGroup(ongoingWars, myLabel, 'ongoingWars')
            scrolllist.append(warGroup)
        if len(facwars):
            myLabel = localization.GetByLabel('UI/Corporations/Wars/FactionalWars')
            warGroup = self.GetWarGroup(facwars, myLabel, 'factional')
            scrolllist.append(warGroup)
        if len(notStartedWars):
            myLabel = localization.GetByLabel('UI/Corporations/Wars/PendingWars')
            warGroup = self.GetWarGroup(notStartedWars, myLabel, 'notStartedWars')
            scrolllist.append(warGroup)
        if len(finishedWars):
            myLabel = localization.GetByLabel('UI/Corporations/Wars/FinishedWars')
            warGroup = self.GetWarGroup(finishedWars, myLabel, 'finished')
            scrolllist.append(warGroup)
        return scrolllist

    def GetWarGroup(self, list, label, type):
        data = {'GetSubContent': self.GetWarSubContent,
         'label': label,
         'id': ('war', type, label),
         'state': 'locked',
         'BlockOpenWindow': 1,
         'showicon': 'hide',
         'showlen': 1,
         'groupName': type,
         'groupItems': list,
         'updateOnToggle': 0}
        return listentry.Get('Group', data)

    def GetWarSubContent(self, items, *args):
        scrolllist = []
        data = util.KeyVal()
        data.label = ''
        if items.groupName == 'factional':
            for war in items.groupItems:
                data.war = war
                scrolllist.append(listentry.Get('WarEntry', data=data))

        else:
            for war in sorted(items.groupItems, key=lambda x: x.timeDeclared, reverse=True):
                data.war = war
                scrolllist.append(listentry.Get('WarEntry', data=data))

        return scrolllist

    def GetEmploymentHistorySubContent(self, itemID):
        scrolllist = []
        employmentHistory = sm.RemoteSvc('corporationSvc').GetEmploymentRecord(itemID)
        nextDate = None
        for job in employmentHistory:
            corp = cfg.eveowners.Get(job.corporationID)
            if job.deleted:
                nameText = localization.GetByLabel('UI/InfoWindow/CorporationClosed', corpName=corp.name)
            else:
                nameText = corp.name
            date = util.FmtDate(job.startDate, 'ls')
            if nextDate is None:
                text = localization.GetByLabel('UI/InfoWindow/InCorpFromAndToThisDay', corpName=nameText, fromDate=date)
            else:
                text = localization.GetByLabel('UI/InfoWindow/InCorpFromAndTo', corpName=nameText, fromDate=date, toDate=nextDate)
            nextDate = date
            scrolllist.append(listentry.Get('LabelTextTop', {'line': True,
             'label': localization.GetByLabel('UI/Common/Corporation'),
             'text': text,
             'typeID': corp.typeID,
             'itemID': job.corporationID}))

        return scrolllist

    def GetAllianceMembersSubContent(self, itemID):
        members = sm.RemoteSvc('allianceRegistry').GetAllianceMembers(itemID)
        cfg.eveowners.Prime([ m.corporationID for m in members ])
        scrolllist = []
        for m in members:
            corp = cfg.eveowners.Get(m.corporationID)
            data = {'line': True,
             'label': localization.GetByLabel('UI/Common/Corporation'),
             'text': corp.name,
             'typeID': corp.typeID,
             'itemID': m.corporationID}
            scrolllist.append(listentry.Get('LabelTextTop', data))

        return scrolllist

    def GetCorpAgentListSubContent(self, tmp, *args):
        divisionID, agents = tmp.agentdata
        scrolllist = []
        scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/AvailableToYou')}))
        noadd = 1
        for agent in agents:
            if agent.divisionID != divisionID:
                continue
            isLimitedToFacWar = False
            if agent.agentTypeID == const.agentTypeFactionalWarfareAgent and sm.StartService('facwar').GetCorporationWarFactionID(agent.corporationID) != session.warfactionid:
                isLimitedToFacWar = True
            if sm.GetService('standing').CanUseAgent(agent.factionID, agent.corporationID, agent.agentID, agent.level, agent.agentTypeID) and isLimitedToFacWar == False:
                scrolllist.append(listentry.Get('AgentEntry', {'charID': agent.agentID,
                 'defaultDivisionID': agent.divisionID}))
                noadd = 0

        if noadd:
            scrolllist.pop(-1)
        scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/NotAvailableToYou')}))
        noadd = 1
        for agent in agents:
            if agent.divisionID != divisionID:
                continue
            isLimitedToFacWar = False
            if agent.agentTypeID == const.agentTypeFactionalWarfareAgent and sm.StartService('facwar').GetCorporationWarFactionID(agent.corporationID) != session.warfactionid:
                isLimitedToFacWar = True
            if not sm.GetService('standing').CanUseAgent(agent.factionID, agent.corporationID, agent.agentID, agent.level, agent.agentTypeID) or isLimitedToFacWar == True:
                scrolllist.append(listentry.Get('AgentEntry', {'charID': agent.agentID,
                 'defaultDivisionID': agent.divisionID}))
                noadd = 0

        if noadd:
            scrolllist.pop(-1)
        return scrolllist

    def __GetIllegalityString(self, illegality):
        textList = []
        if illegality.standingLoss > 0.0:
            t = localization.GetByLabel('UI/InfoWindow/StandingLoss', standingLoss=illegality.standingLoss)
            textList.append(t)
        if illegality.confiscateMinSec <= 1.0:
            t = localization.GetByLabel('UI/InfoWindow/ConfiscationInSec', confiscateMinSec=max(illegality.confiscateMinSec, 0.0))
            textList.append(t)
        if illegality.fineByValue > 0.0:
            t = localization.GetByLabel('UI/InfoWindow/FineOfEstimatedMarketValue', fine=illegality.fineByValue * 100.0)
            textList.append(t)
        if illegality.attackMinSec <= 1.0:
            t = localization.GetByLabel('UI/InfoWindow/AttackInSec', attackMinSec=max(illegality.attackMinSec, 0.0))
            textList.append(t)
        if len(textList) > 0:
            text = ' / '.join(textList)
        else:
            text = ''
        return text

    def GetInvTypeInfo(self, typeID, scrolllist, filterValue, attrList):
        invTypeInfo = cfg.invtypes.Get(typeID)
        for attrID in attrList:
            attrTypeInfo = cfg.dgmattribs.Get(attrID)
            value = filterValue(getattr(invTypeInfo, attrTypeInfo.attributeName, None))
            if value is None:
                continue
            if not attrTypeInfo.published:
                continue
            if attrID == const.attributeVolume:
                packagedVolume = cfg.GetTypeVolume(typeID, 1)
                if value != packagedVolume:
                    text = localization.GetByLabel('UI/InfoWindow/ItemVolumeWithPackagedVolume', volume=value, packaged=packagedVolume, unit=self.FormatUnit(attrTypeInfo.unitID))
                else:
                    formatedValue = self.FormatValue(value, const.attributeVolume)
                    text = localization.GetByLabel('UI/InfoWindow/ValueAndUnit', value=formatedValue, unit=self.FormatUnit(attrTypeInfo.unitID))
            else:
                formatedValue = localizationUtil.FormatNumeric(value, useGrouping=True)
                text = localization.GetByLabel('UI/InfoWindow/ValueAndUnit', value=formatedValue, unit=self.FormatUnit(attrTypeInfo.unitID))
            scrolllist.append(listentry.Get('LabelTextTop', {'line': 1,
             'label': attrTypeInfo.displayName,
             'text': text,
             'iconID': attrTypeInfo.iconID}))

    def GetMetaParentTypeID(self, typeID):
        parentTypeID = None
        if typeID in cfg.invmetatypesByParent:
            parentTypeID = typeID
        elif typeID in cfg.invmetatypes:
            parentTypeID = cfg.invmetatypes.Get(typeID).parentTypeID
        return parentTypeID

    def GetMetaTypeInfo(self, typeID, scrolllist, wnd):
        invTypeInfo = self.GetMetaTypesFromTypeID(typeID)
        wnd.sr.variationTypeDict = []
        sortByGroupID = {}
        sortHeaders = []
        if invTypeInfo:
            for each in invTypeInfo:
                if each.metaGroupID not in sortByGroupID:
                    sortByGroupID[each.metaGroupID] = []
                    sortHeaders.append((each.metaGroupID, each.metaGroupID))
                invType = cfg.invtypes.Get(each.typeID)
                sortByGroupID[each.metaGroupID].append((invType.name, (each, invType)))

        sortHeaders = uiutil.SortListOfTuples(sortHeaders)
        for i, metaGroupID in enumerate(sortHeaders):
            sub = sortByGroupID[metaGroupID]
            sub = uiutil.SortListOfTuples(sub)
            if i > 0:
                scrolllist.append(listentry.Get('Divider'))
            scrolllist.append(listentry.Get('Header', {'line': metaGroupID,
             'label': cfg.invmetagroups.Get(metaGroupID).name,
             'text': None}))
            for metaType, invType in sub:
                wnd.sr.variationTypeDict.append(invType)
                scrolllist.append(listentry.Get('Item', {'GetMenu': None,
                 'itemID': None,
                 'typeID': invType.typeID,
                 'label': invType.typeName,
                 'getIcon': 1}))

    def GetMetaTypesFromTypeID(self, typeID, groupOnly = 0):
        tmp = None
        if typeID in cfg.invmetatypesByParent:
            tmp = copy.deepcopy(cfg.invmetatypesByParent[typeID])
        grp = cfg.invmetagroups.Get(1)
        if not tmp:
            if typeID in cfg.invmetatypes:
                tmp = cfg.invmetatypes.Get(typeID)
            if tmp:
                grp = cfg.invmetagroups.Get(tmp.metaGroupID)
                tmp = self.GetMetaTypesFromTypeID(tmp.parentTypeID)
        else:
            metaGroupID = tmp[0].metaGroupID
            if metaGroupID != 14:
                metaGroupID = 1
            else:
                grp = cfg.invmetagroups.Get(14)
            tmp.append(blue.DBRow(tmp.header, [tmp[0].parentTypeID, tmp[0].parentTypeID, metaGroupID]))
        if groupOnly:
            return grp
        else:
            return tmp

    def GetAttrItemInfo(self, itemID, typeID, scrolllist, attrList = None, banAttrs = []):
        info = sm.GetService('godma').GetItem(itemID)
        if info:
            attrDict = self.GetAttrDict(typeID)
            for each in info.displayAttributes:
                attrDict[each.attributeID] = each.value

            typeVolume = cfg.GetTypeVolume(typeID, 1)
            attrVolume = attrDict.get(const.attributeVolume, None)
            if isinstance(attrVolume, (int, float, long)) and attrVolume != typeVolume:
                fmtUnit = self.FormatUnit(cfg.dgmattribs.Get(const.attributeVolume).unitID)
                attrDict[const.attributeVolume] = localization.GetByLabel('UI/InfoWindow/ItemVolumeWithPackagedVolume', volume=attrDict[const.attributeVolume], packaged=typeVolume, unit=self.FormatUnit(const.unitVolume))
            return self.GetAttrInfo(attrDict, scrolllist, attrList, banAttrs=banAttrs, itemID=itemID)
        else:
            dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
            if dogmaLocation.IsItemLoaded(itemID):
                attrDict = self.GetAttrDict(typeID)
                attrDict.update(dogmaLocation.GetDisplayAttributes(itemID, attrDict.keys()))
                return self.GetAttrInfo(attrDict, scrolllist, attrList, banAttrs=banAttrs, itemID=itemID)
            return self.GetAttrTypeInfo(typeID, scrolllist, attrList, banAttrs=banAttrs, itemID=itemID)

    def GetAttrTypeInfo(self, typeID, scrolllist, attrList = None, attrValues = None, banAttrs = [], itemID = None):
        return self.GetAttrInfo(self.GetAttrDict(typeID), scrolllist, attrList, attrValues, banAttrs, itemID=itemID, typeID=typeID)

    def GetAttrInfo(self, attrdict, scrolllist, attrList = None, attrValues = None, banAttrs = [], itemID = None, typeID = None):
        if attrValues:
            for each in attrValues.displayAttributes:
                attrdict[each.attributeID] = each.value

        attrList = attrList or attrdict.keys()
        aggregateAttributes = defaultdict(list)
        for attrID in tuple(attrList):
            if attrID in const.canFitShipGroups or attrID in const.canFitShipTypes:
                dgmType = cfg.dgmattribs.Get(attrID)
                value = self.GetFormatAndValue(dgmType, attrdict[attrID])
                aggregateAttributes['canFitShip'].append(value)
                attrList.remove(attrID)

        def GetAttr(attrID):
            if attrID not in banAttrs and attrID in attrdict:
                self.GetAttr(attrID, attrdict[attrID], scrolllist, itemID, typeID=typeID)

        order = self.GetAttributeOrder()
        for attrID_ in order:
            if attrID_ in attrList:
                GetAttr(attrID_)

        for attrID_ in attrList:
            if attrID_ not in order:
                GetAttr(attrID_)

        attributeValues = aggregateAttributes.get('canFitShip')
        if attributeValues is not None:
            attrID = const.canFitShipTypes[0]
            attributeInfo = cfg.dgmattribs.Get(attrID)
            attributeValues = localizationUtil.Sort(attributeValues)
            listItem = listentry.Get('LabelMultilineTextTop', {'attributeID': attrID,
             'OnClick': (self.OnAttributeClick, attrID, itemID),
             'line': 1,
             'label': attributeInfo.displayName,
             'text': '<br>'.join(attributeValues),
             'iconID': attributeInfo.iconID,
             'typeID': None,
             'itemID': itemID})
            scrolllist.append(listItem)

    def GetAttrDict(self, typeID):
        ret = {}
        for each in cfg.dgmtypeattribs.get(typeID, []):
            attribute = cfg.dgmattribs.Get(each.attributeID)
            if attribute.attributeCategory == 9:
                ret[each.attributeID] = getattr(cfg.invtypes.Get(typeID), attribute.attributeName)
            else:
                ret[each.attributeID] = each.value

        invType = cfg.invtypes.Get(typeID)
        if not ret.has_key(const.attributeCapacity) and invType.capacity:
            ret[const.attributeCapacity] = invType.capacity
        if invType.categoryID == const.categoryAccessories:
            if const.attributeVolume not in ret and invType.volume:
                formatedValue = localizationUtil.FormatNumeric(invType.volume, useGrouping=True)
                value = localization.GetByLabel('UI/InfoWindow/ValueAndUnit', value=formatedValue, unit=self.FormatUnit(const.unitVolume))
                ret[const.attributeVolume] = value
        if invType.categoryID in (const.categoryCharge, const.categoryModule):
            if const.attributeVolume not in ret and invType.volume:
                value = localization.GetByLabel('UI/InfoWindow/ItemVolume', volume=invType.volume, unit=self.FormatUnit(const.unitVolume))
                ret[const.attributeVolume] = value
        if invType.categoryID in (const.categoryPlanetaryInteraction,) and invType.groupID not in (const.groupPlanetaryLinks,):
            if not ret.has_key(const.attributeVolume) and invType.volume:
                value = localization.GetByLabel('UI/InfoWindow/ItemVolume', volume=invType.volume, unit=self.FormatUnit(const.unitVolume))
                packagedVolume = cfg.GetTypeVolume(typeID, 1)
                if invType.volume != packagedVolume:
                    value = localization.GetByLabel('UI/InfoWindow/ItemVolumeWithPackagedVolume', volume=invType.volume, packaged=packagedVolume, unit=self.FormatUnit(const.unitVolume))
                ret[const.attributeVolume] = value
        if invType.categoryID == const.categoryShip:
            if not ret.has_key(const.attributeMass) and invType.mass:
                ret[const.attributeMass] = invType.mass
            if not ret.has_key(const.attributeVolume) and invType.volume:
                value = localization.GetByLabel('UI/InfoWindow/ItemVolume', volume=invType.volume, unit=self.FormatUnit(const.unitVolume))
                packagedVolume = cfg.GetTypeVolume(typeID, 1)
                if invType.volume != packagedVolume:
                    unit = self.FormatUnit(const.unitVolume)
                    value = localization.GetByLabel('UI/InfoWindow/ItemVolumeWithPackagedVolume', volume=invType.volume, packaged=packagedVolume, unit=unit)
                ret[const.attributeVolume] = value
        attrInfo = sm.GetService('godma').GetType(typeID)
        for each in attrInfo.displayAttributes:
            ret[each.attributeID] = each.value

        return ret

    def GetFormatAndValue(self, attributeType, value):
        attrUnit = self.FormatUnit(attributeType.unitID)
        if attributeType.unitID == const.unitGroupID:
            value = cfg.invgroups.Get(value).name
        elif attributeType.unitID == const.unitTypeID:
            value = cfg.invtypes.Get(value).name
        elif attributeType.unitID == const.unitSizeclass:
            sizeDict = {1: localization.GetByLabel('UI/InfoWindow/SmallSize'),
             2: localization.GetByLabel('UI/InfoWindow/MediumSize'),
             3: localization.GetByLabel('UI/InfoWindow/LargeSize'),
             4: localization.GetByLabel('UI/InfoWindow/XLargeSize')}
            value = sizeDict.get(int(value))
        elif attributeType.unitID == const.unitAttributeID:
            attrInfo2 = cfg.dgmattribs.Get(value)
            value = attrInfo2.displayName or attrInfo2.attributeName
        elif attributeType.attributeID == const.attributeVolume:
            value = value
        elif attributeType.unitID == const.unitLevel:
            value = localization.GetByLabel('UI/InfoWindow/TechLevelX', numLevel=util.FmtAmt(value))
        elif attributeType.unitID == const.unitBoolean:
            if int(value) == 1:
                value = localization.GetByLabel('UI/Common/True')
            else:
                value = localization.GetByLabel('UI/Common/False')
        elif attributeType.unitID == const.unitSlot:
            value = localization.GetByLabel('UI/InfoWindow/SlotX', slotNum=util.FmtAmt(value))
        elif attributeType.unitID == const.unitBonus:
            if value >= 0:
                value = '%s%s' % (attrUnit, value)
        elif attributeType.unitID == const.unitGender:
            genderDict = {1: localization.GetByLabel('UI/Common/Gender/Male'),
             2: localization.GetByLabel('UI/Common/Gender/Unisex'),
             3: localization.GetByLabel('UI/Common/Gender/Female')}
            value = genderDict.get(int(value))
        else:
            value = localization.GetByLabel('UI/InfoWindow/ValueAndUnit', value=self.FormatValue(value, attributeType.unitID), unit=attrUnit)
        return value

    def GetAttr(self, id_, value, scrolllist, itemID = None, typeID = None):
        type_ = cfg.dgmattribs.Get(id_)
        if not type_.published or not value:
            return
        iconID = type_.iconID
        infoTypeID = None
        if not iconID:
            if type_.unitID == const.unitTypeID:
                iconID = cfg.invtypes.Get(value).iconID
                infoTypeID = value
            if type_.unitID == const.unitGroupID:
                iconID = cfg.invgroups.Get(value).iconID
            if type_.unitID == const.unitAttributeID:
                attrInfo2 = cfg.dgmattribs.Get(value)
                iconID = attrInfo2.iconID
        value = self.GetFormatAndValue(type_, value)
        if itemID and infoTypeID and typeID != infoTypeID:
            itemID = None
        listItem = listentry.Get('LabelTextTop', {'attributeID': id_,
         'OnClick': (self.OnAttributeClick, id_, itemID),
         'line': 1,
         'label': type_.displayName,
         'text': value,
         'iconID': iconID,
         'typeID': infoTypeID,
         'itemID': itemID})
        scrolllist.append(listItem)

    def OnAttributeClick(self, id_, itemID):
        ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        if not ctrl:
            return
        if not shift and itemID is not None and (itemID >= const.minPlayerItem or util.IsCharacter(itemID)):
            sm.GetService('godma').LogAttribute(itemID, id_)
        if eve.session.role & service.ROLE_CONTENT == service.ROLE_CONTENT and ctrl and shift:
            self.GetUrlAdamDogmaAttribute(id_)

    def GetUrlAdamDogmaAttribute(self, id_):
        uthread.new(self.ClickURL, 'http://adam:50001/gd/type.py?action=DogmaModifyAttributeForm&attributeID=%s' % id_)

    def ClickURL(self, url, *args):
        blue.os.ShellExecute(url)

    def GetRequiredSkills(self, typeID):
        lst = []
        attrDict = self.GetAttrDict(typeID)
        for i in xrange(1, 7):
            skillID = attrDict.get(getattr(const, 'attributeRequiredSkill%s' % i), None)
            if skillID is not None and getattr(const, 'attributeRequiredSkill%sLevel' % i) in attrDict:
                skillID = int(skillID)
                lvl = attrDict.get(getattr(const, 'attributeRequiredSkill%sLevel' % i), 1.0)
                if lvl:
                    lst.append((skillID, lvl))

        return lst

    def GetRawTrainingTimeForSkillLevel(self, skillID, skillLevel):
        skillTimeConstant = sm.GetService('godma').GetTypeAttribute(skillID, const.attributeSkillTimeConstant)
        primaryAttributeID = sm.GetService('godma').GetTypeAttribute(skillID, const.attributePrimaryAttribute)
        secondaryAttributeID = sm.GetService('godma').GetTypeAttribute(skillID, const.attributeSecondaryAttribute)

        def GetSkillPointsFromSkillObject(skillObject):
            if skillObject is None:
                return 0
            else:
                skillTrainingEnd, spHi, spm = skillObject.skillTrainingEnd, skillObject.spHi, skillObject.spm
                if skillTrainingEnd is not None and spHi is not None:
                    secs = (skillTrainingEnd - blue.os.GetWallclockTime()) / SEC
                    return min(spHi - secs / 60.0 * spm, spHi)
                return skillObject.skillPoints

        charItem = sm.GetService('godma').GetItem(session.charid)
        attrDict = {}
        for each in charItem.displayAttributes:
            attrDict[each.attributeID] = each.value

        playerPrimaryAttribute = attrDict[primaryAttributeID]
        playerSecondaryAttribute = attrDict[secondaryAttributeID]
        rawSkillPointsToTrain = skillUtil.GetSPForLevelRaw(skillTimeConstant, skillLevel)
        trainingRate = skillUtil.GetSkillPointsPerMinute(playerPrimaryAttribute, playerSecondaryAttribute)
        existingSP = 0
        priorLevel = skillLevel - 1
        if priorLevel >= 0:
            mySkill = sm.StartService('skills').GetMySkillsFromTypeID(skillID)
            mySkillLevel = 0
            if mySkill is not None:
                mySkillLevel = mySkill.skillLevel
            if priorLevel == mySkillLevel:
                playerCurrentSP = 0
                skillObj = sm.StartService('skills').GetMyGodmaItem().skills.get(skillID, None)
                if skillObj is not None:
                    playerCurrentSP = GetSkillPointsFromSkillObject(skillObj)
                else:
                    playerCurrentSP = 0
                existingSP = playerCurrentSP
            else:
                existingSP = skillUtil.GetSPForLevelRaw(skillTimeConstant, priorLevel)
        skillPointsToTrain = rawSkillPointsToTrain - existingSP
        trainingTimeInMinutes = float(skillPointsToTrain) / float(trainingRate)
        return trainingTimeInMinutes * MIN

    def GetSkillToolTip(self, skillID, level):
        if session.charid is None:
            return
        mySkill = sm.GetService('skills').GetMySkillsFromTypeID(skillID)
        mySkillLevel = 0
        if mySkill is not None:
            mySkillLevel = mySkill.skillLevel
        tooltipTextList = []
        for i in xrange(int(mySkillLevel) + 1, int(level) + 1):
            timeLeft = self.GetRawTrainingTimeForSkillLevel(skillID, i)
            tooltipTextList.append(localization.GetByLabel('UI/SkillQueue/Skills/SkillLevelAndTrainingTime', skillLevel=i, timeLeft=long(timeLeft)))

        tooltipText = '<br>'.join(tooltipTextList)
        return tooltipText

    def GetSkillAttrs(self):
        skillAttrs = [ getattr(const, 'attributeRequiredSkill%s' % i, None) for i in xrange(1, 7) if hasattr(const, 'attributeRequiredSkill%s' % i) ] + [ getattr(const, 'attributeRequiredSkill%sLevel' % i, None) for i in xrange(1, 7) if hasattr(const, 'attributeRequiredSkill%sLevel' % i) ]
        return skillAttrs

    def GetReqCertInfo(self, typeID, scrolllist, reqCertificates = []):
        if session.charid is None:
            return
        for certificateID in reqCertificates:
            label, grade, desc = sm.GetService('certificates').GetCertificateLabel(certificateID)
            haveCert = sm.StartService('certificates').HaveCertificate(certificateID)
            inProgress = None
            hasPrereqs = None
            certInfo = cfg.certificates.Get(certificateID)
            if not haveCert:
                hasPrereqs = sm.StartService('certificates').HasPrerequisites(certificateID)
                if not hasPrereqs:
                    inProgress = sm.StartService('certificates').IsInProgress(certificateID)
            entryLabel = localization.GetByLabel('UI/InfoWindow/CertificateNameWithGrade', certificateName=label, certificateGrade=grade)
            entry = {'line': 1,
             'text': entryLabel,
             'indent': 1,
             'haveCert': haveCert,
             'inProgress': inProgress,
             'hasPrereqs': hasPrereqs,
             'certID': certificateID,
             'grade': certInfo.grade}
            scrolllist.append(listentry.Get('CertTreeEntry', entry))

    def GetSchematicAttributes(self, schematicID, cycleTime, scrolllist):
        time = util.FmtTimeInterval(cycleTime * SEC, 'minute')
        scrolllist.append(listentry.Get('LabelTextTop', {'line': 1,
         'label': localization.GetByLabel('UI/PI/Common/CycleTime'),
         'text': time,
         'iconID': 1392}))
        scrolllist.append(listentry.Get('Header', data=util.KeyVal(label=localization.GetByLabel('UI/InfoWindow/CanBeUsedOnPinTypes'))))
        pinTypes = []
        for pinRow in cfg.schematicspinmap.get(schematicID, []):
            typeName = cfg.invtypes.Get(pinRow.pinTypeID).typeName
            data = util.KeyVal(label=typeName, typeID=pinRow.pinTypeID, itemID=None, getIcon=1)
            pinTypes.append((data.label, listentry.Get('Item', data=data)))

        pinTypes = uiutil.SortListOfTuples(pinTypes)
        scrolllist += pinTypes

    def GetSchematicTypeScrollList(self, schematicID, scrolllist):
        inputs = []
        outputs = []
        for typeInfo in cfg.schematicstypemap.get(schematicID, []):
            typeName = cfg.invtypes.Get(typeInfo.typeID).typeName
            label = localization.GetByLabel('UI/InfoWindow/TypeNameWithNumUnits', invType=typeInfo.typeID, qty=typeInfo.quantity)
            data = util.KeyVal(label=label, typeID=typeInfo.typeID, itemID=None, getIcon=1, quantity=typeInfo.quantity)
            if typeInfo.isInput:
                inputs.append(data)
            else:
                outputs.append(data)

        scrolllist.append(listentry.Get('Header', data=util.KeyVal(label=localization.GetByLabel('UI/PI/Common/SchematicInput'))))
        for data in inputs:
            scrolllist.append(listentry.Get('Item', data=data))

        scrolllist.append(listentry.Get('Header', data=util.KeyVal(label=localization.GetByLabel('UI/PI/Common/Output'))))
        for data in outputs:
            scrolllist.append(listentry.Get('Item', data=data))

    def GetReqSkillInfo(self, typeID, scrolllist, reqSkills = [], showHeaders = False):
        i = 1
        commands = []
        skills = None
        if typeID is not None:
            skills = self.GetRequiredSkills(typeID)
        if reqSkills:
            skills = reqSkills
        if skills is None:
            return
        for skillID, lvl in skills:
            if showHeaders or typeID is not None:
                attr = cfg.dgmattribs.Get(getattr(const, 'attributeRequiredSkill%s' % i))
                scrolllist.append(listentry.Get('Header', {'line': 1,
                 'label': attr.displayName}))
            ret = self.DrawSkillTree(skillID, lvl, scrolllist, 0)
            scrolllist.append(listentry.Get('Divider'))
            commands = commands + ret
            i += 1

        cmds = {}
        for typeID, level in commands:
            typeID, level = int(typeID), int(level)
            currentLevel = cmds.get(typeID, 0)
            cmds[typeID] = max(currentLevel, level)

        if i > 1 and eve.session.role & service.ROLE_GMH == service.ROLE_GMH:
            scrolllist.append(listentry.Get('Button', {'label': 'GMH: Give me these skills',
             'caption': 'Give',
             'OnClick': self.DoGiveSkills,
             'args': (cmds,)}))
            scrolllist.append(listentry.Get('Divider'))

    def GetRecommendedFor(self, certID, scrolllist):
        recommendedFor = sm.StartService('certificates').GetCertificateRecommendationsFromCertificateID(certID)
        recommendedGroups = {}
        for each in recommendedFor:
            typeID = each.shipTypeID
            groupID = cfg.invtypes.Get(typeID).groupID
            current = recommendedGroups.get(groupID, [])
            current.append(typeID)
            recommendedGroups[groupID] = current

        scrolllist2 = []
        for groupID, value in recommendedGroups.iteritems():
            label = cfg.invgroups.Get(groupID).name
            data = {'GetSubContent': self.GetEntries,
             'label': label,
             'groupItems': value,
             'id': ('cert_shipGroups', groupID),
             'sublevel': 0,
             'showlen': 1,
             'showicon': 'hide',
             'state': 'locked'}
            scrolllist2.append((label, listentry.Get('Group', data)))

        scrolllist2 = uiutil.SortListOfTuples(scrolllist2)
        scrolllist += scrolllist2

    def GetEntries(self, data, *args):
        scrolllist = []
        for each in data.groupItems:
            entry = self.CreateEntry(each)
            scrolllist.append(entry)

        return scrolllist

    def CreateEntry(self, typeID, *args):
        entry = util.KeyVal()
        entry.line = 1
        entry.label = cfg.invtypes.Get(typeID).name
        entry.sublevel = 1
        entry.showinfo = 1
        entry.typeID = typeID
        return listentry.Get('Generic', data=entry)

    def DoGiveSkills(self, cmds, button):
        cntFrom = 1
        cntTo = len(cmds) + 1
        sm.GetService('loading').ProgressWnd('GM Skill Gift', '', cntFrom, cntTo)
        for typeID, level in cmds.iteritems():
            invType = cfg.invtypes.Get(typeID)
            cntFrom = cntFrom + 1
            sm.GetService('loading').ProgressWnd('GM Skill Gift', 'Training of the skill %s to level %d has been completed' % (invType.typeName, level), cntFrom, cntTo)
            sm.RemoteSvc('slash').SlashCmd('/giveskill me %s %s' % (typeID, level))

        sm.GetService('loading').ProgressWnd('Done', '', cntTo, cntTo)

    def DoCreateMaterials(self, commands, header, qty, button):
        runs = {'qty': qty}
        hdr = 'GML: Create in cargo'
        if header:
            hdr = header
        if qty > 1:
            runs = uix.QtyPopup(100000, 1, qty, None, hdr)
        if runs is not None and runs.has_key('qty') and runs['qty'] > 0:
            cntFrom = 1
            cntTo = len(commands) + 1
            sm.GetService('loading').ProgressWnd(localization.GetByLabel('UI/Common/GiveLoot'), '', cntFrom, cntTo)
            for typeID, quantity in commands:
                invType = cfg.invtypes.Get(typeID)
                cntFrom = cntFrom + 1
                actualQty = quantity * runs['qty']
                qtyText = '%(quantity)s items(s) of %(typename)s' % {'quantity': quantity * runs['qty'],
                 'typename': invType.typeName}
                sm.GetService('loading').ProgressWnd(localization.GetByLabel('UI/Common/GiveLoot'), qtyText, cntFrom, cntTo)
                if actualQty > 0:
                    if session.role & service.ROLE_WORLDMOD:
                        sm.RemoteSvc('slash').SlashCmd('/create %s %d' % (typeID, actualQty))
                    elif session.role & service.ROLE_GML:
                        sm.RemoteSvc('slash').SlashCmd('/load me %s %d' % (typeID, actualQty))

            sm.GetService('loading').ProgressWnd('Done', '', cntTo, cntTo)

    def DrawSkillTree(self, typeID, lvl, scrolllist, indent, done = None, firstID = None):
        thisSet = [(typeID, lvl)]
        if done is None:
            done = []
        if firstID is None:
            firstID = typeID
        skills = None
        if session.charid:
            godmaCharItem = sm.GetService('godma').GetItem(session.charid)
            if hasattr(godmaCharItem, 'skills'):
                skills = godmaCharItem.skills
        if int(lvl) <= 0:
            romanNumber = '-'
        else:
            romanNumber = util.IntToRoman(min(5, int(lvl)))
        text = localization.GetByLabel('UI/InfoWindow/SkillAndLevelInRoman', skill=typeID, levelInRoman=romanNumber)
        data = {'line': 1,
         'text': text,
         'skills': skills,
         'typeID': typeID,
         'lvl': lvl,
         'indent': indent + 1,
         'hint': self.GetSkillToolTip(typeID, lvl)}
        scrolllist.append(listentry.Get('SkillTreeEntry', data))
        done.append(typeID)
        current = typeID
        for typeID, lvl in self.GetRequiredSkills(typeID):
            if typeID == current:
                log.LogWarn('Here I have skill which has it self as required skill... skillTypeID is ' + str(typeID))
                continue
            newSet = self.DrawSkillTree(typeID, lvl, scrolllist, indent + 1, done, firstID)
            thisSet = thisSet + newSet

        return thisSet

    def GetEffectTypeInfo(self, typeID, scrolllist, effList):
        thisTypeEffects = cfg.dgmtypeeffects.get(typeID, [])
        for effectID in effList:
            itemDgmEffect = self.TypeHasEffect(effectID, thisTypeEffects)
            if not itemDgmEffect:
                continue
            effTypeInfo = cfg.dgmeffects.Get(effectID)
            if effTypeInfo.published:
                scrolllist.append(listentry.Get('LabelTextTop', {'line': 1,
                 'label': effTypeInfo.displayName,
                 'text': effTypeInfo.description,
                 'iconID': effTypeInfo.iconID}))

    def FilterZero(self, value):
        if value == 0:
            return None
        return value

    def FormatUnit(self, unitID, fmt = 'd'):
        if unitID == const.unitTime:
            return ''
        if unitID == const.unitLength:
            return ''
        if unitID in cfg.dgmunits and fmt == 'd':
            return cfg.dgmunits.Get(unitID).displayName
        return ''

    def FormatValue(self, value, unitID = None):
        if value is None:
            return
        if unitID == const.unitTime:
            return util.FmtDate(long(value * 10000.0), 'll')
        if unitID == const.unitMilliseconds:
            return '%.2f' % (value / 1000.0)
        if unitID in (const.unitInverseAbsolutePercent, const.unitInversedModifierPercent):
            value = 100 - value * 100
        if unitID == const.unitModifierPercent:
            value = abs(value * 100 - 100) * [1, -1][value < 1.0]
        if unitID == const.unitLength:
            return util.FmtDist2(value)
        if unitID == const.unitAbsolutePercent:
            value = value * 100
        if unitID == const.unitHour:
            return util.FmtDate(long(value * const.HOUR), 'll')
        if unitID == const.unitMoney:
            return util.FmtAmt(value)
        if type(value) is str:
            value = eval(value)
        if type(value) is not str and value - int(value) == 0:
            return util.FmtAmt(value)
        if unitID == const.unitAttributePoints:
            return round(value, 1)
        if unitID == const.unitMaxVelocity:
            return localizationUtil.FormatNumeric(value, decimalPlaces=2, useGrouping=True)
        if unitID in (const.unitHitpoints, const.unitVolume):
            if value < 1:
                significantDigits = 2 if unitID == const.unitHitpoints else 3
                decimalPlaces = int(-math.ceil(math.log10(value)) + significantDigits)
            else:
                decimalPlaces = 2
            return localizationUtil.FormatNumeric(value, decimalPlaces=decimalPlaces, useGrouping=True)
        return value

    def TypeHasEffect(self, effectID, itemEffectTypeInfo = None, typeID = None):
        if itemEffectTypeInfo is None:
            itemEffectTypeInfo = cfg.dgmtypeeffects.get(typeID, [])
        for itemDgmEffect in itemEffectTypeInfo:
            if itemDgmEffect.effectID == effectID:
                return itemDgmEffect

        return 0

    def GetStandingsHistorySubContent(self, itemID):
        return sm.GetService('standing').GetStandingRelationshipEntries(itemID)

    def GetRequiredForSubContent(self, typeID):
        scrolllist = []
        if typeID is None:
            return scrolllist
        charSkill = sm.GetService('skills').HasSkill(typeID)
        requiredFor = cfg.GetTypesRequiredBySkill(typeID)
        levels = requiredFor.keys().sort()
        for level in requiredFor.keys():
            level = int(level)
            if not charSkill or charSkill.skillLevel >= level:
                iconID = 'ui_50_64_14'
            else:
                iconID = 'ui_50_64_11'
            data = {'label': localization.GetByLabel('UI/InfoWindow/SkillLevel', romanNumeral=uiutil.IntToRoman(level)),
             'id': ('skillGroups_level', level),
             'iconID': iconID}
            scrolllist.append(listentry.Get('Header', data=data))
            for entry in self.GetRequiredForLevelSubContent(typeID, level):
                scrolllist.append(entry)

        return scrolllist

    def GetRequiredForLevelSubContent(self, typeID, skillLevel):
        scrolllist = []
        requiredFor = cfg.GetTypesRequiredBySkill(typeID)[skillLevel]
        marketGroups = sm.GetService('marketutils').GetMarketGroups()[None]
        for marketGroupID in requiredFor:
            marketGroup = cfg.GetMarketGroup(marketGroupID)
            data = {'GetSubContent': self.GetRequiredForLevelGroupSubContent,
             'label': marketGroup.marketGroupName,
             'skillLevel': int(skillLevel),
             'sublevel': 0,
             'showlen': False,
             'typeID': typeID,
             'marketGroupID': marketGroupID,
             'id': ('skillGroups_group', marketGroupID),
             'state': 'locked',
             'iconID': marketGroup.iconID}
            scrolllist.append(listentry.Get('Group', data=data))

        return scrolllist

    def GetRequiredForLevelGroupSubContent(self, data, *args):
        scrolllist = []
        skillTypeID = data['typeID']
        skillLevel = data['skillLevel']
        skillMarketGroup = data['marketGroupID']
        requiredFor = cfg.GetTypesRequiredBySkill(skillTypeID)[skillLevel][skillMarketGroup]
        if const.metaGroupUnused in requiredFor:
            for typeID in requiredFor[const.metaGroupUnused]:
                typeRec = cfg.invtypes.Get(typeID)
                data = {'label': typeRec.name,
                 'sublevel': 1,
                 'typeID': typeID,
                 'showinfo': True,
                 'getIcon': True}
                scrolllist.append(listentry.Get('Item', data))

        for metaLevel in requiredFor.keys():
            if metaLevel == const.metaGroupUnused:
                continue
            data = {'GetSubContent': self.GetRequiredForLevelGroupMetaSubContent,
             'id': ('skillGroups_Meta', metaLevel),
             'label': cfg.invmetagroups.Get(metaLevel).metaGroupName,
             'groupItems': requiredFor[metaLevel],
             'state': 'locked',
             'sublevel': 1,
             'showicon': uix.GetTechLevelIconID(metaLevel),
             'metaLevel': metaLevel,
             'BlockOpenWindow': True,
             'typeID': skillTypeID,
             'skillLevel': skillLevel,
             'marketGroupID': skillMarketGroup,
             'typeIDs': requiredFor[metaLevel],
             'showlen': False}
            scrolllist.append(listentry.Get('MarketMetaGroupEntry', data))

        return scrolllist

    def GetRequiredForLevelGroupMetaSubContent(self, data):
        skillTypeID = data['typeID']
        skillLevel = data['skillLevel']
        skillMarketGroup = data['marketGroupID']
        metaLevel = data['metaLevel']
        scrolllist = []
        reqFor = cfg.GetTypesRequiredBySkill(skillTypeID)[skillLevel][skillMarketGroup][metaLevel]
        for typeID in reqFor:
            typeRec = cfg.invtypes.Get(typeID)
            data = {'label': typeRec.name,
             'sublevel': 3,
             'typeID': typeID,
             'showinfo': True,
             'getIcon': True}
            scrolllist.append(listentry.Get('Item', data))

        return scrolllist

    def SetDestination(self, itemID):
        sm.StartService('starmap').SetWaypoint(itemID, clearOtherWaypoints=True)

    def Bookmark(self, itemID, typeID, parentID, *args):
        sm.GetService('addressbook').BookmarkLocationPopup(itemID, typeID, parentID)

    def GetColorCodedSecurityStringForSystem(self, solarsystemID, itemName):
        sec, col = util.FmtSystemSecStatus(sm.GetService('map').GetSecurityStatus(solarsystemID), 1)
        col.a = 1.0
        color = util.StrFromColor(col)
        text = '<color=%s>%s</color><t>%s' % (color, sec, itemName)
        return text


class InfoWindow(uicls.Window):
    __guid__ = 'form.infowindow'
    __notifyevents__ = ['OnBountyPlaced']
    default_width = 256
    default_height = 340
    default_left = 0
    default_top = 0
    default_name = 'infoWindow'
    default_iconNum = 'ui_9_64_9'

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        typeID = attributes.get('typeID', None)
        itemID = attributes.get('itemID', None)
        rec = attributes.get('rec', None)
        parentID = attributes.get('parentID', None)
        headerOnly = attributes.get('headerOnly', False)
        historyData = attributes.get('historyData', None)
        abstractinfo = attributes.get('abstractinfo', None)
        height = MINHEIGHTREGULAR
        if typeID and typeID == const.typeMedal:
            height = MINHEIGHTMEDAL
        self.SetMinSize([MINWIDTH, height])
        self.SetWndIcon(self.default_iconNum, hidden=True)
        self.scope = 'station_inflight'
        self.sr.main = uiutil.GetChild(self, 'main')
        uix.Flush(self.sr.topParent)
        self.sr.toparea = uicls.Container(name='topareasub', parent=self.sr.topParent, align=uiconst.TOALL, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding), clipChildren=0, state=uiconst.UI_PICKCHILDREN)
        self.sr.mainiconparent = uicls.Container(name='mainiconparent', parent=self.sr.toparea, align=uiconst.TOLEFT, state=uiconst.UI_NORMAL)
        self.sr.techicon = uicls.Sprite(name='techIcon', parent=self.sr.mainiconparent, align=uiconst.RELATIVE, left=0, width=16, height=16, idx=0)
        self.sr.mainicon = uicls.Container(name='mainicon', parent=self.sr.mainiconparent, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
        self.sr.leftpush = uicls.Container(name='leftpush', parent=self.sr.toparea, align=uiconst.TOLEFT, width=6, state=uiconst.UI_DISABLED)
        self.sr.captionpush = uicls.Container(name='captionpush', parent=self.sr.toparea, align=uiconst.TOTOP, height=6)
        self.sr.captioncontainer = uicls.Container(name='captioncontainer', parent=self.sr.toparea, align=uiconst.TOTOP, height=24, state=uiconst.UI_PICKCHILDREN)
        self.sr.subinfolinkcontainer = uicls.Container(name='subinfolinkcontainer', parent=self.sr.toparea, align=uiconst.TOTOP, height=24)
        self.sr.therestpush = uicls.Container(name='therestpush', parent=self.sr.toparea, align=uiconst.TOTOP, height=6)
        self.sr.therestcontainer = uicls.Container(name='therestcontainer', parent=self.sr.toparea, align=uiconst.TOTOP, height=24)
        self.sr.history = []
        self.sr.historyIdx = None
        self.sr.captioncontainer.OnResize = (self.RecalcContainer, self)
        self.sr.therestcontainer.OnResize = (self.RecalcContainer, self)
        self.goBackBtn = uicls.Icon(parent=self.sr.toparea, align=uiconst.TOPRIGHT, icon='ui_38_16_223', pos=(12, -7, 16, 16), hint=localization.GetByLabel('UI/Control/EveWindow/Previous'))
        self.goForwardBtn = uicls.Icon(parent=self.sr.toparea, align=uiconst.TOPRIGHT, icon='ui_38_16_224', pos=(-2, -7, 16, 16), hint=localization.GetByLabel('UI/Control/EveWindow/Next'))
        self.sr.subcontainer = uicls.Container(name='maincontainersub', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.sr.scroll = uicls.InfoScroll(name='scroll', parent=self.sr.subcontainer, state=uiconst.UI_HIDDEN, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.sr.scroll.sr.ignoreTabTrimming = True
        self.sr.notesedit = uicls.EditPlainText(parent=self.sr.subcontainer, pos=(0, 0, 0, 0), padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding), align=uiconst.TOALL, maxLength=5000, showattributepanel=1, state=uiconst.UI_HIDDEN)
        self.sr.descedit = uicls.EditPlainText(parent=self.sr.subcontainer, state=uiconst.UI_HIDDEN, padding=const.defaultPadding, readonly=1, linkStyle=uiconst.LINKSTYLE_SUBTLE)
        self.sr.itemname = None
        uthread.new(self.LoadData, typeID, itemID, rec=rec, parentID=parentID, headerOnly=headerOnly, historyData=historyData, abstractinfo=abstractinfo)

    def GetMainIconDragData(self, *args):
        typeID = self.sr.typeID
        if not typeID:
            return []
        if typeID == const.typeMedal:
            return []
        invtype = cfg.invtypes.Get(self.sr.typeID)
        categoryID = invtype.Category().categoryID
        fakeNode = uiutil.Bunch()
        fakeNode.typeID = typeID
        if categoryID == const.categoryOwner:
            fakeNode.__guid__ = 'listentry.User'
            fakeNode.itemID = self.sr.itemID
            fakeNode.IsCharacter = invtype.groupID == const.groupCharacter
            fakeNode.IsCorporation = invtype.groupID == const.groupCorporation
            fakeNode.IsFaction = invtype.groupID == const.groupFaction
            fakeNode.IsAlliance = invtype.groupID == const.groupAlliance
            if not (fakeNode.IsCharacter or fakeNode.IsCorporation or fakeNode.IsFaction or fakeNode.IsAlliance):
                return []
            fakeNode.charID = self.sr.itemID
            fakeNode.info = uiutil.Bunch(typeID=self.sr.typeID, name=cfg.eveowners.Get(self.sr.itemID).name)
            return [fakeNode]
        if categoryID == const.categoryCelestial and self.sr.itemID:
            fakeNode.__guid__ = 'xtriui.ListSurroundingsBtn'
            fakeNode.itemID = self.sr.itemID
            label, desc = self.GetNameAndDescription(self.sr.typeID, self.sr.itemID, onlyGetInfo=1)
            fakeNode.label = label or localization.GetByLabel('UI/Common/Unknown')
            return [fakeNode]
        if invtype.id == const.typeCertificate:
            fakeNode.__guid__ = 'listentry.CertEntry'
            fakeNode.typeID = self.sr.typeID
            fakeNode.certID = self.sr.abstractinfo.certificateID
            fakeNode.grade = self.sr.abstractinfo.grade
            className, grade, desc = sm.GetService('certificates').GetCertificateLabel(self.sr.abstractinfo.certificateID)
            label = localization.GetByLabel('UI/InfoWindow/CertificateNameWithGrade', certificateName=className, certificateGrade=grade)
            fakeNode.label = label
            return [fakeNode]
        if invtype.published:
            fakeNode.__guid__ = 'listentry.GenericMarketItem'
        else:
            fakeNode.__guid__ = 'uicls.GenericDraggableForTypeID'
        label = invtype.name
        fakeNode.label = label or 'Unknown'
        return [fakeNode]

    def ShowError(self, args):
        self.sr.topParent.Hide()
        errorPar = uicls.Container(parent=self.sr.main, name='errorPar', align=uiconst.TOALL, left=12, top=6, width=12, height=6, state=uiconst.UI_DISABLED)
        msg = cfg.GetMessage(*args)
        title = uicls.CaptionLabel(text=msg.title, parent=errorPar, align=uiconst.TOTOP)
        title.name = 'errorTitle'
        uicls.Container(parent=errorPar, name='separator', align=uiconst.TOTOP, height=6)
        uicls.EveLabelMedium(text=msg.text, name='errorDetails', parent=errorPar, align=uiconst.TOTOP)

    def HideError(self):
        if not self.IsCollapsed():
            self.sr.topParent.state = uiconst.UI_PICKCHILDREN
        errorPar = uiutil.FindChild(self.sr.main, 'errorPar')
        if errorPar is not None:
            errorPar.Close()

    def RecalcContainer(self, subwnd, *args):
        uix.RefreshHeight(subwnd)
        self.sr.toparea.parent.height = self.sr.therestpush.height + self.sr.captionpush.height + self.sr.captioncontainer.height + self.sr.subinfolinkcontainer.height + self.sr.therestcontainer.height
        self.sr.toparea.parent.height = max(self.sr.toparea.parent.height, self.sr.mainiconparent.width, self.sr.mainiconparent.height) + const.defaultPadding * 2

    def LoadData(self, *args, **kwds):
        if getattr(self, 'IsBusy', False):
            self.pendingLoadData = (args, kwds)
            return
        self._LoadInfoWindow(*args, **kwds)
        if getattr(self, 'pendingLoadData', False):
            pargs, pkwds = self.pendingLoadData
            self.pendingLoadData = None
            self.LoadData(*pargs, **pkwds)

    def _LoadInfoWindow(self, typeID, itemID = None, rec = None, parentID = None, historyData = None, headerOnly = 0, abstractinfo = None):
        try:
            self.ShowLoad()
            self.IsBusy = 1
            self.HideError()
            if self.top == uicore.desktop.height:
                self.Maximize()
            else:
                self.SetState(uiconst.UI_NORMAL)
            self.sr.itemID = itemID
            self.sr.typeID = typeID
            self.sr.rec = rec
            self.sr.abstractinfo = abstractinfo
            self.sr.corpinfo = None
            self.sr.allianceinfo = None
            self.sr.factioninfo = None
            self.sr.warfactioninfo = None
            self.sr.stationinfo = None
            self.sr.plasticinfo = None
            self.sr.voucherinfo = None
            self.sr.itemname = None
            self.sr.variationbtm = None
            self.sr.corpID = None
            self.sr.allianceID = None
            self.sr.scroll.Hide()
            self.sr.notesedit.Hide()
            self.sr.descedit.Hide()
            self.sr.oldnotes = None
            self.sr.maintabs = None
            self.ParseTabs()
            self.sr.captionpush.Flush()
            self.sr.captioncontainer.Flush()
            self.sr.subinfolinkcontainer.Flush()
            self.sr.therestcontainer.Flush()
            self.sr.subinfolinkcontainer.height = 0
            self.sr.mainiconparent.GetDragData = self.GetMainIconDragData
            self.sr.mainiconparent.isDragObject = True
            uiutil.FlushList(self.sr.subcontainer.children[:-3])
            self.GetWindowSettings(typeID, itemID)
            height = MINHEIGHTREGULAR
            if typeID == const.typeMedal:
                height = MINHEIGHTMEDAL
            self.SetMinSize([MINWIDTH, height])
            self.GetIcon(typeID, itemID)
            desc = self.GetNameAndDescription(typeID, itemID)
            bio = None
            if self.sr.isCharacter and itemID:
                if not headerOnly:
                    self.sr.dynamicTabs.append((C_NOTESTAB, 'Notes', localization.GetByLabel('UI/InfoWindow/TabNames/Notes')))
                corpid = None
                corpAge = None
                allianceid = None
                charinfo = None
                corpCharInfo = None
                security = None
                if not util.IsNPC(itemID):
                    if util.IsDustCharacter(itemID):
                        corpCharInfo = sm.GetService('corp').GetInfoWindowDataForChar(itemID, 1)
                    else:
                        parallelCalls = []
                        parallelCalls.append((sm.RemoteSvc('charMgr').GetPublicInfo3, (itemID,)))
                        parallelCalls.append((sm.GetService('corp').GetInfoWindowDataForChar, (itemID, 1)))
                        parallelCalls.append((sm.RemoteSvc('standing2').GetSecurityRating, (itemID,)))
                        charinfo, corpCharInfo, security = uthread.parallel(parallelCalls)
                if charinfo is not None:
                    charinfo = charinfo[0]
                    bio = charinfo.description
                    corpAge = blue.os.GetWallclockTime() - charinfo.startDateTime
                    if getattr(charinfo, 'medal1GraphicID', None):
                        uicls.Icon(icon='ui_50_64_16', parent=self.sr.mainicon, left=70, top=80, size=64, align=uiconst.RELATIVE, idx=0)
                if corpCharInfo:
                    corpid = corpCharInfo.corpID
                    allianceid = corpCharInfo.allianceID
                    self.sr.corpID = corpid
                    self.sr.allianceID = allianceid
                    title = ''
                    titleList = []
                    if corpCharInfo.title:
                        title = corpCharInfo.title
                        titleList.append(title)
                    for ix in xrange(1, 17):
                        titleText = getattr(corpCharInfo, 'title%s' % ix, None)
                        if titleText:
                            titleList.append(titleText)

                    if len(titleList) > 0:
                        title = localizationUtil.FormatGenericList(titleList)
                        text = uicls.EveLabelSmall(text=localization.GetByLabel('UI/InfoWindow/CorpTitle', title=title), parent=self.sr.captioncontainer, align=uiconst.TOTOP)
                        if text.height > 405:
                            text.height = 405
                uicls.Container(name='push', parent=self.sr.captioncontainer, align=uiconst.TOTOP, height=4, state=uiconst.UI_DISABLED)
                uicls.Line(parent=self.sr.captioncontainer, align=uiconst.TOTOP)
                if not util.IsNPC(itemID) and not util.IsDustCharacter(itemID):
                    uicls.Line(parent=self.sr.therestcontainer, align=uiconst.TOTOP)
                    uicls.Container(name='push', parent=self.sr.therestcontainer, align=uiconst.TOTOP, height=4)
                    secText = localization.GetByLabel('UI/InfoWindow/SecurityStatusOfCharacter', secStatus=security)
                    uicls.EveLabelSmall(text=secText, parent=self.sr.therestcontainer, align=uiconst.TOTOP)
                    standing = sm.GetService('standing').GetStanding(eve.session.corpid, itemID)
                    if standing is not None:
                        standingText = localization.GetByLabel('UI/InfoWindow/CorpStandingOfCharacter', corpStanding=standing)
                        uicls.EveLabelSmall(text=standingText, parent=self.sr.therestcontainer, align=uiconst.TOTOP)
                    wanted = False
                    bountyOwnerIDs = (itemID, corpid, allianceid)
                    bountyAmount = self.GetBountyAmount(*bountyOwnerIDs)
                    if bountyAmount > 0:
                        wanted = True
                    bountyAmounts = self.GetBountyAmounts(*bountyOwnerIDs)
                    charBounty = 0
                    corpBounty = 0
                    allianceBounty = 0
                    if len(bountyAmounts):
                        for ownerID, value in bountyAmounts.iteritems():
                            if util.IsCharacter(ownerID):
                                charBounty = value
                            elif util.IsCorporation(ownerID):
                                corpBounty = value
                            elif util.IsAlliance(ownerID):
                                allianceBounty = value

                    bountyHint = localization.GetByLabel('UI/Station/BountyOffice/BountyHint', charBounty=util.FmtISK(charBounty, 0), corpBounty=util.FmtISK(corpBounty, 0), allianceBounty=util.FmtISK(allianceBounty, 0))
                    self.Wanted(bountyAmount, True, wanted, ownerIDs=bountyOwnerIDs, hint=bountyHint)
                if self.sr.isCharacter and util.IsNPC(itemID) and not util.IsDustCharacter(itemID):
                    agentInfo = sm.GetService('agents').GetAgentByID(itemID)
                    if agentInfo:
                        corpid = agentInfo.corporationID
                    else:
                        corpid = sm.RemoteSvc('corpmgr').GetCorporationIDForCharacter(itemID)
                if corpid:
                    uicls.Container(name='push', parent=self.sr.subinfolinkcontainer, align=uiconst.TOTOP, height=4)
                    self.GetCorpLogo(corpid, parent=self.sr.subinfolinkcontainer)
                    self.sr.subinfolinkcontainer.height = 64
                    if not util.IsNPC(itemID) and corpid:
                        uicls.Container(name='push', parent=self.sr.subinfolinkcontainer, align=uiconst.TOLEFT, width=4)
                        tickerName = cfg.corptickernames.Get(corpid).tickerName
                        uicls.EveLabelSmall(text=localization.GetByLabel('UI/InfoWindow/MemberOfCorp', corpName=cfg.eveowners.Get(corpid).name, tickerName=tickerName), parent=self.sr.subinfolinkcontainer, align=uiconst.TOTOP, top=0, left=0)
                        if corpAge is not None:
                            uicls.EveLabelSmall(text=localization.GetByLabel('UI/InfoWindow/MemberFor', timePeriod=util.FmtTimeInterval(corpAge, 'day')), parent=self.sr.subinfolinkcontainer, align=uiconst.TOBOTTOM, left=4)
                        uthread.new(self.ShowRelationshipIcon, itemID, corpid, allianceid)
                    if charinfo is not None:
                        militiaFactionID = charinfo.militiaFactionID
                        if not util.IsNPC(itemID) and (allianceid or militiaFactionID):
                            subinfoCont = uicls.Container(name='subinfo', parent=self.sr.therestcontainer, align=uiconst.TOTOP, height=16, idx=0)
                            uicls.Line(parent=subinfoCont, align=uiconst.TOTOP, padBottom=1)
                            text = ''
                            if allianceid:
                                text = cfg.eveowners.Get(allianceid).name
                                if militiaFactionID:
                                    text += ' | '
                            subinfoText = uicls.EveLabelSmall(text=text, parent=subinfoCont, align=uiconst.TOLEFT, top=4)
                            subinfoCont.height = subinfoText.textheight + 2 * subinfoText.top
                            if militiaFactionID:
                                fwiconCont = uicls.Container(name='subinfo', parent=subinfoCont, align=uiconst.TOLEFT, width=20)
                                fwicon = uicls.Sprite(name='fwIcon', parent=fwiconCont, align=uiconst.TOPLEFT, texturePath='res:/UI/Texture/Icons/FW_Icon_Small.png', pos=(-2, 0, 20, 20))
                                factionText = localization.GetByLabel('UI/FactionWarfare/MilitiaAndFaction', factionName=cfg.eveowners.Get(militiaFactionID).name)
                                factionLabel = uicls.EveLabelSmall(text=factionText, parent=subinfoCont, align=uiconst.TOLEFT, top=4)
                                subinfoCont.height = max(subinfoText.textheight + 2 * subinfoText.top, factionLabel.textheight + 2 * subinfoText.top)
            elif self.sr.isShip and itemID or typeID and sm.GetService('godma').GetType(typeID).agentID:
                if itemID == eve.session.shipid:
                    otherCharID = eve.session.charid
                elif typeID and sm.GetService('godma').GetType(typeID).agentID:
                    otherCharID = sm.GetService('godma').GetType(typeID).agentID
                elif eve.session.solarsystemid is not None:
                    otherCharID = sm.GetService('michelle').GetCharIDFromShipID(itemID)
                else:
                    otherCharID = None
                if otherCharID:
                    btn = uix.GetBigButton(42, self.sr.subinfolinkcontainer, left=0, top=0, iconMargin=0)
                    btn.OnClick = (self.LoadData, cfg.eveowners.Get(otherCharID).typeID, otherCharID)
                    btn.hint = localization.GetByLabel('UI/InfoWindow/ClickForPilotInfo')
                    btn.sr.icon.LoadIconByTypeID(cfg.eveowners.Get(otherCharID).typeID, itemID=otherCharID, ignoreSize=True)
                    btn.sr.icon.SetAlign(uiconst.RELATIVE)
                    btn.sr.icon.SetSize(40, 40)
                    self.sr.subinfolinkcontainer.height = 42
            elif self.sr.abstractinfo is not None:
                if self.sr.isMedal or self.sr.isRibbon:
                    corpid = None
                    info = sm.GetService('medals').GetMedalDetails(itemID).info[0]
                    try:
                        corpid = info.ownerID
                    except:
                        sys.exc_clear()

                    if corpid:
                        uicls.Container(name='push', parent=self.sr.subinfolinkcontainer, align=uiconst.TOTOP, height=4)
                        self.GetCorpLogo(corpid, parent=self.sr.subinfolinkcontainer)
                        self.sr.subinfolinkcontainer.height = 64
                        if corpid and not util.IsNPC(corpid):
                            uicls.Container(name='push', parent=self.sr.subinfolinkcontainer, align=uiconst.TOLEFT, width=4)
                            tickerName = cfg.corptickernames.Get(corpid).tickerName
                            uicls.EveLabelMedium(text=localization.GetByLabel('UI/InfoWindow/MedalIssuedBy', corpName=cfg.eveowners.Get(corpid).name, tickerName=tickerName), parent=self.sr.subinfolinkcontainer, align=uiconst.TOTOP, top=0, left=0)
                        uicls.Line(parent=self.sr.captioncontainer, align=uiconst.TOTOP)
                        uicls.Line(parent=self.sr.therestcontainer, align=uiconst.TOTOP)
                    uicls.Container(name='push', parent=self.sr.therestcontainer, align=uiconst.TOTOP, height=4)
                    recipients = info.numberOfRecipients
                    txt = localization.GetByLabel('UI/InfoWindow/NumberOfTimesAwarded', numTimes=recipients)
                    uicls.EveLabelSmall(text=txt, parent=self.sr.therestcontainer, align=uiconst.TOTOP)
                elif getattr(self.sr.abstractinfo, 'categoryID', None) == const.categoryBlueprint:
                    self.sr.isBlueprint = True
            elif self.sr.isCorporation:
                parallelCalls = []
                if self.sr.corpinfo is None:
                    parallelCalls.append((sm.RemoteSvc('corpmgr').GetPublicInfo, (itemID,)))
                else:
                    parallelCalls.append((ReturnNone, ()))
                parallelCalls.append((sm.GetService('faction').GetFaction, (itemID,)))
                if self.sr.warfactioninfo is None:
                    parallelCalls.append((sm.GetService('facwar').GetCorporationWarFactionID, (itemID,)))
                else:
                    parallelCalls.append((ReturnNone, ()))
                corpinfo, factionID, warFaction = uthread.parallel(parallelCalls)
                self.sr.corpinfo = self.sr.corpinfo or corpinfo
                allianceid = self.sr.corpinfo.allianceID
                uthread.new(self.ShowRelationshipIcon, None, itemID, allianceid)
                uicls.EveLabelMedium(text=localization.GetByLabel('UI/InfoWindow/HeadquartersLocation', location=self.sr.corpinfo.stationID), parent=self.sr.captioncontainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
                uicls.Container(name='push', parent=self.sr.captioncontainer, align=uiconst.TOTOP, height=4)
                uicls.Line(parent=self.sr.captioncontainer, align=uiconst.TOTOP)
                self.RecalcContainer(self.sr.captioncontainer)
                memberDisp = None
                if factionID or warFaction:
                    faction = cfg.eveowners.Get(factionID) if factionID else cfg.eveowners.Get(warFaction)
                    uiutil.GetLogoIcon(itemID=faction.ownerID, parent=self.sr.subinfolinkcontainer, align=uiconst.TOLEFT, state=uiconst.UI_NORMAL, hint=localization.GetByLabel('UI/InfoWindow/ClickForFactionInfo'), OnClick=(self.LoadData, faction.typeID, faction.ownerID), size=64, ignoreSize=True)
                    self.sr.subinfolinkcontainer.height = 64
                    memberDisp = cfg.eveowners.Get(faction.ownerID).name
                if allianceid:
                    alliance = cfg.eveowners.Get(allianceid)
                    uiutil.GetLogoIcon(itemID=allianceid, align=uiconst.TOLEFT, parent=self.sr.subinfolinkcontainer, OnClick=(self.LoadData, alliance.typeID, allianceid), hint=localization.GetByLabel('UI/InfoWindow/ClickForAllianceInfo'), state=uiconst.UI_NORMAL, size=64, ignoreSize=True)
                    self.sr.subinfolinkcontainer.height = 64
                    memberDisp = cfg.eveowners.Get(allianceid).name
                if memberDisp is not None:
                    uicls.Container(name='push', parent=self.sr.subinfolinkcontainer, align=uiconst.TOLEFT, width=4)
                    uicls.EveLabelMedium(text=localization.GetByLabel('UI/InfoWindow/MemberOfAlliance', allianceName=memberDisp), parent=self.sr.subinfolinkcontainer, align=uiconst.TOTOP, top=4, left=0)
                if warFaction is not None:
                    facWarInfoCont = uicls.Container(name='facwarinfo', parent=self.sr.subinfolinkcontainer, align=uiconst.TOTOP, height=28)
                    fwicon = uicls.Sprite(name='fwIcon', parent=facWarInfoCont, align=uiconst.CENTERLEFT, texturePath='res:/UI/Texture/Icons/FW_Icon_Large.png', pos=(2, 0, 32, 32), hint=localization.GetByLabel('UI/Commands/OpenFactionalWarfare'))
                    fwicon.OnClick = sm.GetService('cmd').OpenMilitia
                    uicls.EveLabelMedium(text=localization.GetByLabel('UI/FactionWarfare/MilitiaAndFaction', factionName=cfg.eveowners.Get(warFaction).name), parent=facWarInfoCont, align=uiconst.CENTERLEFT, left=38)
                if not util.IsNPC(itemID):
                    wanted = False
                    if not self.sr.corpinfo.deleted:
                        bountyOwnerIDs = (itemID, allianceid)
                        bountyAmount = self.GetBountyAmount(*bountyOwnerIDs)
                        if bountyAmount > 0:
                            wanted = True
                        bountyAmounts = self.GetBountyAmounts(*bountyOwnerIDs)
                        corpBounty = 0
                        allianceBounty = 0
                        if len(bountyAmounts):
                            for ownerID, value in bountyAmounts.iteritems():
                                if util.IsCorporation(ownerID):
                                    corpBounty = value
                                elif util.IsAlliance(ownerID):
                                    allianceBounty = value

                        bountyHint = localization.GetByLabel('UI/Station/BountyOffice/BountyHintCorp', corpBounty=util.FmtISK(corpBounty, 0), allianceBounty=util.FmtISK(allianceBounty, 0))
                        self.Wanted(bountyAmount, False, wanted, ownerIDs=bountyOwnerIDs, hint=bountyHint)
            elif self.sr.isAlliance:
                if self.sr.allianceinfo is None:
                    self.sr.allianceinfo = sm.GetService('alliance').GetAlliance(itemID)
                uthread.new(self.ShowRelationshipIcon, None, None, itemID)
                wanted = False
                if not self.sr.allianceinfo.deleted:
                    bountyOwnerIDs = (itemID,)
                    bountyAmount = self.GetBountyAmount(*bountyOwnerIDs)
                    if bountyAmount > 0:
                        wanted = True
                    self.Wanted(bountyAmount, False, wanted, ownerIDs=bountyOwnerIDs)
            elif self.sr.isFaction:
                if self.sr.factioninfo is None:
                    self.sr.factioninfo = cfg.factions.GetIfExists(itemID)
                uicls.EveLabelMedium(text=localization.GetByLabel('UI/InfoWindow/HeadquartersLocation', location=self.sr.factioninfo.solarSystemID), parent=self.sr.captioncontainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
                uicls.Container(name='push', parent=self.sr.captioncontainer, align=uiconst.TOTOP, height=4)
                uicls.Line(parent=self.sr.captioncontainer, align=uiconst.TOTOP)
                self.RecalcContainer(self.sr.captioncontainer)
            elif self.sr.isSkill and session.charid:
                hasSkill = sm.GetService('skills').HasSkill(typeID)
                if hasSkill:
                    skillParent = uicls.Container(parent=self.sr.therestcontainer, align=uiconst.TOTOP, height=10, top=4)
                    groupID = cfg.invtypes.Get(typeID).Group().groupID
                    skillLevels = uicls.SkillLevels(parent=skillParent, align=uiconst.TOLEFT, typeID=typeID, groupID=groupID)
                else:
                    labelText = localization.GetByLabel('UI/SkillQueue/Skills/SkillNotInjected')
                    lbl = uicls.EveLabelSmall(text=labelText, parent=self.sr.therestcontainer, align=uiconst.TOTOP)
                    lbl.SetAlpha(0.4)
            invtype = cfg.invtypes.Get(typeID)
            if invtype.groupID == const.groupWormhole:
                desc2 = ''
                slimItem = sm.StartService('michelle').GetItem(itemID)
                if slimItem:
                    wormholeClasses = {0: 'UI/Wormholes/Classes/UnknownSpaceDescription',
                     1: 'UI/Wormholes/Classes/UnknownSpaceDescription',
                     2: 'UI/Wormholes/Classes/UnknownSpaceDescription',
                     3: 'UI/Wormholes/Classes/UnknownSpaceDescription',
                     4: 'UI/Wormholes/Classes/DangerousUnknownSpaceDescription',
                     5: 'UI/Wormholes/Classes/DangerousUnknownSpaceDescription',
                     6: 'UI/Wormholes/Classes/DeadlyUnknownSpaceDescription',
                     7: 'UI/Wormholes/Classes/HighSecuritySpaceDescription',
                     8: 'UI/Wormholes/Classes/LowSecuritySpaceDescription',
                     9: 'UI/Wormholes/Classes/NullSecuritySpaceDescription'}
                    wClass = localization.GetByLabel(wormholeClasses.get(slimItem.otherSolarSystemClass))
                    if slimItem.wormholeAge >= 3:
                        wAge = localization.GetByLabel('UI/InfoWindow/WormholeAgeAboutToClose')
                    elif slimItem.wormholeAge >= 2:
                        wAge = localization.GetByLabel('UI/InfoWindow/WormholeAgeReachingTheEnd')
                    elif slimItem.wormholeAge >= 1:
                        wAge = localization.GetByLabel('UI/InfoWindow/WormholeAgeStartedDecaying')
                    elif slimItem.wormholeAge >= 0:
                        desc2 += localization.GetByLabel('UI/InfoWindow/WormholeAgeNew') + '<br>'
                        wAge = localization.GetByLabel('UI/InfoWindow/WormholeAgeNew')
                    else:
                        wAge = ''
                    if slimItem.wormholeSize < 0.5:
                        remaining = localization.GetByLabel('UI/InfoWindow/WormholeSizeStabilityCriticallyDisrupted')
                    elif slimItem.wormholeSize < 1:
                        remaining = localization.GetByLabel('UI/InfoWindow/WormholeSizeStabilityReduced')
                    else:
                        remaining = localization.GetByLabel('UI/InfoWindow/WormholeSizeNotDisrupted')
                    desc = localization.GetByLabel('UI/InfoWindow/WormholeDescription', wormholeName=desc, wormholeClass=wClass, wormholeAge=wAge, remaining=remaining)
            self.HideGoBack()
            self.HideGoForward()
            if not headerOnly:
                sm.GetService('info').GetWndData(self, typeID, itemID, parentID=parentID)
                historyIdx = None
                if historyData is None:
                    if self.sr.historyIdx is not None:
                        self.sr.history = self.sr.history[:self.sr.historyIdx + 1]
                    history = (typeID,
                     itemID,
                     parentID,
                     len(self.sr.history),
                     rec,
                     abstractinfo)
                    self.sr.history.append(history)
                    self.sr.historyIdx = None
                else:
                    _typeID, _itemID, _parentID, historyIdx, _rec, _abstractinfo = historyData
                    self.sr.historyIdx = historyIdx
                if len(self.sr.history) > 1:
                    if historyIdx != 0:
                        if historyIdx:
                            self.goBackBtn.OnClick = lambda *args: self.Browse(self.sr.history[historyIdx - 1])
                        else:
                            self.goBackBtn.OnClick = lambda *args: self.Browse(self.sr.history[-2])
                        self.ShowGoBack()
                    if historyIdx is not None and historyIdx != len(self.sr.history) - 1:
                        self.goForwardBtn.OnClick = lambda *args: self.Browse(self.sr.history[historyIdx + 1])
                        self.ShowGoForward()
            else:
                desc = ''
                bio = None
            if self is None or self.destroyed:
                return
            tabgroup = []
            for listtype, subtabs, tabName in self.sr.infotabs:
                items = self.sr.data[listtype]['items']
                tabname = self.sr.data[listtype]['name']
                if subtabs:
                    subtabgroup = []
                    sublisttype, subsubtabs = (None, None)
                    for sublisttype, subsubtabs, stName in subtabs:
                        subitems = self.sr.data[sublisttype]['items']
                        subtabname = self.sr.data[sublisttype]['name']
                        if len(subitems):
                            subtabgroup.append([subtabname,
                             self.sr.scroll,
                             self,
                             (sublisttype, None)])

                    if subtabgroup:
                        _subtabs = uicls.TabGroup(name='%s_subtabs' % tabname.lower(), parent=self.sr.subcontainer, idx=0, tabs=subtabgroup, groupID='infowindow_%s' % sublisttype, autoselecttab=0)
                        tabgroup.append([tabname,
                         self.sr.scroll,
                         self,
                         ('selectSubtab', None, _subtabs),
                         _subtabs])
                elif len(items):
                    tabgroup.append([tabname,
                     self.sr.scroll,
                     self,
                     (listtype, None)])

            for listtype, funcName, tabName in self.sr.dynamicTabs:
                if listtype == C_NOTESTAB:
                    tabgroup.append([tabName,
                     self.sr.notesedit,
                     self,
                     (listtype, funcName)])
                else:
                    tabgroup.append([tabName,
                     self.sr.scroll,
                     self,
                     (listtype, funcName)])

            widthRequirements = [MINWIDTH]
            if not headerOnly and self.sr.data['buttons'] and session.charid:
                btns = uicls.ButtonGroup(btns=self.sr.data['buttons'], parent=self.sr.subcontainer, idx=0, unisize=0)
                totalBtnWidth = 0
                for btn in btns.children[0].children:
                    totalBtnWidth += btn.width

                widthRequirements.append(totalBtnWidth)
            if desc:
                tabgroup.insert(0, [localization.GetByLabel('UI/InfoWindow/TabNames/Description'),
                 self.sr.descedit,
                 self,
                 ('readOnlyText', None, desc)])
            if not util.IsNPC(itemID) and bio:
                tabgroup.insert(0, [localization.GetByLabel('UI/InfoWindow/TabNames/Bio'),
                 self.sr.descedit,
                 self,
                 ('readOnlyText', None, bio)])
            if len(tabgroup):
                self.sr.maintabs = uicls.TabGroup(name='maintabs', parent=self.sr.subcontainer, idx=0, tabs=tabgroup, groupID='infowindow')
                widthRequirements.append(self.sr.maintabs.totalTabWidth + 16)
            if len(widthRequirements) > 1:
                height = MINHEIGHTREGULAR
                if typeID == const.typeMedal:
                    height = MINHEIGHTMEDAL
                self.SetMinSize([max(widthRequirements), height])
            self.RecalcContainer(self.sr.captioncontainer)
            self.RecalcContainer(self.sr.therestcontainer)
            self.sr.toparea.state = uiconst.UI_PICKCHILDREN
            if headerOnly:
                self.height = self.sr.toparea.parent.height
            self.HideLoad()
            self.ShowHeaderButtons(1)
            self.IsBusy = 0
        except BadArgs as e:
            if not self.destroyed:
                self.HideLoad()
                self.ShowHeaderButtons(1)
                self.IsBusy = 0
                self.ShowError(e.args)
            sys.exc_clear()
        except:
            if not self.destroyed:
                self.HideLoad()
                self.ShowHeaderButtons(1)
                self.IsBusy = 0
                raise 
            sys.exc_clear()

    def ShowGoBack(self):
        self.goBackBtn.opacity = 1.0
        self.goBackBtn.Enable()

    def HideGoBack(self):
        self.goBackBtn.opacity = 0.25
        self.goBackBtn.Disable()

    def ShowGoForward(self):
        self.goForwardBtn.opacity = 1.0
        self.goForwardBtn.Enable()

    def HideGoForward(self):
        self.goForwardBtn.opacity = 0.25
        self.goForwardBtn.Disable()

    def OnBack(self):
        if self.goBackBtn.state == uiconst.UI_NORMAL:
            self.goBackBtn.OnClick()

    def OnForward(self):
        if self.goForwardBtn.state == uiconst.UI_NORMAL:
            self.goForwardBtn.OnClick()

    def GetWindowSettings(self, typeID, itemID):
        invtype = cfg.invtypes.Get(typeID)
        invgroup = invtype.Group()
        try:
            godmaType = sm.GetService('godma').GetType(typeID)
            if godmaType.constructionType != 0:
                self.sr.isUpgradeable = True
            else:
                self.sr.isUpgradeable = False
        except AttributeError:
            self.sr.isUpgradeable = False

        self.sr.isBookmark = invtype.id == const.typeBookmark
        self.sr.isVoucher = invtype.groupID == const.groupVoucher
        self.sr.isCharacter = invtype.groupID == const.groupCharacter
        self.sr.isStargate = invtype.groupID == const.groupStargate
        self.sr.isControlTower = invtype.groupID == const.groupControlTower
        self.sr.isConstructionPF = invtype.groupID in (const.groupStationUpgradePlatform, const.groupStationImprovementPlatform, const.groupConstructionPlatform)
        self.sr.isCorporation = invtype.groupID == const.groupCorporation
        self.sr.isAlliance = invtype.groupID == const.groupAlliance
        self.sr.isFaction = invtype.groupID == const.groupFaction
        self.sr.isOwned = invtype.groupID in (const.groupWreck,
         const.groupSecureCargoContainer,
         const.groupAuditLogSecureContainer,
         const.groupCargoContainer,
         const.groupFreightContainer,
         const.groupSentryGun,
         const.groupDestructibleSentryGun,
         const.groupMobileSentryGun,
         const.groupDeadspaceOverseersSentry,
         const.groupPlanet) or invtype.categoryID in [const.categoryStructure, const.categorySovereigntyStructure, const.categoryOrbital]
        self.sr.isShip = invgroup.categoryID == const.categoryShip
        self.sr.isStation = invgroup.categoryID == const.categoryStation and invtype.groupID != const.groupStationServices
        self.sr.isModule = invgroup.categoryID in (const.categoryModule, const.categorySubSystem)
        self.sr.isStructure = invgroup.categoryID in (const.categoryStructure,
         const.categoryDeployable,
         const.categorySovereigntyStructure,
         const.categoryOrbital)
        self.sr.isCharge = invgroup.categoryID == const.categoryCharge
        self.sr.isBlueprint = invgroup.categoryID in (const.categoryBlueprint, const.categoryAncientRelic)
        self.sr.isReaction = invgroup.categoryID == const.categoryReaction
        self.sr.isDrone = invgroup.categoryID == const.categoryDrone
        self.sr.isCelestial = invgroup.categoryID in (const.categoryCelestial, const.categoryAsteroid) and invtype.groupID not in (const.groupWreck,
         const.groupCargoContainer,
         const.groupFreightContainer,
         const.groupSecureCargoContainer,
         const.groupAuditLogSecureContainer) or invtype.groupID in (const.groupLargeCollidableStructure, const.groupDeadspaceOverseersStructure, const.groupHarvestableCloud)
        self.sr.isGenericItem = invgroup.categoryID in (const.categoryImplant,
         const.categorySkill,
         const.categoryAccessories,
         const.categoryPlanetaryCommodities,
         const.categoryPlanetaryResources)
        self.sr.isGenericObject = invgroup.categoryID in (const.categoryEntity, const.categoryDrone)
        self.sr.isAnchorable = invgroup.categoryID in (const.categoryStructure, const.categoryDeployable, const.categoryOrbital) or invgroup.groupID in (const.groupSecureCargoContainer, const.groupAuditLogSecureContainer)
        self.sr.isPin = invgroup.categoryID in (const.categoryPlanetaryInteraction,) and invgroup.groupID not in (const.groupPlanetaryLinks, const.groupPlanetaryCustomsOffices)
        self.sr.isPinLink = invgroup.groupID == const.groupPlanetaryLinks
        self.sr.isCargoLink = invgroup.groupID == const.groupPlanetaryCustomsOffices
        self.sr.isPICommodity = invtype.id in cfg.schematicsByType
        self.sr.isApparel = invgroup.categoryID == const.categoryApparel
        self.sr.isPlanet = invgroup.groupID == const.groupPlanet
        self.sr.isCustomsOffice = invgroup.groupID == const.groupPlanetaryCustomsOffices
        self.sr.isStructureUpgrade = invgroup.categoryID == const.categoryStructureUpgrade
        self.sr.isRank = invtype.id == const.typeRank
        self.sr.isMedal = invtype.id == const.typeMedal
        self.sr.isRibbon = invtype.id == const.typeRibbon
        self.sr.isCertificate = invtype.id == const.typeCertificate
        self.sr.isSchematic = invtype.id == const.typeSchematic
        self.sr.isSkill = invgroup.groupID in sm.GetService('skills').GetSkillGroupsIDs()
        self.sr.isAbstract = invgroup.categoryID == const.categoryAbstract
        if self.sr.isVoucher:
            self.sr.voucherinfo = sm.GetService('voucherCache').GetVoucher(itemID)
        if self.sr.isBookmark:
            caption = localization.GetByLabel('UI/InfoWindow/InfoWindowCaption', infoObject=invtype.name)
        elif typeID == const.typeMapLandmark:
            caption = localization.GetByLabel('UI/InfoWindow/LandmarkInformationCaption')
        elif typeID == const.typeSchematic:
            caption = localization.GetByLabel('UI/InfoWindow/InfoWindowCaption', infoObject=localization.GetByLabel('UI/PI/Common/Schematics'))
        elif self.sr.isSkill:
            caption = localization.GetByLabel('UI/InfoWindow/InfoWindowCaption', infoObject=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SkillTabs/Skill'))
        else:
            caption = localization.GetByLabel('UI/InfoWindow/InfoWindowCaption', infoObject=invtype.Group().name)
        self.SetCaption(caption)
        height = MINHEIGHTREGULAR
        if typeID == const.typeMedal:
            height = MINHEIGHTMEDAL
        self.SetMinSize([MINWIDTH, height])

    def GetIcon(self, typeID, itemID):
        invtype = cfg.invtypes.Get(typeID)
        iWidth = iHeight = 64
        rendersize = 128
        self.sr.mainicon.Flush()
        self.sr.techicon.Hide()
        self.sr.mainiconparent.cursor = None
        self.sr.mainiconparent.OnClick = None
        if (self.sr.isShip or self.sr.isStation or self.sr.isStargate or self.sr.isGenericObject or self.sr.isCelestial or self.sr.isOwned or self.sr.isRank) and invtype.groupID not in (const.groupWreck,
         const.groupCargoContainer,
         const.groupSecureCargoContainer,
         const.groupAuditLogSecureContainer,
         const.groupFreightContainer,
         const.groupHarvestableCloud) and invtype.categoryID != const.categoryAsteroid:
            iWidth = iHeight = 128
            if invtype.groupID not in (const.groupRegion, const.groupConstellation, const.groupSolarSystem):
                rendersize = 256
        hasAbstractIcon = False
        if self.sr.isAbstract and self.sr.abstractinfo is not None:
            if self.sr.isRank:
                rank = xtriui.Rank(name='rankicon', align=uiconst.TOPLEFT, left=3, top=2, width=iWidth, height=iHeight, parent=self.sr.mainicon)
                rank.Startup(self.sr.abstractinfo.warFactionID, self.sr.abstractinfo.currentRank)
                hasAbstractIcon = True
            if self.sr.isMedal or self.sr.isRibbon:
                rendersize = 256
                iWidth, iHeight = (128, 256)
                medal = xtriui.MedalRibbon(name='medalicon', align=uiconst.TOPLEFT, left=3, top=2, width=iWidth, height=iHeight, parent=self.sr.mainicon)
                medal.Startup(self.sr.abstractinfo, rendersize)
                hasAbstractIcon = True
            if self.sr.isCertificate:
                mapped = 'ui_79_64_%s' % (int(self.sr.abstractinfo.grade) + 1)
                sprite = uicls.Icon(parent=self.sr.mainicon, icon=mapped, align=uiconst.TOALL)
            if self.sr.isSchematic:
                sprite = uicls.Icon(parent=self.sr.mainicon, icon='ui_27_64_3', align=uiconst.TOALL)
                hasAbstractIcon = True
        if self.sr.isCharacter:
            sprite = uicls.Sprite(parent=self.sr.mainicon, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
            sm.GetService('photo').GetPortrait(itemID, 256, sprite, allowServerTrip=True)
            iWidth = iHeight = 128
            if not util.IsDustCharacter(itemID):
                self.sr.mainiconparent.cursor = uiconst.UICURSOR_MAGNIFIER
                self.sr.mainiconparent.OnClick = (self.OpenPortraitWnd, itemID)
        elif self.sr.isCorporation or self.sr.isFaction or self.sr.isAlliance:
            if self.sr.isCorporation:
                try:
                    cfg.eveowners.Get(itemID)
                except:
                    log.LogWarn('Tried to show info on bad corpID:', itemID)
                    raise BadArgs('InfoNoCorpWithID')

            uiutil.GetLogoIcon(itemID=itemID, parent=self.sr.mainicon, name='corplogo', acceptNone=False, align=uiconst.TOALL)
            self.sr.mainiconparent.cursor = uiconst.UICURSOR_MAGNIFIER
            self.sr.mainiconparent.OnClick = (self.OpenEntityWnd, itemID)
        elif typeID == const.typeMapLandmark:
            landmark = sm.GetService('map').GetLandmark(itemID * -1)
            if landmark.iconID:
                sprite = uicls.Sprite(parent=self.sr.mainicon, align=uiconst.TOALL)
                sprite.texture.resPath = util.IconFile(landmark.iconID)
                sprite.rectLeft = 64
                sprite.rectWidth = 128
                iWidth = iHeight = 128
        elif invtype.categoryID == const.categoryBlueprint and (itemID and itemID < const.minFakeItem or self.sr.abstractinfo is not None):
            uix.GetTechLevelIcon(self.sr.techicon, 0, typeID)
            if itemID and itemID < const.minFakeItem:
                self.sr.blueprintInfo = sm.RemoteSvc('factory').GetBlueprintAttributes(itemID)
                isCopy = self.sr.blueprintInfo.get('copy', False)
            elif self.sr.abstractinfo is not None:
                isCopy = self.sr.abstractinfo.isCopy
            icon = uicls.Icon(parent=self.sr.mainicon, align=uiconst.TOALL, size=rendersize, typeID=typeID, itemID=itemID, ignoreSize=True, isCopy=isCopy)
        elif not hasAbstractIcon:
            uix.GetTechLevelIcon(self.sr.techicon, 0, typeID)
            icon = uicls.Icon(parent=self.sr.mainicon, align=uiconst.TOALL, size=rendersize, typeID=typeID, itemID=itemID, ignoreSize=True)
            if util.IsPreviewable(typeID):
                icon.typeID = typeID
                self.sr.mainiconparent.cursor = uiconst.UICURSOR_MAGNIFIER
                self.sr.mainiconparent.OnClick = (self.OnPreviewClick, icon)
        self.sr.mainiconparent.width = self.sr.mainicon.width = iWidth
        self.sr.mainiconparent.height = self.sr.mainicon.height = iHeight

    def GetNameAndDescription(self, typeID, itemID, onlyGetInfo = 0):
        if typeID == const.typeMapLandmark:
            landmark = sm.GetService('map').GetLandmark(itemID * -1)
            capt = maputils.GetNameFromMapCache(landmark.landmarkNameID, 'landmark')
            desc = maputils.GetNameFromMapCache(landmark.descriptionID, 'landmark')
            label = ''
            self.sr.isCelestial = 0
        else:
            capt = None
            invtype = cfg.invtypes.Get(typeID)
            if itemID in cfg.evelocations.data:
                capt = cfg.evelocations.Get(itemID).name
            if not capt:
                capt = invtype.name
            desc = invtype.description
            label = ''
        if self.sr.isAbstract:
            if self.sr.abstractinfo is not None:
                if self.sr.isRank:
                    capt = localization.GetByLabel('UI/FactionWarfare/Rank')
                    try:
                        rankLabel, rankDescription = sm.GetService('facwar').GetRankLabel(self.sr.abstractinfo.warFactionID, self.sr.abstractinfo.currentRank)
                        desc = rankDescription
                        label = rankLabel
                    except:
                        sys.exc_clear()

                if self.sr.isMedal or self.sr.isRibbon:
                    try:
                        info = sm.GetService('medals').GetMedalDetails(itemID).info[0]
                        desc = info.description
                        label = info.title
                    except:
                        sys.exc_clear()

                if self.sr.isCertificate:
                    try:
                        className, grade, desc = sm.GetService('certificates').GetCertificateLabel(self.sr.abstractinfo.certificateID)
                        label = localization.GetByLabel('UI/InfoWindow/CertificateNameWithGrade', certificateName=className, certificateGrade=grade)
                    except:
                        sys.exc_clear()

                if self.sr.isSchematic:
                    try:
                        label = self.sr.abstractinfo.schematicName
                        desc = ''
                    except:
                        sys.exc_clear()

        elif self.sr.isSkill:
            try:
                label = '&gt; %s' % cfg.invtypes.Get(typeID).Group().name
            except:
                sys.exc_clear()

        elif self.sr.isBookmark and itemID is not None:
            capt = 'Bookmark'
            if self.sr.voucherinfo:
                try:
                    label, desc = sm.GetService('addressbook').UnzipMemo(self.sr.voucherinfo.GetDescription())
                except:
                    desc = self.sr.voucherinfo.GetDescription()
                    sys.exc_clear()

        elif self.sr.isCharacter and itemID is not None:
            capt = cfg.eveowners.Get(itemID).name
            desc = cfg.eveowners.Get(itemID).description
            if desc == capt:
                bloodline = sm.GetService('info').GetBloodlineByTypeID(cfg.eveowners.Get(itemID).typeID)
                desc = localization.GetByMessageID(bloodline.descriptionID)
        elif self.sr.isCorporation and itemID is not None:
            if self.sr.corpinfo is None:
                self.sr.corpinfo = sm.RemoteSvc('corpmgr').GetPublicInfo(itemID)
            if self.sr.corpinfo.corporationID < 1100000:
                desc = cfg.npccorporations.Get(self.sr.corpinfo.corporationID).description
            else:
                desc = self.sr.corpinfo.description
            if uiutil.CheckCorpID(itemID):
                capt = ''
            else:
                capt = cfg.eveowners.Get(itemID).name
                if self.sr.corpinfo.deleted:
                    capt = localization.GetByLabel('UI/InfoWindow/ClosedCorpOrAllianceCaption', corpOrAllianceName=cfg.eveowners.Get(itemID).name)
        elif self.sr.isAlliance and itemID is not None:
            if self.sr.allianceinfo is None:
                self.sr.allianceinfo = sm.GetService('alliance').GetAlliance(itemID)
            capt = cfg.eveowners.Get(itemID).name
            desc = self.sr.allianceinfo.description
            warFactionID = sm.GetService('facwar').GetAllianceWarFactionID(itemID)
            if warFactionID is not None:
                fwicon = uicls.Sprite(name='fwIcon', parent=self.sr.subinfolinkcontainer, align=uiconst.CENTERLEFT, texturePath='res:/UI/Texture/Icons/FW_Icon_Large.png', pos=(2, 0, 32, 32), hint=localization.GetByLabel('UI/Commands/OpenFactionalWarfare'))
                fwicon.OnClick = sm.GetService('cmd').OpenMilitia
                uicls.EveLabelMedium(text=localization.GetByLabel('UI/FactionWarfare/MilitiaAndFaction', factionName=cfg.eveowners.Get(warFactionID).name), parent=self.sr.subinfolinkcontainer, align=uiconst.CENTERLEFT, left=38)
                self.sr.subinfolinkcontainer.height = 32
            if self.sr.allianceinfo.deleted:
                capt = localization.GetByLabel('UI/InfoWindow/ClosedCorpOrAllianceCaption', corpOrAllianceName=cfg.eveowners.Get(itemID).name)
        elif self.sr.isStation:
            if itemID is not None:
                if self.sr.stationinfo is None:
                    self.sr.stationinfo = sm.GetService('map').GetStation(itemID)
                capt = self.sr.stationinfo.stationName
                if itemID < 61000000 and self.sr.stationinfo.stationTypeID not in (12294, 12295, 12242):
                    desc = localization.GetByMessageID(self.sr.stationinfo.descriptionID)
                else:
                    desc = self.sr.stationinfo.description
            else:
                desc = cfg.invtypes.Get(typeID).description or cfg.invtypes.Get(typeID).name
        elif self.sr.isCelestial or self.sr.isStargate:
            desc = ''
            if invtype.groupID in (const.groupSolarSystem, const.groupConstellation, const.groupRegion):
                locationTrace = self.GetLocationTrace(itemID, [])
                label = invtype.name + '<br><br>' + locationTrace
                mapdesc = cfg.mapcelestialdescriptions.GetIfExists(itemID)
                if mapdesc:
                    desc = mapdesc.description
            if not desc:
                desc = invtype.description or invtype.name
            desc = desc + '<br>'
            capt = invtype.name
            if invtype.groupID == const.groupBeacon:
                beacon = sm.GetService('michelle').GetItem(itemID)
                if beacon and hasattr(beacon, 'dunDescriptionID') and beacon.dunDescriptionID:
                    desc = localization.GetByMessageID(beacon.dunDescriptionID)
            locationname = None
            if invtype.categoryID == const.categoryAsteroid or invtype.groupID == const.groupHarvestableCloud:
                locationname = invtype.name
            elif itemID is not None:
                try:
                    if itemID < const.minPlayerItem or self.sr.rec is not None and self.sr.rec.singleton:
                        locationname = cfg.evelocations.Get(itemID).name
                    else:
                        locationname = invtype.name
                except KeyError:
                    locationname = invtype.name
                    sys.exc_clear()

            if locationname and locationname[0] != '@':
                capt = locationname
        elif self.sr.isFaction:
            capt = ''
            if self.sr.factioninfo is None:
                self.sr.factioninfo = cfg.factions.GetIfExists(itemID)
            desc = localization.GetByMessageID(self.sr.factioninfo.descriptionID)
        elif self.sr.isCustomsOffice:
            capt = cfg.invtypes.Get(typeID).name
            bp = sm.GetService('michelle').GetBallpark()
            slimItem = None
            if bp is not None:
                slimItem = bp.GetInvItem(itemID)
            if slimItem:
                capt = uix.GetSlimItemName(slimItem)
        actionMenu = self.GetActionMenu(itemID, typeID, self.sr.rec)
        infoicon = self.sr.headerIcon
        if actionMenu:
            self.SetHeaderIcon()
            infoicon = self.sr.headerIcon
            infoicon.state = uiconst.UI_NORMAL
            infoicon.expandOnLeft = 1
            infoicon.GetMenu = lambda *args: self.GetIconActionMenu(itemID, typeID, self.sr.rec)
            infoicon.hint = localization.GetByLabel('UI/InfoWindow/ActionMenuHint')
            self.sr.presetMenu = infoicon
            infoicon.state = uiconst.UI_NORMAL
        elif infoicon:
            infoicon.Hide()
        if onlyGetInfo:
            return (capt or '', desc or '')
        if capt:
            self.sr.captionText = uicls.EveLabelMedium(text=capt, parent=self.sr.captioncontainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
            self.sr.captioncontainer.height = 30
            if label:
                alpha = 0
                if self.sr.isSkill:
                    labelType = uicls.EveLabelSmall
                    alpha = 0.6
                else:
                    labelType = uicls.EveLabelMedium
                lbl = labelType(text=label, parent=self.sr.captioncontainer, align=uiconst.TOTOP, tabs=[84], state=uiconst.UI_DISABLED)
                if alpha != 0:
                    lbl.SetAlpha(alpha)
        return desc or ''

    def GetLocationTrace(self, itemID, trace, recursive = 0):
        parentID = sm.GetService('map').GetParent(itemID)
        if parentID != const.locationUniverse:
            parentItem = sm.GetService('map').GetItem(parentID)
            if parentItem:
                label = localization.GetByLabel('UI/InfoWindow/LocationTrace', locationType=parentItem.typeID, locationName=parentItem.itemName)
                trace += self.GetLocationTrace(parentID, [label], 1)
        if recursive:
            return trace
        else:
            trace.reverse()
            item = sm.GetService('map').GetItem(itemID)
            if item and cfg.invtypes.Get(item.typeID).groupID == const.groupSolarSystem and item.security is not None:
                sec = sm.GetService('map').GetSecurityStatus(itemID)
                label = localization.GetByLabel('UI/InfoWindow/SecurityLevelInLocationTrace', secLevel=util.FmtSystemSecStatus(sec))
                trace += [label]
            return '<br>'.join(trace)

    def OnPreviewClick(self, obj, *args):
        sm.GetService('preview').PreviewType(getattr(obj, 'typeID'))

    def OpenPortraitWnd(self, charID, *args):
        form.PortraitWindow.CloseIfOpen()
        form.PortraitWindow.Open(charID=charID)

    def OpenEntityWnd(self, entityID, *args):
        form.EntityWindow.CloseIfOpen()
        form.EntityWindow.Open(entityID=entityID)

    def GetIconActionMenu(self, itemID, typeID, rec):
        self.SaveNote(closing=0)
        return self.GetActionMenu(itemID, typeID, rec)

    def GetActionMenu(self, itemID, typeID, invItem):
        m = []
        m = sm.GetService('menu').GetMenuFormItemIDTypeID(itemID, typeID, filterFunc=[localization.GetByLabel('UI/Commands/ShowInfo')], invItem=invItem, ignoreMarketDetails=0)
        if self.sr.isCharacter or self.sr.isCorporation:
            if not util.IsNPC(itemID) and not util.IsDustCharacter(itemID):
                m.append((uiutil.MenuLabel('UI/InfoWindow/ShowContracts'), self.ShowContracts, (itemID,)))
        if self.sr.isCharacter and not util.IsNPC(itemID) and not int(sm.GetService('machoNet').GetGlobalConfig().get('hideReportBot', 0)):
            m.append((uiutil.MenuLabel('UI/InfoWindow/ReportBot'), self.ReportBot, (itemID,)))
        return m

    def ReportBot(self, itemID, *args):
        if eve.Message('ConfirmReportBot', {'name': cfg.eveowners.Get(itemID).name}, uiconst.YESNO) != uiconst.ID_YES:
            return
        if itemID == session.charid:
            raise UserError('ReportBotCannotReportYourself')
        sm.RemoteSvc('userSvc').ReportBot(itemID)
        eve.Message('BotReported', {'name': cfg.eveowners.Get(itemID).name})

    def ShowContracts(self, itemID, *args):
        sm.GetService('contracts').Show(lookup=cfg.eveowners.Get(itemID).name)

    def Browse(self, settings, *args):
        if getattr(self, 'browsing', 0):
            return
        self.browsing = 1
        typeID, itemID, parentID, historyIdx, rec, abstractinfo = settings
        self.LoadData(typeID, itemID, rec, parentID, settings, abstractinfo=abstractinfo)
        self.browsing = 0

    def ShowRelationshipIcon(self, itemID, corpid, allianceid):
        ret = sm.GetService('addressbook').GetRelationship(itemID, corpid, allianceid)
        relationships = [ret.persToCorp,
         ret.persToPers,
         ret.persToAlliance,
         ret.corpToPers,
         ret.corpToCorp,
         ret.corpToAlliance,
         ret.allianceToPers,
         ret.allianceToCorp,
         ret.allianceToAlliance]
        relationship = 0.0
        for r in relationships:
            if r != 0.0 and r > relationship or relationship == 0.0:
                relationship = r

        flag = None
        iconNum = 0
        if relationship > const.contactGoodStanding:
            flag = state.flagStandingHigh
            iconNum = 3
        elif relationship > const.contactNeutralStanding and relationship <= const.contactGoodStanding:
            flag = state.flagStandingGood
            iconNum = 3
        elif relationship < const.contactNeutralStanding and relationship >= const.contactBadStanding:
            flag = state.flagStandingBad
            iconNum = 4
        elif relationship < const.contactBadStanding:
            flag = state.flagStandingHorrible
            iconNum = 4
        if flag:
            if itemID:
                w = h = 14
                t = l = 110
                iconw = iconh = 15
            else:
                w = h = 12
                t = l = 50
                iconw = iconh = 13
            col = sm.GetService('state').GetStateFlagColor(flag)
            icon = uicls.Container(parent=self.sr.mainicon, pos=(0, 0, 10, 10), name='flag', state=uiconst.UI_DISABLED, align=uiconst.TOPRIGHT, idx=0)
            uicls.Sprite(parent=icon, pos=(0, 0, 10, 10), name='icon', state=uiconst.UI_DISABLED, rectWidth=10, rectHeight=10, texturePath='res:/UI/Texture/classes/Bracket/flagIcons.png', align=uiconst.RELATIVE)
            uicls.Fill(parent=icon)
            icon.width = w
            icon.height = h
            icon.top = t
            icon.left = l
            icon.children[1].color.SetRGB(*col)
            icon.children[0].rectLeft = iconNum * 10
            icon.children[0].width = iconw
            icon.children[0].height = iconh
            i = 0.0
            while i < 0.6:
                icon.children[1].color.a = i
                i += 0.05
                blue.pyos.synchro.SleepWallclock(30)

    def GetCorpLogo(self, corpID, parent = None):
        logo = uiutil.GetLogoIcon(itemID=corpID, parent=parent, state=uiconst.UI_NORMAL, hint=localization.GetByLabel('UI/InfoWindow/ClickForCorpInfo'), align=uiconst.TOLEFT, pos=(0, 0, 64, 64), ignoreSize=True)
        parent.height = 64
        if not util.IsNPC(corpID):
            try:
                uicls.Frame(parent=logo, color=(1.0, 1.0, 1.0, 0.1))
            except:
                pass

        logo.OnClick = (self.LoadData, const.typeCorporation, corpID)

    def Wanted(self, bounty, isChar, showSprite, isNPC = False, ownerIDs = None, hint = None):
        if not isNPC:
            self.bountyOwnerIDs = (self.sr.itemID,) if ownerIDs is None else ownerIDs
            utilMenu = uicls.PlaceBountyUtilMenu(parent=self.sr.therestcontainer, ownerID=self.sr.itemID, bountyOwnerIDs=self.bountyOwnerIDs)
        if showSprite:
            if isChar or isNPC:
                width = 128
                height = 34
                top = 2
            else:
                width = 64
                height = 17
                top = 1
            uicls.Sprite(name='wanted', parent=self.sr.mainicon, idx=0, texturePath='res:/UI/Texture/wanted.png', width=width, height=height, align=uiconst.CENTERBOTTOM, hint=localization.GetByLabel('UI/InfoWindow/BountyHint', amount=util.FmtISK(bounty, False)), top=top)
        self.bountyLabelInfo = uicls.EveLabelSmall(text='', parent=self.sr.therestcontainer, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        self.bountyLabelInfo.text = localization.GetByLabel('UI/Common/BountyAmount', bountyAmount=util.FmtISK(bounty, False))
        if hint is not None:
            self.bountyLabelInfo.hint = hint

    def OnBountyPlaced(self, ownerID):
        if ownerID == self.sr.itemID:
            bounty = self.GetBountyAmount(*self.bountyOwnerIDs)
            self.bountyLabelInfo.text = localization.GetByLabel('UI/Common/BountyAmount', bountyAmount=util.FmtISK(bounty, False))

    def GetBountyAmount(self, *ownerIDs):
        bountyAmount = sm.GetService('bountySvc').GetBounty(*ownerIDs)
        return bountyAmount

    def GetBountyAmounts(self, *ownerIDs):
        bountyAmounts = sm.GetService('bountySvc').GetBounties(*ownerIDs)
        return bountyAmounts

    def ParseTabs(self, tabs = None):
        if tabs is None:
            tabs = self.GetInfoTabs()
            self.sr.data = {}
            self.sr.dynamicTabs = []
            self.sr.infotabs = tabs
            self.sr.data['buttons'] = []
        for listtype, subtabs, tabName in tabs:
            self.sr.data[listtype] = {'name': tabName,
             'items': [],
             'subtabs': subtabs,
             'inited': 0,
             'headers': []}
            if subtabs:
                self.ParseTabs(subtabs)

    def GetInfoTabs(self):
        return [(C_ATTIBUTESTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Attributes')),
         (C_CORPMEMBERSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/CorpMembers')),
         (C_NEIGHBORSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Neighbors')),
         (C_CHILDRENTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Children')),
         (C_FITTINGTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Fitting')),
         (C_CERTPREREQTAB, [(C_SKILLSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Skills')), (C_CERTIFICATETAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Certificates'))], localization.GetByLabel('UI/InfoWindow/TabNames/Prerequisites')),
         (C_CERTRECOMMENDEDTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Recommended')),
         (C_CERTRECOMMENDEDFORTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/RecommendedFor')),
         (C_VARIATIONSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Variations')),
         (C_LEGALITYTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Legality')),
         (C_JUMPSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Jumps')),
         (C_MODULESTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Modules')),
         (C_ORBITALBODIESTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/OrbitalBodies')),
         (C_SYSTEMSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Systems')),
         (C_LOCATIONTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Location')),
         (C_AGENTINFOTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/AgentInfo')),
         (C_AGENTSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Agents')),
         (C_ROUTETAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Route')),
         (C_INSURANCETAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Insurance')),
         (C_SERVICESTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Services')),
         (C_STANDINGSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Standings')),
         (C_DECORATIONSTAB, [(C_DECORATIONCERTIFICATETAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Certificates')), (C_MEDALSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Medals')), (C_RANKSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Ranks'))], localization.GetByLabel('UI/InfoWindow/TabNames/Decorations')),
         (C_MEMBEROFCORPSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/MemberCorps')),
         (C_MARKETACTIVITYTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/MarketActivity')),
         (C_DATATAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Data')),
         (C_BILLOFMATERIALSTAB, [(C_MANUFACTURINGTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Manufacturing')),
           (C_COPYINGTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Copying')),
           (C_RESEARCHINGMATERIALEFFTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/ResearchingMaterialEfficiency')),
           (C_RESEARCHTIMEPRODTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/ResearchingTimeProductivity')),
           (C_DUPLICATINGTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Duplicating')),
           (C_INVENTIONTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Invention')),
           (C_REVERSEENGINEERINGTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/ReverseEngineering'))], localization.GetByLabel('UI/InfoWindow/TabNames/BillOfMaterials')),
         (C_EMPLOYMENTHISTORYTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/EmploymentHistory')),
         (C_ALLIANCEHISTORYTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/AllianceHistory')),
         (C_WARHISTORYTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/WarHistory')),
         (C_FUELREQTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/FuelRequirements')),
         (C_MATERIALREQTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/MaterialRequirements')),
         (C_UPGRADEMATERIALREQTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/UpgradeRequirements')),
         (C_PLANETCONTROLTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/PlanetControl')),
         (C_REACTIONTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Reaction')),
         (C_NOTESTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Notes')),
         (C_DOGMATAB, [], 'Dogma'),
         (C_MEMBERSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Members')),
         (C_UNKNOWNTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Unknown')),
         (C_HIERARCHYTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Hierarchy')),
         (C_SCHEMATICSTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/Schematics')),
         (C_PRODUCTIONINFO, [], localization.GetByLabel('UI/InfoWindow/TabNames/ProductionInfo')),
         (C_REQUIREDFORTAB, [], localization.GetByLabel('UI/InfoWindow/TabNames/RequiredFor'))]

    def _OnClose(self, *args):
        self.SaveNote(1)
        for each in ['scroll', 'notesedit', 'descedit']:
            item = getattr(self.sr, each, None)
            if item is not None and not item.destroyed:
                item.Close()
            setattr(self.sr, each, None)

        self.sr.corpinfo = None
        self.sr.allianceinfo = None
        self.sr.factioninfo = None
        self.sr.warfactioninfo = None
        self.sr.plasticinfo = None
        self.sr.voucherinfo = None
        self.sr.allianceID = None
        self.sr.corpID = None
        uicls.Window._OnClose(self, *args)
        sm.GetService('info').CloseWnd(self)

    def SaveNote(self, closing = 0, *args):
        edit = uicls.EditPlainTextCore
        if isinstance(self, edit):
            try:
                dad = self.parent.parent.parent
            except AttributeError:
                sys.exc_clear()
                return

        else:
            dad = self
        if not getattr(dad.sr, 'itemID', None):
            return
        oldnotes = getattr(dad.sr, 'oldnotes', None)
        if oldnotes is None:
            return
        if not closing:
            t = uthread.new(self.SaveNote_thread, dad, oldnotes)
            t.context = 'tactical::SaveNote'
            return
        self.SaveNote_thread(dad, oldnotes)

    def SaveNote_thread(self, dad, oldnotes):
        if dad.sr.isCharacter:
            text = dad.sr.notesedit.GetValue()
            if text is None:
                return
            if len(uiutil.StripTags(text)):
                if oldnotes != text:
                    setattr(dad.sr, 'oldnotes', text)
                    uthread.pool('infosvc::SetNote', sm.RemoteSvc('charMgr').SetNote, dad.sr.itemID, text[:5000])
            elif oldnotes:
                uthread.pool('infosvc::SetNote', sm.RemoteSvc('charMgr').SetNote, dad.sr.itemID, '')

    def SetActive(self, *args):
        uicls.Window.SetActive(self, *args)
        sm.GetService('info').OnActivateWnd(self)

    def Load(self, passedargs, *args):
        listtype = None
        if type(passedargs) == types.TupleType:
            if len(passedargs) == 2:
                listtype, funcName = passedargs
                func = getattr(self, 'Load%s' % funcName, None)
                if func:
                    func()
                elif listtype in self.sr.data:
                    self.sr.scroll.Load(contentList=self.sr.data[listtype]['items'], headers=self.sr.data[listtype]['headers'])
            elif len(passedargs) == 3:
                listtype, funcName, string = passedargs
                if listtype == 'readOnlyText':
                    self.sr.descedit.sr.window = self
                    self.sr.descedit.SetValue(string, scrolltotop=1)
                elif listtype == 'selectSubtab':
                    listtype, string, subtabgroup = passedargs
                    subtabgroup.AutoSelect()
        else:
            self.sr.scroll.Clear()
        variationBtm = getattr(self.sr, 'variationbtm', None)
        if variationBtm is not None:
            if listtype == C_VARIATIONSTAB:
                self.sr.variationbtm.state = uiconst.UI_PICKCHILDREN
            else:
                self.sr.variationbtm.Hide()

    def LoadNotes(self):
        if not self.sr.data[C_NOTESTAB]['inited']:
            itemID = self.sr.itemID
            oldnotes = ''
            if self.sr.isCharacter and itemID:
                oldnotes = sm.RemoteSvc('charMgr').GetNote(itemID)
            self.sr.notesedit.SetValue(oldnotes, scrolltotop=1)
            self.sr.oldnotes = oldnotes
            self.sr.data[C_NOTESTAB]['inited'] = 1

    def LoadEmploymentHistory(self):
        self.LoadGeneric(C_EMPLOYMENTHISTORYTAB, sm.GetService('info').GetEmploymentHistorySubContent)

    def LoadAllianceHistory(self):
        self.LoadGeneric(C_ALLIANCEHISTORYTAB, sm.GetService('info').GetAllianceHistorySubContent)

    def LoadWarHistory(self):
        self.LoadGeneric(C_WARHISTORYTAB, sm.GetService('info').GetWarHistorySubContent)

    def LoadAllianceMembers(self):
        self.LoadGeneric(C_MEMBERSTAB, sm.GetService('info').GetAllianceMembersSubContent)

    def LoadRequiredFor(self):
        self.LoadGenericType(C_REQUIREDFORTAB, sm.GetService('info').GetRequiredForSubContent)

    def LoadStandings(self):
        self.LoadGeneric(C_STANDINGSTAB, sm.GetService('info').GetStandingsHistorySubContent)

    def LoadUpgradeMaterialRequirements(self):
        if not self.sr.data[C_UPGRADEMATERIALREQTAB]['inited']:
            t = sm.GetService('godma').GetType(self.sr.typeID)
            upgradeToType = cfg.invtypes.Get(t.constructionType)
            materialList = cfg.invtypematerials.get(t.constructionType)
            menuFunc = lambda itemID = t.constructionType: sm.GetService('menu').GetMenuFormItemIDTypeID(None, itemID, ignoreMarketDetails=0)
            upgradesIntoEntry = listentry.Get('LabelTextTop', {'line': 1,
             'label': localization.GetByLabel('UI/InfoWindow/UpgradesInto'),
             'text': upgradeToType.name,
             'typeID': upgradeToType.typeID,
             'GetMenu': menuFunc})
            self.sr.data[C_UPGRADEMATERIALREQTAB]['items'].append(upgradesIntoEntry)
            self.sr.data[C_UPGRADEMATERIALREQTAB]['items'].append(listentry.Get('Divider'))
            commands = []
            for discard, resourceTypeID, quantity in materialList:
                resourceType = cfg.invtypes.Get(resourceTypeID)
                menuFunc = lambda itemID = resourceType.typeID: sm.GetService('menu').GetMenuFormItemIDTypeID(None, itemID, ignoreMarketDetails=0)
                text = localizationUtil.FormatNumeric(quantity, useGrouping=True, decimalPlaces=0)
                le = listentry.Get('LabelTextTop', {'line': 1,
                 'label': resourceType.typeName,
                 'text': text,
                 'iconID': resourceType.iconID,
                 'typeID': resourceType.typeID,
                 'GetMenu': menuFunc})
                commands.append((resourceTypeID, quantity))
                self.sr.data[C_UPGRADEMATERIALREQTAB]['items'].append(le)

            if eve.session.role & service.ROLE_GML == service.ROLE_GML:
                self.sr.data[C_UPGRADEMATERIALREQTAB]['items'].append(listentry.Get('Divider'))
                self.sr.data[C_UPGRADEMATERIALREQTAB]['items'].append(listentry.Get('Button', {'label': 'GML: Create in cargo',
                 'caption': 'Create',
                 'OnClick': sm.GetService('info').DoCreateMaterials,
                 'args': (commands, '', 1)}))
            self.sr.data[C_UPGRADEMATERIALREQTAB]['inited'] = 1
        self.sr.scroll.Load(fixedEntryHeight=27, contentList=self.sr.data[C_UPGRADEMATERIALREQTAB]['items'])

    def LoadGeneric(self, label, getSubContent):
        if not self.sr.data[label]['inited']:
            self.sr.data[label]['items'].extend(getSubContent(self.sr.itemID))
            self.sr.data[label]['inited'] = True
        self.sr.scroll.Load(fixedEntryHeight=27, contentList=self.sr.data[label]['items'])

    def LoadGenericType(self, label, getSubContent):
        if not self.sr.data[label]['inited']:
            self.sr.data[label]['items'].extend(getSubContent(self.sr.typeID))
            self.sr.data[label]['inited'] = True
        self.sr.scroll.Load(fixedEntryHeight=27, contentList=self.sr.data[label]['items'])

    def LoadFuelRequirements(self):
        if not self.sr.data[C_FUELREQTAB]['inited']:
            purposeDict = [(1, localization.GetByLabel('UI/InfoWindow/ControlTowerOnline')),
             (2, localization.GetByLabel('UI/InfoWindow/ControlTowerPower')),
             (3, localization.GetByLabel('UI/InfoWindow/ControlTowerCPU')),
             (4, localization.GetByLabel('UI/InfoWindow/ControlTowerReinforced'))]
            cycle = sm.GetService('godma').GetType(self.sr.typeID).posControlTowerPeriod
            rs = sm.RemoteSvc('posMgr').GetControlTowerFuelRequirements()
            controlTowerResourcesByTypePurpose = {}
            for entry in rs:
                if not controlTowerResourcesByTypePurpose.has_key(entry.controlTowerTypeID):
                    controlTowerResourcesByTypePurpose[entry.controlTowerTypeID] = {entry.purpose: [entry]}
                elif not controlTowerResourcesByTypePurpose[entry.controlTowerTypeID].has_key(entry.purpose):
                    controlTowerResourcesByTypePurpose[entry.controlTowerTypeID][entry.purpose] = [entry]
                else:
                    controlTowerResourcesByTypePurpose[entry.controlTowerTypeID][entry.purpose].append(entry)

            commands = []
            for purposeID, caption in purposeDict:
                self.sr.data[C_FUELREQTAB]['items'].append(listentry.Get('Header', {'label': caption}))
                if self.sr.typeID in controlTowerResourcesByTypePurpose:
                    if purposeID in controlTowerResourcesByTypePurpose[self.sr.typeID]:
                        for row in controlTowerResourcesByTypePurpose[self.sr.typeID][purposeID]:
                            extraList = []
                            if row.factionID is not None:
                                label = localization.GetByLabel('UI/InfoWindow/FactionSpace', factionName=cfg.eveowners.Get(row.factionID).name)
                                extraList.append(label)
                            if row.minSecurityLevel is not None:
                                label = localization.GetByLabel('UI/InfoWindow/SecurityLevel', secLevel=row.minSecurityLevel)
                                extraList.append(label)
                            if len(extraList):
                                t = localizationUtil.FormatGenericList(extraList)
                                extraText = localization.GetByLabel('UI/InfoWindow/IfExtraText', extraText=t)
                            else:
                                extraText = ''
                            if cycle / 3600000L == 1:
                                text = localization.GetByLabel('UI/InfoWindow/FuelRequirementPerHour', qty=row.quantity, extraText=extraText)
                            else:
                                numHours = cycle / 3600000L
                                text = localization.GetByLabel('UI/InfoWindow/FuelRequirement', qty=row.quantity, numHours=numHours, extraText=extraText)
                            resourceType = cfg.invtypes.Get(row.resourceTypeID)
                            menuFunc = lambda itemID = resourceType.typeID: sm.StartService('menu').GetMenuFormItemIDTypeID(None, itemID, ignoreMarketDetails=0)
                            le = listentry.Get('LabelTextTop', {'line': 1,
                             'label': resourceType.typeName,
                             'text': text,
                             'iconID': resourceType.iconID,
                             'typeID': resourceType.typeID,
                             'GetMenu': menuFunc})
                            commands.append((row.resourceTypeID, row.quantity))
                            self.sr.data[C_FUELREQTAB]['items'].append(le)

            if eve.session.role & service.ROLE_GML == service.ROLE_GML:
                self.sr.data[C_FUELREQTAB]['items'].append(listentry.Get('Divider'))
                self.sr.data[C_FUELREQTAB]['items'].append(listentry.Get('Button', {'label': 'GML: Create in cargo',
                 'caption': 'Create',
                 'OnClick': sm.GetService('info').DoCreateMaterials,
                 'args': (commands, '', 10)}))
            self.sr.data[C_FUELREQTAB]['inited'] = 1
        self.sr.scroll.Load(fixedEntryHeight=27, contentList=self.sr.data[C_FUELREQTAB]['items'])

    def LoadMaterialRequirements(self):
        if not self.sr.data[C_MATERIALREQTAB]['inited']:
            stationTypeID = sm.GetService('godma').GetType(self.sr.typeID).stationTypeID
            ingredients = sm.RemoteSvc('factory').GetMaterialCompositionOfItemType(stationTypeID)
            commands = []
            for material in ingredients:
                commands.append((material.typeID, material.quantity))
                text = localization.GetByLabel('UI/Common/NumUnits', numItems=material.quantity)
                materialTypeID = cfg.invtypes.Get(material.typeID)
                le = listentry.Get('LabelTextTop', {'line': 1,
                 'label': materialTypeID.name,
                 'text': text,
                 'iconID': materialTypeID.iconID,
                 'typeID': materialTypeID.typeID})
                self.sr.data[C_MATERIALREQTAB]['items'].append(le)

            self.sr.data[C_MATERIALREQTAB]['inited'] = 1
            if eve.session.role & service.ROLE_GML == service.ROLE_GML:
                self.sr.data[C_MATERIALREQTAB]['items'].append(listentry.Get('Divider'))
                self.sr.data[C_MATERIALREQTAB]['items'].append(listentry.Get('Button', {'label': 'GML: Create in cargo',
                 'caption': 'Create',
                 'OnClick': sm.GetService('info').DoCreateMaterials,
                 'args': (commands, '', 1)}))
        self.sr.scroll.Load(fixedEntryHeight=27, contentList=self.sr.data[C_MATERIALREQTAB]['items'])

    def LoadReaction(self):
        if not self.sr.data[C_REACTIONTAB]['inited']:
            res = [ (row.typeID, row.quantity) for row in cfg.invtypereactions[self.sr.typeID] if row.input == 1 ]
            prod = [ (row.typeID, row.quantity) for row in cfg.invtypereactions[self.sr.typeID] if row.input == 0 ]
            godma = sm.GetService('godma')
            commands = []
            for label, what in [(localization.GetByLabel('UI/InfoWindow/Resources'), res), (localization.GetByLabel('UI/InfoWindow/Products'), prod)]:
                self.sr.data[C_REACTIONTAB]['items'].append(listentry.Get('Header', {'label': label}))
                for typeID, quantity in what:
                    invtype = cfg.invtypes.Get(typeID)
                    amount = godma.GetType(typeID).moonMiningAmount
                    text = localization.GetByLabel('UI/Common/NumUnits', numItems=quantity * amount)
                    menuFunc = lambda typeID = typeID: sm.GetService('menu').GetMenuFormItemIDTypeID(None, typeID, ignoreMarketDetails=0, filterFunc=['UI/Commands/ShowInfo'])
                    commands.append((typeID, quantity * amount))
                    le = listentry.Get('LabelTextTop', {'line': 1,
                     'label': invtype.name,
                     'text': text,
                     'typeID': typeID,
                     'iconID': invtype.iconID,
                     'GetMenu': menuFunc})
                    self.sr.data[C_REACTIONTAB]['items'].append(le)

            if eve.session.role & service.ROLE_GML == service.ROLE_GML:
                self.sr.data[C_REACTIONTAB]['items'].append(listentry.Get('Divider'))
                self.sr.data[C_REACTIONTAB]['items'].append(listentry.Get('Button', {'label': 'GML: Create in cargo',
                 'caption': 'Create',
                 'OnClick': sm.GetService('info').DoCreateMaterials,
                 'args': (commands, '', 10)}))
            self.sr.data[C_REACTIONTAB]['inited'] = 1
        self.sr.scroll.Load(contentList=self.sr.data[C_REACTIONTAB]['items'])

    def LoadDecorations(self):
        if not self.sr.data[C_DECORATIONSTAB]['inited']:
            itemID = self.sr.itemID
            rank = sm.StartService('facwar').GetCharacterRankInfo(itemID, self.sr.corpID)
            if rank is not None:
                self.sr.data[C_RANKSTAB]['items'].append(sm.GetService('info').GetRankEntry(rank))
            certs = sm.StartService('certificates').GetCertificatesByCharacter(itemID)
            self.GetPublicCerts(certs)
            self.GetPublicMedals(itemID)
            subtabs = self.GetSubTabs(C_DECORATIONSTAB, self.sr.infotabs)
            subtabgroup = []
            sublisttype, subsubtabs = (None, None)
            for sublisttype, subsubtabs, stName in subtabs:
                subitems = self.sr.data[sublisttype]['items']
                subtabname = self.sr.data[sublisttype]['name']
                if len(subitems):
                    subtabgroup.append([subtabname,
                     self.sr.scroll,
                     self,
                     (sublisttype, None)])

            if len(subtabgroup) > 0 and self.sr.maintabs:
                _subtabs = uicls.TabGroup(name='decorations_subtabs', parent=self.sr.subcontainer, idx=1, tabs=subtabgroup, groupID='infowindow_%s' % sublisttype)
                self.sr.maintabs.sr.Get('%s_tab' % localization.GetByLabel('UI/InfoWindow/TabNames/Decorations'), None).sr.panelparent = _subtabs
                self.sr.decorations_subtabs = _subtabs
                self.sr.data[C_DECORATIONSTAB]['inited'] = 1
                return
            self.sr.decorations_subtabs = None
        if getattr(self.sr, 'decorations_subtabs', None) is not None:
            self.sr.decorations_subtabs.AutoSelect()
        else:
            self.sr.scroll.Load(contentList=[], noContentHint=localization.GetByLabel('UI/Common/NoPublicDecorations'))

    def GetSubTabs(self, listtype, infotabs):
        for _listtype, subtabs, tabName in infotabs:
            if _listtype == listtype:
                return subtabs

        return []

    def GetPublicMedals(self, charID):
        scrolllist = sm.StartService('charactersheet').GetMedalScroll(charID, True, True)
        self.sr.data[C_MEDALSTAB]['items'].extend(scrolllist)

    def GetPublicCerts(self, certs):
        allCertInfo = {}
        for cert in certs:
            allCertInfo[cert.certificateID] = cfg.certificates.Get(cert.certificateID)

        categoryData = sm.RemoteSvc('certificateMgr').GetCertificateCategories()
        scrolllist = []
        allCategories = sm.StartService('certificates').GetCategories(allCertInfo)
        for category, value in allCategories.iteritems():
            categoryObj = categoryData[category]
            data = {'GetSubContent': self.GetCertSubContent,
             'label': localization.GetByMessageID(categoryObj.categoryNameID),
             'groupItems': value,
             'id': ('infoCertGroups_cat', category),
             'sublevel': 0,
             'showlen': 0,
             'showicon': 'hide',
             'cat': category,
             'state': 'locked'}
            scrolllist.append((data.get('label', ''), listentry.Get('Group', data)))

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        self.sr.data[C_DECORATIONCERTIFICATETAB]['items'].extend(scrolllist)

    def GetCertSubContent(self, dataX, *args):
        scrolllist = []
        dataWnd = uicls.Window.GetIfOpen(windowID=unicode(dataX.id))
        if not dataWnd:
            for entry in self.sr.scroll.GetNodes():
                if entry.__guid__ != 'listentry.Group' or entry.id == dataX.id:
                    continue
                if entry.open:
                    if entry.panel:
                        entry.panel.Toggle()
                    else:
                        uicore.registry.SetListGroupOpenState(entry.id, 0)
                        entry.scroll.PrepareSubContent(entry)

        entries = self.GetCertEntries(dataX)
        return entries

    def GetCertEntries(self, data, *args):
        scrolllist = []
        highestEntries = sm.StartService('certificates').GetHighestLevelOfClass(data.groupItems)
        for each in highestEntries:
            certEntry = sm.StartService('info').GetCertEntry(each)
            scrolllist.append((certEntry.get('label', ''), listentry.Get('CertEntry', certEntry)))

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        return scrolllist

    def LoadProcessPinSchematics(self):
        if not self.sr.data[C_SCHEMATICSTAB]['inited']:
            schematicItems = []
            for schematicRow in cfg.schematicsByPin.get(self.sr.typeID, []):
                schematic = cfg.schematics.Get(schematicRow.schematicID)
                abstractinfo = util.KeyVal(schematicName=schematic.schematicName, schematicID=schematic.schematicID, cycleTime=schematic.cycleTime)
                le = listentry.Get('Item', {'itemID': None,
                 'typeID': const.typeSchematic,
                 'label': schematic.schematicName,
                 'getIcon': 0,
                 'abstractinfo': abstractinfo})
                schematicItems.append(le)

            self.sr.data[C_SCHEMATICSTAB]['items'] = schematicItems
            self.sr.data[C_SCHEMATICSTAB]['inited'] = 1
        self.sr.scroll.Load(contentList=self.sr.data[C_SCHEMATICSTAB]['items'])

    def LoadCommodityProductionInfo(self):
        if not self.sr.data[C_PRODUCTIONINFO]['inited']:
            schematicItems = []
            producingStructureLines = []
            producingSchematicLines = []
            consumingSchematicLines = []
            for typeRow in cfg.schematicsByType.get(self.sr.typeID, []):
                data = util.KeyVal()
                if typeRow.schematicID not in cfg.schematics:
                    self.LogWarn('CONTENT ERROR - Schematic ID', typeRow.schematicID, 'is in type map but not in main schematics list')
                    continue
                schematic = cfg.schematics.Get(typeRow.schematicID)
                abstractinfo = util.KeyVal(schematicName=schematic.schematicName, schematicID=schematic.schematicID, typeID=typeRow.typeID, isInput=typeRow.isInput, quantity=typeRow.quantity, cycleTime=schematic.cycleTime)
                le = listentry.Get('Item', {'itemID': None,
                 'typeID': const.typeSchematic,
                 'label': schematic.schematicName,
                 'getIcon': 0,
                 'abstractinfo': abstractinfo})
                if typeRow.isInput:
                    consumingSchematicLines.append(le)
                else:
                    producingSchematicLines.append(le)

            godma = sm.GetService('godma')
            for pinType in cfg.typesByGroups.get(const.groupExtractorPins, []):
                pinType = cfg.invtypes.Get(pinType.typeID)
                pinProducedType = godma.GetTypeAttribute(pinType.typeID, const.attributeHarvesterType)
                if pinProducedType and pinProducedType == self.sr.typeID:
                    producingStructureLines.append(listentry.Get('Item', {'itemID': None,
                     'typeID': pinType.typeID,
                     'label': pinType.typeName,
                     'getIcon': 0}))

            if len(producingSchematicLines) > 0:
                schematicItems.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/SchematicsProducedBy')}))
                schematicItems.extend(producingSchematicLines)
            if len(producingStructureLines) > 0:
                schematicItems.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/StructuresProducedBy')}))
                schematicItems.extend(producingStructureLines)
            if len(consumingSchematicLines) > 0:
                schematicItems.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/SchematicsConsuming')}))
                schematicItems.extend(consumingSchematicLines)
            self.sr.data[C_PRODUCTIONINFO]['items'] = schematicItems
            self.sr.data[C_PRODUCTIONINFO]['inited'] = 1
        self.sr.scroll.Load(contentList=self.sr.data[C_PRODUCTIONINFO]['items'])

    def LoadPlanetControlInfo(self):
        controlLabel = C_PLANETCONTROLTAB
        if not self.sr.data[controlLabel]['inited']:
            planetID = self.sr.itemID
            lines = []
            bp = sm.GetService('michelle').GetBallpark()
            planetItem = bp.GetInvItem(planetID) if bp is not None else None
            controller = planetItem.ownerID if planetItem is not None else None
            if controller is not None:
                lines.append(listentry.Get('OwnerWithIconEntry', {'label': localization.GetByLabel('UI/InfoWindow/Sovereign'),
                 'line': 1,
                 'ownerID': controller}))
            requirementsText = localization.GetByLabel('UI/InfoWindow/PlanetControlRequirementHint')
            lines.append(listentry.Get('Generic', {'label': requirementsText,
             'maxLines': None}))
            self.sr.data[controlLabel]['items'] = lines
            self.sr.data[controlLabel]['inited'] = 1
        self.sr.scroll.Load(contentList=self.sr.data[controlLabel]['items'], noContentHint=localization.GetByLabel('UI/InfoWindow/PlanetNotContested'))


class SkillTreeEntry(listentry.Text):
    __guid__ = 'listentry.SkillTreeEntry'

    def Startup(self, *args):
        listentry.Text.Startup(self, args)
        self.sr.text.color.SetRGB(1.0, 1.0, 1.0, 0.75)
        self.sr.have = uicls.Icon(parent=self, left=5, top=0, height=16, width=16, align=uiconst.CENTERLEFT)

    def Load(self, args):
        listentry.Text.Load(self, args)
        data = self.sr.node
        if data.skills is not None:
            if data.typeID in data.skills:
                if data.skills[data.typeID].skillLevel >= data.lvl:
                    self.sr.have.LoadIcon('ui_38_16_193')
                    self.sr.have.hint = localization.GetByLabel('UI/InfoWindow/TrainedAndOfRequiredLevel')
                else:
                    self.sr.have.LoadIcon('ui_38_16_195')
                    self.sr.have.hint = localization.GetByLabel('UI/InfoWindow/TrainedButNotOfRequiredLevel')
            else:
                self.sr.have.LoadIcon('ui_38_16_194')
                self.sr.have.hint = localization.GetByLabel('UI/InfoWindow/NotTrained')
        else:
            self.sr.have.LoadIcon('ui_38_16_194')
            self.sr.have.hint = localization.GetByLabel('UI/InfoWindow/NotTrained')
        self.sr.have.left = 15 * data.indent - 11
        self.sr.text.left = 15 * data.indent + 5

    def GetMenu(self):
        m = []
        data = self.sr.node
        if data is not None:
            if data.typeID:
                if data.skills is not None and data.typeID in data.skills:
                    skill = sm.StartService('skills').GetMySkillsFromTypeID(data.typeID)
                    if skill is not None:
                        m += sm.GetService('skillqueue').GetAddMenuForSkillEntries(skill)
                m += sm.StartService('menu').GetMenuFormItemIDTypeID(None, data.typeID, ignoreMarketDetails=0)
        return m


class EntityWindow(uicls.Window):
    __guid__ = 'form.EntityWindow'
    default_windowID = 'EntityWindow'

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        entityID = attributes.entityID
        self.entityID = entityID
        self.photoSize = 128
        self.width = self.photoSize + 2 * const.defaultPadding
        self.height = self.width + 20
        self.SetMinSize([self.width, self.height])
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        self.picParent = uicls.Container(name='picpar', parent=self.sr.main, align=uiconst.TOALL, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.Load()

    def Load(self):
        self.SetCaption(cfg.eveowners.Get(self.entityID).name)
        uiutil.GetLogoIcon(self.entityID, parent=self.picParent, acceptNone=False, align=uiconst.TOPRIGHT, height=128, width=128, state=uiconst.UI_NORMAL)


class PortraitWindow(uicls.Window):
    __guid__ = 'form.PortraitWindow'
    default_windowID = 'PortraitWindow'

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        charID = attributes.charID
        self.charID = charID
        self.photoSize = 512
        self.width = self.photoSize + 2 * const.defaultPadding
        self.height = self.width + 46
        self.SetMinSize([self.width, self.height])
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        caption = localization.GetByLabel('UI/Preview/ViewFullBody')
        btns = [[caption,
          self.SwitchToFullBody,
          (),
          81,
          1,
          1,
          0]]
        btnGroup = uicls.ButtonGroup(btns=btns, parent=self.sr.main, idx=0)
        self.switchBtn = btnGroup.GetBtnByLabel(caption)
        self.picParent = uicls.Container(name='picpar', parent=self.sr.main, align=uiconst.TOALL, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.pic = uicls.Sprite(parent=self.picParent, align=uiconst.TOALL)
        self.pic.GetMenu = self.PicMenu
        self.Load(charID)
        previewWnd = form.PreviewWnd.GetIfOpen()
        if previewWnd and previewWnd.previewingWhat == 'character':
            previewWnd.CloseByUser()

    def Load(self, charID):
        charName = cfg.eveowners.Get(charID).name
        caption = localization.GetByLabel('UI/InfoWindow/PortraitCaption', character=charID)
        self.SetCaption(caption)
        sm.GetService('photo').GetPortrait(charID, self.photoSize, self.pic)

    def PicMenu(self, *args):
        m = []
        if not util.IsDustCharacter(self.charID):
            m.append((uiutil.MenuLabel('UI/Commands/CapturePortrait'), sm.StartService('photo').SavePortraits, [self.charID]))
        m.append((uiutil.MenuLabel('/Carbon/UI/Common/Close'), self.CloseByUser))
        return m

    def SwitchToFullBody(self):
        try:
            self.switchBtn.Disable()
            wnd = sm.GetService('preview').PreviewCharacter(self.charID)
        finally:
            self.switchBtn.Enable()

        if wnd:
            self.CloseByUser()


class InfoScroll(uicls.Scroll):
    __guid__ = 'uicls.InfoScroll'

    def Load(self, contentList = [], *args, **kwargs):
        for child in self.children:
            if child.name == 'skillTimeLabel':
                child.Close()

        uicls.Scroll.Load(self, contentList=contentList, *args, **kwargs)
        skillsList = False
        skills = {}
        for entry in contentList:
            if entry.__guid__ == 'listentry.SkillTreeEntry':
                skillsList = True
                if entry.typeID in skills:
                    if entry.lvl > skills[entry.typeID]:
                        skills[entry.typeID] = entry.lvl
                else:
                    skills[entry.typeID] = entry.lvl

        if skillsList:
            totalTime = 0
            for skill in skills:
                mySkill = sm.StartService('skills').GetMySkillsFromTypeID(skill)
                mySkillLevel = 0
                if mySkill is not None:
                    mySkillLevel = mySkill.skillLevel
                for i in xrange(int(mySkillLevel) + 1, int(skills[skill]) + 1):
                    timeLeft = sm.StartService('info').GetRawTrainingTimeForSkillLevel(skill, i)
                    totalTime += timeLeft

            totalTimeText = localization.GetByLabel('UI/SkillQueue/Skills/TotalTrainingTime', timeLeft=long(totalTime))
            if totalTime > 0:
                uicls.EveLabelMediumBold(parent=self, name='skillTimeLabel', align=uiconst.TOTOP, text=totalTimeText, idx=0, padTop=2, padBottom=2)


C_ATTIBUTESTAB = 1
C_CORPMEMBERSTAB = 2
C_NEIGHBORSTAB = 3
C_CHILDRENTAB = 4
C_FITTINGTAB = 5
C_CERTPREREQTAB = 6
C_SKILLSTAB = 7
C_CERTIFICATETAB = 8
C_CERTRECOMMENDEDTAB = 9
C_CERTRECOMMENDEDFORTAB = 10
C_VARIATIONSTAB = 11
C_LEGALITYTAB = 13
C_JUMPSTAB = 14
C_MODULESTAB = 15
C_ORBITALBODIESTAB = 16
C_SYSTEMSTAB = 17
C_LOCATIONTAB = 18
C_AGENTINFOTAB = 19
C_AGENTSTAB = 20
C_ROUTETAB = 21
C_INSURANCETAB = 22
C_SERVICESTAB = 23
C_STANDINGSTAB = 24
C_DECORATIONSTAB = 25
C_DECORATIONCERTIFICATETAB = 26
C_MEDALSTAB = 27
C_RANKSTAB = 28
C_MEMBEROFCORPSTAB = 29
C_MARKETACTIVITYTAB = 30
C_DATATAB = 31
C_BILLOFMATERIALSTAB = 32
C_MANUFACTURINGTAB = 33
C_COPYINGTAB = 34
C_RESEARCHINGMATERIALEFFTAB = 35
C_RESEARCHTIMEPRODTAB = 36
C_DUPLICATINGTAB = 37
C_INVENTIONTAB = 38
C_REVERSEENGINEERINGTAB = 39
C_EMPLOYMENTHISTORYTAB = 40
C_ALLIANCEHISTORYTAB = 53
C_FUELREQTAB = 41
C_MATERIALREQTAB = 42
C_UPGRADEMATERIALREQTAB = 43
C_PLANETCONTROLTAB = 44
C_REACTIONTAB = 45
C_NOTESTAB = 46
C_DOGMATAB = 47
C_MEMBERSTAB = 48
C_UNKNOWNTAB = 49
C_HIERARCHYTAB = 50
C_SCHEMATICSTAB = 51
C_PRODUCTIONINFO = 52
C_WARHISTORYTAB = 54
C_REQUIREDFORTAB = 55