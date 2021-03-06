#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/sys/sessions.py
from __future__ import with_statement
import blue
import bluepy
import uthread
import weakref
import localization
import log
import copy
import types
import util
import macho
import sys
import service
import base
import const
import random
from collections import deque
from collections import defaultdict
from service import *
SESSIONCHANGEDELAY = 10 * const.SEC
allObjectConnections = weakref.WeakKeyDictionary({})
allConnectedObjects = weakref.WeakKeyDictionary({})
service_sessions = {}
local_sid = 0
sessionsByAttribute = {'userid': {},
 'userType': {},
 'charid': {},
 'objectID': {}}
sessionsBySID = {}
allSessionsBySID = weakref.WeakValueDictionary({})
__contextOnlyTypes__ = []

def ThrottlePerMinute(max = 1, message = 'GenericStopSpamming'):

    def Helper(f):

        def Wrapper(*args, **kwargs):
            if session is not None and session.role & ROLE_PLAYER == ROLE_PLAYER:
                session.Throttle(f.__name__, max, const.MIN, message)
            return f(*args, **kwargs)

        return Wrapper

    return Helper


def ThrottlePer5Minutes(max = 1, message = 'GenericStopSpamming'):

    def Helper(f):

        def Wrapper(*args, **kwargs):
            if session is not None and session.role & ROLE_PLAYER == ROLE_PLAYER:
                session.Throttle(f.__name__, max, 5 * const.MIN, message)
            return f(*args, **kwargs)

        return Wrapper

    return Helper


def ThrottlePerSecond(max = 1, message = 'GenericStopSpamming'):

    def Helper(f):

        def Wrapper(*args, **kwargs):
            if session is not None and session.role & ROLE_PLAYER == ROLE_PLAYER:
                session.Throttle(f.__name__, max, const.SEC, message)
            return f(*args, **kwargs)

        return Wrapper

    return Helper


dyingObjects = deque()

def ObjectKillah():
    n = 0
    while 1:
        maxNumObjects = prefs.GetValue('objectKillahMaxObjects', -1)
        sleepTime = prefs.GetValue('objectKilla.SleepWallclockTime', 30)
        if dyingObjects and (maxNumObjects <= 0 or n < maxNumObjects):
            delay = (dyingObjects[0][0] - blue.os.GetWallclockTime()) / SEC
            delay = min(delay, 30)
            if delay > 0:
                blue.pyos.synchro.SleepWallclock(1000 * delay)
            else:
                dietime, diediedie = dyingObjects.popleft()
                try:
                    with bluepy.Timer('sessions::' + diediedie.GetObjectConnectionLogClass()):
                        diediedie.DisconnectObject()
                except Exception:
                    log.LogException()
                    sys.exc_clear()

                del diediedie
                n += 1
        else:
            if maxNumObjects > 0 and n >= maxNumObjects:
                log.general.Log("ObjectKillah killed the maximum number of allowed objects for this round, %d, which means that we're lagging behind! Sleeping for %d seconds" % (maxNumObjects, sleepTime), log.LGWARN)
            elif n > 0:
                if maxNumObjects > 0:
                    log.general.Log('ObjectKillah killed %d objects for this round out of a maximum of %d. Sleeping for %d seconds' % (n, maxNumObjects, sleepTime), log.LGINFO)
                else:
                    log.general.Log('ObjectKillah killed %d objects for this round. Sleeping for %d seconds' % (n, sleepTime), log.LGINFO)
            n = 0
            blue.pyos.synchro.SleepWallclock(1000 * sleepTime)


uthread.new(ObjectKillah).context = 'sessions::ObjectKillah'

def SessionKillah(machoNet):
    DEF_SESS_TIMEOUT = 120
    DEF_CTXSESS_TIMEOUT = 60
    DEF_SLEEPTIME = 30
    sleepTime = prefs.GetValue('sessionKillah.SleepTime', DEF_SLEEPTIME) * 1000
    while True:
        try:
            blue.pyos.synchro.SleepWallclock(sleepTime)
            killSessions = prefs.GetValue('sessionKillah.Enable', False)
            sessTimeout = prefs.GetValue('sessionKillah.SessionTimeout', DEF_SESS_TIMEOUT) * 1000
            ctxSessTimeout = prefs.GetValue('sessionKillah.ContextSessionTimeout', DEF_CTXSESS_TIMEOUT) * 1000
            sleepTime = prefs.GetValue('sessionKillah.SleepTime', DEF_SLEEPTIME) * 1000
            ReadContextSessionTypesPrefs()
            if killSessions:
                now = blue.os.GetWallclockTime()
                toRemove = defaultdict(list)
                for transport in machoNet.transportsByID.itervalues():

                    def AddIfIrrelevant(sess, timeout):
                        if sess.role & ROLE_SERVICE == 0 and not sess.connectedObjects and getattr(sess, 'charid', None):
                            if sess.contextOnly:
                                irrelevant = now - sess.lastRemoteCall >= timeout
                            else:
                                irrelevant = sess.irrelevanceTime is not None and now - sess.irrelevanceTime >= timeout
                            if irrelevant:
                                toRemove[transport].append(sess.sid)

                    for sess in transport.sessions.itervalues():
                        AddIfIrrelevant(sess, sessTimeout)

                    for sess in transport.contextSessions.itervalues():
                        AddIfIrrelevant(sess, ctxSessTimeout)

                myNodeID = machoNet.GetNodeID()
                for transport, sids in toRemove.iteritems():
                    try:
                        log.LogInfo('Asking proxy ', transport.nodeID, ' to remove ', len(sids), ' session(s)')
                        proxySessionMgr = machoNet.session.ConnectToRemoteService('sessionMgr', nodeID=transport.nodeID)
                        proxySessionMgr.RemoveSessionsFromServer(myNodeID, sids)
                    except StandardError:
                        log.LogException('While removing irrelevant session from serer')
                        sys.exc_clear()

        except Exception:
            log.LogException('In SessionKillah loop, caught to keep thread alive')
            sys.exc_clear()


def ReadContextSessionTypesPrefs():
    global __contextOnlyTypes__
    try:
        __contextOnlyTypes__ = []
        PREFS_PARAMETER = 'ContextSessionTypes'
        prefValue = prefs.GetValue(PREFS_PARAMETER, None)
        if prefValue is not None:
            log.LogInfo('CTXSESS: ', PREFS_PARAMETER, ' = ', prefValue)
            contextTypes = prefValue.split(',')
            for typeName in contextTypes:
                if typeName in const.session.SESSION_NAME_TO_TYPE:
                    __contextOnlyTypes__.append(const.session.SESSION_NAME_TO_TYPE[typeName])
                else:
                    log.LogError("Ignoring invalid session type '", typeName, "' in prefs parameter '", PREFS_PARAMETER, "'")

        else:
            log.LogInfo('CTXSESS: ', PREFS_PARAMETER, ' not provided, no context sessions will bre created')
    except StandardError:
        log.LogException("Exception while parsing prefs parameter '", PREFS_PARAMETER, "'")


ReadContextSessionTypesPrefs()

def GetUndeadObjects():
    global allSessionsBySID
    global allConnectedObjects
    global allObjectConnections
    from util import allMonikers
    while 1:
        obs = []
        for each in allConnectedObjects.iterkeys():
            obs.append(each)

        break

    while 1:
        con = []
        for each in allObjectConnections.iterkeys():
            con.append(each)

        break

    while 1:
        ses = []
        for each in allSessionsBySID.itervalues():
            ses.append(each)

        break

    while 1:
        mon = []
        for each in allMonikers.iterkeys():
            mon.append(each)

        break

    zombies = []
    bombies = []
    for each in con:
        liveone = 0
        for other in ses:
            for yetanother in other.connectedObjects.itervalues():
                if each is yetanother[0]:
                    liveone = 1
                    break

        if not liveone:
            for other in mon:
                if other.boundObject is each:
                    liveone = 1
                    break

        if not liveone:
            zombies.append(each)

    for each in obs:
        liveone = 0
        for other in con:
            if other.__object__ is each:
                liveone = 1
                for yetanother in zombies:
                    if yetanother is other:
                        liveone = 2

                if liveone:
                    break

        if not liveone:
            zombies.append(each)
        elif liveone == 2:
            bombies.append(each)

    return (zombies, bombies)


class MasqueradeMask(object):

    def __init__(self, props):
        self.__prevStorage = UpdateLocalStorage(props)

    def __enter__(self):
        pass

    def __exit__(self, e, v, tb):
        self.UnMask()

    def UnMask(self):
        SetLocalStorage(self.__prevStorage)
        self.__prevStorage = None


callTimerKeys = {}
serviceCallTimes = {}
webCallTimes = {}
userCallTimes = {}
outstandingCallTimers = []
methodCallHistory = deque(maxlen=1000)

class RealCallTimer():
    TimerType = 2

    def __init__(self, k):
        k = callTimerKeys.setdefault(k, k)
        self.key = k
        UpdateLocalStorage({'calltimer.key': k})
        if not session:
            self.mask = GetServiceSession('DefaultCallTimer').Masquerade()
        else:
            self.mask = None
        self.start = blue.os.GetWallclockTimeNow()
        outstandingCallTimers.append((k, self.start))

    def Done(self):
        stop = blue.os.GetWallclockTimeNow()
        t = stop - self.start
        if t < 0:
            log.general.Log('blue.os.GetWallclockTimeNow() is running backwards... now=%s, start=%s' % (stop, self.start), 2, 1)
            t = 0
        if session and not session.role & ROLE_SERVICE:
            if getattr(session, 'clientID', 0):
                other = userCallTimes
            else:
                other = webCallTimes
        else:
            other = serviceCallTimes
        for calltimes in (session.calltimes, other):
            if self.key not in calltimes:
                theCallTime = [0,
                 0,
                 -1,
                 -1,
                 0,
                 0]
                calltimes[self.key] = theCallTime
            else:
                theCallTime = calltimes[self.key]
            theCallTime[0] += 1
            theCallTime[1] += t
            if theCallTime[2] == -1 or t < theCallTime[2]:
                theCallTime[2] = t
            if theCallTime[3] == -1 or t > theCallTime[3]:
                theCallTime[3] = t

        if self.mask:
            self.mask.UnMask()
        if macho.mode == 'client':
            k = (self.key, self.start, t)
            methodCallHistory.append(k)
        try:
            outstandingCallTimers.remove((self.key, self.start))
        except:
            sys.exc_clear()

    def __enter__(self):
        pass

    def __exit__(self, e, v, tb):
        self.Done()


class BasicCallTimer(object):
    TimerType = 1

    def __init__(self, k):
        k = callTimerKeys.setdefault(k, k)
        self.key = k
        self.start = blue.os.GetWallclockTimeNow()

    def Done(self):
        stop = blue.os.GetWallclockTimeNow()
        elapsed = stop - self.start
        if session and not session.role & ROLE_SERVICE:
            if getattr(session, 'clientID', 0):
                callTimes = userCallTimes
            else:
                callTimes = webCallTimes
        else:
            callTimes = serviceCallTimes
        if elapsed < 0:
            log.general.Log('blue.os.GetWallclockTimeNow() is running backwards... now=%s, start=%s' % (stop, self.start), 2, 1)
            elapsed = 0
        if self.key not in callTimes:
            callEntry = [0,
             0,
             -1,
             -1,
             0,
             0]
            callTimes[self.key] = callEntry
        else:
            callEntry = callTimes[self.key]
        callEntry[0] += 1
        callEntry[1] += elapsed
        if callEntry[2] == -1 or elapsed < callEntry[2]:
            callEntry[2] = elapsed
        if callEntry[3] == -1 or elapsed > callEntry[3]:
            callEntry[3] = elapsed

    def __enter__(self):
        pass

    def __exit__(self, e, v, tb):
        self.Done()


class DummyCallTimer(object):
    TimerType = 0

    def __init__(self, k):
        pass

    def Done(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, e, v, tb):
        pass


CallTimer = DummyCallTimer

def EnableCallTimers(timerType):
    global CallTimer
    was = CallTimer.TimerType
    if timerType == 0:
        CallTimer = DummyCallTimer
    elif timerType == 1:
        CallTimer = BasicCallTimer
    else:
        CallTimer = RealCallTimer
    import base
    base.CallTimer = CallTimer
    return was


def CallTimersEnabled():
    return CallTimer.TimerType


def GetCallTimes():
    return (userCallTimes, serviceCallTimes, webCallTimes)


class CoreSession():
    __guid__ = 'base.CoreSession'
    __persistvars__ = ['userid',
     'languageID',
     'role',
     'charid',
     'address',
     'userType',
     'maxSessionTime',
     'sessionType']
    __nonpersistvars__ = ['sid',
     'c2ooid',
     'connectedObjects',
     'connectedServices',
     'clientID',
     'localSID',
     'numCestStreams',
     'contextOnly',
     'receivedVersion',
     'irrelevanceTime']
    __attributesWithDefaultValueOfZero__ = []

    def __init__(self, sid, localSID, role, sessionType, defaultVarList = []):
        if sessionType not in const.session.VALID_SESSION_TYPES:
            raise ValueError('Trying to create a session with an invalid session type')
        d = self.__dict__
        d['additionalNoSetAttributes'] = []
        defaultVarList = self.__persistvars__ + defaultVarList
        for attName in defaultVarList:
            d[attName] = self.GetDefaultValueOfAttribute(attName)

        d['version'] = 1
        d['receivedVersion'] = 1
        d['irrelevanceTime'] = None
        d['sid'] = sid
        d['localSID'] = localSID
        d['role'] = None
        d['sessionType'] = sessionType
        d['c2ooid'] = 1
        d['connectedObjects'] = {}
        d['connectedServices'] = {}
        d['calltimes'] = {}
        d['notificationID'] = 0L
        d['numCestStreams'] = 0
        d['machoObjectsByID'] = {}
        d['machoObjectConnectionsByObjectID'] = {}
        d['sessionVariables'] = {}
        d['lastRemoteCall'] = blue.os.GetWallclockTime()
        d['nextSessionChange'] = None
        d['sessionChangeReason'] = 'Initial State'
        d['rwlock'] = None
        d['sessionhist'] = []
        d['hasproblems'] = 0
        d['mutating'] = 0
        d['changing'] = None
        d['additionalDistributedProps'] = []
        d['additionalNonIntegralAttributes'] = []
        d['longAttributes'] = []
        d['additionalAttributesToPrint'] = []
        d['additionalHexAttributes'] = []
        d['callThrottling'] = {}
        d['contextOnly'] = macho.mode == 'server' and sessionType in __contextOnlyTypes__
        self.__ChangeAttribute('role', role)
        self.LogSessionHistory('Session created')

    def Throttle(self, key, throttleTimes, throttleInterval, userErrorMessage, userErrorParams = None):
        lastKeyTimes = self.callThrottling.get(key, [])
        now = blue.os.GetWallclockTime()
        if len(lastKeyTimes) >= throttleTimes:
            temp = []
            earliestTime = None
            for time in lastKeyTimes:
                if now - time < throttleInterval:
                    temp.append(time)
                    if earliestTime is None or time < earliestTime:
                        earliestTime = time

            if len(temp) >= throttleTimes:
                self.callThrottling[key] = temp
                remainingTime = earliestTime + throttleInterval - now if earliestTime is not None else throttleInterval
                mergedErrorParams = {'remainingTime': max(0L, remainingTime)}
                if userErrorParams is not None:
                    mergedErrorParams.update(userErrorParams)
                raise UserError(userErrorMessage, mergedErrorParams)
            else:
                lastKeyTimes = temp
        lastKeyTimes.append(now)
        self.callThrottling[key] = lastKeyTimes

    def IsMutating(self):
        return self.mutating

    def IsChanging(self):
        return self.changing is not None

    def IsItSafe(self):
        return not (self.IsMutating() or self.IsChanging())

    def IsItSemiSafe(self):
        return self.IsItSafe() or self.IsMutating() and self.IsChanging()

    def WaitUntilSafe(self):
        if session.IsItSafe():
            return
        timeWaited = 0
        while timeWaited <= 30000 and not session.IsItSafe():
            blue.pyos.synchro.SleepWallclock(100)
            timeWaited += 100

        if not session.IsItSafe():
            raise RuntimeError('Session did not become safe within 30secs')

    def RegisterMachoObjectConnection(self, objectID, connection, refID):
        connectionID = GetObjectUUID(connection)
        if objectID not in self.machoObjectConnectionsByObjectID:
            self.machoObjectConnectionsByObjectID[objectID] = [0, weakref.WeakValueDictionary({})]
        self.machoObjectConnectionsByObjectID[objectID][1][connectionID] = connection
        self.machoObjectConnectionsByObjectID[objectID][0] = max(self.machoObjectConnectionsByObjectID[objectID][0], refID)

    def UnregisterMachoObjectConnection(self, objectID, connection):
        connectionID = GetObjectUUID(connection)
        if objectID not in self.machoObjectConnectionsByObjectID:
            return None
        else:
            if connectionID in self.machoObjectConnectionsByObjectID[objectID][1]:
                log.LogTraceback('Unexpected Crapola:  connectionID still found in machoObjectConnectionsByObjectID[objectID]')
                del self.machoObjectConnectionsByObjectID[objectID][1][connectionID]
            if not self.machoObjectConnectionsByObjectID[objectID][1]:
                refID = self.machoObjectConnectionsByObjectID[objectID][0]
                del self.machoObjectConnectionsByObjectID[objectID]
                return refID
            return None

    def RegisterMachoObject(self, objectID, object, refID):
        if objectID not in sessionsByAttribute['objectID']:
            sessionsByAttribute['objectID'][objectID] = {self.sid: refID}
        else:
            sessionsByAttribute['objectID'][objectID][self.sid] = max(refID, sessionsByAttribute['objectID'][objectID].get(self.sid, 0))
        if objectID in self.machoObjectsByID:
            self.machoObjectsByID[objectID][0] = max(refID, self.machoObjectsByID[objectID][0])
        else:
            self.machoObjectsByID[objectID] = [refID, object]

    def UnregisterMachoObject(self, objectID, refID, suppressnotification = 1):
        try:
            if objectID in self.machoObjectConnectionsByObjectID:
                del self.machoObjectConnectionsByObjectID[objectID]
            if objectID in sessionsByAttribute['objectID']:
                if self.sid in sessionsByAttribute['objectID'][objectID]:
                    if refID is None or refID >= sessionsByAttribute['objectID'][objectID][self.sid]:
                        del sessionsByAttribute['objectID'][objectID][self.sid]
                        if not sessionsByAttribute['objectID'][objectID]:
                            del sessionsByAttribute['objectID'][objectID]
            if objectID in self.machoObjectsByID:
                if refID is None or refID >= self.machoObjectsByID[objectID][0]:
                    object = self.machoObjectsByID[objectID][1]
                    del self.machoObjectsByID[objectID]
                    if macho.mode != 'client' and not suppressnotification and getattr(self, 'clientID', 0) and not getattr(self, 'clearing_session', 0):
                        sm.services['machoNet'].Scattercast('+clientID', [self.clientID], 'OnMachoObjectDisconnect', objectID, self.clientID, refID)
                    if isinstance(object, ObjectConnection):
                        object.DisconnectObject()
        except StandardError:
            log.LogException()
            sys.exc_clear()

    def DumpSession(self, prefix, reason):
        log.general.Log(prefix + ':  ' + reason + ".  It's history is as follows:", 1, 2)
        lastEntry = ''
        for eachHistoryRecord in self.sessionhist:
            header = prefix + ':  ' + util.FmtDateEng(eachHistoryRecord[0], 'll') + ': '
            lines = eachHistoryRecord[1].split('\n')
            tmp = eachHistoryRecord[2]
            if tmp == lastEntry:
                txt = '< same >'
            else:
                txt = tmp
            lastEntry = tmp
            footer = ', ' + txt
            for eachLine in lines[:len(lines) - 1]:
                log.general.Log(header + eachLine, 1, 2)

            log.general.Log(header + lines[len(lines) - 1] + footer, 1, 2)

        log.general.Log(prefix + ':  Current Session Data:  %s' % strx(self), 1, 2)
        currentcall = GetLocalStorage().get('base.currentcall', None)
        if currentcall:
            try:
                currentcall = currentcall()
                log.general.Log('currentcall was: ' + strx(currentcall))
            except ReferenceError:
                sys.exc_clear()

    def Masquerade(self, props = None):
        w = weakref.ref(self)
        if self.charid:
            tmp = {'base.session': w,
             'base.charsession': w}
        else:
            tmp = {'base.session': w}
        if props is not None:
            tmp.update(props)
        return MasqueradeMask(tmp)

    def GetActualSession(self):
        return self

    def LogSessionHistory(self, reason, details = None, noBlather = 0):
        if self.role & ROLE_SERVICE and not self.hasproblems:
            return
        timer = PushMark('LogSessionHistory')
        try:
            if details is None:
                details = ''
                for each in ['sid', 'clientID'] + self.__persistvars__:
                    if getattr(self, each, None) is not None:
                        details = details + each + ':' + strx(getattr(self, each)) + ', '

                details = 'session=' + details[:-2]
            else:
                details = 'info=' + strx(details)
            self.__dict__['sessionhist'].append((blue.os.GetWallclockTime(), strx(reason)[:255], strx(details)[:255]))
            if len(self.__dict__['sessionhist']) > 120:
                self.__dict__['sessionhist'] = self.__dict__['sessionhist'][70:]
            if not noBlather and log.general.IsOpen(1):
                log.general.Log('SessionHistory:  reason=%s, %s' % (reason, strx(details)), 1, 1)
        finally:
            PopMark(timer)

    def LogSessionError(self, what, novalidate = 0):
        self.__LogSessionProblem(what, 4, novalidate)

    def __LogSessionProblem(self, what, how, novalidate = 0):
        self.hasproblems = 1
        self.LogSessionHistory(what)
        if log.general.IsOpen(how):
            log.general.Log('A session related error has occurred.  Session history:', how, 2)
            for eachHistoryRecord in self.sessionhist:
                s = ''.join(map(strx, util.FmtDateEng(eachHistoryRecord[0], 'll') + ': ' + eachHistoryRecord[1] + ', ' + eachHistoryRecord[2]))
                if len(s) > 5000:
                    s = s[:5000]
                while len(s) > 255:
                    log.general.Log(s[:253], how, 2)
                    s = '- ' + s[253:]

                log.general.Log(s, how, 2)

            log.general.Log('Session Data (should be identical to last history record):  %s' % strx(self), how, 2)
            try:
                currentcall = GetLocalStorage().get('base.currentcall', None)
                if currentcall:
                    currentcall = currentcall()
                    log.general.Log('currentcall was: ' + strx(currentcall))
            except ReferenceError:
                sys.exc_clear()

        if not novalidate:
            self.ValidateSession('session-error-dump')

    def SetSessionVariable(self, k, v):
        if v is None:
            try:
                del self.__dict__['sessionVariables'][k]
            except:
                sys.exc_clear()

        else:
            self.__dict__['sessionVariables'][k] = v

    def GetSessionVariable(self, k, defaultValue = None):
        try:
            return self.__dict__['sessionVariables'][k]
        except:
            sys.exc_clear()
            if defaultValue is not None:
                self.__dict__['sessionVariables'][k] = defaultValue
                return defaultValue
            return

    def GetDistributedProps(self, getAll):
        retval = []
        if self.role & ROLE_SERVICE == 0:
            for attribute in self.__persistvars__ + self.additionalDistributedProps:
                if getAll or self.__dict__[attribute] != self.GetDefaultValueOfAttribute(attribute):
                    retval.append(attribute)

        return retval

    __dependant_attributes__ = {'userid': ['role',
                'charid',
                'callback',
                'languageID',
                'userType',
                'maxSessionTime'],
     'sid': ['userid']}

    def DependantAttributes(self, attribute):
        retval = self.__dependant_attributes__.get(attribute, [])
        retval2 = {}
        for each in retval:
            retval2[each] = 1
            for other in self.DependantAttributes(each):
                retval2[other] = 1

        return retval2.keys()

    def GetDefaultValueOfAttribute(self, attribute):
        if attribute == 'role':
            return ROLE_LOGIN
        if attribute == 'sessionType':
            return self.__dict__.get('sessionType', None)
        if attribute in self.__attributesWithDefaultValueOfZero__:
            return 0
        if attribute == 'languageID' and macho.mode == 'client':
            return strx(prefs.GetValue('languageID', 'EN'))

    def ClearAttributes(self, isRemote = 0, dontSendMessage = False):
        if prefs.GetValue('quickShutdown', False):
            machoNet = sm.GetServiceIfRunning('machoNet')
            if machoNet and machoNet.IsClusterShuttingDown() and self.userid:
                log.general.Log('Cluster shutting down, rejecting session clearing %s' % self.userid, log.LGINFO)
                return
        if not self.changing:
            self.changing = 'ClearAttributes'
        try:
            if getattr(self, 'clearing_session', 0):
                self.LogSessionHistory("Tried to clear a cleared/clearing session's attributes")
            else:
                self.LogSessionHistory('Clearing session attributes')
                for each in self.__dict__['connectedObjects'].values():
                    each[0].DisconnectObject()

                for objectID in copy.copy(self.__dict__['machoObjectsByID']):
                    self.UnregisterMachoObject(objectID, None)

                if self.sid in sessionsBySID:
                    self.ValidateSession('pre-clear')
                    sid = self.sid
                    del sessionsBySID[sid]
                    for attr in sessionsByAttribute:
                        v = getattr(self, attr, None)
                        try:
                            del sessionsByAttribute[attr][v][sid]
                            if not sessionsByAttribute[attr][v]:
                                del sessionsByAttribute[attr][v]
                        except:
                            sys.exc_clear()

                self.__dict__['clearing_session'] = 1
                d = {}
                for each in self.__persistvars__:
                    if each not in ('connectedObjects', 'c2ooid'):
                        d[each] = self.GetDefaultValueOfAttribute(each)

                self.SetAttributes(d, isRemote, dontSendMessage=dontSendMessage)
                self.__dict__['connectedObjects'] = {}
                self.__dict__['machoObjectsByID'] = {}
                d['sessionVariables'] = {}
                sm.ScatterEvent('OnSessionEnd', self.sid)
                self.LogSessionHistory('Session attributes cleared')
        finally:
            self.changing = None

    def ValidateSession(self, prefix):
        bad = False
        if not self.contextOnly:
            if not getattr(self, 'clearing_session', 0):
                for attribute in sessionsByAttribute.iterkeys():
                    value = getattr(self, attribute, None)
                    if value:
                        valueSIDs = sessionsByAttribute[attribute]
                        if value not in valueSIDs:
                            self.LogSessionHistory('sessionsByAttribute[%s] broken, %s is not found' % (attribute, value))
                            bad = True
                        elif self.sid not in valueSIDs[value]:
                            self.LogSessionHistory('sessionsByAttribute[%s][%s] broken, %s is not found' % (attribute, value, self.sid))
                            bad = True
                        elif value in ('userid', 'charid') and len(valueSIDs[value][self.sid]) != 1:
                            self.LogSessionHistory('sessionsByAttribute[%s][%s] broken, this user/char has multiple sessions (%d)' % (attribute, value, len(valueSIDs[value][self.sid])))
                            bad = True

                if bad:
                    self.LogSessionError("The session failed it's %s validation check.  Session dump and stack trace follows." % (prefix,), 1)
                    log.LogTraceback()
        return bad

    def DisconnectFilteredObjects(self, disappeared):
        if disappeared:
            objects = []
            for oid in self.connectedObjects.iterkeys():
                objConn = self.connectedObjects[oid][0]
                object = objConn.__object__
                if object is not None and hasattr(object, '__sessionfilter__'):
                    for attribute in disappeared.iterkeys():
                        if attribute in object.__sessionfilter__:
                            objects.append((objConn, oid))
                            break

            for objConn, oid in objects:
                with self.Masquerade({'base.caller': weakref.ref(objConn)}):
                    try:
                        if oid in self.connectedObjects:
                            objConn.DisconnectObject()
                    except StandardError:
                        log.LogException()
                        sys.exc_clear()

    def CallProcessChangeOnObjects(self, notify, isRemote):
        objects = []
        notifyNodes = []
        for oid in self.connectedObjects.iterkeys():
            objConn = self.connectedObjects[oid][0]
            object = objConn.__object__
            if object is not None and hasattr(object, '__sessionfilter__') and hasattr(object, 'ProcessSessionChange'):
                for attribute in notify.iterkeys():
                    if attribute in object.__sessionfilter__:
                        objects.append((objConn, object, oid))
                        break

        for objConn, object, oid in objects:
            with self.Masquerade({'base.caller': weakref.ref(objConn)}):
                try:
                    if oid in self.connectedObjects:
                        notifyNodes.append(object.ProcessSessionChange(isRemote, self, notify))
                except StandardError:
                    log.LogException()
                    sys.exc_clear()

        return notifyNodes

    def ComputeNotifySets(self, changes, pairs):
        notify = {}
        disappeared = {}
        for attribute in changes.iterkeys():
            currentEffectiveValue = self.__dict__.get(attribute, self.GetDefaultValueOfAttribute(attribute))
            newValue = changes[attribute][1] if pairs else changes[attribute]
            if currentEffectiveValue != newValue:
                notify[attribute] = (currentEffectiveValue, newValue)
                if currentEffectiveValue and not newValue:
                    disappeared[attribute] = 1

        return (notify, disappeared)

    def __ChangeAttribute(self, attribute, newValue):
        self.__dict__['nextSessionChange'] = blue.os.GetSimTime() + base.sessionChangeDelay
        if getattr(self, 'clearing_session', 0):
            self.__dict__[attribute] = newValue
        else:
            valueSIDs = sessionsByAttribute.get(attribute, None)
            if valueSIDs is None:
                self.__dict__[attribute] = newValue
            else:
                try:
                    if newValue and newValue not in valueSIDs:
                        valueSIDs[newValue] = {}
                    oldValue = self.__dict__[attribute]
                    if not self.contextOnly:
                        if oldValue and oldValue in valueSIDs and self.sid in valueSIDs[oldValue]:
                            del valueSIDs[oldValue][self.sid]
                    self.__dict__[attribute] = newValue
                    if not self.contextOnly:
                        if newValue:
                            valueSIDs[newValue][self.sid] = 1
                        if oldValue and oldValue in valueSIDs and not len(valueSIDs[oldValue]):
                            del valueSIDs[oldValue]
                    if not charsession and attribute == 'charid' and newValue:
                        UpdateLocalStorage({'base.charsession': weakref.ref(self)})
                except:
                    self.DumpSession('ARGH!!!', 'This session is blowing up during change attribute')
                    raise 

    def RecalculateDependantAttributes(self, d):
        pass

    def SetAttributes(self, requestedChanges, isRemote = 0, dontSendMessage = False):
        if prefs.GetValue('quickShutdown', False):
            machoNet = sm.GetServiceIfRunning('machoNet')
            if machoNet and machoNet.IsClusterShuttingDown() and getattr(self, 'userid', None):
                log.general.Log('Cluster shutting down, rejecting session change %s' % self.userid, log.LGINFO)
                return
        if not self.changing:
            self.changing = 'SetAttributes'
        try:
            self.LogSessionHistory('Setting session attributes')
            try:
                requestedChanges = copy.copy(requestedChanges)
                nonPersisted = []
                for attribute in requestedChanges:
                    if attribute not in self.__persistvars__:
                        nonPersisted.append(attribute)

                if nonPersisted:
                    log.LogTraceback(extraText=strx(nonPersisted), severity=log.LGWARN)
                    for attribute in nonPersisted:
                        del requestedChanges[attribute]

                dependantAttributes = []
                changes = {}
                for attribute in requestedChanges.iterkeys():
                    dependantAttributes += self.DependantAttributes(attribute)
                    if requestedChanges[attribute] is not None and attribute not in ['address', 'languageID'] + self.additionalNonIntegralAttributes:
                        try:
                            if attribute in self.longAttributes:
                                changes[attribute] = long(requestedChanges[attribute])
                            else:
                                changes[attribute] = int(requestedChanges[attribute])
                        except TypeError:
                            log.general.Log('%s is not an integer %s' % (attribute, strx(requestedChanges[attribute])), 4, 1)
                            log.LogTraceback()
                            raise 

                    else:
                        changes[attribute] = requestedChanges[attribute]

                charID = requestedChanges.get('charid', None)
                if charID is not None and charID != self.charid:
                    changes.update(sm.GetService('sessionMgr').GetInitialValuesFromCharID(charID))
                for attribute in dependantAttributes:
                    if attribute not in changes:
                        changes[attribute] = self.GetDefaultValueOfAttribute(attribute)

                self.RecalculateDependantAttributes(changes)
                self.ValidateSession('pre-change')
                notify, disappeared = self.ComputeNotifySets(changes, pairs=False)
                if notify:
                    if 'userid' in notify and notify['userid'][0] and notify['userid'][1]:
                        self.LogSessionError("A session's userID may not change, %s=>%s" % notify['userid'])
                        raise RuntimeError("A session's userID may not change")
                    mask = None
                    try:
                        if self.role & ROLE_SERVICE == 0:
                            mask = self.Masquerade()
                            if not self.contextOnly:
                                sm.NotifySessionChange('DoSessionChanging', isRemote, self, notify)
                            self.DisconnectFilteredObjects(disappeared)
                        for attribute in notify:
                            self.__ChangeAttribute(attribute, changes[attribute])

                        self.ValidateSession('post-change')
                        if self.role & ROLE_SERVICE == 0 and not dontSendMessage:
                            if not self.contextOnly:
                                notifyAdditionalNodes = list(sm.NotifySessionChange('ProcessSessionChange', isRemote, self, notify))
                                notifyAdditionalNodes.append(self.CallProcessChangeOnObjects(notify, isRemote))
                            else:
                                notifyAdditionalNodes = sm.GetService('sessionMgr').ProcessSessionChange(isRemote, self, notify)
                            clientID = getattr(self, 'clientID', None)
                            if clientID and not isRemote:
                                if not (self.role & (ROLE_LOGIN | ROLE_PLAYER) or self.role & (ROLE_SERVICE | ROLE_REMOTESERVICE)):
                                    self.LogSessionError("A distributed session's role should probably always have login and player rights, even before a change broadcast")
                                sessionChangeLayer = sm.services['machoNet'].GetGPCS('sessionchange')
                                if sessionChangeLayer is not None:
                                    sessionChangeLayer.SessionChanged(clientID, self.sid, notify, notifyAdditionalNodes)
                            if not self.contextOnly:
                                sm.NotifySessionChange('OnSessionChanged', isRemote, self, notify)
                    finally:
                        if mask is not None:
                            mask.UnMask()

            finally:
                self.LogSessionHistory('Session attributes set')

        finally:
            self.changing = None

    def RecalculateDependantAttributesWithChanges(self, changes):
        pass

    def ApplyRemoteAttributeChanges(self, changes, initialState):
        if not self.changing:
            self.changing = 'ApplyInitialState' if initialState else 'ApplyRemoteAttributeChanges'
        try:
            self.LogSessionHistory('Receiving and performing %s' % self.changing)
            if self.role & ROLE_SERVICE:
                errorString = 'A service session may not change via %s, changes=%s' % (self.changing, strx(changes))
                self.LogSessionError(errorString)
                raise RuntimeError(errorString)
            if not self.role & (ROLE_LOGIN | ROLE_PLAYER):
                self.LogSessionError("A distributed session's role should probably always have login and player rights, even during a change broadcast")
            self.ValidateSession('pre-change')
            if initialState:
                self.RecalculateDependantAttributes(changes)
            else:
                self.RecalculateDependantAttributesWithChanges(changes)
            notify, disappeared = self.ComputeNotifySets(changes, pairs=not initialState)
            if notify:
                if 'userid' in notify and notify['userid'][0] and notify['userid'][1]:
                    self.LogSessionError("A session's userID may not change, %s=>%s" % notify['userid'])
                    raise RuntimeError("A session's userID may not change")
                if not initialState and 'role' in notify and self.charid and notify['role'][1] != self.role:
                    self.LogSessionError("A session's role should probably not change for active characters, even in remote attribute stuff")
                mask = None
                try:
                    mask = self.Masquerade()
                    if not self.contextOnly:
                        sm.NotifySessionChange('DoSessionChanging', True, self, notify)
                    self.DisconnectFilteredObjects(disappeared)
                    for attribute in notify:
                        self.__ChangeAttribute(attribute, changes[attribute] if initialState else changes[attribute][1])

                    self.ValidateSession('post-change')
                    if not self.contextOnly:
                        sm.NotifySessionChange('ProcessSessionChange', True, self, notify)
                        self.CallProcessChangeOnObjects(notify, isRemote=True)
                        sm.NotifySessionChange('OnSessionChanged', True, self, notify)
                finally:
                    if mask is not None:
                        mask.UnMask()
                    self.LogSessionHistory(self.changing)

        finally:
            self.changing = None

    def DelayedInitialStateChange(self):
        if self.role & ROLE_SERVICE != 0:
            errorString = 'A service session may not change via DelayedInitialStateChange'
            self.LogSessionError(errorString)
            raise RuntimeError(errorString)
        if macho.mode != 'server':
            raise RuntimeError('DelayedInitialStateChange called on %s, can only be called on server', macho.mode)
        mask = None
        try:
            self.LogSessionHistory('CTXSESS: Performing a delayed initial state change on session', self.sid)
            if not self.changing:
                self.changing = 'ApplyInitialState'
            changes = {attr:self.__dict__[attr] for attr in self.GetDistributedProps(False)}
            notify = {}
            for attribute, myValue in changes.iteritems():
                defaultValue = self.GetDefaultValueOfAttribute(attribute)
                if myValue != defaultValue:
                    notify[attribute] = (defaultValue, myValue)

            if notify:
                mask = self.Masquerade()
                sm.NotifySessionChange('DoSessionChanging', True, self, notify)
                for attribute, value in changes.iteritems():
                    valueSIDs = sessionsByAttribute.get(attribute, None)
                    if valueSIDs is not None:
                        if value not in valueSIDs:
                            valueSIDs[value] = {}
                        valueSIDs[value][self.sid] = 1

                sessionsBySID[self.sid] = self
                self.ValidateSession('post-delayedinitialstatechange')
                sm.NotifySessionChange('ProcessSessionChange', True, self, notify)
                self.CallProcessChangeOnObjects(notify, isRemote=True)
                sm.NotifySessionChange('OnSessionChanged', True, self, notify)
        finally:
            if mask is not None:
                mask.UnMask()
            self.LogSessionHistory('Delayed ApplyInitialState')
            self.changing = None

    def __repr__(self):
        ret = '<Session: ('
        for each in ['sid',
         'clientID',
         'changing',
         'mutating',
         'contextOnly'] + self.additionalAttributesToPrint + self.__persistvars__:
            if getattr(self, each, None) is not None:
                if each in ['role'] + self.additionalHexAttributes:
                    ret = ret + each + ':' + strx(hex(getattr(self, each))) + ', '
                else:
                    ret = ret + each + ':' + strx(getattr(self, each)) + ', '

        ret = ret[:-2] + ')>'
        return ret

    def __setattr__(self, attr, value):
        if attr in ['sid', 'clientID'] + self.additionalNoSetAttributes + self.__persistvars__:
            raise RuntimeError('ReadOnly', attr)
        else:
            self.__dict__[attr] = value

    def DisconnectObject(self, object, key = None, delaySecs = 1):
        for k, v in self.connectedObjects.items():
            obConn, = v
            if obConn.__object__ is object and (key is None or key == (obConn.__dict__['__session__'].sid, obConn.__dict__['__c2ooid__'])):
                obConn.DisconnectObject(delaySecs)

    def RedirectObject(self, object, serviceName = None, bindParams = None, key = None):
        for k, v in self.connectedObjects.items():
            obConn, = v
            if obConn.__object__ is object and (key is None or key == (obConn.__dict__['__session__'].sid, obConn.__dict__['__c2ooid__'])):
                obConn.RedirectObject(serviceName, bindParams)

    def ConnectToObject(self, object, serviceName = None, bindParams = None):
        c2ooid = self.__dict__['c2ooid']
        self.__dict__['c2ooid'] += 1
        return ObjectConnection(self, object, c2ooid, serviceName, bindParams)

    def ConnectToClientService(self, svc, idtype = None, theID = None):
        if theID is None or idtype is None:
            if self.role & ROLE_SERVICE:
                log.LogTraceback()
                raise RuntimeError('You must specify an ID type and ID to identify the client')
            else:
                theID = self.clientID
                idtype = 'clientID'
        elif not self.role & ROLE_SERVICE and macho.mode != 'client' and not IsInClientContext():
            log.LogTraceback()
            raise RuntimeError('You cannot cross the wire except in the context of a service')
        if currentcall:
            currentcall.UnLockSession()
        return sm.services['sessionMgr'].ConnectToClientService(svc, idtype, theID)

    def ConnectToService(self, svc, **keywords):
        return ServiceConnection(self, svc, **keywords)

    def ConnectToAllServices(self, svc, batchInterval = 0):
        if not self.role & ROLE_SERVICE and macho.mode != 'client' and not IsInClientContext():
            raise RuntimeError('You cannot cross the wire except in the context of a service')
        return sm.services['machoNet'].ConnectToAllServices(svc, self, batchInterval=batchInterval)

    def ConnectToRemoteService(self, svc, nodeID = None):
        if not self.role & ROLE_SERVICE and macho.mode != 'client' and not IsInClientContext():
            raise RuntimeError('You cannot cross the wire except in the context of a service')
        if macho.mode == 'server' and nodeID is None:
            nodeID = sm.GetService(svc).MachoResolve(self)
            if type(nodeID) == types.StringType:
                raise RuntimeError(nodeID)
            elif nodeID is None:
                return self.ConnectToService(svc)
        if nodeID is not None and nodeID == sm.services['machoNet'].GetNodeID():
            return self.ConnectToService(svc)
        return sm.services['machoNet'].ConnectToRemoteService(svc, nodeID, self)

    def ConnectToSolServerService(self, svc, nodeID = None):
        if not self.role & ROLE_SERVICE and macho.mode != 'client' and not IsInClientContext():
            raise RuntimeError('You cannot cross the wire except in the context of a service')
        if macho.mode == 'server' and nodeID is None:
            nodeID = sm.GetService(svc).MachoResolve(self)
            if type(nodeID) == types.StringType:
                raise RuntimeError(nodeID)
            elif nodeID is None:
                return self.ConnectToService(svc)
        if macho.mode == 'server' and (nodeID is None or nodeID == sm.services['machoNet'].GetNodeID()):
            return self.ConnectToService(svc)
        else:
            return sm.services['machoNet'].ConnectToRemoteService(svc, nodeID, self)

    def ConnectToProxyServerService(self, svc, nodeID = None):
        if not self.role & ROLE_SERVICE and macho.mode != 'client' and not IsInClientContext():
            raise RuntimeError('You cannot cross the wire except in the context of a service')
        if macho.mode == 'proxy' and (nodeID is None or nodeID == sm.services['machoNet'].GetNodeID()):
            return self.ConnectToService(svc)
        else:
            return sm.services['machoNet'].ConnectToRemoteService(svc, nodeID, self)

    def ConnectToAnyService(self, svc):
        if not self.role & ROLE_SERVICE and macho.mode != 'client' and not IsInClientContext():
            raise RuntimeError('You cannot cross the wire except in the context of a service')
        if svc in sm.services:
            return self.ConnectToService(svc)
        else:
            return self.ConnectToRemoteService(svc)

    def ConnectToAllNeighboringServices(self, svc, batchInterval = 0):
        if not self.role & ROLE_SERVICE and macho.mode != 'client' and not IsInClientContext():
            raise RuntimeError('You cannot cross the wire except in the context of a service')
        return sm.services['machoNet'].ConnectToAllNeighboringServices(svc, self, batchInterval=batchInterval)

    def ConnectToAllProxyServerServices(self, svc, batchInterval = 0):
        if not self.role & ROLE_SERVICE and macho.mode != 'client' and not IsInClientContext():
            raise RuntimeError('You cannot cross the wire except in the context of a service')
        if macho.mode == 'proxy':
            return sm.services['machoNet'].ConnectToAllSiblingServices(svc, self, batchInterval=batchInterval)
        else:
            return sm.services['machoNet'].ConnectToAllNeighboringServices(svc, self, batchInterval=batchInterval)

    def ConnectToAllSolServerServices(self, svc, batchInterval = 0):
        if not self.role & ROLE_SERVICE and macho.mode != 'client' and not IsInClientContext():
            raise RuntimeError('You cannot cross the wire except in the context of a service')
        if macho.mode == 'server':
            return sm.services['machoNet'].ConnectToAllSiblingServices(svc, self, batchInterval=batchInterval)
        else:
            return sm.services['machoNet'].ConnectToAllNeighboringServices(svc, self, batchInterval=batchInterval)

    def RemoteServiceCall(self, dest, service, method, *args, **keywords):
        return self.RemoteServiceCallWithoutTheStars(dest, service, method, args, keywords)

    def RemoteServiceCallWithoutTheStars(self, dest, service, method, *args, **keywords):
        if not self.role & ROLE_SERVICE and macho.mode != 'client' and not IsInClientContext():
            raise RuntimeError('You cannot cross the wire except in the context of a service')
        return sm.services['machoNet'].RemoteServiceCallWithoutTheStars(self, dest, service, method, args, keywords)

    def RemoteServiceNotify(self, dest, service, method, *args, **keywords):
        return self.RemoteServiceNotifyWithoutTheStars(dest, service, method, args, keywords)

    def RemoteServiceNotifyWithoutTheStars(self, dest, service, method, args, keywords):
        if not self.role & ROLE_SERVICE and macho.mode != 'client' and not IsInClientContext():
            raise RuntimeError('You cannot cross the wire except in the context of a service')
        sm.services['machoNet'].RemoteServiceNotifyWithoutTheStars(self, args, keywords)

    def ResetSessionChangeTimer(self, reason):
        sm.GetService('sessionMgr').LogInfo("Resetting next legal session change timer, reason='", reason, "', was ", util.FmtDateEng(self.nextSessionChange or blue.os.GetSimTime()))
        self.nextSessionChange = None

    def ServiceProxy(self, serviceName):
        return service.ServiceProxy(serviceName, self)


class ObjectConnection():
    __passbyvalue__ = 0
    __restrictedcalls__ = {'PseudoMethodCall': 1,
     'LogPseudoMethodCall': 1,
     'GetObjectConnectionLogClass': 1,
     'RedirectObject': 1,
     'Objectcast': 1}

    def __init__(self, sess, object, c2ooid, serviceName = None, bindParams = None):
        if object is None:
            sess.LogSessionError('Establishing an object connection to None')
            log.LogTraceback()
        self.__dict__['__last_used__'] = blue.os.GetWallclockTime()
        self.__dict__['__constructing__'] = 1
        self.__dict__['__deleting__'] = 0
        self.__dict__['__machoObjectUUID__'] = GetObjectUUID(object)
        self.__dict__['__redirectObject__'] = None
        self.__dict__['__disconnected__'] = 1
        self.__dict__['__session__'] = weakref.proxy(sess)
        self.__dict__['__c2ooid__'] = c2ooid
        self.__dict__['__object__'] = object
        self.__dict__['__serviceName__'] = serviceName
        self.__dict__['__bindParams__'] = bindParams
        self.__dict__['__publicattributes__'] = getattr(object, '__publicattributes__')
        try:
            lock = None
            if not object.sessionConnections:
                if sess.role & service.ROLE_PLAYER:
                    sm.GetService(serviceName).LogInfo('Player session re-aquiring big lock.  Session:', sess)
                    lock = (sm.GetService(serviceName).LockService(bindParams), bindParams)
                object.service = weakref.proxy(sm.GetService(serviceName))
                object.session = weakref.proxy(object.service.session)
                for depServiceName in getattr(object, '__dependencies__', []):
                    if not hasattr(object.service, depServiceName):
                        dep = object.service.session.ConnectToService(depServiceName)
                        setattr(object.service, depServiceName, dep)
                    setattr(object, depServiceName, getattr(object.service, depServiceName))

                self.PseudoMethodCall(object, 'OnRun')
            if sess.role & service.ROLE_PLAYER and lock is None:
                charid = sess.charid
                lock = (object.service.LockService((bindParams, charid)), (bindParams, charid))
            if sess.sid not in object.sessionConnections:
                self.PseudoMethodCall(object, 'OnSessionAttach')
                object.sessionConnections[sess.sid] = sess
                object.objectConnections[sess.sid] = {}
            object.objectConnections[sess.sid][c2ooid] = self
            sess.connectedObjects[self.__c2ooid__] = (self,)
            self.__disconnected__ = 0
            self.__pendingDisconnect__ = 0
            allObjectConnections[self] = 1
            allConnectedObjects[object] = 1
        finally:
            if lock is not None:
                sm.GetService(serviceName).UnLockService(lock[1], lock[0])

        self.__dict__['__constructing__'] = 0

    def GetSession(self):
        return self.__session__

    def __del__(self):
        if not self.__deleting__:
            self.__deleting__ = 1
            if not self.__disconnected__:
                if log.methodcalls.IsOpen(2):
                    log.methodcalls.Log("Curious....   Disconnecting during __del__ wasn't entirely expected...", 2, 1)
                self.DisconnectObject(30)

    def __str__(self):
        return 'ObjectConnection to ' + strx(self.__object__)

    def __repr__(self):
        return self.__str__()

    def GetInstanceID(self):
        return self.__object__.machoInstanceID

    def PseudoMethodCall(self, object, method, *args, **keywords):
        self.__dict__['__last_used__'] = blue.os.GetWallclockTime()
        if hasattr(object, method):
            with self.__session__.Masquerade({'base.caller': weakref.ref(self)}):
                with CallTimer(macho.GetLogName(object) + '::' + method):
                    try:
                        result = apply(getattr(object, method), args, keywords)
                    except Exception as e:
                        self.LogPseudoMethodCall(e, method)
                        raise 

                    self.LogPseudoMethodCall(result, method)
            return result

    def LogPseudoMethodCall(self, result, method, *args, **keywords):
        logChannel = log.methodcalls
        if logChannel.IsOpen(log.LGINFO):
            logname = macho.GetLogName(self.__object__)
            if isinstance(result, Exception):
                eorr = ', EXCEPTION='
            else:
                eorr = ', retval='
            if keywords:
                logwhat = [logname,
                 '::',
                 method,
                 ' args=',
                 args,
                 ', keywords={',
                 keywords,
                 '}',
                 eorr,
                 result]
            else:
                logwhat = [logname,
                 '::',
                 method,
                 ' args=',
                 args,
                 eorr,
                 result]
            timer = PushMark(logname + '::LogPseudoMethodCall')
            try:
                s = ''.join(map(strx, logwhat))
                if len(s) > 2500:
                    s = s[:2500]
                while len(s) > 255:
                    logChannel.Log(s[:253], log.LGINFO, 1)
                    s = '- ' + s[253:]

                logChannel.Log(s, log.LGINFO, 1)
            except TypeError:
                logChannel.Log('[X]'.join(map(strx, logwhat)).replace('\x00', '\\0'), log.LGINFO, 1)
                sys.exc_clear()
            except UnicodeEncodeError:
                logChannel.Log('[U]'.join(map(lambda x: x.encode('ascii', 'replace'), map(unicode, logwhat))), log.LGINFO, 1)
                sys.exc_clear()
            finally:
                PopMark(timer)

    def GetObjectConnectionLogClass(self):
        return macho.AssignLogName(self.__object__)

    def __GetObjectType(self):
        return 'ObjectConnection to ' + self.GetObjectConnectionLogClass()

    def RedirectObject(self, serviceName = None, bindParams = None):
        if serviceName is None:
            serviceName = self.__serviceName__
        if bindParams is None:
            bindParams = self.__bindParams__
        self.__redirectObject__ = (serviceName, bindParams)

    def DisconnectObject(self, delaySecs = 0):
        if delaySecs:
            if not self.__pendingDisconnect__:
                dyingObjects.append((blue.os.GetWallclockTime() + delaySecs * SEC, self))
                self.__pendingDisconnect__ = 1
            else:
                self.__pendingDisconnect__ += 1
                if self.__pendingDisconnect__ in (10, 100, 1000, 10000, 100000, 1000000, 10000000):
                    if not prefs.GetValue('suppressObjectKillahDupSpam', 0):
                        log.LogTraceback('Many duplicate requests (%d) to add object to objectKillah dyingObjects list - %r %r' % (self.__pendingDisconnect__, self, self.GetObjectConnectionLogClass()), severity=log.LGWARN)
            return
        if not self.__disconnected__:
            self.__disconnected__ = 1
            try:
                if not sm.IsServiceRunning(self.__serviceName__):
                    return
                service = sm.GetService(self.__serviceName__)
                lock = None
                if self.__session__.role & ROLE_PLAYER:
                    charid = getattr(self.__session__, 'charid')
                    lock = sm.GetService(self.__serviceName__).LockService((self.__bindParams__, charid))
                try:
                    objectID = GetObjectUUID(self)
                    if objectID in self.__session__.machoObjectsByID:
                        objectType = self.__GetObjectType()
                        self.__session__.LogSessionHistory('%s object %s disconnected from this session by the server' % (objectType, objectID), strx(self.__object__))
                        self.__session__.UnregisterMachoObject(objectID, None, 0)
                    service.RemoveSessionConnectionFromObject(self)
                finally:
                    if lock:
                        sm.GetService(self.__serviceName__).UnLockService((self.__bindParams__, charid), lock)

            except ReferenceError:
                pass
            except StandardError:
                log.LogException()

            self.__object__ = None

    def __getattr__(self, method):
        if method in self.__dict__:
            return self.__dict__[method]
        if not method.isupper():
            if method in self.__dict__['__publicattributes__']:
                return getattr(self.__object__, method)
            if method.startswith('__'):
                raise AttributeError(method)
        if self.__c2ooid__ not in self.__session__.connectedObjects:
            self.__session__.LogSessionHistory('Object no longer live:  c2ooid=' + strx(self.__c2ooid__) + ', serviceName=' + strx(self.__serviceName__) + ', bindParams=' + strx(self.__bindParams__) + ', uuid=' + strx(self.__machoObjectUUID__), None, 1)
            self.__session__.LogSessionError('This object connection is no longer live')
            raise RuntimeError('This object connection is no longer live')
        self.__dict__['__last_used__'] = blue.os.GetWallclockTime()
        if self.__session__.role & (ROLE_SERVICE | ROLE_REMOTESERVICE) == ROLE_SERVICE:
            if method.endswith('_Ex'):
                return service.FastCallWrapper(self.__session__, self.__object__, method[:-3], self)
            else:
                return service.FastCallWrapper(self.__session__, self.__object__, method, self)
        return service.ObjectCallWrapper(self.__session__, self.__object__, method, self, self.GetObjectConnectionLogClass())


class ServiceConnection():
    __restrictedcalls__ = {'Lock': 1,
     'UnLock': 1,
     'GetMachoObjectBoundToSession': 1}

    def __init__(self, sess, service, **keywords):
        self.__session__ = weakref.proxy(sess)
        self.__service__ = service
        self.__remote__ = keywords.get('remote', 0)
        sm.StartService(self.__service__)

    def Lock(self, lockID):
        return sm.GetService(self.__service__).LockService(lockID)

    def UnLock(self, lockID, lock):
        sm.GetService(self.__service__).UnLockService(lockID, lock)

    def GetInstanceID(self):
        return sm.GetService(self.__service__).startedWhen

    def __getitem__(self, key):
        mn = sm.services['machoNet']
        if type(key) == types.TupleType:
            nodeID = mn.GetNodeFromAddress(key[0], key[1])
        elif type(key) == types.IntType:
            nodeID = key
        else:
            srv = sm.StartServiceAndWaitForRunningState(self.__service__)
            nodeID = self.MachoResolve(key)
        if nodeID == mn.GetNodeID():
            return self
        else:
            return self.__session__.ConnectToRemoteService(self.__service__, nodeID)

    def __nonzero__(self):
        return 1

    def __str__(self):
        sess = 'unknown'
        try:
            sess = strx(self.__session__)
        except:
            pass

        return 'ServiceConnection, Service:' + strx(self.__service__) + '. Session:' + sess

    def __repr__(self):
        return self.__str__()

    def __getattr__(self, method):
        if method in self.__dict__:
            return self.__dict__[method]
        if method.startswith('__'):
            raise AttributeError(method)
        svc = sm.StartService(self.__service__)
        if not self.__remote__ and (self.__session__.role & ROLE_SERVICE or macho.mode == 'client' or method == 'MachoResolve'):
            self.__WaitForRunningState(svc)
            if method.endswith('_Ex'):
                return service.FastCallWrapper(self.__session__, svc, method[:-3], self)
            else:
                return service.FastCallWrapper(self.__session__, svc, method, self)
        if self.__session__.role & ROLE_SERVICE:
            return service.UnlockedServiceCallWrapper(self.__session__, svc, method, self, self.__service__)
        else:
            return service.ServiceCallWrapper(self.__session__, svc, method, self, self.__service__)

    def __WaitForRunningState(self, svc):
        desiredStates = (service.SERVICE_RUNNING,)
        errorStates = (service.SERVICE_FAILED, service.SERVICE_STOPPED)
        sm.WaitForServiceObjectState(svc, desiredStates, errorStates)


def GetAllSessionInfo():
    return (allSessionsBySID, sessionsBySID, sessionsByAttribute)


def GetNewSid():
    return random.getrandbits(63)


def GetSessionMaps():
    return (sessionsBySID, sessionsByAttribute)


def CreateSession(sid = None, sessionType = const.session.SESSION_TYPE_GAME, role = ROLE_LOGIN):
    global local_sid
    if sessionType not in const.session.VALID_SESSION_TYPES:
        raise ValueError('Trying to create a session with an invalid session type')
    local_sid += 1
    if sid is None:
        sid = GetNewSid()
    if sid in sessionsBySID:
        log.general.Log('Session SID collision!', log.LGERR)
        log.general.Log('Local session being broken %s' % (sessionsBySID[sid],), log.LGERR)
    s = base.Session(sid, local_sid, role, sessionType)
    if not s.contextOnly:
        sessionsBySID[sid] = s
    allSessionsBySID[sid] = s
    return s


def GetServiceSession(serviceKey, refcounted = False):
    if serviceKey not in service_sessions:
        ret = CreateSession(GetNewSid(), const.session.SESSION_TYPE_SERVICE, ROLE_SERVICE)
        ret.serviceName = serviceKey
        service_sessions[serviceKey] = ret
    else:
        ret = service_sessions[serviceKey]
    if refcounted:
        if not hasattr(ret, 'remoteServiceSessionRefCount'):
            ret.__dict__['remoteServiceSessionRefCount'] = 1
        else:
            ret.__dict__['remoteServiceSessionRefCount'] += 1
    return ret


def CountSessions(attr, val):
    cnt = 0
    for v in val:
        try:
            r = []
            for sid in sessionsByAttribute[attr].get(v, {}).iterkeys():
                if sid in sessionsBySID:
                    cnt += 1
                else:
                    r.append(sid)

            for each in r:
                del sessionsByAttribute[attr][v][each]

        except:
            srv = sm.services['sessionMgr']
            srv.LogError('Session map borked')
            srv.LogError('sessionsByAttribute=', sessionsByAttribute)
            srv.LogError('sessionsBySID=', sessionsBySID)
            log.LogTraceback()
            raise 

    return cnt


def FindSessions(attr, val):
    ret = []
    for v in val:
        try:
            r = []
            for sid in sessionsByAttribute[attr].get(v, {}).iterkeys():
                if sid in sessionsBySID:
                    ret.append(sessionsBySID[sid])
                else:
                    r.append(sid)

            for each in r:
                del sessionsByAttribute[attr][v][each]

        except:
            srv = sm.services['sessionMgr']
            srv.LogError('Session map borked')
            srv.LogError('sessionsByAttribute=', sessionsByAttribute)
            srv.LogError('sessionsBySID=', sessionsBySID)
            log.LogTraceback()
            raise 

    if len(ret) > 1 and attr in ('charid', 'userid'):
        return sorted(ret, key=lambda s: s.localSID, reverse=True)
    return ret


def FindClients(attr, val):
    ret = []
    for v in val:
        try:
            r = []
            for sid in sessionsByAttribute[attr].get(v, {}).iterkeys():
                if sid in sessionsBySID:
                    s = sessionsBySID[sid]
                    if hasattr(s, 'clientID'):
                        ret.append(s.clientID)
                else:
                    r.append(sid)

            for each in r:
                del sessionsByAttribute[attr][v][each]

        except:
            srv = sm.services['sessionMgr']
            srv.LogError('Session map borked')
            srv.LogError('sessionsByAttribute=', sessionsByAttribute)
            srv.LogError('sessionsBySID=', sessionsBySID)
            log.LogTraceback()
            raise 

    return ret


def FindClientsAndHoles(attr, val, maxCount):
    ret = []
    nf = []
    attributes = attr.split('&')
    if attributes[0] not in sessionsByAttribute:
        log.LogWarn('FindClientsAndHoles by non-existent attribute ', attributes[0])
        return (0, ret, nf)
    if len(attributes) > 1:
        if len(attributes) != len(val):
            raise RuntimeError('For a complex session query, the value must be a tuple of equal length to the complex query params')
        for i in range(len(val[0])):
            f = 0
            r = []
            for sid in sessionsByAttribute[attributes[0]].get(val[0][i], {}).iterkeys():
                if sid in sessionsBySID:
                    sess = sessionsBySID[sid]
                    k = 1
                    for j in range(1, len(val)):
                        if attributes[j] in ('corprole', 'rolesAtAll', 'rolesAtHQ', 'rolesAtBase', 'rolesAtOther'):
                            corprole = getattr(sess, attributes[j])
                            k = 0
                            for r2 in val[j]:
                                if r2 and r2 & corprole == r2:
                                    k = 1
                                    break

                        elif getattr(sess, attributes[j]) not in val[j]:
                            k = 0
                        if not k:
                            break

                    if k:
                        f = 1
                        clientID = getattr(sessionsBySID[sid], 'clientID', None)
                        if clientID is not None:
                            if maxCount is not None and len(ret) >= maxCount:
                                return (1, [], [])
                            ret.append(clientID)
                else:
                    r.append(sid)

            for each in r:
                del sessionsByAttribute[attributes[0]][val[0][i]][each]

            if not f:
                nf.append(val[0][i])

        if len(nf):
            nf2 = list(copy.copy(val))
            nf2[0] = nf
            nf = nf2
        return (0, ret, nf)
    for v in val:
        f = 0
        r = []
        for sid in sessionsByAttribute[attr].get(v, {}).iterkeys():
            if sid in sessionsBySID:
                clientID = getattr(sessionsBySID[sid], 'clientID', None)
                if clientID is not None:
                    if maxCount is not None and len(ret) >= maxCount:
                        return (1, [], [])
                    ret.append(clientID)
                    f = 1
            else:
                r.append(sid)

        for each in r:
            del sessionsByAttribute[attr][v][each]

        if not f:
            nf.append(v)

    return (0, ret, nf)


def FindSessionsAndHoles(attr, val, maxCount):
    ret = []
    nf = []
    attributes = attr.split('&')
    if len(attributes) > 1:
        if len(attributes) != len(val):
            raise RuntimeError('For a complex session query, the value must be a tuple of equal length to the complex query params')
        for i in range(len(val[0])):
            f = 0
            r = []
            for sid in sessionsByAttribute[attributes[0]].get(val[0][i], {}).iterkeys():
                if sid in sessionsBySID:
                    sess = sessionsBySID[sid]
                    k = 1
                    for j in range(1, len(val)):
                        if attributes[j] in ('corprole', 'rolesAtAll', 'rolesAtHQ', 'rolesAtBase', 'rolesAtOther'):
                            corprole = getattr(sess, attributes[j])
                            k = 0
                            for r2 in val[j]:
                                if r2 and r2 & corprole == r2:
                                    k = 1
                                    break

                        elif getattr(sess, attributes[j]) not in val[j]:
                            k = 0
                        if not k:
                            break

                    if k:
                        f = 1
                        clientID = getattr(sessionsBySID[sid], 'clientID', None)
                        if clientID is not None:
                            if maxCount is not None and len(ret) >= maxCount:
                                return (1, [], [])
                            ret.append(sessionsBySID[sid])
                else:
                    r.append(sid)

            for each in r:
                del sessionsByAttribute[attributes[0]][val[0][i]][each]

            if not f:
                nf.append(val[0][i])

        if len(nf):
            nf2 = list(copy.copy(val))
            nf2[0] = nf
            nf = nf2
        return (0, ret, nf)
    for v in val:
        f = 0
        r = []
        for sid in sessionsByAttribute[attr].get(v, {}).iterkeys():
            if sid in sessionsBySID:
                clientID = getattr(sessionsBySID[sid], 'clientID', None)
                if clientID is not None:
                    if maxCount is not None and len(ret) >= maxCount:
                        return (1, [], [])
                    ret.append(sessionsBySID[sid])
                    f = 1
            else:
                r.append(sid)

        for each in r:
            del sessionsByAttribute[attr][v][each]

        if not f:
            nf.append(v)

    return (0, ret, nf)


def GetSessions(sid = None):
    if sid is None:
        return sessionsBySID.values()
    else:
        return sessionsBySID.get(sid, None)


def CloseSession(sess, isRemote = False):
    if sess is not None:
        if hasattr(sess, 'remoteServiceSessionRefCount'):
            sess.__dict__['remoteServiceSessionRefCount'] -= 1
            if sess.__dict__['remoteServiceSessionRefCount'] > 0:
                return
        if sess.sid in sessionsBySID:
            sess.ClearAttributes(isRemote)


class ObjectcastCallWrapper():

    def __init__(self, object):
        self.object = weakref.proxy(object)

    def __call__(self, method, *args):
        sm.services['machoNet'].ObjectcastWithoutTheStars(self.object, method, args)


class UpdatePublicAttributesCallWrapper():

    def __init__(self, object):
        self.object = weakref.proxy(object)

    def __call__(self, *args, **keywords):
        pa = {}
        k = keywords.get('partial', [])
        for each in getattr(self.object, '__publicattributes__', []):
            if k and each not in k:
                continue
            if hasattr(self.object, each):
                pa[each] = getattr(self.object, each)

        sm.services['machoNet'].Objectcast(self.object, 'OnObjectPublicAttributesUpdated', GetObjectUUID(self.object), pa, args, keywords)


objectsByUUID = weakref.WeakValueDictionary({})
objectUUID = 0L

def GetObjectUUID(object):
    global objectUUID
    global objectsByUUID
    if hasattr(object, '__machoObjectUUID__'):
        return object.__machoObjectUUID__
    else:
        objectUUID += 1L
        if macho.mode == 'client':
            t = 'C=0:%s' % objectUUID
        else:
            t = 'N=%s:%s' % (sm.services['machoNet'].GetNodeID(), objectUUID)
        setattr(object, '__machoObjectUUID__', t)
        if not hasattr(object, '__publicattributes__'):
            setattr(object, '__publicattributes__', [])
        setattr(object, 'Objectcast', ObjectcastCallWrapper(object))
        setattr(object, 'UpdatePublicAttributes', UpdatePublicAttributesCallWrapper(object))
        objectsByUUID[t] = object
        return t


def GetObjectByUUID(uuid):
    try:
        return objectsByUUID.get(uuid, None)
    except ReferenceError:
        sys.exc_clear()
        return None


class SessionMgr(service.Service):
    __guid__ = 'svc.sessionMgr'
    __displayname__ = 'Session manager'
    __exportedcalls__ = {'GetSessionStatistics': [ROLE_SERVICE],
     'CloseUserSessions': [ROLE_SERVICE],
     'GetProxyNodeFromID': [ROLE_SERVICE],
     'GetClientIDsFromID': [ROLE_SERVICE],
     'UpdateSessionAttributes': [ROLE_SERVICE],
     'ConnectToClientService': [ROLE_SERVICE],
     'PerformSessionChange': [ROLE_SERVICE],
     'GetLocalClientIDs': [ROLE_SERVICE],
     'EndAllGameSessions': [ROLE_ADMIN | ROLE_SERVICE],
     'PerformHorridSessionAttributeUpdate': [ROLE_SERVICE],
     'BatchedRemoteCall': [ROLE_SERVICE],
     'GetSessionDetails': [ROLE_SERVICE],
     'TerminateClientConnections': [ROLE_SERVICE | ROLE_ADMIN],
     'RemoveSessionsFromServer': [ROLE_SERVICE]}
    __dependencies__ = []
    __notifyevents__ = ['ProcessSessionChange',
     'DoSessionChanging',
     'DoSimClockRebase',
     'OnGlobalConfigChanged']

    def __init__(self):
        service.Service.__init__(self)
        if macho.mode == 'server':
            self.__dependencies__ += ['authentication', 'DB2']
        self.sessionClientIDCache = {'userid': {},
         'charid': {}}
        self.proxies = {}
        self.clientIDsByCharIDCache = {}
        self.sessionChangeShortCircuitReasons = []
        self.additionalAttribsAllowedToUpdate = []
        self.additionalStatAttribs = []
        self.additionalSessionDetailsAttribs = []
        self.sessionStatistics = None
        self.timeSessionStatsComputed = None
        if macho.mode == 'server':
            uthread.new(SessionKillah, sm.GetService('machoNet')).context = 'sessions::SessionKillah'

    def GetProxySessionManager(self, nodeID):
        if nodeID not in self.proxies:
            self.proxies[nodeID] = self.session.ConnectToProxyServerService('sessionMgr', nodeID)
        return self.proxies[nodeID]

    def GetLocalClientIDs(self):
        ret = []
        for each in GetSessions():
            if hasattr(each, 'clientID'):
                ret.append(each.clientID)

        return ret

    def GetReason(self, oldReason, newReason, timeLeft):
        return localization.GetByLabel('/Carbon/UI/Sessions/SessionChangeInProgressBase')

    def __RaisePSCIP(self, oldReason, newReason, timeLeft = None):
        if oldReason is None:
            oldReason = ''
        if newReason is None:
            newReason = ''
        reason = self.GetReason(oldReason, newReason, timeLeft)
        self.LogInfo('raising a PerformSessionChangeInProgress user error with reason ', reason)
        raise UserError('PerformSessionChangeInProgress', {'reason': reason})

    def PerformSessionLockedOperation(self, *args, **keywords):
        return self.PerformSessionChange(*args, **keywords)

    def PerformSessionChange(self, sessionChangeReason, func, *args, **keywords):
        if 'hostileMutation' in keywords or 'violateSafetyTimer' in keywords or 'wait' in keywords:
            kw2 = copy.copy(keywords)
            hostile = keywords.get('hostileMutation', 0)
            wait = keywords.get('wait', 0)
            violateSafetyTimer = keywords.get('violateSafetyTimer', 0)
            if 'violateSafetyTimer' in kw2:
                del kw2['violateSafetyTimer']
            if 'hostileMutation' in kw2:
                del kw2['hostileMutation']
            if 'wait' in kw2:
                del kw2['wait']
        else:
            hostile = 0
            violateSafetyTimer = 0
            kw2 = keywords
            wait = 0
        self.LogInfo('Performing a locked session changing operation, reason=', sessionChangeReason)
        if macho.mode == 'client':
            sess = session
            if not violateSafetyTimer and hostile in (0, 1) and sess.charid:
                if sess.nextSessionChange is not None and sess.nextSessionChange > blue.os.GetSimTime():
                    if wait > 0:
                        t = 1000 * (2 + (session.nextSessionChange - blue.os.GetSimTime()) / const.SEC)
                        self.LogInfo('PerformSessionChange is sleeping for %s ms' % t)
                        blue.pyos.synchro.SleepWallclock(t)
                if sess.nextSessionChange is not None and sess.nextSessionChange > blue.os.GetSimTime():
                    self.LogError("Too frequent session change attempts.  You'll just get yourself stuck doing this.  Ignoring.")
                    self.LogError('func=', func, ', args=', args, ', keywords=', keywords)
                    if sessionChangeReason in self.sessionChangeShortCircuitReasons:
                        return
                    self.__RaisePSCIP(sess.sessionChangeReason, sessionChangeReason, sess.nextSessionChange - blue.os.GetSimTime())
            else:
                self.LogInfo('Passing session change stuck prevention speedbump.  hostile=', hostile)
        else:
            raise RuntimeError('Not Yet Implemented')
        if sess.mutating and hostile in (0, 1):
            if sessionChangeReason in self.sessionChangeShortCircuitReasons:
                self.LogInfo('Ignoring session change attempt due to ' + sessionChangeReason + ' overzealousness')
                return
            self.__RaisePSCIP(sess.sessionChangeReason, sessionChangeReason)
        try:
            if hostile not in (2, 4):
                self.LogInfo('Incrementing the session mutation flag')
                sess.mutating += 1
            if sess.mutating == 1:
                self.LogInfo('Chaining ProcessSessionMutating event')
                sm.ChainEvent('ProcessSessionMutating', func, args, kw2)
                sess.sessionChangeReason = sessionChangeReason
            if hostile == 0:
                prev = sess.nextSessionChange
                if not violateSafetyTimer:
                    sess.nextSessionChange = blue.os.GetSimTime() + base.sessionChangeDelay
                localNextSessionChange = sess.nextSessionChange
                self.LogInfo('Pre-op updating next legal session change to ', util.FmtDateEng(sess.nextSessionChange))
                self.LogInfo('Executing the session modification method')
                try:
                    return apply(func, args, kw2)
                except:
                    if localNextSessionChange >= sess.nextSessionChange:
                        sess.nextSessionChange = prev
                        self.LogInfo('post-op exception handler reverting next legal session change to ', util.FmtDateEng(sess.nextSessionChange))
                    else:
                        self.LogInfo("post-op exception handler - Someone else has modified nextSessionChange, so DON'T revert it - modified value is ", util.FmtDateEng(sess.nextSessionChange))
                    raise 

            elif hostile in (1, 3):
                self.LogInfo('Initiating Remote Mutation (local state change only), args=', args, ', keywords=', kw2)
            else:
                self.LogInfo('Finalizing Remote Mutation (local state change only), args=', args, ', keywords=', kw2)
        finally:
            self.LogInfo('Post-op updating next legal session change to ', util.FmtDateEng(sess.nextSessionChange))
            if hostile not in (1, 3):
                self.LogInfo('Decrementing the session mutation flag')
                sess.mutating -= 1
                if sess.mutating == 0:
                    self.LogInfo('Scattering OnSessionMutated event')
                    sm.ScatterEvent('OnSessionMutated', func, args, kw2)

    def GetProxyNodeFromID(self, idtype, theID, refresh = 0):
        if idtype != 'clientID':
            clientID = self.GetClientIDsFromID(idtype, theID, refresh)[0]
        else:
            clientID = theID
        return sm.services['machoNet'].GetProxyNodeIDFromClientID(clientID)

    def IsPlayerCharacter(self, charID):
        raise Exception('stub function not implemented')

    def GetClientIDsFromID(self, idtype, theID, refresh = 0):
        clientIDs = []
        if theID in sessionsByAttribute[idtype]:
            sids = sessionsByAttribute[idtype][theID]
            for sid in sids:
                if sid in sessionsBySID:
                    s = sessionsBySID[sid]
                    if getattr(s, 'clientID', 0):
                        if theID in self.sessionClientIDCache[idtype]:
                            del self.sessionClientIDCache[idtype][theID]
                        clientIDs.append(s.clientID)

        if not refresh and theID in self.sessionClientIDCache[idtype]:
            return self.sessionClientIDCache[idtype][theID]
        if not hasattr(self, 'dbzcluster'):
            self.dbzcluster = self.DB2.GetSchema('zcluster')
        clientID = None
        if idtype == 'charid':
            if self.IsPlayerCharacter(theID):
                if theID in self.clientIDsByCharIDCache:
                    clientID, lastTime = self.clientIDsByCharIDCache[theID]
                    if blue.os.GetWallclockTime() - lastTime > const.SEC:
                        clientID = None
                    else:
                        clientIDs.append(clientID)
                if clientID is None:
                    client = self.dbzcluster.Sessions_ByCharacterID(theID)
                    if len(client) and client[0].clientID:
                        clientID = client[0].clientID
                        clientIDs.append(clientID)
                self.clientIDsByCharIDCache[theID] = (clientID, blue.os.GetWallclockTime())
            else:
                log.LogTraceback('Thou shall only use GetClientIDsFromID for player characters', show_locals=1)
                clientID = None
        elif idtype == 'userid':
            for row in self.dbzcluster.Sessions_ByUserID(theID):
                if row.clientID:
                    clientIDs.append(row.clientID)

        else:
            raise RuntimeError('Can only currently characterID to locate a client through the DB')
        if not clientIDs:
            raise UnMachoDestination('The dude is not logged on')
        else:
            self.sessionClientIDCache[idtype][theID] = clientIDs
            return clientIDs

    def DoSessionChanging(self, *args):
        pass

    def ProcessSessionChange(self, isRemote, sess, change):
        if 'userid' in change and change['userid'][0] in self.sessionClientIDCache['userid']:
            del self.sessionClientIDCache['userid'][change['userid'][0]]
        if 'charid' in change and change['charid'][0] in self.sessionClientIDCache['charid']:
            del self.sessionClientIDCache['charid'][change['charid'][0]]
        if macho.mode == 'proxy':
            return -1

    def DoSimClockRebase(self, times):
        oldSimTime, newSimTime = times
        try:
            session.nextSessionChange += newSimTime - oldSimTime
        except:
            log.LogException('Exception while trying to rebase the session change timer')

    def OnGlobalConfigChanged(self, config):
        if 'sessionChangeDelay' in config:
            base.sessionChangeDelay = int(config['sessionChangeDelay']) * const.SEC

    def TypeAndNodeValidationHook(self, idType, id):
        pass

    def UpdateSessionAttributes(self, idtype, theID, dict):
        if idtype not in ['charid', 'userid'] + self.additionalAttribsAllowedToUpdate:
            raise RuntimeError("You shouldn't be calling this, as you obviously don't know what you're doing.  This is like one of the most sensitive things in the system, dude.")
        if macho.mode == 'proxy' and theID not in sessionsByAttribute[idtype]:
            raise UnMachoDestination('Wrong proxy or client not connected')
        if macho.mode == 'server' and idtype in ('userid', 'charid'):
            proxyNodeID = None
            try:
                proxyNodeID = self.GetProxyNodeFromID(idtype, theID, 1)
            except UnMachoDestination:
                sys.exc_clear()

            if proxyNodeID is not None:
                return self.GetProxySessionManager(proxyNodeID).UpdateSessionAttributes(idtype, theID, dict)
        sessions = FindSessions(idtype, [theID])
        if idtype == 'charid' and dict.has_key('flagRolesOnly') and sessions and len(sessions) > 0:
            sessioncorpid = sessions[0].corpid
            rolecorpid = dict['corpid']
            if sessioncorpid != rolecorpid:
                self.LogError('Character session is wrong!!! Character', theID, 'has session corp', sessioncorpid, 'but should be', rolecorpid, "I'll fix his session but please investigate why this occurred! Update dict:", dict, 'Session:', sessions[0])
        if dict.has_key('flagRolesOnly'):
            del dict['flagRolesOnly']
        self.TypeAndNodeValidationHook(idtype, theID)
        parallelCalls = []
        for each in sessions:
            if hasattr(each, 'clientID'):
                parallelCalls.append((self.PerformHorridSessionAttributeUpdate, (each.clientID, dict)))
            else:
                each.LogSessionHistory('Updating session information via sessionMgr::UpdateSessionAttributes')
                each.SetAttributes(dict)
                each.LogSessionHistory('Updated session information via sessionMgr::UpdateSessionAttributes')

        if len(parallelCalls) > 60:
            log.LogTraceback('Horrid session change going haywire.  Redesign the calling code!')
        uthread.parallel(parallelCalls)

    def PerformHorridSessionAttributeUpdate(self, clientID, dict):
        try:
            if macho.mode == 'server':
                proxyNodeID = self.GetProxyNodeFromID('clientID', clientID)
                return self.GetProxySessionManager(proxyNodeID).PerformHorridSessionAttributeUpdate(clientID, dict)
            s = sm.services['machoNet'].GetSessionByClientID(clientID)
            if s:
                s.LogSessionHistory('Updating session information via sessionMgr::UpdateSessionAttributes')
                s.SetAttributes(dict)
                s.LogSessionHistory('Updated session information via sessionMgr::UpdateSessionAttributes')
        except StandardError:
            log.LogException()
            sys.exc_clear()

    def GetSessionFromParams(self, idtype, theID):
        if idtype == 'clientID':
            s = sm.services['machoNet'].GetSessionByClientID(theID)
            if s is None:
                raise UnMachoDestination('Wrong proxy or client not connected, session not found by clientID=%s' % theID)
            return s
        if theID not in sessionsByAttribute[idtype]:
            raise UnMachoDestination('Wrong proxy or client not connected, session not found by %s=%s' % (idtype, theID))
        else:
            sids = sessionsByAttribute[idtype][theID].keys()
            if not len(sids) == 1:
                raise UnMachoDestination('Ambiguous idtype/id pair (%s/%s).  There are %d sessions that match them.' % (idtype, theID, len(sids)))
            else:
                sid = sids[0]
            if sid not in sessionsBySID:
                raise UnMachoDestination("The client's session is in an invalid or terminating state")
            return sessionsBySID[sid]

    def ConnectToClientService(self, svc, idtype, theID):
        if macho.mode == 'proxy':
            s = self.GetSessionFromParams(idtype, theID)
            return sm.services['machoNet'].ConnectToRemoteService(svc, macho.MachoAddress(clientID=s.clientID, service=svc), s)
        proxyNodeID = self.GetProxyNodeFromID(idtype, theID)
        try:
            return self.GetProxySessionManager(proxyNodeID).ConnectToClientService(svc, idtype, theID)
        except UnMachoDestination:
            sys.exc_clear()
            if not refreshed:
                return self.GetProxySessionManager(self.GetProxyNodeFromID(idtype, theID, 1)).ConnectToClientService(svc, idtype, theID)

    def GetSessionStatistics(self):
        now = blue.os.GetWallclockTime()
        statAttributes = ['userid', 'usertype'] + self.additionalStatAttribs
        if self.sessionStatistics is None or now - self.timeSessionStatsComputed > 5 * const.SEC:
            self.timeSessionStatsComputed = now
            self.sessionStatistics = {}
            for attribute, valuesOfAttribute in sessionsByAttribute.iteritems():
                if attribute in statAttributes:
                    attrValueCounts = {}
                    for attrValue, valueSessions in valuesOfAttribute.iteritems():
                        attrValueCounts[attrValue] = len(valueSessions)

                    self.sessionStatistics[attribute] = [len(valuesOfAttribute), attrValueCounts]

            self._AddToSessionStatistics()
        return self.sessionStatistics

    def _AddToSessionStatistics(self):
        machoChar = CRESTChar = machoUser = CRESTUser = 0
        for sess in base.sessionsBySID.itervalues():
            if sess.sessionType == const.session.SESSION_TYPE_GAME:
                if sess.charid:
                    machoChar += 1
                else:
                    machoUser += 1
            elif sess.sessionType == const.session.SESSION_TYPE_CREST:
                if sess.charid:
                    CRESTChar += 1
                else:
                    CRESTUser += 1

        self.sessionStatistics['CARBON:MachoChar'] = (machoChar, {None: machoChar})
        self.sessionStatistics['CARBON:MachoUser'] = (machoUser, {None: machoUser})
        self.sessionStatistics['CARBON:CRESTChar'] = (CRESTChar, {None: CRESTChar})
        self.sessionStatistics['CARBON:CRESTUser'] = (CRESTUser, {None: CRESTUser})

    def Run(self, memstream = None):
        service.Service.Run(self, memstream)
        self.AppRun(memstream)

    def AppRun(self, memstream = None):
        pass

    def BatchedRemoteCall(self, batchedCalls):
        retvals = []
        for callID, (service, method, args, keywords) in batchedCalls.iteritems():
            try:
                c = '%s::%s (Batched\\Server)' % (service, method)
                timer = PushMark(c)
                try:
                    with CallTimer(c):
                        retvals.append((0, callID, apply(getattr(sm.GetService(service), method), args, keywords)))
                finally:
                    PopMark(timer)

            except StandardError as e:
                if getattr(e, '__passbyvalue__', 0):
                    retvals.append((1, callID, strx(e)))
                else:
                    retvals.append((1, callID, e))
                sys.exc_clear()

        return retvals

    def GetSessionValuesFromRowset(self, si):
        return {}

    def GetInitialValuesFromCharID(self, charID):
        return {}

    def CloseUserSessions(self, userIDs, reason, clientID = None):
        if type(userIDs) not in (types.ListType, types.TupleType):
            userIDs = [userIDs]
        for each in FindSessions('userid', userIDs):
            if clientID is None or not hasattr(each, 'clientID') or each.clientID != clientID:
                each.LogSessionHistory(reason)
                CloseSession(each)

    def TerminateClientConnections(self, reason, filter):
        if macho.mode != 'proxy' or not isinstance(filter, types.DictType) or len(filter) == 0:
            raise RuntimeError('TerminateClientConnections should only be called on a proxy and with a non-empty filter dictionnary')
        numDisconnected = 0
        for clientSession in GetSessions():
            blue.pyos.BeNice()
            if hasattr(clientSession, 'clientID') and not clientSession.role & ROLE_SERVICE:
                clientID = getattr(clientSession, 'clientID')
                if clientID is None:
                    continue
                skip = False
                for attr, value in filter.iteritems():
                    if not (hasattr(clientSession, attr) and getattr(clientSession, attr) == value):
                        skip = True
                        break

                if not skip:
                    numDisconnected += 1
                    clientSession.LogSessionHistory('Connection terminated by administrator %s, reason is: %s' % (str(session.userid), reason))
                    sm.GetService('machoNet').TerminateClient(reason, clientID)

        return numDisconnected

    def EndAllGameSessions(self, remote = 0):
        if remote:
            self.session.ConnectToAllProxyServerServices('sessionMgr').EndAllGameSessions()
        else:
            txt = ''
            for s in GetSessions():
                blue.pyos.BeNice()
                if hasattr(s, 'clientID') and not s.role & ROLE_SERVICE:
                    sid = s.sid
                    s.LogSessionHistory('Session closed by administrator %s' % str(session.userid))
                    CloseSession(s, True)

    def RemoveSessionsFromServer(self, nodeID, sessionIDs):
        if macho.mode != 'proxy':
            raise RuntimeError('RemoveSessionsFromServer should only be called on a proxy')
        log.LogInfo('CTXSESS: RemoveSessionsFromServer(nodeID=', nodeID, '), with ', len(sessionIDs), ' session IDs')
        mn = sm.services['machoNet']
        serverTID = mn.transportIDbySolNodeID.get(nodeID, None)
        if serverTID is not None:
            serverTransport = mn.transportsByID[serverTID]
            for sid in sessionIDs:
                sess = sessionsBySID.get(sid, None)
                if sess is not None:
                    uthread.worker('SessionMgr::RemoveSesssionsFromServer', serverTransport.RemoveSessionFromServer, sess)

        else:
            log.LogWarning('RemoveSessionsFromServer() called with unknown or non-server nodeID ', nodeID)

    def GetSessionDetails(self, clientID, sid):
        import htmlwriter
        macho = sm.GetService('machoNet')
        if clientID:
            s = macho.GetSessionByClientID(clientID)
        else:
            s = GetSessions(sid)
        if s is None:
            return
        info = [['sid', s.sid],
         ['version', s.version],
         ['clientID', getattr(s, 'clientID', '')],
         ['userid', s.userid],
         ['userType', s.userType],
         ['role', s.role],
         ['charid', s.charid],
         ['lastRemoteCall', s.lastRemoteCall]]
        for each in self.additionalSessionDetailsAttribs:
            info.append([each, s.__dict__[each]])

        sessionsBySID, sessionsByAttribute = GetSessionMaps()
        for each in info:
            if each[0] == 'sid':
                if each[1] not in sessionsBySID:
                    each[1] = str(each[1]) + ' <b>(Not in sessionsBySID)</b>'
            elif each[0] in sessionsByAttribute:
                a = getattr(s, each[0])
                if a:
                    if a not in sessionsByAttribute[each[0]]:
                        each[1] = str(each[1]) + " <b>(Not in sessionsByAttribute['%s'])</b>" % each[0]
                    elif s.sid not in sessionsByAttribute[each[0]].get(a, {}):
                        each[1] = str(each[1]) + " <b>(Not in sessionsByAttribute['%s']['%s'])</b>" % (each[0], a)

        info.append(['IP Address', getattr(s, 'address', '?')])
        connectedObjects = []
        hd = ['ObjectID', 'References', 'Object']
        for k, v in s.machoObjectsByID.iteritems():
            tmp = [k, '%s.%s' % (util.FmtDateEng(v[0]), v[0] % const.SEC), htmlwriter.Swing(str(v[1]))]
            if isinstance(v[1], ObjectConnection):
                tmp[2] = str(tmp[2]) + ' (c2ooid=%s)' % str(v[1].__dict__['__c2ooid__'])
                if v[1].__dict__['__c2ooid__'] not in s.connectedObjects:
                    tmp[2] = str(tmp[2]) + ' <b>(Not in s.connectedObjects)</b>'
                else:
                    object = v[1].__dict__['__object__']
                    if s.sid not in object.sessionConnections:
                        tmp[2] = str(tmp[2]) + ' <b>(s.sid not in object.sessionConnections)</b>'
                    if s.sid not in object.objectConnections or v[1].__dict__['__c2ooid__'] not in object.objectConnections[s.sid]:
                        tmp[2] = str(tmp[2]) + ' <b>([s.sid][c2ooid]) not part of object.objectConnections)</b>'
            if k not in sessionsByAttribute['objectID']:
                tmp[2] = str(tmp[2]) + " <b>(Not in sessionsByAttribute['objectID'])</b>"
            elif s.sid not in sessionsByAttribute['objectID'][k]:
                tmp[2] = str(tmp[2]) + " <b>(Not in sessionsByAttribute['objectID']['%s'])</b>" % k
            connectedObjects.append(tmp)

        sessionHistory = []
        lastEntry = ''
        i = 0
        for each in s.sessionhist:
            tmp = each[2].replace('\n', '<br>')
            if tmp == lastEntry:
                txt = '< same >'
            else:
                txt = tmp
            lastEntry = tmp
            sessionHistory.append((each[0],
             i,
             each[1],
             htmlwriter.Swing(txt)))
            i += 1

        streamInfo = []
        try:
            streams = macho.transportsByID[macho.transportIDbySessionID[s.sid]].readers
            for stream in streams:
                streamInfo.append((stream.address,
                 stream.sequence_number,
                 stream.reconnects,
                 ''))

        except KeyError:
            pass

        return (info,
         connectedObjects,
         sessionHistory,
         s.calltimes,
         s.sessionVariables,
         streamInfo)


def IsInClientContext():
    return 'base.ClientContext' in GetLocalStorage()


def IsSessionChangeDisconnect(change, character = False):
    key = 'charid' if character else 'userid'
    if key in change and change[key][0] is not None and change[key][1] is None:
        return change[key][0]
    else:
        return False


class ClientContext(UpdatedLocalStorage):

    def __init__(self, applicationID = None, languageID = None):
        UpdatedLocalStorage.__init__(self, {'base.ClientContext': True,
         'applicationID': applicationID,
         'languageID': languageID})


class MethodCachingContext(UpdatedLocalStorage):

    def __init__(self, methodCachingScope):
        UpdatedLocalStorage.__init__(self, {'base.MethodCachingContext': methodCachingScope})


def CachedMethodCalled(cacheKey, details):
    try:
        cacheScope = GetLocalStorage()['base.MethodCachingContext']
        if details:
            clientTimes = details['versionCheck']
            if clientTimes:
                clientTime = clientTimes[0]
                cacheScope[cacheKey] = (sm.GetService('objectCaching').__versionchecktimes__[clientTime], 'sessionInfo' in details)
    except KeyError:
        pass


exports = {'base.CreateSession': CreateSession,
 'base.SessionMgr': SessionMgr,
 'base.GetServiceSession': GetServiceSession,
 'base.CloseSession': CloseSession,
 'base.GetSessions': GetSessions,
 'base.FindSessions': FindSessions,
 'base.CountSessions': CountSessions,
 'base.FindClientsAndHoles': FindClientsAndHoles,
 'base.FindSessionsAndHoles': FindSessionsAndHoles,
 'base.ObjectConnection': ObjectConnection,
 'base.GetCallTimes': GetCallTimes,
 'base.CallTimer': CallTimer,
 'base.EnableCallTimers': EnableCallTimers,
 'base.CallTimersEnabled': CallTimersEnabled,
 'base.FindClients': FindClients,
 'base.GetSessionMaps': GetSessionMaps,
 'base.GetAllSessionInfo': GetAllSessionInfo,
 'base.allObjectConnections': allObjectConnections,
 'base.allConnectedObjects': allConnectedObjects,
 'base.GetUndeadObjects': GetUndeadObjects,
 'base.GetObjectUUID': GetObjectUUID,
 'base.GetObjectByUUID': GetObjectByUUID,
 'base.sessionChangeDelay': SESSIONCHANGEDELAY,
 'base.GetNewSid': GetNewSid,
 'base.sessionsBySID': sessionsBySID,
 'base.allSessionsBySID': allSessionsBySID,
 'base.sessionsByAttribute': sessionsByAttribute,
 'base.outstandingCallTimers': outstandingCallTimers,
 'base.dyingObjects': dyingObjects,
 'base.methodCallHistory': methodCallHistory,
 'base.IsInClientContext': IsInClientContext,
 'base.IsSessionChangeDisconnect': IsSessionChangeDisconnect,
 'base.ClientContext': ClientContext,
 'base.MethodCachingContext': MethodCachingContext,
 'base.CachedMethodCalled': CachedMethodCalled,
 'base.ThrottlePerMinute': ThrottlePerMinute,
 'base.ThrottlePer5Minutes': ThrottlePer5Minutes,
 'base.ThrottlePerSecond': ThrottlePerSecond}