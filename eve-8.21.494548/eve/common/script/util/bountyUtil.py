#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/common/script/util/bountyUtil.py
import util
import blue

def GetMinimumBountyAmount(ownerID):
    if util.IsCharacter(ownerID):
        return const.MIN_BOUNTY_AMOUNT_CHAR
    if util.IsCorporation(ownerID):
        return const.MIN_BOUNTY_AMOUNT_CORP
    if util.IsAlliance(ownerID):
        return const.MIN_BOUNTY_AMOUNT_ALLIANCE
    return 0


def CacheBounties(bountyDict, bountiesToCache):
    for bounty in bountiesToCache:
        bountyDict[bounty.targetID] = (bounty, blue.os.GetWallclockTime())


exports = {'bountyUtil.GetMinimumBountyAmount': GetMinimumBountyAmount,
 'bountyUtil.CacheBounties': CacheBounties}