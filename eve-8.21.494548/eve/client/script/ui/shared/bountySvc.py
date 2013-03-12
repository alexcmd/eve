#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/bountySvc.py
from service import Service
import blue
import uthread
import util
import telemetry
import bountyUtil
import killRightTracker
import localization

class BountyService(Service):
    __guid__ = 'svc.bountySvc'
    __notifyevents__ = ['DoBallsAdded',
     'OnKillRightCreated',
     'OnKillRightUsed',
     'OnKillRightActivated']

    def __init__(self, *args, **kwargs):
        Service.__init__(self, *args, **kwargs)
        self.bounties = {}
        self.cacheTime = 5 * const.MIN
        self.myKillRights = []
        self.killRightTracker = killRightTracker.KillRightTracker(self.FetchKillRightsFromServer, blue.os.GetWallclockTime, 5 * const.MIN)

    def GetBounty(self, *ownerIDs):
        ownerIDs = [ ownerID for ownerID in ownerIDs if ownerID is not None ]
        self.FetchBounties(ownerIDs)
        return sum((self.bounties[ownerID][0].bounty for ownerID in ownerIDs))

    def GetBountyFromCache(self, ownerID):
        return self.bounties[ownerID][0].bounty

    def GetBounties(self, *ownerIDs):
        ownerIDs = [ ownerID for ownerID in ownerIDs if ownerID is not None ]
        self.FetchBounties(ownerIDs)
        return {ownerID:self.bounties[ownerID][0].bounty for ownerID in ownerIDs}

    def AddToBounty(self, ownerID, amount):
        newBounty = sm.ProxySvc('bountyProxy').AddToBounty(ownerID, amount)
        bountyUtil.CacheBounties(self.bounties, [newBounty])
        sm.GetService('objectCaching').InvalidateCachedMethodCall('bountyProxy', 'GetMyBounties')

    def CanHaveBounty(self, slimItem):
        try:
            categoryID = slimItem.categoryID
        except AttributeError:
            return False

        if categoryID == const.categoryShip and slimItem.charID is not None:
            return True
        if categoryID == const.categoryStructure:
            return True
        return False

    def QuickHasBounty(self, slimItem):
        if not self.CanHaveBounty(slimItem):
            return False
        for ownerID in (slimItem.charID, slimItem.corpID, slimItem.allianceID):
            try:
                bounty = self.bounties[ownerID][0].bounty
            except KeyError:
                bounty = 0

            if bounty > 0:
                return True

        return False

    def QuickHasKillRight(self, slimItem):
        if getattr(slimItem, 'charID', None) is None:
            return False
        if self.killRightTracker.GetKillRightsFromCache(slimItem.charID):
            return True
        for killRight in self.myKillRights:
            if killRight.fromID == session.charid and killRight.toID == slimItem.charID:
                return True

        return False

    def FetchBounties(self, targetIDs):
        bountiesToUpdate = {targetID for targetID in targetIDs if self.IsObsolete(targetID)}
        self.LogInfo('FetchBounties - Got', len(bountiesToUpdate), 'that are not cached or expired')
        if bountiesToUpdate:
            bounties = [ bounty for targetID, bounty in self.GetBountiesFromServer(bountiesToUpdate) ]
            bountyUtil.CacheBounties(self.bounties, bounties)

    def IsObsolete(self, targetID, useTime = None):
        if useTime is None:
            useTime = blue.os.GetWallclockTime()
        try:
            return blue.os.GetWallclockTime() > self.bounties[targetID][1] + self.cacheTime
        except KeyError:
            return True

    def GetBountiesFromServer(self, targetIDs):
        return sm.ProxySvc('bountyProxy').GetBounties(targetIDs)

    def DoBallsAdded(self, slimItems, *args, **kwargs):
        uthread.pool('BountySvc::DoBallsAdded', self._DoBallsAdded, slimItems)

    def OnKillRightCreated(self, killRightID, fromID, toID, expiryTime):
        sm.GetService('objectCaching').InvalidateCachedMethodCall('bountyProxy', 'GetMyKillRights')

    def OnKillRightUsed(self, killRightID, toID):
        try:
            del self.killRightTracker.killRightsByToID[toID]
        except KeyError:
            pass

        sm.GetService('objectCaching').InvalidateCachedMethodCall('bountyProxy', 'GetMyKillRights')

    def OnKillRightActivated(self):
        eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/KilLRightActivated')})

    @telemetry.ZONE_METHOD
    def _DoBallsAdded(self, slimItems):
        ownersToQuery = set()
        charIDs = set()
        validItemIDs = set()
        for ball, slim in slimItems:
            if slim.categoryID not in (const.categoryShip, const.categoryStructure):
                continue
            if slim.charID is not None and util.IsOwner(slim.charID):
                charIDs.add(slim.charID)
            if slim.corpID is not None and util.IsOwner(slim.corpID):
                ownersToQuery.add(slim.corpID)
                validItemIDs.add(slim.itemID)
            if slim.allianceID is not None and util.IsOwner(slim.allianceID):
                ownersToQuery.add(slim.allianceID)
                validItemIDs.add(slim.itemID)

        self.LogInfo('_DoBallsAdded fetching possible bounties for', len(validItemIDs), 'entities with', len(ownersToQuery), 'seperate owners')
        if ownersToQuery or charIDs:
            self.FetchBountiesAndKillRightsFromServer(ownersToQuery, charIDs)
            sm.ChainEvent('ProcessBountyInfoUpdated', validItemIDs)

    @telemetry.ZONE_METHOD
    def PrimeOwnersFromMembers(self, members):
        if not sm.GetService('machoNet').GetGlobalConfig().get('EnableBountyFetchingForChat', False):
            self.LogInfo('PrimeOwnersForMember - disabled')
            return
        ownerIDsToPrime = set()
        charIDs = set()
        self.LogInfo('PrimeOwnersFromMembers - got', len(members))
        for member in members.itervalues():
            ownerIDsToPrime.add(member.charID)
            charIDs.add(member.charID)
            if util.IsNPC(member.corpID):
                continue
            ownerIDsToPrime.add(member.corpID)
            if member.allianceID is None:
                continue
            ownerIDsToPrime.add(member.allianceID)

        self.LogInfo('PrimeOwnersFromMembers - Need to Fetch', len(ownerIDsToPrime))
        if ownerIDsToPrime or charIDs:
            self.FetchBountiesAndKillRightsFromServer(ownerIDsToPrime, charIDs)

    def GetTopPilotBounties(self, page = 0):
        return self.GetTopBounties(sm.ProxySvc('bountyProxy').GetTopPilotBounties, page)

    def GetTopCorpBounties(self, page = 0):
        return self.GetTopBounties(sm.ProxySvc('bountyProxy').GetTopCorpBounties, page)

    def GetTopAllianceBounties(self, page = 0):
        return self.GetTopBounties(sm.ProxySvc('bountyProxy').GetTopAllianceBounties, page)

    def GetTopBounties(self, fetcher, page):
        newBounties, lastFetchingTime = fetcher(page)
        bountiesToCache = [ bounty for bounty in newBounties if self.IsObsolete(bounty.targetID, lastFetchingTime) ]
        self.LogInfo('GetTopBounties::Got', len(newBounties), 'but caching', len(bountiesToCache))
        bountyUtil.CacheBounties(self.bounties, bountiesToCache)
        return sorted(newBounties, key=lambda x: x.bounty, reverse=True)

    def GetTopPilotBountyHunters(self, page = 0):
        return sm.ProxySvc('bountyProxy').GetTopPilotBountyHunters(page)[0]

    def GetTopCorporationBountyHunters(self, page = 0):
        return sm.ProxySvc('bountyProxy').GetTopCorporationBountyHunters(page)[0]

    def GetTopAllianceBountyHunters(self, page = 0):
        return sm.ProxySvc('bountyProxy').GetTopAllianceBountyHunters(page)[0]

    def GetMyBounties(self):
        return sm.ProxySvc('bountyProxy').GetMyBounties()

    def GMReimburseBounties(self):
        sm.ProxySvc('bountyProxy').GMReimburseBounties()

    def GMClearBountyCache(self):
        objectCaching = sm.GetService('objectCaching')
        for entry in objectCaching.cachedMethodCalls.keys():
            if entry[0] == 'bountyProxy':
                objectCaching.InvalidateCachedMethodCall(*entry)

        sm.ProxySvc('bountyProxy').GMClearBountyCache()

    def SearchBounties(self, targetID):
        if util.IsCharacter(targetID):
            fetcher = sm.ProxySvc('bountyProxy').SearchCharBounties
        elif util.IsCorporation(targetID):
            fetcher = sm.ProxySvc('bountyProxy').SearchCorpBounties
        elif util.IsAlliance(targetID):
            fetcher = sm.ProxySvc('bountyProxy').SearchAllianceBounties
        bountyAndRank = fetcher(targetID)
        bountyUtil.CacheBounties(self.bounties, [ bounty for rank, bounty in bountyAndRank ])
        return bountyAndRank

    def CancelSellKillRight(self, killRightID, toID):
        sm.ProxySvc('bountyProxy').CancelSellKillRight(killRightID, toID)
        self.killRightTracker.OnKillRightRemoved(toID, killRightID)
        sm.GetService('objectCaching').InvalidateCachedMethodCall('bountyProxy', 'GetMyKillRights')
        sm.ScatterEvent('OnKillRightSellCancel', killRightID)

    def SellKillRight(self, killRightID, price, restrictedTo = None):
        killRights = sm.ProxySvc('bountyProxy').SellKillRight(killRightID, price, restrictedTo)
        if killRights is not None:
            for killRight in killRights:
                self.killRightTracker.OnKillRightAdded(killRight)

        sm.GetService('objectCaching').InvalidateCachedMethodCall('bountyProxy', 'GetMyKillRights')

    def GetMyKillRights(self):
        killRights = sm.ProxySvc('bountyProxy').GetMyKillRights()
        self.myKillRights = killRights
        return killRights

    def GetKillRights(self, toIDs):
        toIDs = [ toID for toID in toIDs if toID is not None and util.IsCharacter(toID) and util.IsOwner(toID) ]
        validIDs = [session.charid, session.corpid]
        if session.allianceid is not None:
            validIDs.append(session.allianceid)
        return self.killRightTracker.GetKillRights(toIDs, *validIDs)

    def FetchKillRightsFromServer(self, toIDs):
        self.LogInfo('Fetching', len(toIDs), 'kill rights from the server')
        return sm.ProxySvc('bountyProxy').GetKillRightsOnCharacters(toIDs)

    def FetchBountiesAndKillRightsFromServer(self, charIDs, ownerIDs):
        bountiesToFetch = {ownerID for ownerID in ownerIDs if self.IsObsolete(ownerID)}
        killRightsToFetch = self.killRightTracker.GetInvalidKillRights(charIDs)
        self.LogInfo('FetchBountiesAndKillRightsFromServer - fetching', len(bountiesToFetch), 'for bounties and', len(killRightsToFetch), 'for killRights')
        if not (bountiesToFetch or killRightsToFetch):
            self.LogInfo('FetchBountiesAndKillRightsFromServer - Bailing out because nothing to fetch')
            return
        myKillRights, (bounties, killRights) = uthread.parallel([(self.GetMyKillRights, ()), (sm.ProxySvc('bountyProxy').GetBountiesAndKillRights, (bountiesToFetch, killRightsToFetch))])
        bountyUtil.CacheBounties(self.bounties, [ bounty for targetID, bounty in bounties ])
        self.killRightTracker.CacheKillRights(killRights, killRightsToFetch)

    def ClearAllKillRightData(self):
        self.killRightTracker.killRightsByToID.clear()
        sm.GetService('objectCaching').InvalidateCachedMethodCall('bountyProxy', 'GetMyKillRights')

    def GetBestKillRight(self, toID):
        for killRight in self.GetMyKillRights():
            if killRight.fromID == session.charid and killRight.toID == toID:
                return (killRight.killRightID, None)

        killRights = self.GetKillRights([toID])
        if not killRights:
            return (None, None)
        killRight = min(killRights, key=lambda x: x.price)
        return (killRight.killRightID, killRight.price)

    def BuyKillRight(self, killRightID, toID, shipID, price):
        try:
            sm.RemoteSvc('killRightMgr').BuyKillRight(killRightID, price)
        except UserError as e:
            if e.msg in ('NoValidKillRight', 'KillRightExpired', 'KillRightNotForSale'):
                self.killRightTracker.OnKillRightRemoved(toID, killRightID)
                sm.ChainEvent('ProcessBountyInfoUpdated', [shipID])
            raise 

    def ActivateKillRight(self, killRightID, toID, shipID):
        try:
            sm.RemoteSvc('killRightMgr').ActivateKillRight(killRightID)
        except UserError as e:
            if e.msg in ('NoValidKillRight', 'KillRightExpired'):
                self.killRightTracker.OnKillRightRemoved(toID, killRightID)
                sm.GetService('objectCaching').InvalidateCachedMethodCall('bountyProxy', 'GetMyKillRights')
                sm.ChainEvent('ProcessBountyInfoUpdated', [shipID])
            raise 