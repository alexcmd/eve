#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/util/searchUtil.py
import listentry
import localization
import localizationUtil
import uix

def Search(searchStr, groupIDList, exact = 0, getWindow = 1, searchWndName = 'mySearch'):
    searchStr = searchStr.replace('*', '')
    if len(searchStr) < 1:
        sm.GetService('loading').StopCycle()
        raise UserError('LookupStringMinimum', {'minimum': 1})
    else:
        if len(searchStr) >= 100:
            sm.GetService('loading').StopCycle()
            eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/Common/SearchStringTooLong')})
            return
        if exact == const.searchByPartialTerms and not localizationUtil.IsSearchTextIdeographic(session.languageID, searchStr):
            if len([ x for x in searchStr.split() if len(x) >= const.searchMinWildcardLength ]) == 0:
                eve.Message('PartialSearchLessThanMinLength', {'minChars': const.searchMinWildcardLength})
                exact = const.searchByExactTerms
    query = searchStr.strip()
    s = sm.ProxySvc('search')
    resultsDict = s.Query(query, groupIDList, exact=exact)
    if resultsDict is None:
        resultsDict = {}
    resultHeaders = [(const.searchResultAgent, 'UI/Search/UniversalSearch/Agents'),
     (const.searchResultCharacter, 'UI/Search/UniversalSearch/Characters'),
     (const.searchResultFaction, 'UI/Search/UniversalSearch/Factions'),
     (const.searchResultCorporation, 'UI/Search/UniversalSearch/Corporations'),
     (const.searchResultAlliance, 'UI/Search/UniversalSearch/Alliances'),
     (const.searchResultRegion, 'UI/Search/UniversalSearch/Regions'),
     (const.searchResultSolarSystem, 'UI/Search/UniversalSearch/SolarSystems'),
     (const.searchResultStation, 'UI/Common/LocationTypes/Stations'),
     (const.searchResultConstellation, 'UI/Search/UniversalSearch/Constellations'),
     (const.searchResultInventoryType, 'UI/Search/UniversalSearch/Types'),
     ('ASSETS', 'UI/Search/UniversalSearch/Assets')]
    if const.searchResultAgent in groupIDList:
        auraNames = [localization.GetByLabel('UI/Agents/AuraAgentName').lower(), localization.GetByLabel('UI/Agents/AuraAgentName', localization.LOCALE_SHORT_ENGLISH).lower()]
        queryCheck = query.lower()
        if exact == const.searchByPartialTerms:
            for name in auraNames:
                if name.startswith(queryCheck):
                    if const.searchResultAgent not in resultsDict:
                        resultsDict[const.searchResultAgent] = []
                    resultsDict[const.searchResultAgent] = [sm.GetService('agents').GetAuraAgentID()] + resultsDict[const.searchResultAgent]
                    break

        else:
            for name in auraNames:
                if queryCheck == name:
                    if const.searchResultAgent not in resultsDict:
                        resultsDict[const.searchResultAgent] = []
                    resultsDict[const.searchResultAgent] = [sm.GetService('agents').GetAuraAgentID()] + resultsDict[const.searchResultAgent]
                    break

    scrolllist = []
    totalResults = 0
    ownerPrime = []
    corpTickersToPrime = []
    for k, label in resultHeaders:
        lst = resultsDict.get(k, [])
        entryList = []
        if lst:
            entryList = []
            lst = resultsDict[k]
            if k == const.searchResultAgent:
                entryType = 'AgentEntry'
                for agentID in lst:
                    entryList.append({'charID': agentID})

            elif k in (const.searchResultCorporation,
             const.searchResultAlliance,
             const.searchResultFaction,
             const.searchResultCharacter):
                entryType = 'User'
                ownerPrime.extend(lst)
                if k == const.searchResultCorporation:
                    corpTickersToPrime.extend(lst)
                for ownerID in lst:
                    entryList.append({'charID': ownerID})

            elif k == const.searchResultSolarSystem:
                entryType = 'Generic'
                for itemID in lst:
                    data = {'itemID': itemID,
                     'typeID': const.typeSolarSystem,
                     'label': cfg.evelocations.Get(itemID).name,
                     'sublevel': 1}
                    entryList.append(data)

            elif k == const.searchResultConstellation:
                entryType = 'Generic'
                for itemID in lst:
                    data = {'itemID': itemID,
                     'typeID': const.typeConstellation,
                     'label': cfg.evelocations.Get(itemID).name,
                     'sublevel': 1}
                    entryList.append(data)

            elif k == const.searchResultRegion:
                entryType = 'Generic'
                for itemID in lst:
                    data = {'itemID': itemID,
                     'typeID': const.typeRegion,
                     'label': cfg.evelocations.Get(itemID).name,
                     'sublevel': 1}
                    entryList.append(data)

            elif k == const.searchResultStation:
                entryType = 'Generic'
                for itemID in lst:
                    data = {'itemID': itemID,
                     'typeID': cfg.stations.Get(itemID).stationTypeID,
                     'label': cfg.evelocations.Get(itemID).name,
                     'sublevel': 1}
                    entryList.append(data)

            elif k == const.searchResultInventoryType:
                entryType = 'Item'
                for typeID in lst:
                    data = {'itemID': None,
                     'typeID': typeID,
                     'getIcon': 1,
                     'label': cfg.invtypes.Get(typeID).name}
                    entryList.append(data)

        elif k == 'ASSETS' and const.searchResultInventoryType in resultsDict:
            lst = resultsDict[const.searchResultInventoryType]
            if lst:
                entryType = 'ItemWithLocation'
                entryList = []
        if entryList:
            totalResults += len(entryList)
            sectionHeader = localization.GetByLabel('UI/Search/UniversalSearch/SectionHeader', resultType=localization.GetByLabel(label), numberReturned=len(entryList))
            data = {'GetSubContent': GetSearchSubContent,
             'label': sectionHeader,
             'groupItems': (entryType, entryList),
             'id': ('search_cat', k),
             'sublevel': 0,
             'showlen': 0,
             'showicon': 'hide',
             'cat': k,
             'state': 'locked'}
            scrolllist.append(listentry.Get('Group', data))

    cfg.eveowners.Prime(ownerPrime)
    cfg.corptickernames.Prime(corpTickersToPrime)
    if len(scrolllist) >= 1:
        sm.GetService('loading').StopCycle()
    if getWindow:
        header = localization.GetByLabel('UI/Common/Search')
        if totalResults >= const.searchMaxResults:
            top = localization.GetByLabel('UI/Search/UniversalSearch/WindowHeaderOverMax', maxNumber=const.searchMaxResults)
        else:
            top = localization.GetByLabel('UI/Search/UniversalSearch/WindowHeaderNumResults', numResults=totalResults)
        chosen = uix.ListWnd(scrolllist, 'generic', header, top, 0, isModal=0, minChoices=0, windowName=searchWndName, lstDataIsGrouped=1, unstackable=1, noContentHint=localization.GetByLabel('UI/Search/UniversalSearch/NoResultsReturned'))
        if chosen:
            return chosen[1]
    else:
        return scrolllist


def GetSearchSubContent(dataX, *args):
    scrolllist = []
    entryType, typeList = dataX['groupItems']
    for x in typeList:
        scrolllist.append(listentry.Get(entryType, x))

    return scrolllist


def QuickSearch(searchStr, groupIDList, exact = const.searchByPartialTerms, hideNPC = 0, onlyAltName = 0):
    searchStr = searchStr.replace('*', '')
    if len(searchStr) < 1:
        sm.GetService('loading').StopCycle()
        raise UserError('LookupStringMinimum', {'minimum': 1})
    else:
        if len(searchStr) >= 100:
            sm.GetService('loading').StopCycle()
            eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/Common/SearchStringTooLong')})
            return None
        if exact == const.searchByPartialTerms and not localizationUtil.IsSearchTextIdeographic(session.languageID, searchStr):
            if len([ x for x in searchStr.split() if len(x) >= const.searchMinWildcardLength ]) == 0:
                eve.Message('PartialSearchLessThanMinLength', {'minChars': const.searchMinWildcardLength})
                exact = const.searchByExactTerms
    query = searchStr.strip()
    s = sm.ProxySvc('search')
    return s.QuickQuery(query, groupIDList, hideNPC=hideNPC, onlyAltName=onlyAltName, exact=exact)


def IsMatch(searchStr, candidate, exact):
    if exact == const.searchByPartialTerms and not localizationUtil.IsSearchTextIdeographic(session.languageID, searchStr):
        if len([ x for x in searchStr.split() if len(x) >= const.searchMinWildcardLength ]) == 0:
            exact = const.searchByExactTerms
    searchStr = searchStr.lower().strip()
    candidate = candidate.lower().strip()
    if exact == const.searchByPartialTerms:
        searchTermList = searchStr.split()
        candTermList = candidate.lower().split()
        matches = True
        for searchTerm in searchTermList:
            termMatches = False
            for candTerm in candTermList:
                if candTerm.startswith(searchTerm):
                    termMatches = True
                    break

            if not termMatches:
                matches = False
                break

        return matches
    if exact == const.searchByExactTerms:
        candTermList = candidate.split()
        return all([ s in candTermList for s in searchStr.split() ])
    if exact == const.searchByExactPhrase:
        searchTermList = searchStr.split()
        lBound = 0
        uBound = len(searchTermList)
        candTermList = candidate.split()
        for idx in range(uBound, len(candTermList) + 1):
            if searchTermList == candTermList[lBound:idx]:
                return True
            lBound += 1

        return False
    if exact == const.searchByOnlyExactPhrase:
        return searchStr == candidate
    raise RuntimeError('Unknown value passed in for exact flag')


exports = {'searchUtil.Search': Search,
 'searchUtil.QuickSearch': QuickSearch,
 'searchUtil.IsMatch': IsMatch}