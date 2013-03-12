#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/util/rateLimitedQueue.py
import sys
import time
import collections
QueueEntry = collections.namedtuple('QueueEntry', ['serialNumber', 'firstTime', 'queueTime'])

class RateLimitedQueue(object):

    def __init__(self, maxReadyItems = sys.maxint, maxReadyRate = sys.maxint, maxReadyGrowth = 0, maxQueuedItems = sys.maxint, maxCompleteItems = sys.maxint, numCompleteFunc = None):
        self.maxReadyItems = maxReadyItems
        self.maxReadyRate = maxReadyRate
        self.maxReadyGrowth = maxReadyGrowth
        self.maxQueuedItems = maxQueuedItems
        self.maxCompleteItems = maxCompleteItems
        self.queue = collections.deque()
        self.queueMap = dict()
        self.nextSerialNumber = 0
        self.numReady = 0
        self.numReadied = 0
        self.maxReadyBoost = 0
        self.ticker = None
        if numCompleteFunc is None:
            self.numCompleteFunc = lambda : self.nextSerialNumber - len(self.queueMap)
        else:
            self.numCompleteFunc = numCompleteFunc

    NONE = 0
    QUEUED = 1
    READY = 2
    COMPLETE = NONE

    def State(self, key):
        queueEntry = self.queueMap.get(key, None)
        if queueEntry is None:
            return RateLimitedQueue.NONE
        if queueEntry.serialNumber == -1:
            return RateLimitedQueue.READY
        return RateLimitedQueue.QUEUED

    def NumQueued(self):
        return len(self.queueMap) - self.numReady

    def NumReady(self):
        return self.numReady

    def NumTotal(self):
        return len(self.queueMap)

    def NumComplete(self):
        return self.numCompleteFunc()

    def GetQueue(self):
        return [ k for k in self.queue if k in self.queueMap and self.queueMap[k].serialNumber != -1 ]

    def GetReadySet(self):
        return {k for k in self.queueMap if self.queueMap[k].serialNumber == -1}

    def QueuePosition(self, key):
        queueEntry = self.queueMap.get(key, None)
        if queueEntry is not None and queueEntry.serialNumber != -1:
            firstEntry = self.queueMap[self.queue[0]]
            return (queueEntry.serialNumber - firstEntry.serialNumber, time.clock() - queueEntry.firstTime)
        else:
            return

    def Enqueue(self, key, bypassQueue = False):
        queueEntry = self.queueMap.get(key, None)
        now = time.clock()
        if bypassQueue:
            if queueEntry is not None:
                if queueEntry.serialNumber != -1:
                    self.Remove(key)
                else:
                    self.queueMap[key] = QueueEntry(serialNumber=-1, firstTime=queueEntry.firstTime, queueTime=now)
                    return RateLimitedQueue.READY
            else:
                self.nextSerialNumber += 1
            self.queueMap[key] = QueueEntry(serialNumber=-1, firstTime=now, queueTime=now)
            self.numReady += 1
            self.numReadied += 1
        else:
            if queueEntry is None:
                if self.NumQueued() >= self.maxQueuedItems:
                    return
                queueEntry = QueueEntry(serialNumber=self.nextSerialNumber, firstTime=now, queueTime=now)
                self.nextSerialNumber += 1
                self.queue.append(key)
                self.queueMap[key] = queueEntry
            else:
                self.queueMap[key] = QueueEntry(serialNumber=queueEntry.serialNumber, firstTime=queueEntry.firstTime, queueTime=now)
            self.MakeReady()
        return self.State(key)

    def Complete(self, key):
        if self.State(key) != RateLimitedQueue.READY or self.numCompleteFunc() >= self.maxCompleteItems:
            return None
        delay = time.clock() - self.queueMap[key].firstTime
        del self.queueMap[key]
        self.numReady -= 1
        self.MakeReady()
        return delay

    def Process(self, key, bypassQueue = False):
        state = self.Enqueue(key, bypassQueue)
        if state == RateLimitedQueue.READY and self.Complete(key) is not None:
            return RateLimitedQueue.NONE
        return state

    def Remove(self, key):
        state = self.State(key)
        if state != RateLimitedQueue.NONE:
            del self.queueMap[key]
            if state == RateLimitedQueue.READY:
                self.numReady -= 1
                self.MakeReady()
            elif len(self.queue) > 0 and self.queue[0] == key:
                self._ClearQueueJunk()
            return True
        return False

    def QueueFrontWaitTime(self, default = None):
        if len(self.queue) > 0:
            return time.clock() - self.queueMap[self.queue[0]].firstTime
        else:
            return default

    def Timeout(self, olderThan, fromQueue = True, fromReady = True):
        deadline = time.clock() - olderThan
        timedOut = [ k for k, q in self.queueMap.iteritems() if q.queueTime < deadline ]
        self.numReady -= len({k:q for k, q in self.queueMap.iteritems() if q.queueTime < deadline and q.serialNumber == -1})
        self.queueMap = {k:q for k, q in self.queueMap.items() if q.queueTime >= deadline}
        self._ClearQueueJunk()
        self.MakeReady()
        return timedOut

    def Tick(self):
        self.numReadied = 0
        effectiveMaxReadyItems = min(self.maxReadyItems + self.maxReadyBoost + self.maxReadyGrowth, self.NumTotal())
        self.maxReadyBoost = max(effectiveMaxReadyItems - self.maxReadyItems, 0)
        self.MakeReady()

    def MakeReady(self):
        maxItems = len(self.queue)
        maxItems = min(maxItems, self.maxReadyRate - self.numReadied)
        maxItems = min(maxItems, self.maxReadyItems + self.maxReadyBoost - self.numReady)
        maxItems = min(maxItems, self.maxCompleteItems - self.numCompleteFunc() - self.numReady)
        numItemsReadied = 0
        while numItemsReadied < maxItems and len(self.queue) > 0:
            key = self.queue.popleft()
            queueEntry = self.queueMap[key]
            self.queueMap[key] = QueueEntry(serialNumber=-1, firstTime=queueEntry.firstTime, queueTime=queueEntry.queueTime)
            numItemsReadied += 1
            self._ClearQueueJunk()

        self.numReady += numItemsReadied
        self.numReadied += numItemsReadied

    def _ClearQueueJunk(self):
        try:
            queueEntry = self.queueMap.get(self.queue[0], None)
            while queueEntry is None or queueEntry.serialNumber == -1:
                self.queue.popleft()
                queueEntry = self.queueMap.get(self.queue[0], None)

        except IndexError:
            pass


exports = {'util.RateLimitedQueue': RateLimitedQueue}