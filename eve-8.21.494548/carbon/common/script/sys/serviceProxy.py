#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/sys/serviceProxy.py
import svc
import logging
import zlib
import types
import inspect
import service
import random
import uthread

class ServiceProxy(object):
    __guid__ = 'service.ServiceProxy'
    _methods = {}

    def __init__(self, serviceName, session):
        self._serviceName = serviceName
        self._session = session
        if serviceName not in self._methods or prefs.clusterMode == 'LOCAL':
            self._methods[serviceName] = self._WrapService(serviceName)
        for methodName, method in self._methods[serviceName].iteritems():
            setattr(self, methodName, types.MethodType(method, self, self.__class__))

    def __repr__(self):
        return '<ServiceProxy service=%s session=%s>' % (str(self._serviceName), str(self._session))

    def _WrapService(self, serviceName):
        serviceClass = getattr(svc, sm.GetServiceImplementation(serviceName))
        defaultResolve = getattr(serviceClass, '__serviceproxyresolve__', None)
        exportedCalls = getattr(serviceClass, '__exportedcalls__', {})
        exportedCalls = [ (k, v) for k, v in exportedCalls.iteritems() if isinstance(v, dict) ]
        wrappedMethods = {}
        for methodName, definition in exportedCalls:
            resolve = definition.get('resolve', defaultResolve)
            if resolve is not None:
                wrappedMethods[methodName] = self._WrapServiceMethod(methodName, getattr(serviceClass, methodName), resolve)

        return wrappedMethods

    def _WrapServiceMethod(self, methodName, method, resolve):
        resolveConst, resolveArgument = resolve
        argspec = inspect.getargspec(method)
        if isinstance(resolveArgument, str):
            resolveArgumentIndex = argspec[0].index(resolveArgument) - 1
        elif isinstance(resolveArgument, int) and resolveArgument in const.cluster.NODES:
            resolveArgumentIndex = None
        else:
            raise RuntimeError("Resolve argument '%s' for ServiceProxy '%s' is invalid" % (str(resolveArgument), self))

        def wrapped(self, *args, **kwargs):
            try:
                if resolveArgumentIndex is None:
                    resolveValue = resolveArgument
                else:
                    resolveValue = kwargs.get(resolveArgument, args[resolveArgumentIndex])
                    if isinstance(resolveValue, basestring):
                        resolveValue = zlib.crc32(resolveValue)
                    elif resolveValue is None:
                        resolveValue = 0
            except ValueError:
                raise RuntimeError("ServiceProxy could not find the resolve argument '%s' for the method '%s'" % (str(resolveArgument), methodName))

            if resolveArgument == const.cluster.NODE_ALL:
                nodes = self._GetNodesFromServiceID(resolveConst, server=True, proxy=True)
            elif resolveArgument == const.cluster.NODE_ALL_SERVER:
                nodes = self._GetNodesFromServiceID(resolveConst, server=True)
            elif resolveArgument == const.cluster.NODE_ALL_PROXY:
                nodes = self._GetNodesFromServiceID(resolveConst, proxy=True)
            elif resolveArgument == const.cluster.NODE_ANY:
                nodes = random.choice(self._GetNodesFromServiceID(resolveConst, server=True, proxy=True))
            elif resolveArgument == const.cluster.NODE_ANY_SERVER:
                nodes = random.choice(self._GetNodesFromServiceID(resolveConst, server=True))
            elif resolveArgument == const.cluster.NODE_ANY_PROXY:
                nodes = random.choice(self._GetNodesFromServiceID(resolveConst, proxy=True))
            else:
                machoNet = sm.GetService('machoNet').session.ConnectToSolServerService('machoNet')
                serviceMod = const.cluster.SERVICE_MODS.get(resolveConst, const.cluster.SERVICE_MOD_DEFAULT)
                nodes = machoNet.GetNodeFromAddress(resolveConst, resolveValue % serviceMod)
            return ServiceProxyCall(self._session, self._serviceName, methodName, nodes)(*args, **kwargs)

        execdict = {'wrapped': wrapped}
        exec 'def %s%s: return wrapped(%s)' % (methodName, inspect.formatargspec(*argspec), ', '.join(argspec[0])) in execdict
        wrapped = execdict.get(methodName, wrapped)
        setattr(wrapped, '__doc__', method.__doc__)
        setattr(wrapped, '__name__', method.__name__)
        return wrapped

    def _GetNodesFromServiceID(self, serviceID, server = False, proxy = False):
        machoNet = sm.GetService('machoNet')
        serviceMask = 1 << serviceID - 1
        nodes = machoNet.ResolveServiceMaskToNodeIDs(serviceMask)
        if serviceMask & machoNet.serviceMask:
            nodes.add(machoNet.GetNodeID())
        if proxy == False:
            nodes = [ nodeID for nodeID in nodes if nodeID < const.maxNodeID ]
        if server == False:
            nodes = [ nodeID for nodeID in nodes if nodeID >= const.maxNodeID ]
        if not len(nodes):
            raise RuntimeError('ServiceProxy::GetNodesFromServiceID found no nodes for serviceID=%s (server=%s, proxy=%s)' % (serviceID, server, proxy))
        return list(nodes)


class ServiceProxyCall(object):
    __guid__ = 'service.ServiceProxyCall'

    def __init__(self, session, serviceName, methodName, nodes):
        self._session = session
        self._serviceName = serviceName
        self._methodName = methodName
        self._nodes = nodes

    def __call__(self, *args, **kwargs):
        if not isinstance(self._nodes, (list, set, tuple)):
            return self._CallNode(self._nodes, *args, **kwargs)
        calls = [ (self._CallNode, [nodeID] + list(args), kwargs) for nodeID in self._nodes ]
        return uthread.parallel(calls)

    def _CallNode(self, nodeID, *args, **kwargs):
        service = self._session.ConnectToRemoteService(self._serviceName, nodeID=nodeID)
        return getattr(service, self._methodName)(*args, **kwargs)