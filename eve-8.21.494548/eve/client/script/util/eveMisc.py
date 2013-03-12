#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/util/eveMisc.py
import blue
import sys
import util
import uthread
import log
import uix
import uiconst

def LaunchFromShip(items, whoseBehalfID = None, ignoreWarning = False):
    oldItems = []
    drones = False
    for item in items:
        if getattr(item, 'categoryID', 0) == const.categoryDrone:
            drones = True
        qty = getattr(item, 'quantity', 0)
        if qty < 0:
            oldItems.insert(0, (item.itemID, 1))
        elif qty > 0:
            oldItems.append((item.itemID, qty))

    try:
        if drones:
            ret = sm.StartService('gameui').GetShipAccess().LaunchDrones(oldItems, whoseBehalfID, ignoreWarning)
        else:
            ret = sm.StartService('gameui').GetShipAccess().Drop(oldItems, whoseBehalfID, ignoreWarning)
    except UserError as e:
        if e.msg in ('LaunchCPWarning', 'LaunchUpgradePlatformWarning'):
            reply = eve.Message(e.msg, e.dict, uiconst.YESNO)
            if reply == uiconst.ID_YES:
                LaunchFromShip(items, whoseBehalfID, ignoreWarning=True)
            sys.exc_clear()
            return
        raise e

    newIDs = {}
    errorByLabel = {}
    for itemID, seq in ret.iteritems():
        newIDs[itemID] = []
        for each in seq:
            if type(each) is tuple:
                errorByLabel[each[0]] = each
            else:
                newIDs[itemID].append(each)

    sm.ScatterEvent('OnItemLaunch', newIDs)

    def raise_(e):
        raise e

    for error in errorByLabel.itervalues():
        uthread.new(raise_, UserError(*error))


def IsItemOfRepairableType(item):
    return item.singleton and (item.categoryID in (const.categoryDeployable,
     const.categoryShip,
     const.categoryDrone,
     const.categoryStructure,
     const.categoryModule) or item.groupID in (const.groupCargoContainer,
     const.groupSecureCargoContainer,
     const.groupAuditLogSecureContainer,
     const.groupFreightContainer,
     const.groupTool))


def CSPAChargedAction(message, obj, function, *args):
    try:
        return apply(getattr(obj, function), args)
    except UserError as e:
        if e.msg == 'ContactCostNotApproved':
            info = e.args[1]
            if eve.Message(message, {'amount': info['totalCost'],
             'amountISK': info['totalCostISK']}, uiconst.YESNO) != uiconst.ID_YES:
                return None
            kwArgs = {'approvedCost': info['totalCost']}
            return apply(getattr(obj, function), args, kwArgs)
        raise 


exports = util.AutoExports('util', globals())