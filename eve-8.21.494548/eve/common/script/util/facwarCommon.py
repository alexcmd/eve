#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/common/script/util/facwarCommon.py
import util
import math
COLOR_FRIEND = (0.078, 0.118, 0.18, 1.0)
COLOR_FRIEND_BAR = (0.318, 0.471, 0.714, 1.0)
COLOR_FRIEND_LIGHT = (0.475, 0.671, 0.835, 1.0)
COLOR_FOE = (0.196, 0.067, 0.051, 1.0)
COLOR_FOE_BAR = (0.78, 0.259, 0.196, 1.0)
COLOR_FOE_LIGHT = (0.851, 0.435, 0.412, 1.0)
COLOR_CENTER_BG = (0.2, 0.2, 0.196, 0.8)
STATE_STABLE = 1
STATE_CONTESTED = 2
STATE_VULNERABLE = 3
STATE_CAPTURED = 4
BENEFIT_MEDICALCLONES = 1
BENEFIT_MARKETREDUCTION = 2
BENEFIT_STATIONCOPYSLOTS = 3
BENEFIT_PLANETDISTRICTS = 4
BENEFITS_BY_LEVEL = {1: ((BENEFIT_MEDICALCLONES, 10), (BENEFIT_MARKETREDUCTION, 10), (BENEFIT_STATIONCOPYSLOTS, 1)),
 2: ((BENEFIT_MEDICALCLONES, 20), (BENEFIT_MARKETREDUCTION, 20), (BENEFIT_STATIONCOPYSLOTS, 2)),
 3: ((BENEFIT_MEDICALCLONES, 30), (BENEFIT_MARKETREDUCTION, 30), (BENEFIT_STATIONCOPYSLOTS, 3)),
 4: ((BENEFIT_MEDICALCLONES, 40), (BENEFIT_MARKETREDUCTION, 40), (BENEFIT_STATIONCOPYSLOTS, 4)),
 5: ((BENEFIT_MEDICALCLONES, 50), (BENEFIT_MARKETREDUCTION, 50), (BENEFIT_STATIONCOPYSLOTS, 5))}
FACTION_ENEMIES = {const.factionCaldariState: [const.factionMinmatarRepublic, const.factionGallenteFederation],
 const.factionMinmatarRepublic: [const.factionCaldariState, const.factionAmarrEmpire],
 const.factionAmarrEmpire: [const.factionMinmatarRepublic, const.factionGallenteFederation],
 const.factionGallenteFederation: [const.factionCaldariState, const.factionAmarrEmpire]}
FACTION_FRIENDS = {const.factionCaldariState: const.factionAmarrEmpire,
 const.factionMinmatarRepublic: const.factionGallenteFederation,
 const.factionAmarrEmpire: const.factionCaldariState,
 const.factionGallenteFederation: const.factionMinmatarRepublic}

def IsWarfareFaction(factionID):
    return factionID in FACTION_FRIENDS


def IsEnemyFaction(enemyID, factionID):
    if factionID in FACTION_ENEMIES and enemyID in FACTION_ENEMIES[factionID]:
        return True
    return False


def IsFriendlyFaction(friendID, factionID):
    if factionID in FACTION_FRIENDS and (friendID == FACTION_FRIENDS[factionID] or friendID == factionID):
        return True
    return False


def GetFactionMainEnemy(factionID):
    if factionID == const.factionCaldariState:
        return const.factionGallenteFederation
    if factionID == const.factionGallenteFederation:
        return const.factionCaldariState
    if factionID == const.factionAmarrEmpire:
        return const.factionMinmatarRepublic
    if factionID == const.factionMinmatarRepublic:
        return const.factionAmarrEmpire
    raise RuntimeError("I don't know who the main enemy of", factionID, "is, are you sure it's a faction that is involved in factional warfare?")


def GetFactionSecondaryEnemy(factionID):
    if factionID == const.factionCaldariState:
        return const.factionMinmatarRepublic
    if factionID == const.factionGallenteFederation:
        return const.factionAmarrEmpire
    if factionID == const.factionAmarrEmpire:
        return const.factionGallenteFederation
    if factionID == const.factionMinmatarRepublic:
        return const.factionCaldariState
    raise RuntimeError("I don't know who the secondary enemy of", factionID, "is, are you sure it's a faction that is involved in factional warfare?")


def GetSolarSystemUpgradeLevel(solarSystemID, factionID):
    if boot.role == 'client':
        facwarSvc = sm.GetService('facwar')
        lps = facwarSvc.GetSolarSystemLPs()
        if lps == 0:
            return 0
        if factionID is not None:
            occupierID = facwarSvc.GetSystemOccupier(solarSystemID)
            if occupierID is not None and IsEnemyFaction(factionID, occupierID):
                lps = 0
    else:
        facWarMgr = sm.GetService('facWarMgr')
        lps = facWarMgr.GetSolarSystemLPsEx(solarSystemID)
        if lps == 0:
            return 0
        if factionID is not None:
            occupierID = facWarMgr.GetOccupier(solarSystemID)
            if occupierID is not None and IsEnemyFaction(factionID, occupierID):
                lps = 0
    return GetLPUpgradeLevel(lps)


def GetLPUpgradeLevel(lps):
    for i, threshold in enumerate(const.facwarSolarSystemUpgradeThresholds):
        if lps < threshold:
            return i

    return i + 1


def GetAdjustedClonePrice(solarSystemID, factionID, basePrice):
    level = GetSolarSystemUpgradeLevel(solarSystemID, factionID)
    return basePrice * (1 - 0.1 * level)


def GetAdjustedFeePercentage(solarSystemID, factionID, feePercentage):
    level = GetSolarSystemUpgradeLevel(solarSystemID, factionID)
    return feePercentage * (1 - 0.1 * level)


def GetDonationTax(factionID):
    if boot.role == 'client':
        facwarSvc = sm.GetService('facwar')
        zoneInfo = facwarSvc.GetFacWarZoneInfo(factionID)
        percentControlled = zoneInfo.factionPoints / zoneInfo.maxWarZonePoints
    else:
        facWarZoneMgr = sm.GetService('facWarZoneMgr')
        points, maxPoints = facWarZoneMgr.GetZonePoints(factionID)
        percentControlled = points / maxPoints
    rawTax = 5 * math.pow(percentControlled, 3)
    donationTax = round(1 - 1 / (1 + rawTax), 2)
    return donationTax


exports = util.AutoExports('facwarCommon', locals())