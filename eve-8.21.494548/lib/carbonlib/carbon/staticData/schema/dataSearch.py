#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\carbon\staticData\schema\dataSearch.py
import dataWalker
import re

class SearchResults:

    def __init__(self, dataQuery, schemaQuery, ignoreCase, exactMatch, regularExpression):
        self.searchResultObjects = None
        self._dataQuery = dataQuery
        self._schemaQuery = schemaQuery
        self._ignoreCase = ignoreCase
        self._exactMatch = exactMatch
        self._regularExpression = regularExpression

    def Callback(self, rootObj, obj, schemaNode, path):
        if self._dataQuery:
            for queryPath, queryValue in self._dataQuery.iteritems():
                queryRegularExpression = re.compile(queryPath)
                if queryRegularExpression.match(path):
                    match = False
                    obj = str(obj)
                    queryValue = str(queryValue)
                    if self._ignoreCase:
                        if schemaNode['type'] in ('string', 'resPath'):
                            obj = obj.lower()
                            queryValue = queryValue.lower()
                            match = queryValue == obj
                    if not match:
                        if not self._exactMatch and not self._regularExpression:
                            queryValue = re.compile('.*' + re.escape(queryValue) + '.*')
                            match = queryValue.match(obj) != None
                        elif self._regularExpression:
                            queryValue = re.compile(queryValue)
                            match = queryValue.match(obj) != None
                        else:
                            match = queryValue == obj
                    if match:
                        self.AppendMatch(rootObj, path)
                        return False

        if self._schemaQuery:
            for queryPath, query in self._schemaQuery.iteritems():
                starSearch = queryPath.endswith('*')
                if starSearch:
                    queryPath = queryPath.replace('*', '')
                if path.startswith(queryPath) and starSearch or path == queryPath:
                    for queryField, queryValue in query.iteritems():
                        if queryField in schemaNode and schemaNode[queryField] == queryValue:
                            self.AppendMatch(rootObj, path)
                            return False

        return True

    def AppendMatch(self, rootObj, path):
        if type(self.searchResultObjects) == type({}):
            if path == 'root':
                self.searchResultObjects = rootObj
            else:
                keySearchRes = re.search('root\\[\\S*\\]|root\\<\\S*\\>', path)
                if keySearchRes:
                    key = keySearchRes.group()
                    key = key.replace('root[', '').replace(']', '')
                    key = key.replace('root<', '').replace('>', '')
                    keyType = type(rootObj.keys()[0])
                    self.searchResultObjects[keyType(key)] = rootObj[keyType(key)]
                else:
                    self.searchResultObjects = rootObj
        elif type(self.searchResultObjects) == type([]):
            if path == 'root':
                self.searchResultObjects = rootObj
            else:
                key = re.search('root\\[\\S*\\]', path).group().replace('root[', '').replace(']', '')
                self.searchResultObjects.append(rootObj[int(key)])
        else:
            self.searchResultObjects = rootObj


def Search(data, schema, dataQuery = None, schemaQuery = None, ignoreCase = False, exactMatch = False, regularExpression = False):
    results = SearchResults(dataQuery, schemaQuery, ignoreCase, exactMatch, regularExpression)
    results.searchResultObjects = type(data)()
    dataWalker.Walk(data, schema, continueWalkingFunction=results.Callback)
    return results.searchResultObjects