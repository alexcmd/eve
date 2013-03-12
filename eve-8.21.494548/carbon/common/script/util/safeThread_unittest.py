#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/util/safeThread_unittest.py
import unittest

def mockUthreadNew(function, *args, **kwargs):
    function(*args, **kwargs)
    return mock.Mock()


class sleepTests(unittest.TestCase):

    def setUp(self):
        mock.SetGlobalReference(globals())
        self.blue = mock.Mock('blue', insertAsGlobal=True)
        self.blue.pyos.GetArg = lambda *args, **kwargs: 'stuff that may or may not be in the command line blah blah blah blah'
        self.uthread = mock.Mock('uthread', insertAsGlobal=True)
        self.uthread.new = mockUthreadNew
        self.SafeThread = SafeThread()
        self.SafeThread.SafeThreadLoop = self.mockSafeThreadLoop
        self.SafeThread.init('idString')
        self.nowList = []
        self.numCalls = 0
        self.numLoops = 10
        self.sleepTime = 1000
        mock.SetYieldDuration(0)

    def tearDown(self):
        del self.SafeThread
        del self.blue
        del self.uthread

    def mockSafeThreadLoop(self, now):
        self.numCalls += 1
        self.nowList.append(now)
        if self.numCalls >= self.numLoops:
            return SafeThread.KILL_ME

    def testSleepTimes(self):
        self.SafeThread.LaunchSafeThreadLoop_MS(self.sleepTime)
        expectedList = range(self.numLoops)
        for i in range(self.numLoops):
            expectedList[i] *= self.sleepTime

        self.assertTrue(expectedList == self.nowList, 'Expected time list did not match actual time list.' + str(expectedList) + str(self.nowList))