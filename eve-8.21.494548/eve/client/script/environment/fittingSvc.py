#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/fittingSvc.py
import service
import util
import uthread
import blue
import re
import listentry
import form
import uix
import sys
import localization
from collections import defaultdict
import uiconst
CORP_FITTINGS_LOCAL_CACHE_TIME = 10 * const.MIN

class fittingSvc(service.Service):
    __guid__ = 'svc.fittingSvc'
    __exportedcalls__ = {'GetFittingDictForActiveShip': [],
     'ChangeOwner': []}
    __startupdependencies__ = ['settings', 'invCache']
    __notifyevents__ = ['OnSkillFinished']

    def __init__(self):
        service.Service.__init__(self)
        self.fittings = {}
        self.hasSkillByFittingID = {}

    def Run(self, ms = None):
        self.state = service.SERVICE_RUNNING
        self.fittings = {}
        self.corpFittingTime = 0

    def GetFittingMgr(self, ownerID):
        if ownerID == session.charid:
            return sm.RemoteSvc('charFittingMgr')
        if ownerID == session.corpid:
            return sm.RemoteSvc('corpFittingMgr')
        raise RuntimeError("Can't find the fitting manager you're asking me to get. ownerID:", ownerID)

    def HasLegacyClientFittings(self):
        if len(settings.char.generic.Get('fittings', {})) > 0:
            return True
        return False

    def GetLegacyClientFittings(self):
        return settings.char.generic.Get('fittings', {})

    def DeleteLegacyClientFittings(self):
        settings.char.generic.Set('fittings', None)

    def GetFittingDictForActiveShip(self):
        shipID = util.GetActiveShip()
        shipInv = self.invCache.GetInventoryFromId(shipID, locationID=session.stationid2)
        fitData = self.CreateFittingData(shipInv.List())
        return (shipInv.GetItem().typeID, fitData)

    def CreateFittingData(self, items):
        fitData = []
        dronesByType = defaultdict(int)
        chargesByType = defaultdict(int)
        iceByType = defaultdict(int)
        for item in items:
            if cfg.IsShipFittingFlag(item.flagID) and item.categoryID in (const.categoryModule, const.categorySubSystem):
                fitData.append((int(item.typeID), int(item.flagID), 1))
            elif item.categoryID == const.categoryDrone and item.flagID == const.flagDroneBay:
                typeID = item.typeID
                dronesByType[typeID] += item.stacksize
            elif item.categoryID == const.categoryCharge and item.flagID == const.flagCargo:
                typeID = item.typeID
                chargesByType[typeID] += item.stacksize
            elif hasattr(item, 'groupID') and item.groupID == const.groupIceProduct and item.flagID == const.flagCargo:
                typeID = item.typeID
                iceByType[typeID] += item.stacksize

        flag = const.flagDroneBay
        for drone, quantity in dronesByType.iteritems():
            fitData.append((int(drone), int(flag), int(quantity)))

        flag = const.flagCargo
        for charge, quantity in chargesByType.iteritems():
            fitData.append((int(charge), int(flag), int(quantity)))

        flag = const.flagCargo
        for ice, quantity in iceByType.iteritems():
            fitData.append((int(ice), int(flag), int(quantity)))

        return fitData

    def DisplayFittingFromItems(self, shipTypeID, items):
        newItems = []
        for item in items:
            if not hasattr(item, 'flagID'):
                item.flagID = item.flag
            if not hasattr(item, 'stacksize'):
                item.stacksize = item.qtyDropped + item.qtyDestroyed
            item.categoryID = cfg.invtypes.Get(item.typeID).categoryID
            newItems.append(item)

        fitData = self.CreateFittingData(newItems)
        fitting = util.KeyVal()
        fitting.shipTypeID = shipTypeID
        fitting.name = cfg.invtypes.Get(shipTypeID).typeName
        fitting.ownerID = None
        fitting.fittingID = None
        fitting.description = ''
        fitting.fitData = fitData
        self.DisplayFitting(fitting)

    def PersistFitting(self, ownerID, name, description, fit = None):
        if name is None or name.strip() == '':
            raise UserError('FittingNeedsToHaveAName')
        name = name.strip()
        fitting = util.KeyVal()
        fitting.name = name[:const.maxLengthFittingName]
        fitting.description = description[:const.maxLengthFittingDescription]
        self.PrimeFittings(ownerID)
        if ownerID == session.corpid:
            maxFittings = const.maxCorpFittings
        else:
            maxFittings = const.maxCharFittings
        if len(self.fittings[ownerID]) >= maxFittings:
            owner = cfg.eveowners.Get(ownerID).ownerName
            raise UserError('OwnerMaxFittings', {'owner': owner,
             'maxFittings': maxFittings})
        if fit is None:
            fitting.shipTypeID, fitting.fitData = self.GetFittingDictForActiveShip()
        else:
            fitting.shipTypeID, fitting.fitData = fit
        self.VerifyFitting(fitting)
        fitting.ownerID = ownerID
        fitting.fittingID = self.GetFittingMgr(ownerID).SaveFitting(ownerID, fitting)
        self.fittings[ownerID][fitting.fittingID] = fitting
        self.UpdateFittingWindow()
        return fitting

    def PersistManyFittings(self, ownerID, fittings):
        if ownerID == session.corpid:
            maxFittings = const.maxCorpFittings
        else:
            maxFittings = const.maxCharFittings
        self.PrimeFittings(ownerID)
        if len(self.fittings[ownerID]) + len(fittings) > maxFittings:
            owner = cfg.eveowners.Get(ownerID).ownerName
            raise UserError('OwnerMaxFittings', {'owner': owner,
             'maxFittings': maxFittings})
        fittingsToSave = {}
        tmpFittingID = -1
        for fitt in fittings:
            if fitt.name is None or fitt.name.strip() == '':
                raise UserError('FittingNeedsToHaveAName')
            fitting = util.KeyVal()
            fitting.fittingID = tmpFittingID
            fitting.name = fitt.name.strip()[:const.maxLengthFittingName]
            fitting.description = fitt.description[:const.maxLengthFittingDescription]
            fitting.shipTypeID = fitt.shipTypeID
            fitting.fitData = fitt.fitData
            self.VerifyFitting(fitting)
            fitting.ownerID = ownerID
            fittingsToSave[tmpFittingID] = fitting
            tmpFittingID -= 1

        newFittingIDs = self.GetFittingMgr(ownerID).SaveManyFittings(ownerID, fittingsToSave)
        for row in newFittingIDs:
            self.fittings[ownerID][row.realFittingID] = fittingsToSave[row.tempFittingID]
            self.fittings[ownerID][row.realFittingID].fittingID = row.realFittingID

        self.UpdateFittingWindow()
        return fitting

    def VerifyFitting(self, fitting):
        if fitting.name.find('@@') != -1 or fitting.description.find('@@') != -1:
            raise UserError('InvalidFittingInvalidCharacter')
        if fitting.shipTypeID is None:
            raise UserError('InvalidFittingDataTypeID', {'typeName': fitting.shipTypeID})
        shipType = cfg.invtypes.Get(fitting.shipTypeID, None)
        if shipType is None:
            raise UserError('InvalidFittingDataTypeID', {'typeName': fitting.shipTypeID})
        if cfg.invtypes.Get(fitting.shipTypeID).categoryID != const.categoryShip:
            raise UserError('InvalidFittingDataShipNotShip', {'typeName': shipType.typeName})
        if len(fitting.fitData) == 0:
            raise UserError('ParseFittingFittingDataEmpty')
        for typeID, flag, qty in fitting.fitData:
            type = cfg.invtypes.GetIfExists(typeID)
            if type is None:
                raise UserError('InvalidFittingDataTypeID', {'typeID': typeID})
            try:
                int(flag)
            except TypeError:
                raise UserError('InvalidFittingDataInvalidFlag', {'type': type.typeID})

            if not (cfg.IsShipFittingFlag(flag) or flag in (const.flagDroneBay, const.flagCargo)):
                raise UserError('InvalidFittingDataInvalidFlag', {'type': type.typeID})
            try:
                int(qty)
            except TypeError:
                raise UserError('InvalidFittingDataInvalidQuantity', {'type': type.typeID})

            if qty == 0:
                raise UserError('InvalidFittingDataInvalidQuantity', {'type': type.typeID})

        return True

    def GetFittings(self, ownerID):
        self.PrimeFittings(ownerID)
        return self.fittings[ownerID]

    def PrimeFittings(self, ownerID):
        if ownerID not in self.fittings or ownerID == session.corpid and self.corpFittingTime < blue.os.GetWallclockTime():
            self.fittings[ownerID] = self.GetFittingMgr(ownerID).GetFittings(ownerID)
            if ownerID == session.corpid:
                self.corpFittingTime = blue.os.GetWallclockTime() + CORP_FITTINGS_LOCAL_CACHE_TIME

    def DeleteFitting(self, ownerID, fittingID):
        self.LogInfo('deleting fitting', fittingID, 'from owner', ownerID)
        self.GetFittingMgr(ownerID).DeleteFitting(ownerID, fittingID)
        if ownerID in self.fittings and fittingID in self.fittings[ownerID]:
            del self.fittings[ownerID][fittingID]
        self.UpdateFittingWindow()

    def LoadFitting(self, ownerID, fittingID):
        if session.stationid is None:
            raise UserError('CannotLoadFittingInSpace')
        fitting = self.fittings.get(ownerID, {}).get(fittingID, None)
        if fitting is None:
            raise UserError('FittingDoesNotExist')
        itemTypes = defaultdict(lambda : 0)
        modulesByFlag = {}
        dronesByType = {}
        chargesByType = {}
        iceByType = {}
        shipInv = self.invCache.GetInventoryFromId(util.GetActiveShip(), locationID=session.stationid2)
        rigsToFit = False
        fitRigs = False
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        for typeID, flag, qty in fitting.fitData:
            try:
                dogmaLocation.CheckSkillRequirementsForType(typeID, 'FittingHasSkillPrerequisites')
            except UserError:
                continue

            if cfg.IsShipFittingFlag(flag):
                modulesByFlag[flag] = typeID
                if const.flagRigSlot0 <= flag <= const.flagRigSlot7:
                    rigsToFit = True
            elif flag == const.flagDroneBay:
                dronesByType[typeID] = qty
            elif flag == const.flagCargo:
                groupID = cfg.invtypes.Get(typeID).groupID
                if groupID == const.groupIceProduct:
                    iceByType[typeID] = qty
                else:
                    chargesByType[typeID] = qty
            else:
                self.LogError('LoadFitting::flag neither fitting nor drone bay', typeID, flag)
            skipType = False
            for item in shipInv.List(flag):
                if item.typeID == typeID:
                    itemQty = item.stacksize
                    if itemQty == qty:
                        skipType = True
                        break
                    else:
                        qty -= itemQty

            if skipType:
                continue
            itemTypes[typeID] += qty

        if rigsToFit:
            if self.HasRigFitted():
                eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Fitting/ShipHasRigsAlready')})
            elif eve.Message('FitRigs', {}, uiconst.YESNO) == uiconst.ID_YES:
                fitRigs = True
        inv = self.invCache.GetInventory(const.containerHangar)
        itemsToFit = defaultdict(set)
        for item in inv.List():
            if item.typeID in itemTypes:
                qtyNeeded = itemTypes[item.typeID]
                if qtyNeeded == 0:
                    continue
                quantityToTake = min(item.stacksize, qtyNeeded)
                itemsToFit[item.typeID].add(item.itemID)
                itemTypes[item.typeID] -= quantityToTake

        failedToLoad = shipInv.FitFitting(util.GetActiveShip(), itemsToFit, session.stationid2, modulesByFlag, dronesByType, chargesByType, iceByType, fitRigs)
        for typeID, qty in failedToLoad:
            itemTypes[typeID] += qty

        text = ''
        for typeID, qty in itemTypes.iteritems():
            if qty > 0:
                text += '%sx %s<br>' % (qty, cfg.invtypes.Get(typeID).typeName)

        if text != '':
            text = localization.GetByLabel('UI/Fitting/MissingItems', types=text)
            eve.Message('CustomInfo', {'info': text})

    def HasRigFitted(self):
        shipInv = self.invCache.GetInventoryFromId(util.GetActiveShip(), locationID=session.stationid2)
        for item in shipInv.List():
            if const.flagRigSlot0 <= item.flagID <= const.flagRigSlot7:
                return True

        return False

    def UpdateFittingWindow(self):
        wnd = form.FittingMgmt.GetIfOpen()
        if wnd is not None:
            wnd.DrawFittings()

    def ChangeNameAndDescription(self, fittingID, ownerID, name, description):
        if name is None or name.strip() == '':
            raise UserError('FittingNeedsToHaveAName')
        name = name.strip()
        fittings = self.GetFittings(ownerID)
        if fittingID in fittings:
            fitting = fittings[fittingID]
            if name != fitting.name or description != fitting.description:
                if name.find('@@') != -1 or description.find('@@') != -1:
                    raise UserError('InvalidFittingInvalidCharacter')
                self.GetFittingMgr(ownerID).UpdateNameAndDescription(fittingID, ownerID, name, description)
                self.fittings[ownerID][fittingID].name = name
                self.fittings[ownerID][fittingID].description = description
        self.UpdateFittingWindow()

    def GetFitting(self, ownerID, fittingID):
        self.PrimeFittings(ownerID)
        if fittingID in self.fittings[ownerID]:
            return self.fittings[ownerID][fittingID]

    def ChangeOwner(self, ownerID, fittingID, newOwnerID):
        fitting = self.GetFitting(ownerID, fittingID)
        if fitting is None:
            raise UserError('FittingDoesNotExistAnymore')
        fit = (fitting.shipTypeID, fitting.fitData)
        if fitting.name is None or fitting.name.strip() == '':
            raise UserError('FittingNeedsToHaveAName')
        return self.PersistFitting(newOwnerID, fitting.name.strip(), fitting.description, fit=fit)

    def CheckFittingExist(self, ownerID, shipTypeID, fitData):
        fittings = self.GetFittings(ownerID)
        fittingExists = False
        for fitting in fittings.itervalues():
            if fitting.shipTypeID != shipTypeID:
                continue
            if fitting.fitData != fitData:
                continue
            fittingExists = True

        return fittingExists

    def DisplayFittingFromString(self, fittingString):
        fitting, truncated = self.GetFittingFromString(fittingString)
        if fitting == -1:
            raise UserError('FittingInvalidForViewing')
        self.DisplayFitting(fitting, truncated=truncated)

    def DisplayFitting(self, fitting, truncated = False):
        if uicore.uilib.Key(uiconst.VK_SHIFT):
            fittingsList = fittingString.split(';')
            fittingsList.sort()
            newFittingStr = '__'.join(fittingsList).replace(':', '_')
            windowID = 'ViewFitting_%s' % newFittingStr
        else:
            windowID = 'ViewFitting'
        wnd = form.ViewFitting.GetIfOpen(windowID=windowID)
        if wnd:
            wnd.ReloadWnd(windowID=windowID, fitting=fitting, truncated=truncated)
        else:
            form.ViewFitting.Open(windowID=windowID, fitting=fitting, truncated=truncated)

    def GetStringForFitting(self, fitting):
        typesByFlag = {}
        drones = []
        charges = []
        ice = []
        for typeID, flag, qty in fitting.fitData:
            categoryID = cfg.invtypes.Get(typeID).categoryID
            groupID = cfg.invtypes.Get(typeID).groupID
            if categoryID in (const.categoryModule, const.categorySubSystem):
                typesByFlag[flag] = typeID
            elif categoryID == const.categoryDrone:
                drones.append((typeID, qty))
            elif categoryID == const.categoryCharge:
                charges.append((typeID, qty))
            elif groupID == const.groupIceProduct:
                ice.append((typeID, qty))

        typesDict = {}
        for flag, typeID in typesByFlag.iteritems():
            if typeID not in typesDict:
                typesDict[typeID] = 0
            typesDict[typeID] += 1

        ret = str(fitting.shipTypeID) + ':'
        for typeID, qty in typesDict.iteritems():
            subString = str(typeID) + ';' + str(qty) + ':'
            ret += subString

        for typeID, qty in drones:
            subString = str(typeID) + ';' + str(qty) + ':'
            ret += subString

        for typeID, qty in charges:
            subString = str(typeID) + ';' + str(qty) + ':'
            ret += subString

        for typeID, qty in ice:
            subString = str(typeID) + ';' + str(qty) + ':'
            ret += subString

        ret = ret.strip(':')
        ret += '::'
        return ret

    def GetFittingFromString(self, fittingString):
        effectSlots = {const.effectHiPower: const.flagHiSlot0,
         const.effectMedPower: const.flagMedSlot0,
         const.effectLoPower: const.flagLoSlot0,
         const.effectRigSlot: const.flagRigSlot0,
         const.effectSubSystem: const.flagSubSystemSlot0}
        truncated = False
        if not fittingString.endswith('::'):
            truncated = True
            fittingString = fittingString[:fittingString.rfind(':')]
        data = fittingString.split(':')
        fitting = util.KeyVal()
        fitData = []
        for line in data:
            typeInfo = line.split(';')
            if line == '':
                continue
            if len(typeInfo) == 1:
                fitting.shipTypeID = int(typeInfo[0])
                continue
            typeID, qty = typeInfo
            typeID, qty = int(typeID), int(qty)
            powerEffectID = sm.GetService('godma').GetPowerEffectForType(typeID)
            if powerEffectID is not None:
                startSlot = effectSlots[powerEffectID]
                for flag in xrange(startSlot, startSlot + qty):
                    fitData.append((typeID, flag, 1))

                effectSlots[powerEffectID] = flag + 1
            else:
                categoryID = cfg.invtypes.Get(typeID).categoryID
                groupID = cfg.invtypes.Get(typeID).groupID
                if categoryID == const.categoryDrone:
                    fitData.append((typeID, const.flagDroneBay, qty))
                elif categoryID == const.categoryCharge:
                    fitData.append((typeID, const.flagCargo, qty))
                elif groupID == const.groupIceProduct:
                    fitData.append((typeID, const.flagCargo, qty))
                else:
                    continue

        shipName = cfg.invtypes.Get(fitting.shipTypeID).typeName
        fitting.name = shipName
        fitting.ownerID = None
        fitting.fittingID = None
        fitting.description = ''
        fitting.fitData = fitData
        return (fitting, truncated)

    def GetFittingInfoScrollList(self, fitting):
        scrolllist = []
        typesByRack = self.GetTypesByRack(fitting)
        for key, effectID in [('hiSlots', const.effectHiPower),
         ('medSlots', const.effectMedPower),
         ('lowSlots', const.effectLoPower),
         ('rigSlots', const.effectRigSlot),
         ('subSystems', const.effectSubSystem)]:
            slots = typesByRack[key]
            if len(slots) > 0:
                label = cfg.dgmeffects.Get(effectID).displayName
                scrolllist.append(listentry.Get('Header', {'label': label}))
                for type, qty in slots.iteritems():
                    data = util.KeyVal()
                    data.typeID = type
                    data.showinfo = 1
                    data.label = str(util.FmtAmt(qty)) + 'x ' + cfg.invtypes.Get(type).typeName
                    scrolllist.append(listentry.Get('FittingModuleEntry', data=data))

        charges = typesByRack['charges']
        if len(charges) > 0:
            scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Generic/Charges')}))
            for type, qty in charges.iteritems():
                data = util.KeyVal()
                data.typeID = type
                data.showinfo = 1
                data.label = str(util.FmtAmt(qty)) + 'x ' + cfg.invtypes.Get(type).typeName
                scrolllist.append(listentry.Get('FittingModuleEntry', data=data))

        ice = typesByRack['ice']
        if len(ice) > 0:
            scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Inflight/MoonMining/Processes/Fuel')}))
            for type, qty in ice.iteritems():
                data = util.KeyVal()
                data.typeID = type
                data.showinfo = 1
                data.label = str(util.FmtAmt(qty)) + 'x ' + cfg.invtypes.Get(type).typeName
                scrolllist.append(listentry.Get('FittingModuleEntry', data=data))

        drones = typesByRack['drones']
        if len(drones) > 0:
            scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Drones/Drones')}))
            for type, qty in drones.iteritems():
                data = util.KeyVal()
                data.typeID = type
                data.showinfo = 1
                data.label = str(util.FmtAmt(qty)) + 'x ' + cfg.invtypes.Get(type).typeName
                scrolllist.append(listentry.Get('FittingModuleEntry', data=data))

        return scrolllist

    def GetTypesByRack(self, fitting):
        ret = {'hiSlots': {},
         'medSlots': {},
         'lowSlots': {},
         'rigSlots': {},
         'subSystems': {},
         'charges': {},
         'drones': {},
         'ice': {}}
        for typeID, flag, qty in fitting.fitData:
            if cfg.invtypes.Get(typeID).categoryID == const.categoryCharge:
                ret['charges'][typeID] = qty
            elif cfg.invtypes.Get(typeID).groupID == const.groupIceProduct:
                ret['ice'][typeID] = qty
            elif flag >= const.flagHiSlot0 and flag <= const.flagHiSlot7:
                if typeID not in ret['hiSlots']:
                    ret['hiSlots'][typeID] = 0
                ret['hiSlots'][typeID] += 1
            elif flag >= const.flagMedSlot0 and flag <= const.flagMedSlot7:
                if typeID not in ret['medSlots']:
                    ret['medSlots'][typeID] = 0
                ret['medSlots'][typeID] += 1
            elif flag >= const.flagLoSlot0 and flag <= const.flagLoSlot7:
                if typeID not in ret['lowSlots']:
                    ret['lowSlots'][typeID] = 0
                ret['lowSlots'][typeID] += 1
            elif flag >= const.flagRigSlot0 and flag <= const.flagRigSlot7:
                if typeID not in ret['rigSlots']:
                    ret['rigSlots'][typeID] = 0
                ret['rigSlots'][typeID] += 1
            elif flag >= const.flagSubSystemSlot0 and flag <= const.flagSubSystemSlot7:
                if typeID not in ret['subSystems']:
                    ret['subSystems'][typeID] = 0
                ret['subSystems'][typeID] += 1
            elif flag == const.flagDroneBay:
                ret['drones'][typeID] = qty

        return ret

    def HasSkillForFit(self, fitting):
        fittingID = fitting.fittingID
        try:
            return self.hasSkillByFittingID[fittingID]
        except KeyError:
            self.LogInfo('HasSkillForFit::Cache miss', fittingID)
            sys.exc_clear()

        hasSkill = self.hasSkillByFittingID[fittingID] = self.CheckSkillRequirementsForFit(fitting)
        return hasSkill

    def CheckSkillRequirementsForFit(self, fitting):
        godma = sm.GetService('godma')
        if not godma.CheckSkillRequirementsForType(fitting.shipTypeID):
            return False
        for typeID, flag, qty in fitting.fitData:
            if not godma.CheckSkillRequirementsForType(typeID):
                return False

        return True

    def GetAllFittings(self):
        ret = {}
        charFittings = self.GetFittings(session.charid)
        corpFittings = self.GetFittings(session.corpid)
        for fittingID in charFittings:
            ret[fittingID] = charFittings[fittingID]

        for fittingID in corpFittings:
            ret[fittingID] = corpFittings[fittingID]

        return ret

    def OnSkillFinished(self, skillID, skillTypeID = None, skillLevel = None):
        self.hasSkillByFittingID = {}