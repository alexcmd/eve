#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/common/script/sys/eveService.py
import service
import types
import locks
import log
import blue
ROLE_BANNING = 2L
ROLE_MARKET = 4L
ROLE_MARKETH = 8L
ROLE_CSMADMIN = 16L
ROLE_CSMDELEGATE = 32L
ROLE_PINKCHAT = 64L
ROLE_VGSADMIN = 128L
ROLE_PETITIONEE = 256L
ROLE_CDKEYS = 512L
ROLE_VGSMANAGER = 1024L
ROLE_CENTURION = 2048L
ROLE_WORLDMOD = 4096L
ROLE_LEGIONEER = 262144L
ROLE_HEALSELF = 4194304L
ROLE_HEALOTHERS = 8388608L
ROLE_NEWSREPORTER = 16777216L
ROLE_SPAWN = 8589934592L
ROLE_BATTLESERVER = 17179869184L
ROLE_WIKIEDITOR = 68719476736L
ROLE_TRANSFER = 137438953472L
ROLE_GMS = 274877906944L
service.ROLEMASK_ELEVATEDPLAYER = service.ROLEMASK_ELEVATEDPLAYER & ~ROLE_NEWSREPORTER
exports = {}
consts = {}
for i in globals().items():
    if type(i[1]) in (types.IntType, types.LongType):
        exports['service.' + i[0]] = i[1]
        consts[i[0]] = i[1]

def GetClusterSingletonNodeFromAddress(mn, machoresolve):
    try:
        num = int(machoresolve.split('_')[1])
    except:
        log.general.Log('clustersingleton machoresolve without mod number. Using 0')
        num = 0

    numMod = num % const.CLUSTERSINGLETON_MOD
    if num >= const.CLUSTERSINGLETON_MOD:
        log.general.Log('clustersingleton machoresolve with out-of-bounds mod number', num, 'rolling over to', numMod, log.LGWARN)
    return mn.GetNodeFromAddress(const.cluster.SERVICE_CLUSTERSINGLETON, numMod)


def _MachoResolveAdditional(self, sess):
    if self.__machoresolve__ is not None:
        mn = sm.services['machoNet']
        if not sess.role & service.ROLE_SERVICE:
            if self.__machoresolve__ == 'station':
                if not sess.stationid2:
                    return 'You must be located at a station to use this service'
                return mn.GetNodeFromAddress('station', sess.stationid2)
            if self.__machoresolve__ == 'solarsystem':
                if not sess.solarsystemid:
                    return 'You must be located in a solar system to use this service'
                return mn.GetNodeFromAddress(const.cluster.SERVICE_BEYONCE, sess.solarsystemid)
            if self.__machoresolve__ == 'solarsystem2':
                if not sess.solarsystemid2:
                    return 'Your location must belong to a known solarsystem'
                return mn.GetNodeFromAddress(const.cluster.SERVICE_BEYONCE, sess.solarsystemid2)
            if self.__machoresolve__ in ('location', 'locationPreferred'):
                if not sess.locationid:
                    if self.__machoresolve__ == 'locationPreferred':
                        return
                    return 'You must be located in a solar system or at station to use this service'
                if sess.solarsystemid:
                    return mn.GetNodeFromAddress(const.cluster.SERVICE_BEYONCE, sess.solarsystemid)
                if session.stationid:
                    return mn.GetNodeFromAddress('station', sess.stationid)
                if session.worldspaceid:
                    return mn.GetNodeFromAddress(const.cluster.SERVICE_WORLDSPACE, sess.worldspaceid)
                raise RuntimeError('machoresolving a location bound service with without a location session')
            elif self.__machoresolve__ in ('character',):
                if sess.charid is None:
                    return
                else:
                    return mn.GetNodeFromAddress(const.cluster.SERVICE_CHARACTER, sess.charid % const.CHARNODE_MOD)
            elif self.__machoresolve__ in ('corporation',):
                if sess.corpid is None:
                    return 'You must have a corpid in your session to use this service'
                else:
                    return mn.GetNodeFromAddress(const.cluster.SERVICE_CHATX, sess.corpid % 200)
            else:
                if self.__machoresolve__ == 'bulk':
                    if sess.userid is None:
                        return 'You must have a userid in your session to use this service'
                    return mn.GetNodeFromAddress(const.cluster.SERVICE_BULK, sess.userid % const.BULKNODE_MOD)
                if self.__machoresolve__.startswith('clustersingleton'):
                    return GetClusterSingletonNodeFromAddress(mn, self.__machoresolve__)
                raise RuntimeError('This service is crap (%s)' % self.__logname__)


class EveService(service.CoreService):
    pass


class AppProxyService(EveService):
    __solservice__ = None

    def __init__(self):
        self.solNodeID = None
        EveService.__init__(self)

    def GetSolNodeService(self):
        if not getattr(self, '__solservice__'):
            self.LogError('Application Proxy Service incorrectly configured. The service requires the __solservice__ attribute which is a tuple of (solServiceName, serviceMask, serviceBucket)')
            return
        solServiceName, serviceMask, bucket = self.__solservice__
        if self.solNodeID is not None:
            if self.solNodeID not in sm.services['machoNet'].transportIDbySolNodeID:
                self.LogWarn('Sol node', self.solNodeID, ' is no longer available. Finding a new one...')
                self.solNodeID = None
        if self.solNodeID is None:
            svc = self.session.ConnectToSolServerService('machoNet', None)
            nodeID = svc.GetNodeFromAddress(serviceMask, bucket)
            if nodeID is None or nodeID <= 0:
                raise RuntimeError('Could not find any sol nodes with mask %s' % serviceMask)
            self.LogInfo('Found a new sol node at', nodeID)
            self.solNodeID = nodeID
        svc = self.session.ConnectToSolServerService(solServiceName, nodeID=self.solNodeID)
        return svc


class ClusterSingletonService(EveService):
    __ready__ = 0

    def Run(self, *args):
        service.Service.Run(self, *args)
        sm.RegisterForNotifyEvent(self, 'OnClusterStartup')
        sm.RegisterForNotifyEvent(self, 'OnNodeDeath')

    def PrimeService(self):
        raise NotImplementedError('You cannot inherit from ClusterSingletonService without implementing PrimeService()')

    def _MachoResolveClusterSingleton(self):
        if getattr(self, '__machoresolve__', None):
            serviceNodeID = GetClusterSingletonNodeFromAddress(self.machoNet, self.__machoresolve__)
        else:
            serviceNodeID = self.MachoResolve(session)
        return serviceNodeID

    def _ShouldPrimeService(self):
        if self.__ready__:
            return False
        serviceNodeID = self._MachoResolveClusterSingleton()
        myNodeID = self.machoNet.GetNodeID()
        if serviceNodeID and myNodeID != serviceNodeID:
            return False
        return True

    def _PrimeService(self):
        with locks.TempLock((self, 'PrimeService')):
            if not self.__ready__:
                try:
                    self.LogInfo('Priming clustersingleton service...')
                    startTime = blue.os.GetWallclockTimeNow()
                    self.PrimeService()
                    self.LogNotice('Done priming clustersingleton service %s in %.3f seconds.' % (self.__logname__, (blue.os.GetWallclockTimeNow() - startTime) / float(const.SEC)))
                except Exception as e:
                    log.LogException('Error priming Cluster Singleton service %s' % self.__logname__)
                finally:
                    self.__ready__ = 1

    def PreCallAction(self, methodName):
        if not self._ShouldPrimeService():
            return
        self._PrimeService()

    def OnClusterStartup(self):
        if not self._ShouldPrimeService():
            return
        self.LogNotice('I am the right node for this cluster singleton service at startup. Priming the service...')
        self._PrimeService()

    def OnNodeDeath(self, nodeID, confirmed, reason = None):
        if not self._ShouldPrimeService():
            return
        self.LogWarn('Old Cluster Singleton node %s for this service has died. I will now service calls. Starting by priming Service' % nodeID)
        self._PrimeService()


exports.update({'service._MachoResolveAdditional': _MachoResolveAdditional,
 'service.Service': EveService,
 'service.consts': consts,
 'service.AppProxyService': AppProxyService,
 'service.ClusterSingletonService': ClusterSingletonService})