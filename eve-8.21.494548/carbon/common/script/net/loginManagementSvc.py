#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/net/loginManagementSvc.py
import sys
import service
import blue
import const
import log
import base
import localization
import uthread
import string
import util

def _QueueTicker(queue, name, svc):
    while queue.ticker is not None:
        svc.LogInfo('Started Login Queue Ticker task for queue ', name)
        blue.pyos.synchro.SleepWallclock(60000)
        if queue.ticker is not None:
            try:
                if queue.queueTimeout > 0:
                    l = queue.Timeout(queue.queueTimeout)
                    if len(l) > 0:
                        svc.LogWarn('Timed ', len(l), " clients out of login queue '", name, "' (timeout = ", queue.queueTimeout, ' sec)')
                queue.Tick()
            except:
                log.LogException('Exception in _QueueTicker tasklet')


class LoginManagementService(service.Service):
    __guid__ = 'svc.loginManagementSvc'
    __displayname__ = 'Login queues management system'
    __exportedcalls__ = {'CreateQueue': [service.ROLE_SERVICE],
     'GetQueue': [service.ROLE_SERVICE],
     'GetQueueStats': [service.ROLE_SERVICE],
     'GetQueueSettings': [service.ROLE_SERVICE],
     'SetQueueSettings': [service.ROLE_SERVICE],
     'QueuesDisabled': [service.ROLE_SERVICE]}
    __configvalues__ = {'enableQueuesInLocal': False}

    def Run(self, memStream = None):
        self.queuesByName = {}

    def Stop(self, memStream):
        for q in queuesByName.itervalues():
            q.ticker = None

        service.Service.Stop(self, memStream)

    def CreateQueue(self, qname, defMaxCompleteItems, defMaxReadyItems, defMaxReadyRate = sys.maxint, defMaxReadyGrowth = 0, defMaxQueuedItems = sys.maxint, defTimeout = 180.0, numCompleteFunc = None):
        if qname is None:
            raise RuntimeError("'qname' cannot be None")

        def GetOrSetPref(setting, defVal):
            prefKey = 'LoginQueue_' + qname + '_' + setting
            pref = prefs.GetValue(prefKey, None)
            if pref is None:
                self.LogWarn('Login Queue setting %s not in prefs, setting to default (%s)' % (prefKey, defVal))
                prefs.SetValue(prefKey, defVal)
                pref = prefs.GetValue(prefKey, defVal)
            try:
                return int(pref)
            except ValueError:
                self.LogError("Login Queue setting %s has invalid value '%s' in prefs, using default (%s)" % (prefKey, pref, defVal))
                return int(defVal)

        maxReadyItems = GetOrSetPref('MaxReady', defMaxReadyItems)
        maxReadyRate = GetOrSetPref('MaxLoginRate', defMaxReadyRate)
        maxReadyGrowth = GetOrSetPref('ReadyGrowth', defMaxReadyGrowth)
        maxQueuedItems = GetOrSetPref('MaxInQueue', defMaxQueuedItems)
        maxCompleteItems = GetOrSetPref('MaxLoggedIn', defMaxCompleteItems)
        timeout = GetOrSetPref('QueueTimeout', defTimeout)
        if self.QueuesDisabled():
            maxReadyItems = sys.maxint
            maxReadyRate = sys.maxint
            maxReadyGrowth = 0
            maxQueuedItems = sys.maxint
            maxCompleteItems = sys.maxint
            timeout = 0
        if qname in self.queuesByName:
            return self.queuesByName[qname]
        else:
            log.LogInfo("Creating Login Queue '", qname, "'")
            queue = util.RateLimitedQueue(maxReadyItems=maxReadyItems, maxReadyRate=maxReadyRate, maxReadyGrowth=maxReadyGrowth, maxQueuedItems=maxQueuedItems, maxCompleteItems=maxCompleteItems, numCompleteFunc=numCompleteFunc)
            self.queuesByName[qname] = queue
            queue.queueTimeout = timeout
            queue.ticker = uthread.new(_QueueTicker, queue, qname, self)
            return queue

    def GetQueue(self, qname, default = None):
        return self.queuesByName.get(qname, default)

    def GetQueueStats(self, qname = None, default = None):
        if qname is None:
            return {qname:self._GetQueueStats(queue) for qname, queue in self.queuesByName.iteritems()}
        else:
            queue = self.queuesByName.get(qname, None)
            if queue is not None:
                return self._GetQueueStats(queue)
            return default

    def GetQueueSettings(self, qname = None, default = None):
        if qname is None:
            return {qname:self._GetQueueSettings(queue) for qname, queue in self.queuesByName.iteritems()}
        else:
            queue = self.queuesByName.get(qname, None)
            if queue is not None:
                return self._GetQueueSettings(queue)
            return default

    def SetQueueSettings(self, qname, **kwargs):
        if qname is None:
            raise RuntimeError("'qname' cannot be None")
        if qname not in self.queuesByName:
            raise RuntimeError("There is no Login Queue named '" + str(qname) + "'")
        queue = self.queuesByName[qname]
        validKeys = self._GetQueueSettings(queue)
        for k in kwargs.iterkeys():
            if k not in validKeys:
                raise RuntimeError("Invalid Queue Setting: '" + str(k) + "'")

        def UpdatePref(setting, pref, blankValue):
            if setting in kwargs:
                attrname = string.lower(setting[0]) + setting[1:]
                value = kwargs[setting] if kwargs[setting] is not None else blankValue
                try:
                    value = int(value)
                except ValueError:
                    self.LogError("Queue Setting %s = '%s' is invalid (is not an integer)" % (setting, value))
                    return

                setattr(queue, attrname, value)
                prefKey = 'LoginQueue_' + qname + '_' + pref
                prefs.SetValue(prefKey, value)

        UpdatePref('MaxQueuedItems', 'MaxInQueue', sys.maxint)
        UpdatePref('MaxReadyItems', 'MaxReady', sys.maxint)
        UpdatePref('MaxReadyRate', 'MaxLoginRate', sys.maxint)
        UpdatePref('MaxCompleteItems', 'MaxLoggedIn', sys.maxint)
        UpdatePref('MaxReadyGrowth', 'ReadyGrowth', 0)
        UpdatePref('QueueTimeout', 'QueueTimeout', 0)

    def _GetQueueStats(self, queue):
        wait = queue.QueueFrontWaitTime()
        return {'NumQueued': queue.NumQueued(),
         'NumReady': queue.NumReady(),
         'NumComplete': queue.NumComplete(),
         'QueueFrontWaitTime': round(wait) if wait is not None else 0.0}

    def _GetQueueSettings(self, queue):
        return {'MaxQueuedItems': queue.maxQueuedItems,
         'MaxReadyItems': queue.maxReadyItems,
         'MaxReadyRate': queue.maxReadyRate,
         'MaxCompleteItems': queue.maxCompleteItems,
         'MaxReadyGrowth': queue.maxReadyGrowth,
         'QueueTimeout': queue.queueTimeout}

    def QueuesDisabled(self):
        return prefs.clusterMode == 'LOCAL' and not self.enableQueuesInLocal

    def SignalTickerStop(self):
        self.ticker = None