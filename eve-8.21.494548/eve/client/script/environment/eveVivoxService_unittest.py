#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/eveVivoxService_unittest.py
import unittest
VIVOX_NONE = 0
VIVOX_INITIALIZING = 1
VXCCONNECTORSTATE_INITIALIZED = 2
VXCLOGINSTATE_LOGGEDOUT = 0
VXCLOGINSTATE_LOGGINGIN = 1
VXCLOGINSTATE_LOGGEDIN = 2
VXCLOGINSTATE_LOGGINGOUT = 3
VXCLOGINSTATE_ERROR = 4

class _TestEveVivox(unittest.TestCase):

    def setUp(self):
        mock.SetUp(self, globals())
        self.sm = mock.Mock('sm', insertAsGlobal=True)
        self.eve = mock.Mock('eve', insertAsGlobal=True)
        self.vivox = EveVivoxService()
        self.vivox.connector = mock.Mock('connector')
        self.vivox.enabled = True
        self.vivox.members = {'150132482': [[150136972, 0, 'sip:150136972U1099691492cdf2c4d00416a3534faa81@evc.vivox.com']]}
        self.vivox.vivoxUserName = 'bogusUser'
        self.vivox.password = 'bogusPassword'
        self.vivox.vivoxLoginState = VXCLOGINSTATE_LOGGEDIN
        self.vivox.speakingChannel = None
        self.vivox.autoJoinQueue = []
        self.vivox.prettyChannelNames = {}
        self.channelID = 150132482

        def MockSvc(svcName):
            if svcName == 'LSC':
                mockLSCSvc = mock.Mock('LSC')
                return mockLSCSvc
            if svcName == 'voiceMgr':
                mockVoiceMgr = mock.Mock('voiceMgr')
                mockVoiceMgr.LogChannelLeft = lambda *args: mock.Mock('LogChannelLeft')
                mockVoiceMgr.LogChannelJoined = lambda *args: mock.Mock('LogChannelJoined')
                return mockVoiceMgr
            if svcName == 'fleet':
                mockFleetSvc = mock.Mock('fleetSvc')
                mockFleetSvc.IsVoiceMuted = lambda *args: False
                return mockFleetSvc

        self.vivox.voiceMgr = MockSvc('voiceMgr')
        self.sm.RemoteSvc = lambda *args: MockSvc(args[0])
        self.eve.LocalSvc = lambda *args: MockSvc(args[0])
        self.sm.GetService = lambda *args: MockSvc(args[0])

    def tearDown(self):
        mock.TearDown(self)

    def testOnLeftChannelEchoWhenEchoIsSpeakingChannel(self):
        self.vivox.members = {'Echo': [[150136972, 0, 'sip:150136972U1099691492cdf2c4d00416a3534faa81@evc.vivox.com']]}
        leavingChannel = 'Echo'
        self.vivox.speakingChannel = 'Echo'
        self.vivox._OnLeftChannel(leavingChannel)
        speakingChannelCorrect = self.vivox.speakingChannel != str(self.channelID)
        channelPopped = leavingChannel not in self.vivox.members
        self.assertTrue(speakingChannelCorrect, 'speaking channel is not correct ' + '\nleavingChannel:\n' + leavingChannel + '\nspeakingChannel:\n' + str(self.vivox.speakingChannel))
        self.assertTrue(channelPopped, 'channel which was left has not been removed from members ' + '\nleavingChannel:\n' + leavingChannel + '\nself.vivox.members:\n' + str(self.vivox.members))

    def testOnLeftChannelEchoWhenEchoIsNotSpeakingChannel(self):
        leavingChannel = 'Echo'
        self.vivox.members = {'Echo': [[150136972, 0, 'sip:150136972U1099691492cdf2c4d00416a3534faa81@evc.vivox.com']]}
        self.vivox.speakingChannel = 'Elvis'
        self.vivox._OnLeftChannel('Echo')
        speakingChannelCorrect = self.vivox.speakingChannel == self.vivox.speakingChannel
        channelPopped = leavingChannel not in self.vivox.members
        self.assertTrue(speakingChannelCorrect, 'spekaing channel is not correct ' + '\nleavingChannel:\n' + leavingChannel + '\nspeakingChannel:\n' + 'Elvis')
        self.assertTrue(channelPopped, 'channel which was left has not been removed from members ' + '\nleavingChannel:\n' + leavingChannel + '\nself.vivox.members:\n' + str(self.vivox.members))

    def testOnLeftChannelOfTypeIntWhichIsNotSpeakingChannel(self):
        leavingChannel = str(self.channelID)
        self.vivox.speakingChannel = '123'
        self.vivox.nextChannel = 'Elvis'
        self.vivox.previousSpeakingChannel = 'oldChannel'
        self.vivox.prettyChannelNames = {}
        self.vivox.GetPrettyChannelName = lambda *args: 'bogusChannelName'
        self.eve.Message = mock.Mock('Message')
        self.vivox._OnLeftChannel(leavingChannel)
        speakingChannelCorrect = self.vivox.speakingChannel == '123'
        channelPopped = leavingChannel not in self.vivox.members
        self.assertTrue(speakingChannelCorrect, 'spekaing channel is not correct ' + '\nleavingChannel:\n' + leavingChannel + '\nspeakingChannel:\n' + self.vivox.speakingChannel + '\\speakingChannel should be 123')
        self.assertTrue(channelPopped, 'channel which was left has not been removed from members ' + '\nleavingChannel:\n' + leavingChannel + '\nself.vivox.members:\n' + str(self.vivox.members))

    def testOnLeftChannelOfTypeIntThatIsSpeakingChannlAlsoJoinEcho(self):
        leavingChannel = str(self.channelID)
        self.vivox.speakingChannel = str(self.channelID)
        self.vivox.autoJoinQueue = ['Echo']
        self.vivox.previousSpeakingChannel = 'oldChannel'
        self.vivox.prettyChannelNames = {}
        self.vivox.GetPrettyChannelName = lambda *args: 'bogusChannelName'
        self.vivox.JoinEchoChannel = mock.Mock('JoinEchoChannel')
        self.eve.Message = mock.Mock('Message')
        self.vivox._OnLeftChannel(leavingChannel)
        speakingChannelCorrect = self.vivox.speakingChannel != str(self.channelID)
        channelPopped = leavingChannel not in self.vivox.members
        callToJoinEchoMade = False
        for each in mock.GetCallLog():
            if 'JoinEchoChannel()' == each:
                callToJoinEchoMade = True
                break

        self.assertTrue(callToJoinEchoMade, 'No call was made to join echo channel')
        self.assertTrue(speakingChannelCorrect, 'spekaing channel is not correct ' + '\nleavingChannel:\n' + leavingChannel + '\nspeakingChannel:\n' + str(self.vivox.speakingChannel))
        self.assertTrue(channelPopped, 'channel which was left has not been removed from members ' + '\nleavingChannel:\n' + leavingChannel + '\nself.vivox.members:\n' + str(self.vivox.members))

    def testOnLeftChannelOfTypeTuple(self):
        self.vivox.members['squad555'] = [[150136972, 0, 'sip:150136972U1099691492cdf2c4d00416a3534faa81@evc.vivox.com']]
        leavingChannel = 'squad555'
        self.vivox.speakingChannel = str(self.channelID)
        self.vivox.nextChannel = 'Elvis'
        self.vivox.previousSpeakingChannel = 'oldChannel'
        self.vivox.prettyChannelNames = {}
        self.vivox.GetPrettyChannelName = lambda *args: 'bogusChannelName'
        self.eve.Message = mock.Mock('Message')
        self.vivox._OnLeftChannel(leavingChannel)
        speakingChannelCorrect = self.vivox.speakingChannel != leavingChannel
        channelPopped = leavingChannel not in self.vivox.members
        self.assertTrue(speakingChannelCorrect, 'spekaing channel is not correct ' + '\nleavingChannel:\n' + leavingChannel + '\nspeakingChannel:\n' + str(self.vivox.speakingChannel))
        self.assertTrue(channelPopped, 'channel which was left has not been removed from members ' + '\nleavingChannel:\n' + leavingChannel + '\nself.vivox.members:\n' + str(self.vivox.members))