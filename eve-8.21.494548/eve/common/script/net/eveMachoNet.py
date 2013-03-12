#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/common/script/net/eveMachoNet.py
import sys
import base
import util
import macho
import log
import service
import const
import svc
globals().update(service.consts)

class EveMachoNetService(svc.machoNet):
    __guid__ = 'svc.eveMachoNet'
    __replaceservice__ = 'machoNet'
    __gpcsmethodnames__ = ['Broadcast',
     'ClusterBroadcast',
     'ConnectToAllNeighboringServices',
     'ConnectToAllServices',
     'ConnectToAllSiblingServices',
     'ConnectToRemoteService',
     'NarrowcastByAllianceIDs',
     'NarrowcastByCharIDs',
     'NarrowcastByClientIDs',
     'NarrowcastByClientIDsWithoutTheStars',
     'NarrowcastByCorporationIDs',
     'NarrowcastByFleetIDs',
     'NarrowcastByNodeIDs',
     'NarrowcastByShipIDs',
     'NarrowcastBySolarSystemID2s',
     'NarrowcastBySolarSystemIDs',
     'NarrowcastByStationIDs',
     'NarrowcastByStationID2s',
     'NarrowcastByUserIDs',
     'NarrowcastToClientAndObservers',
     'NarrowcastToObservers',
     'SinglecastByServiceMask',
     'NodeBroadcast',
     'Objectcast',
     'ObjectcastWithoutTheStars',
     'OnObjectPublicAttributesUpdated',
     'ProxyBroadcast',
     'Queuedcast',
     'QueuedcastWithoutTheStars',
     'ReliableSinglecastByCharID',
     'ReliableSinglecastByUserID',
     'RemoteServiceCall',
     'RemoteServiceCallWithoutTheStars',
     'RemoteServiceNotify',
     'RemoteServiceNotifyWithoutTheStars',
     'ResetAutoResolveCache',
     'Scattercast',
     'ScattercastWithoutTheStars',
     'ServerBroadcast',
     'SinglecastByAllianceID',
     'SinglecastByCharID',
     'SinglecastByClientID',
     'SinglecastByCorporationID',
     'SinglecastByFleetID',
     'SinglecastByNodeID',
     'SinglecastByShipID',
     'SinglecastBySolarSystemID',
     'SinglecastBySolarSystemID2',
     'SinglecastByStationID',
     'SinglecastByStationID2',
     'SinglecastByUserID',
     'SinglecastByWorldSpaceID']
    __server_scattercast_session_variables__ = ('userid',
     'charid',
     'shipid',
     'objectID',
     'fleetid',
     'wingid',
     'squadid')
    __notifyevents__ = svc.machoNet.__notifyevents__
    __notifyevents__.extend(['OnGlobalConfigChanged'])
    svc.machoNet.metricsMap.update({'EVE:Online': const.zmetricCounter_EVEOnline,
     'EVE:CREST': const.zmetricCounter_EVECREST,
     'EVE:Trial': const.zmetricCounter_EVETrial,
     'DUST:Online': const.zmetricCounter_DUSTOnline,
     'DUST:User': const.zmetricCounter_DUSTUser,
     'DUST:Battle': const.zmetricCounter_DUSTBattle})

    def __init__(self):
        svc.machoNet.__init__(self)
        self.logAllClientCalls = prefs.GetValue('logAllClientCalls', None)
        self.clientCallLogChannel = log.Channel(str(macho.mode), 'ClientCalls')
        self.sessionWatchIDs = None
        try:
            self.sessionWatchIDs = ({int(s) for s in strx(prefs.GetValue('sessionWatch_userID', '')).split(',') if s},
             {int(s) for s in strx(prefs.GetValue('sessionWatch_charID', '')).split(',') if s},
             {int(s) for s in strx(prefs.GetValue('sessionWatch_corpID', '')).split(',') if s},
             {int(s) for s in strx(prefs.GetValue('sessionWatch_userType', '')).split(',') if s})
            if len(self.sessionWatchIDs[0]) == 0 and len(self.sessionWatchIDs[1]) == 0 and len(self.sessionWatchIDs[2]) == 0 and len(self.sessionWatchIDs[3]) == 0:
                self.sessionWatchIDs = None
        except:
            log.LogException()
            sys.exc_clear()

        self.clusterSolarsystemStatistics = ({}, {}, 0)

    def Run(self, memStream = None):
        svc.machoNet.Run(self, memStream)
        if macho.mode == 'server' and self.connectToCluster:
            self.dbzuser = self.DB2.GetSchema('zuser')

    def _GetSubscriptionInfoRow(self, sess):
        return [sess.charid,
         sess.corpid,
         sess.allianceid,
         sess.warfactionid,
         sess.role]

    def GetClusterGameStatistics(self, key, default):
        if key == 'EVE':
            return self.clusterSolarsystemStatistics
        else:
            return default

    def SetClusterSessionCounts(self, clusterSessionStatistics):
        if clusterSessionStatistics is not None:
            sol, station, c = self.clusterSolarsystemStatistics
            if 'solarsystemid2' in clusterSessionStatistics:
                solarsystemidCounts = clusterSessionStatistics['solarsystemid'][1] if 'solarsystemid' in clusterSessionStatistics else {}
                for solarsystemid, solarsystemid2Count in clusterSessionStatistics['solarsystemid2'][1].iteritems():
                    solID = solarsystemid - 30000000
                    sol[solID] = sol.get(solID, 0) + solarsystemid2Count
                    stationCount = solarsystemid2Count - solarsystemidCounts.get(solarsystemid, 0)
                    if stationCount > 0:
                        station[solID] = station.get(solID, 0) + stationCount

            if len(self.clusterSessionStatsHistory) == self.proxyStatSmoothie:
                oldestStatistics = self.clusterSessionStatsHistory[0][1]
                if 'solarsystemid2' in oldestStatistics:
                    solarsystemidCounts = oldestStatistics['solarsystemid'][1] if 'solarsystemid' in oldestStatistics else {}
                    for solarsystemid, solarsystemid2Count in oldestStatistics['solarsystemid2'][1].iteritems():
                        solID = solarsystemid - 30000000
                        sol[solID] = sol.get(solID, 0) - solarsystemid2Count
                        stationCount = solarsystemid2Count - solarsystemidCounts.get(solarsystemid, 0)
                        if stationCount > 0:
                            station[solID] = station.get(solID, 0) - stationCount

            numSamples = min(self.proxyStatSmoothie, len(self.clusterSessionStatsHistory))
            self.clusterSolarsystemStatistics = (sol, station, numSamples)
        svc.machoNet.SetClusterSessionCounts(self, clusterSessionStatistics)

    def _StoreMetricsToDB(self, metrics):
        try:
            svc.machoNet._StoreMetricsToDB(self, metrics)
            onlineCount = metrics['EVE:Online'][0] if 'EVE:Online' in metrics else 0
            trialCount = metrics['EVE:Trial'][0] if 'EVE:Trial' in metrics else 0
            onlineCount2 = metrics['DUST:Online'][0] if 'DUST:Online' in metrics else 0
            trialCount2 = 0
            self.dbzuser.OnlineCounts_Insert(onlineCount, trialCount, onlineCount2, trialCount2)
        except StandardError:
            log.LogException()
            sys.exc_clear()
        except:
            log.LogException()
            raise 

    def _GetNodeFromAddressFromDB(self, myNodeID, serviceMapping, address, suggestedNodeID, expectedLoadValue, serviceMask):
        if serviceMapping == 2 and (address < const.minSolarSystem or address > const.maxSolarSystem):
            log.LogException()
            raise RuntimeError('Address is not a solar system (%s)' % address)
        return svc.machoNet._GetNodeFromAddressFromDB(self, myNodeID, serviceMapping, address, suggestedNodeID, expectedLoadValue, serviceMask)

    def GuessNodeIDFromAddress(self, serviceName, address):
        alternatives = []
        if service in ('aggressionMgr', 'director', 'entity'):
            alternatives = [('beyonce', address)]
            for each in ('aggressionMgr', 'director', 'entity'):
                alternatives.append((each, address))

        elif service == 'brokerMgr':
            alternatives = [('station', address)]
        elif service in ('i2', 'skillMgr', 'dogmaIM', 'invbroker', 'ship'):
            if address[1] == const.groupSolarSystem:
                alternatives = [('beyonce', address[0])]
            elif address[1] == const.groupStation:
                alternatives = [('station', address[0])]
            for each in ('i2', 'skillMgr', 'dogmaIM', 'invbroker', 'ship'):
                alternatives.append((each, address))

        elif service in ('corpStationMgr', 'factory', 'broker'):
            alternatives = [('station', address)]
        elif service == 'tradeMgr':
            alternatives = [('station', address[0])]
        elif service == 'station' and macho.mode == 'server':
            try:
                key = ('beyonce', sm.services['stationSvc'].GetStation(address, prime=0).solarSystemID)
                if key[1]:
                    alternatives.append(key)
            except StandardError:
                log.LogException('Could not locate the station you asked for without blocking')
                sys.exc_clear()

        for alt_service, alt_address in alternatives:
            nodeID = self._addressCache.Get(alt_service, alt_address)
            if nodeID is not None:
                self._addressCache.Set(serviceName, address, nodeID)
                return nodeID

    def _GetNodeFromAddressAdjustments(self, service, address):
        if boot.role == 'server':
            if service in ('worldspace', const.cluster.SERVICE_WORLDSPACE) and util.IsWorldSpace(address):
                wss = sm.GetService('worldSpaceServer')
                service, address = wss.GetWorldSpaceMachoAddress(address)
            if service == 'station':
                try:
                    key = (const.cluster.SERVICE_BEYONCE, sm.StartService('stationSvc').GetStation(address).solarSystemID)
                    service, address = key
                except StandardError:
                    log.LogException()
                    raise RuntimeError('The station you asked for does not reside in any known solar system')

        suggestedNodeID = None
        if service in ('beyonce', const.cluster.SERVICE_BEYONCE) and int(address) == 30000380:
            suggestedNodeID = self.GetNodeFromAddress(const.cluster.SERVICE_POLARIS, 0)
        if service in ('planetMgr', const.cluster.SERVICE_PLANETMGR):
            address = address % const.PLANETARYMGR_MOD
        return (suggestedNodeID, service, address)

    def _GetTransportIDsFromBroadcastAddress(self, address):
        if address.idtype is None:
            idtype = None
            scattered = 0
        elif address.idtype[0] in ('*', '+'):
            idtype = address.idtype[1:]
            scattered = 1
        else:
            idtype = address.idtype
            scattered = 0
        if len(address.narrowcast):
            clientIDs = []
            nodeIDs = []
            done = 0
            if idtype == 'clientID':
                if macho.mode == 'server' and len(address.narrowcast) >= 2 * len(self.transportIDbyProxyNodeID):
                    nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                else:
                    clientIDs = address.narrowcast
                done = 1
            elif idtype == 'nodeID':
                nodeIDs = address.narrowcast
                done = 1
            elif idtype == 'serviceMask':
                nodeIDs = self.ResolveServiceMaskToNodeIDs(address.narrowcast[0])
                done = 1
            elif macho.mode == 'server':
                if idtype in self.__server_scattercast_session_variables__:
                    if scattered:
                        nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                        done = 1
                elif len(address.narrowcast) == 1:
                    if idtype == 'multicastID':
                        nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                        done = 1
                    elif idtype == 'stationid':
                        nodeID = self.CheckAddressCache('station', address.narrowcast[0], lazyGetIfNotFound=True)
                        if self.GetNodeID() == nodeID:
                            if scattered:
                                self.LogInfo('Scattercasting by stationID on the right node.  Ignored.')
                        else:
                            self.LogWarn('Sending a packet by stationid on the wrong node.  Resorting to a scattercast.')
                            self.LogWarn('nodeID: ', nodeID, ', my nodeID: ', self.GetNodeID(), ', stationID: ', address.narrowcast[0])
                            nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                            done = 1
                    elif idtype in ('solarsystemid', 'solarsystemid2'):
                        nodeID = self.CheckAddressCache('beyonce', address.narrowcast[0], lazyGetIfNotFound=True)
                        if self.GetNodeID() == nodeID:
                            if scattered:
                                self.LogInfo('Scattercasting by solarsystemid on the right node.  Ignored.')
                        else:
                            self.LogWarn('Sending a packet by solarsystemid on the wrong node.  Resorting to a scattercast.')
                            self.LogWarn('nodeID: ', nodeID, ', my nodeID: ', self.GetNodeID(), ', solarsystemid(2): ', address.narrowcast[0])
                            nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                            done = 1
                    elif idtype == 'corpid':
                        nodeID = self.CheckAddressCache('chatx', address.narrowcast[0] % 200, lazyGetIfNotFound=True)
                        if self.GetNodeID() == nodeID:
                            if scattered:
                                self.LogInfo('Scattercasting by corpid on the right node.  Ignored.')
                        else:
                            self.LogWarn('Sending a packet by corpid on the wrong node.  Resorting to a scattercast.')
                            self.LogWarn('nodeID: ', nodeID, ', my nodeID: ', self.GetNodeID(), ', corpID: ', address.narrowcast[0])
                            nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                            done = 1
                    elif idtype == 'allianceid':
                        nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                        done = 1
                    else:
                        self.LogWarn('Sending a packet by some funky address type (', idtype, ').  Resorting to scattercast')
                        nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                        done = 1
                elif idtype == 'corpid&corprole' and len(address.narrowcast[0]) == 1:
                    nodeID = self.CheckAddressCache('chatx', address.narrowcast[0][0] % 200, lazyGetIfNotFound=True)
                    if self.GetNodeID() == nodeID:
                        if scattered:
                            self.LogInfo('Scattercasting by corpid&corprole on the right node.  Ignored.')
                    else:
                        self.LogWarn('Sending a packet by corpid&corprole on the wrong node.  Resorting to a scattercast.')
                        self.LogWarn('nodeID: ', nodeID, ', my nodeID: ', self.GetNodeID(), ', corpID: ', address.narrowcast[0][0])
                        nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                        done = 1
                elif idtype in ('stationid&corpid&corprole', 'stationid&corpid') and len(address.narrowcast[0]) == 1 and len(address.narrowcast[1]) == 1:
                    stationNodeID = self.CheckAddressCache('station', address.narrowcast[0][0], lazyGetIfNotFound=True)
                    corpNodeID = self.CheckAddressCache('chatx', address.narrowcast[1][0] % 200, lazyGetIfNotFound=True)
                    if self.GetNodeID() in (stationNodeID, corpNodeID):
                        if scattered:
                            self.LogInfo('Scattercasting by stationid&corpid&corprole on the station node or corp node.  Ignored.')
                    else:
                        self.LogWarn('Sending a packet by stationid&corpid&corprole on the wrong node.  Resorting to a scattercast.')
                        self.LogWarn('corpNodeID: ', corpNodeID, ', stationNodeID: ', stationNodeID, ', my nodeID: ', self.GetNodeID(), ', corpID: ', address.narrowcast[1][0], ', stationID: ', address.narrowcast[0][0])
                        nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                        done = 1
                elif idtype == 'corpid&corprole&solarsystemid' and len(address.narrowcast[0]) == 1 and len(address.narrowcast[2]) == 1:
                    solNodeID = self.CheckAddressCache('beyonce', address.narrowcast[2][0], lazyGetIfNotFound=True)
                    corpNodeID = self.CheckAddressCache('chatx', address.narrowcast[0][0] % 200, lazyGetIfNotFound=True)
                    if self.GetNodeID() in (solNodeID, corpNodeID):
                        if scattered:
                            self.LogInfo('Scattercasting by corpid&corprole&solarsystemid on the solarsystem node or corp node.  Ignored.')
                    else:
                        self.LogWarn('Sending a packet by corpid&corprole&solarsystemid on the wrong node.  Resorting to a scattercast.')
                        self.LogWarn('corpNodeID: ', corpNodeID, ', solNodeID: ', solNodeID, ', my nodeID: ', self.GetNodeID(), ', corpID: ', address.narrowcast[0][0], ', solarsystemID: ', address.narrowcast[2][0])
                        nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                        done = 1
                elif idtype in ('corpid&solarsystemid', 'solarsystemid&corpid') and len(address.narrowcast[0]) == 1 and len(address.narrowcast[1]) == 1:
                    if idtype == 'solarsystemid&corpid':
                        idxSol = 0
                        idxCorp = 1
                    else:
                        idxSol = 1
                        idxCorp = 0
                    solNodeID = self.CheckAddressCache('beyonce', address.narrowcast[idxSol][0], lazyGetIfNotFound=True)
                    corpNodeID = self.CheckAddressCache('chatx', address.narrowcast[idxCorp][0] % 200, lazyGetIfNotFound=True)
                    if self.GetNodeID() in (solNodeID, corpNodeID):
                        if scattered:
                            self.LogInfo('Scattercasting by corpid&corprole&solarsystemid on the solarsystem node or corp node.  Ignored.')
                    else:
                        self.LogWarn('Sending a packet by corpid&corprole&solarsystemid on the wrong node.  Resorting to a scattercast.')
                        self.LogWarn('corpNodeID: ', corpNodeID, ', solNodeID: ', solNodeID, ', my nodeID: ', self.GetNodeID(), ', corpID: ', address.narrowcast[idxCorp][0], ', solarsystemID: ', address.narrowcast[idxSol][0])
                        nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                        done = 1
                elif idtype == 'allianceid&corprole':
                    nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                    done = 1
                else:
                    if not scattered:
                        self.LogWarn('Sending a packet via a non-scattered complex address that resorts to a scattercast.  address: ', address)
                    else:
                        self.LogInfo('Sending a packet via a scattered complex address.  address: ', address)
                    nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                    done = 1
            elif macho.mode == 'proxy' and idtype == 'multicastID':
                if len(address.narrowcast) == 1:
                    clientIDs = self.subscriptionsByAddress.get(address.narrowcast[0][0], {}).get(address.narrowcast[0][1], {}).iterkeys()
                else:
                    for family, multicastID in address.narrowcast:
                        clientIDs.extend(self.subscriptionsByAddress.get(family, {}).get(multicastID, {}).keys())

                done = 1
            if not done:
                if len(address.narrowcast) == 1 and (idtype, address.narrowcast[0]) in self.spam:
                    spam = 1
                elif macho.mode == 'server':
                    if self.transportIDbyProxyNodeID:
                        spam, clientIDs, notfound = base.FindClientsAndHoles(idtype, address.narrowcast, len(self.transportIDbyProxyNodeID) * 2)
                    else:
                        spam, clientIDs, notfound = base.FindClientsAndHoles(idtype, address.narrowcast, 20)
                else:
                    spam, clientIDs, notfound = base.FindClientsAndHoles(idtype, address.narrowcast, None)
                if len(address.narrowcast) == 1 and spam:
                    self.LogInfo('Interpreting ', address.narrowcast, ' as a persistant spam address.')
                    if len(self.spam) > 1000:
                        self.spam.clear()
                    self.spam[idtype, address.narrowcast[0]] = 1
                if spam or macho.mode == 'server' and address.idtype[0] == '*' and len(notfound):
                    clientIDs = []
                    if macho.mode == 'server':
                        nodeIDs = self.transportIDbyProxyNodeID.iterkeys()
                    else:
                        nodeIDs = self.transportIDbySolNodeID.iterkeys()
            transportIDs = {}
            if macho.mode == 'server' and self.transportIDbyProxyNodeID:
                for clientID in clientIDs:
                    nodeID = self.GetProxyNodeIDFromClientID(clientID)
                    if nodeID in self.transportIDbyProxyNodeID:
                        transportIDs[self.transportIDbyProxyNodeID[nodeID]] = 1
                        if len(transportIDs) == len(self.transportIDbyProxyNodeID):
                            if len(transportIDs) > 2:
                                self.LogInfo('All proxies targeted in a clientID based routing decision. If this happens frequently, the caller might consider a better casting method.', address)
                            break

            else:
                for each in clientIDs:
                    if self.transportIDbyClientID.has_key(each) and self.transportsByID.has_key(self.transportIDbyClientID[each]):
                        transportIDs[self.transportIDbyClientID[each]] = 1
                    else:
                        self.LogInfo('Transport for client ', each, ' not found while sending narrowcast.')

            for each in nodeIDs:
                if macho.mode == 'server' and self.transportIDbyProxyNodeID.has_key(each) and self.transportsByID.has_key(self.transportIDbyProxyNodeID[each]):
                    transportIDs[self.transportIDbyProxyNodeID[each]] = 1
                elif macho.mode == 'proxy' and self.transportIDbySolNodeID.has_key(each) and self.transportsByID.has_key(self.transportIDbySolNodeID[each]):
                    transportIDs[self.transportIDbySolNodeID[each]] = 1
                elif self.transportIDbyAppNodeID.has_key(each) and self.transportsByID.has_key(self.transportIDbyAppNodeID[each]):
                    transportIDs[self.transportIDbyAppNodeID[each]] = 1
                elif self.transportIDbySolNodeID.has_key(each) and self.transportsByID.has_key(self.transportIDbySolNodeID[each]):
                    transportIDs[self.transportIDbySolNodeID[each]] = 1
                else:
                    self.LogInfo('Transport for node ', each, ' not found while sending narrowcast.')

            transportIDs = transportIDs.keys()
        elif idtype == 'nodeID':
            if address.idtype[0] == '+':
                transportIDs = self.transportIDbyProxyNodeID.values()
            else:
                transportIDs = self.transportIDbySolNodeID.values()
        elif macho.mode == 'server':
            transportIDs = self.transportsByID.keys()
        else:
            transportIDs = self.transportIDbyClientID.values()
        if transportIDs:
            self.broadcastsResolved.Add(len(transportIDs))
        else:
            self.broadcastsMissed.Add()
        return transportIDs

    def OnGlobalConfigChanged(self, config):
        if 'oldShutdown' in config:
            val = int(config['oldShutdown'])
            self.LogNotice('Setting oldShutdown to', val)
            prefs.SetValue('oldShutdown', val)
        settings = {}
        if 'stacklessioVersion' in config:
            settings['version'] = int(config['stacklessioVersion'])
        if 'stacklessioUseNoblock' in config:
            settings['useNoblock'] = bool(config['stacklessioUseNoblock'])
        if 'stacklessioAllocChunkSize' in config:
            settings['allocChunkSize'] = int(config['stacklessioAllocChunkSize'])
        if settings:
            import stacklessio._socket
            stacklessio._socket.apply_settings(settings)
            self.LogNotice('Applied stacklessio settings for client: ', repr(settings))

    def LogClientCall(self, session, objectName, method, args, kwargs):
        with util.ExceptionEater('LogClientCall'):

            def CleanKeywordArgs(kwargs):
                cleanKwargs = {}
                if kwargs:
                    cleanKwargs = {k:v for k, v in kwargs.iteritems() if k != 'machoVersion'}
                return cleanKwargs

            excludedMethods = ['GetTime']
            if method in excludedMethods:
                return
            logAll = self.logAllClientCalls
            if logAll is None and prefs.clusterMode == 'LOCAL':
                logAll = 1
            if logAll:
                self.clientCallLogChannel = log.Channel(str(macho.mode), 'ClientCalls')
                callerInfo = 'User %s' % session.userid
                try:
                    callerInfo = 'Char %s (%s)' % (session.charid, cfg.eveowners.Get(session.charid).name)
                except:
                    pass

                kwargsTxt = ''
                if kwargs:
                    kk = CleanKeywordArgs(kwargs)
                    if kk:
                        kwargsTxt = '. kwargs = %s' % repr(kk)
                self.clientCallLogChannel.Log('%s called %s.%s%s%s' % (callerInfo,
                 objectName,
                 method,
                 repr(args)[:128],
                 kwargsTxt[:128]), log.LGNOTICE)
            if not self.sessionWatchIDs:
                return
            charID = getattr(session, 'charid', None)
            if not charID:
                return
            userID = getattr(session, 'userid', None)
            corpID = getattr(session, 'corpid', None)
            userType = getattr(session, 'userType', None)
            solarSystemID = getattr(session, 'solarsystemid2', None)
            logIt = False
            if userID in self.sessionWatchIDs[0]:
                logIt = True
            elif charID in self.sessionWatchIDs[1]:
                logIt = True
            elif corpID in self.sessionWatchIDs[2]:
                logIt = True
            elif userType in self.sessionWatchIDs[3]:
                logIt = True
            elif session.role & ROLEMASK_ELEVATEDPLAYER:
                logIt = True
            if logIt:
                a = repr(args)
                k = repr(CleanKeywordArgs(kwargs))
                sm.GetService('eventLog').LogOwnerEvent('ClientCall', charID, solarSystemID, userID, objectName, method, len(a), a[:1024], len(k), k[:1024])


exports = {'macho.MachoException': MachoException,
 'macho.MachoWrappedException': MachoWrappedException,
 'macho.UnMachoDestination': UnMachoDestination,
 'macho.UnMachoChannel': UnMachoChannel,
 'macho.WrongMachoNode': WrongMachoNode}
util.InitWhitelist()