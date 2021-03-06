#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/util/benchmark1.py
import blue
import log
import util
import sys
import uiutil
import os
import yaml
import time
import uthread
import appUtils
import trinity
import bluepy
from service import ROLEMASK_ELEVATEDPLAYER, ROLE_SPAWN, ROLE_WORLDMOD, ROLE_HEALOTHERS, ROLE_GML, ROLE_GMH
SleepSim = blue.pyos.synchro.SleepSim
Yield = blue.pyos.synchro.Yield
Progress = lambda title, text, current, total: sm.GetService('loading').ProgressWnd(title, text, current, total)
OUTPUT_FILE = 'benchmark.yaml'
logChannel = log.GetChannel('Benchmark.Progress')

class Quitter(Exception):
    pass


def Quit(msg = ''):
    raise Quitter(msg)


def Log(*args):
    args = ('BMScript:',) + args
    args = [ str(i) for i in args ]
    txt = ' '.join(args)
    for line in txt.split('\n'):
        logChannel.Log(line, log.LGWARN)


def LogException():
    import traceback, StringIO
    s = StringIO.StringIO()
    excType, val, tb = sys.exc_info()
    traceback.print_exception(excType, val, tb, None, s)
    Log('Exception:')
    Log(s.getvalue())
    s.close()


def Try(this, methodType = None):
    scale = None
    try:
        if methodType is not None:
            Log('Detected methodType %s' % methodType)
            if methodType == 0:
                method, duration, scale = this
                seconds = duration * 60
                if scale == 1:
                    Log('Running %s for %s iterations' % (method, duration))
                    for run in xrange(duration):
                        Log('------------------------------------------------------')
                        Log('Starting Run %s of %s' % (run + 1, duration))
                        method()
                        Log('Run completed')

                    Log('Completed %s iterations of %s' % (duration, method))
                elif scale == 0:
                    starttime = time.time()
                    length = time.time() - starttime
                    Log('Running %s for %s minutes' % (method, duration))
                    while length <= seconds:
                        Log('------------------------------------------------------')
                        Log('Timestamp Begin: %s from %s' % (length, seconds))
                        method()
                        length = time.time() - starttime

                    Log('Completed duration testing (%s minutes)' % duration)
            elif methodType == 1:
                method, var, state = this
                method(var, state)
            else:
                Log('Invalid methodType: %s %s' % (methodType, methodType.__class__))
        else:
            this()
    except:
        Log('FAIL: %s %s' % (this, methodType))
        LogException()
        sys.exc_clear()


def MakeTopmost():
    triapp = trinity.app
    pos = triapp.GetWindowRect()
    triapp.SetWindowPos(pos.left, pos.top)


def SwitchUI():
    uicore.cmd.CmdHideUI()


class Script(object):
    __notifyevents__ = ['OnClientReady', 'OnNewState']

    def __init__(self):
        self.events = {}
        self.ballparkOK = False
        self.defaults = None
        self.benchmark = sm.GetService('benchmark')
        self.sessions = []
        self.screenDimensions = None
        self.platform = None
        self.platformID = None
        self.runID = None
        self.DoDBSetup()
        sm.RegisterNotify(self)

    def DoDBSetup(self):
        connStr = prefs.GetValue('bmdbconn', None)
        if connStr is not None:
            try:
                import db
                self.dbsess = db.Session(connStr)
                self.defDB = connStr
            except (WindowsError, ImportError):
                sys.exc_clear()
                self.dbsess = 0
                self.defDB = None

        else:
            self.dbsess = 0
            self.defDB = None

    def OnClientReady(self, what):
        Log('Received ClientReady event ' + repr(what))
        self.events[what] = True

    def OnNewState(self, *args):
        Log('Received OnNewState event')
        self.events['newstate'] = True

    def WaitForEvent(self, what):
        Log('Waiting for event %s' % repr(what))
        while what not in self.events or not self.events[what]:
            Yield()

        self.events[what] = False
        Log('Event %s received' % repr(what))

    def WaitForEvents(self, events, all = False):
        Log('Waiting for events %s' % events)
        got = []
        if not all:
            while True:
                for e in events:
                    if e in self.events and self.events[e]:
                        got.append(e)
                        break

                if got:
                    break
                Yield()

        else:
            left = events[:]
            while True:
                for e in left:
                    if e in self.events and self.events[e]:
                        got.append(e)
                        left.remove(e)

                if got == events:
                    break
                Yield()

        for e in got:
            self.events[e] = False

        Log('Events %s received' % got)
        return e

    def WaitForSession(self):
        if blue.os.GetSimTime() <= session.nextSessionChange:
            ms = 1000 + 1000L * (session.nextSessionChange - blue.os.GetSimTime()) / 10000000L
            Log('Waiting for session change to complete, %fs' % (ms / 1000.0))
            SleepSim(ms)

    def WaitForBallpark(self):
        if self.ballparkOK:
            return
        bp = sm.GetService('michelle').GetBallpark()
        Log('Waiting For Ballpark')
        tries = 0
        while not bp:
            tries += 1
            bp = sm.GetService('michelle').GetBallpark()
            SleepSim(250)

        while not len(bp.balls) and not bp.validState:
            tries += 1
            SleepSim(250)

        if tries:
            self.WaitForEvent('newstate')
        self.ballparkOK = True

    def WaitForWarpin(self):
        import destiny
        self.WaitForBallpark()
        bp = sm.GetService('michelle').GetBallpark()
        triesLeft = 10
        ball = None
        while triesLeft and not ball:
            Log('WaitForWarpin: Looking for my balls... (%d)' % triesLeft)
            ball = bp.balls.get(bp.ego, None) or bp.balls.get(session.shipid, None)
            if ball:
                break
            SleepSim(1000)
            triesLeft -= 1

        if ball:
            while ball.mode == destiny.DSTBALL_WARP:
                Yield()

        else:
            Log("WaitForWarpin: Wtf? Couldn't find my own balls... But the show must go on!")

    def WaitForEula(self):
        Log('Waiting for the EULA')
        self.WaitForEvent('login')
        SleepSim(2000)
        MakeTopmost()

    def WaitForCharsel(self):
        self.WaitForEvent('charsel')

    def GetState(self):
        stateDict = {}
        platform = self.GetPlatform()
        for key, value in platform.iteritems():
            stateDict[key] = value

        for key, value in [('bmoutput', prefs.GetValue('bmoutput', '0:0')),
         ('dbop', prefs.GetValue('bmoutput', '0:0').split(':')[0]),
         ('fiop', prefs.GetValue('bmoutput', '0:0').split(':')[1]),
         ('bmaccount', prefs.GetValue('bmaccount', 'None')),
         ('bmdbconn', prefs.GetValue('bmdbconn', 'None')),
         ('defDB', self.defDB),
         ('platformID', self.platformID),
         ('runID', self.runID)]:
            try:
                stateDict[key] = value
            except:
                sys.exc_clear()

        return stateDict

    def ChangeScreenMode(self, w = None, h = None, fullScreen = None):
        d = sm.GetService('device')
        if not self.defaults:
            self.defaults = d.GetSettings()
        if w and h and fullScreen is not None:
            settings = d.GetFailsafeMode(sm.services['device'].adapters[0], not fullScreen, dimensions=(w, h))
            device = d.CreationToSettings(settings)
            self.screenDimensions = (w, h)
        else:
            device = self.defaults
            self.screenDimensions = None
        d.SetDevice(device, fallback=0, keepSettings=0, hideTitle=not device.Windowed)

    def GetSessionName(self, name):
        return name

    def FindClosestStation(self):
        self.WaitForBallpark()
        bp = sm.GetService('michelle').GetBallpark()
        candidates = [ (b.surfaceDist, k) for k, b in bp.balls.iteritems() if bp.GetInvItem(k) and bp.GetInvItem(k).groupID == const.groupStation ]
        candidates.sort()
        if not candidates:
            return None
        return candidates[0][1]

    def SlashCmd(self, cmd):
        count = 0
        while True:
            try:
                sm.RemoteSvc('slash').SlashCmd(cmd)
                break
            except:
                sys.exc_clear()
                count += 1
                if count == 10:
                    Quit('Slash command failed after 10 tries: %s' % cmd)
                SleepSim(10000)

    class DotNotate(object):

        def __init__(self, d):
            self.__dict__ = d

    def FormatVersion(self, version):
        a = (version & 18446462598732840960L) >> 48
        b = (version & 281470681743360L) >> 32
        c = (version & 4294901760L) >> 16
        d = version & 65535
        v = '%d.%02d.%02d.%d' % (a,
         b,
         c,
         d)
        return v

    def GetPlatform(self):
        env = blue.pyos.GetEnv()
        server = 'localhost'
        for arg in blue.pyos.GetArg():
            if arg.startswith('/server:'):
                server = arg.split(':')[1]

        if blue.win32.IsTransgaming():
            tgplatform = env.get('CEDEGA_PATH', 'NULL')
            tghostname = env.get('USER', 'NULL')
            if tgplatform != 'NULL':
                hostName = tghostname + '_LINUX_TG'
            else:
                hostName = tghostname + '_MAC_TG'
        else:
            hostName = env.get('COMPUTERNAME', 'NULL')
        soundCard = 'placeholder'
        device = sm.StartService('device')
        dev = trinity.device
        deviceCount = trinity.adapters.GetAdapterCount()
        adapter = dev.adapter
        aid = trinity.adapters.GetAdapterInfo(adapter)
        video = str(aid.description)
        driverVersion = self.FormatVersion(aid.driverVersion)
        dxversion = 'dx9'
        hdre = device.IsHdrEnabled()
        bloom = device.GetBloom()
        sbs = 1024
        rcs = blue.motherLode.maxMemUsage / 1024 / 1024
        sm3 = device.SupportsSM3()
        turrets = settings.user.ui.Get('turretsEnabled', 1)
        effects = settings.user.ui.Get('effectsEnabled', 1)
        missiles = settings.user.ui.Get('missilesEnabled', 1)
        trails = settings.user.ui.Get('trails', 1)
        drones = settings.user.ui.Get('droneModelsEnabled', 1)
        explode = settings.user.ui.Get('explosionEffectsEnabled', 1)
        userot = settings.public.generic.Get('userotcache', 1)
        lazyload = settings.public.generic.Get('lazyLoading', 1)
        preload = settings.public.generic.Get('preload', 1)
        async = settings.public.generic.Get('asyncLoad', 1)
        return {'hostname': hostName,
         'cpuid': env.get('PROCESSOR_IDENTIFIER', 'NULL'),
         'cpucount': int(env.get('NUMBER_OF_PROCESSORS', 1)),
         'cpuspeed': int(blue.os.GetCycles()[1] / 1000000),
         'ram': 1 + blue.win32.GlobalMemoryStatus()['TotalPhys'] / 1024 / 1024,
         'soundcard': soundCard,
         'videocard': video,
         'videodriver': driverVersion,
         'adapterCount': int(deviceCount),
         'startTime': blue.os.GetWallclockTime(),
         'version': boot.keyval['version'].split('=')[1],
         'build': int(boot.keyval['build'].split('=')[1]),
         'server': server,
         'branch': boot.keyval['branch'].split('=')[1],
         'hdr': int(hdre),
         'shadowBufferSize': int(sbs),
         'resourceCacheSize': int(rcs),
         'bloomEnabled': int(bloom),
         'turretsEnabled': int(turrets),
         'effectsEnabled': int(effects),
         'missilesEnabled': int(missiles),
         'trailsEnabled': int(trails),
         'droneModelsEnabled': int(drones),
         'explosionEffects': int(explode),
         'userotcache': int(userot),
         'lazyloading': int(lazyload),
         'preload': int(preload),
         'asyncloading': int(async),
         'dxversion': dxversion,
         'supportsSM3': sm3}

    def Platform(self):
        platform = self.DotNotate(self.platform)
        try:
            if self.defDB and self.dbsess:
                platformID = self.dbsess.Execute('dbo.bm2PlatformSelectID', [platform.hostname,
                 platform.cpuid,
                 platform.cpucount,
                 platform.cpuspeed,
                 platform.ram,
                 platform.soundcard,
                 platform.videocard,
                 platform.videodriver,
                 platform.adapterCount])
                self.dbsess.Execute('dbo.bm2Platform_Update', [platformID,
                 platform.cpuid,
                 platform.cpucount,
                 platform.cpuspeed,
                 platform.ram,
                 platform.soundcard,
                 platform.videocard,
                 platform.videodriver,
                 platform.adapterCount])
                return platformID
        except:
            sys.exc_clear()

    def GenerateRunID(self):
        platform = self.DotNotate(self.platform)
        self.platformID = self.Platform()
        if self.defDB and self.dbsess:
            newRunID = self.dbsess.Execute('dbo.bm2TrinityRun_Add', [self.platformID,
             platform.startTime,
             platform.version,
             platform.build,
             platform.server,
             platform.branch,
             platform.hdr,
             platform.shadowBufferSize,
             platform.resourceCacheSize,
             platform.bloomEnabled,
             platform.turretsEnabled,
             platform.effectsEnabled,
             platform.missilesEnabled,
             platform.trailsEnabled,
             platform.dxversion])
            return newRunID
        Log('No DB connection')
        return 1

    def LoginUser(self, server = None, user = None, password = None):
        Log('Entering login data')
        Log("Logging in. Username: '%s', Server: '%s'" % (user, server))
        statusText = serverStatus = None
        try:
            statusText, serverStatus = sm.GetService('machoNet').GetServerStatus('%s:%s' % (server, 26000))
            SleepSim(5000)
            Log("Server status: '%s'" % serverStatus)
        except:
            Log('Server status: None')
            sys.exc_clear()

        if serverStatus == None or serverStatus == {}:
            sys.exc_clear()
            Log('Cannot connect to server, status is None or empty.')
            eve.Message('UnableToConnectToServer')
            self.CancelLogin()
            return
        serverbuild = serverStatus.get('boot_build', None)
        if serverbuild != boot.build:
            Log('Client and server have different builds! client: %s, server: %s' % (boot.build, serverbuild))
            eve.Message('PatchTestServerWarning', {'serverVersion': serverbuild,
             'clientVersion': boot.build})
            if serverbuild > boot.build:
                Log('Client is older than server.')
                self.CancelLogin()
                return
        try:
            uiutil.GetChild(uicore.layer.login, 'username').SetValue(user)
            uiutil.GetChild(uicore.layer.login, 'password').SetValue(password)
            uicore.layer.login.Confirm()
        except:
            sys.exc_clear()
            self.invalidFields = []
            self.invalidFields.append('username')
            self.invalidFields.append('password')
            self.invalidFieldsText = ''
            field = self.invalidFields.pop(0)
            while len(self.invalidFields) > 0:
                field = self.invalidFields.pop(0)
                if len(self.invalidFieldsText):
                    if len(self.invalidFields) == 0:
                        self.invalidFieldsText = '%s %s %s' % (self.invalidFieldsText, 'and', field)
                    else:
                        self.invalidFieldsText = '%s, %s' % (self.invalidFieldsText, field)
                else:
                    self.invalidFieldsText = field

            if self.invalidFieldsText is not None:
                eve.Message('LoginParameterIncorrect', {'invalidFields': self.invalidFieldsText})
                self.CancelLogin()
                return

        Log('Waiting for character selection')
        self.WaitForCharsel()

    def CancelLogin(self):
        sm.GetService('loading').CleanUp()
        Quit('Login error!')

    def SelectCharacter(self, charName = None):
        if not session.role & ROLEMASK_ELEVATEDPLAYER:
            Quit('Permission denied')
        ok = False
        role = session.role
        if role & (ROLE_SPAWN | ROLE_WORLDMOD):
            if role & ROLE_HEALOTHERS and role & ROLE_GML and role & ROLE_GMH:
                ok = True
        if not ok:
            Quit('The benchmark script requires GML, GMH, HEALOTHERS, TRANSFER and either SPAWN or WORLDMOD.')
        Log('Selecting character %s' % repr(charName))
        characterInfo = sm.RemoteSvc('charUnboundMgr').GetCharacterInfo()
        if charName:
            if charName.isdigit():
                charid = int(charName)
            else:
                for i in characterInfo:
                    if i['characterName'].lower() == charName.lower():
                        charid = i['characterID']
                        break
                else:
                    charid = None

        else:
            charid = characterInfo[0]['characterID']
        sm.GetService('sessionMgr').PerformSessionChange('charsel', sm.RemoteSvc('charUnboundMgr').SelectCharacterID, charid)
        events = self.WaitForEvents(['station', 'inflight', 'worldspace'])
        if events == 'inflight':
            Log('Inflight, stopping ship (I)')
            uicore.cmd.CmdStopShip()
            self.WaitForBallpark()
        Log('selected character, character is in %s' % repr(events))
        return events

    def Undock(self):
        if not session.stationid:
            return
        self.WaitForSession()
        Log('Undocking')
        station = sm.GetService('station')
        shipID = util.GetActiveShip()
        station.UndockAttempt(shipID)
        self.WaitForEvent('inflight')
        SleepSim(7500)
        Log('Inflight, stopping ship (II)')
        uicore.cmd.CmdStopShip()
        self.WaitForBallpark()

    def Dock(self, stationID = None, fast = True):
        if session.stationid and (session.stationid == stationID or not stationID):
            Log('Dock issued, but already docked!')
            return
        Log('Dock pending...')
        if not session.stationid:
            self.WaitForWarpin()
        self.WaitForSession()
        if stationID is None:
            stationID = self.FindClosestStation()
        if stationID is None:
            Log('Docking to last visited station')
            self.SlashCmd('/tr me last')
        else:
            Log('Docking to station %s' % stationID)
            if fast:
                Log('Using /tr')
                self.SlashCmd('/tr me %s' % stationID)
            else:
                sm.GetService('menu').Dock(stationID)
        self.WaitForEvents(['station', 'worldspace'])
        self.ballparkOK = False
        return session.stationid

    def WarpTo(self, itemID, minRange = 0):
        sm.GetService('michelle').GetRemotePark().CmdWarpToStuff('item', itemID, minRange=minRange)

    def Hop(self, distance):
        sm.RemoteSvc('slash').SlashCmd('/hop %s' % distance)

    def TravelTo(self, itemID):
        stationID = None
        if util.IsSolarSystem(itemID):
            solarSystemID = itemID
        else:
            stationID = itemID
            solarSystemID = cfg.stations.Get(itemID).solarSystemID
        Log('RouteID: %s' % self.routeID)
        Log('Travel: Destination systemID %s, stationID %s' % (solarSystemID, stationID))
        self.Undock()
        self.Hop(10000)
        Log('Stopping ship')
        uicore.cmd.CmdStopShip()
        ap = sm.GetService('autoPilot')
        ap.SetOff()
        while session.solarsystemid2 != solarSystemID:
            if not ap.GetState():
                Log('Travel: Activating autopilot...')
                sm.StartService('starmap').SetWaypoint(solarSystemID, clearOtherWaypoints=True)
                sm.GetService('autoPilot').SetOn()
            SleepSim(5000)

        Log('Travel: Arrived in destination system!')

    def Save(self):
        connected = prefs.GetValue('bmdbconn', 0)
        output = prefs.GetValue('bmoutput', '0:0')
        try:
            dbop, fiop = output.split(':')
        except:
            dbop = 0
            fiop = 0
            sys.exc_clear()

        if dbop and connected:
            ids = [ sm.GetService('benchmark').SaveSession(sess, self.runID, dbconn=connected) for sess in self.sessions ]
            Log('Saved sessions %s' % ids)
        if fiop:
            filler = None
            ids = [ sm.GetService('benchmark').SaveSession(sess, self.runID, dbconn=filler) for sess in self.sessions ]
            Log('Saved sessions')
        del self.sessions[:]

    def Benchmark(self, ms = None, sessionName = None, description = None, runID = None, snapShot = False):
        sess = self.benchmark.CreateSession(sessionName, description, runID)
        if ms is not None:
            uthread.new(sess.CaptureStart)
            SleepSim(ms)
            sess.CaptureEnd()
        elif snapShot:
            sess.Snap()
            sess.CreateSnapshot()
        else:
            uthread.new(sess.CaptureStart)
        self.sessions.append(sess)
        return sess

    def bm_Template(self):
        Log('The FooBar benchmark! Barring the Foo!')
        sess = self.benchmark.CreateSession('CHANGE ME', 'Some description for this benchmark, for the database')
        sess.Snap()
        sess.Snap()
        sess.CreateAverages()
        self.sessions.append(sess)

    def bm_CharSel(self):
        Log('Measuring charsel framerate')
        self.Benchmark(10000, 'CharSelPerformance1', '15 seconds of framerate measurement in character selection', self.runID)

    def bm_StationPerformance(self):
        self.Dock()
        Log('stationperformance1')
        self.Benchmark(10000, 'StationPerformance1', '10 seconds of framerate in station', self.runID)
        Log('stationperformance2')
        SwitchUI()
        self.Benchmark(10000, 'StationPerformance2', '10 seconds of framerate in station, no UI', self.runID)
        SwitchUI()

    def bm_SpacePerformance(self):
        if session.stationid:
            self.Undock()
        Log('Stopping ship')
        uicore.cmd.CmdStopShip()
        Log('spaceperformance1')
        self.Benchmark(10000, 'SpacePerformance1', '10 seconds of framerate outside station', self.runID)
        Log('spaceperformance2')
        SwitchUI()
        self.Benchmark(10000, 'SpacePerformance2', '10 seconds of framerate outside station, no UI', self.runID)
        SwitchUI()

    def bm_AutopilotPerformance(self):
        if self.defDB and self.dbsess:
            self.routeID, self.startID, self.endID = self.dbsess.Execute('dbo.bm2Route_GetRandom', [])[0][1][0]
        else:
            sys.exc_clear()
            self.routeID = 1
            self.startID = 60014659
            self.endID = 60006358
        Log('autopilotperformance1')
        self.Dock(self.startID, True)
        self.Undock()
        Log('Stopping ship')
        uicore.cmd.CmdStopShip()
        bm = self.Benchmark(None, 'AutopilotPerformance1', 'Trip from Kisogo to Madirmilire', self.runID)
        self.TravelTo(self.endID)
        SleepSim(5000)
        bm.CaptureEnd()

    def bm_RattingPerformance(self):
        Log('rattingperformance1')
        self.Dock()
        self.Undock()
        Log('Stopping ship')
        uicore.cmd.CmdStopShip()
        sm.GetService('slash').SlashCmd('/tr me offset=randvec(100au)')
        SleepSim(7500)
        try:
            sm.GetService('slash').SlashCmd('/entity deploy 32 "Guristas Ascriber"')
            sm.GetService('slash').SlashCmd('/entity deploy  8 "Guristas Conquistador"')
            SleepSim(2000)
            targets = []
            bp = sm.GetService('michelle').GetBallpark()
            for ballID in bp.balls.keys():
                item = bp.GetInvItem(ballID)
                if item and item.categoryID == 11:
                    targets.append(ballID)

            bm = self.Benchmark(None, 'RattingPerformance1', 'Destroying NPCs', self.runID)
            for targetID in targets:
                SleepSim(500)
                sm.GetService('slash').SlashCmd('/heal %d 0' % targetID)

            SleepSim(2000)
            bm.CaptureEnd()
            sm.GetService('insider').HealRemove(const.groupWreck)
        finally:
            sm.RemoteSvc('slash').SlashCmd('/nukem')
            SleepSim(2000)
            sm.GetService('insider').HealRemove(const.groupWreck)

    def bm_Fitting(self):
        self.Dock(60014659)
        sm.GetService('station').LoadSvc(None, close=True)
        sm.GetService('station').LoadSvc('fitting')
        SleepSim(4000)
        ship = sm.GetService('godma').GetItem(session.shipid)
        t, a, p = sm.GetService('modtest').GetModuleLists()
        t = t + a + p
        total = len(t)
        current = 0
        errors = []
        while t:
            SleepSim(1000)
            sm.RemoteSvc('slash').SlashCmd('/unload me all')
            slotsLeft = {'hiPower': [ x + const.flagHiSlot0 for x in range(int(ship.hiSlots)) ],
             'medPower': [ x + const.flagMedSlot0 for x in range(int(ship.medSlots)) ],
             'loPower': [ x + const.flagLoSlot0 for x in range(int(ship.lowSlots)) ]}
            for item in t[:]:
                rec, effects = item
                Progress('Module Fitting Test', 'Fitting %d/%d: %s' % (current, total, rec.name), current, total)
                current += 1
                try:
                    slotType = [ eff.effectName for eff in effects if eff.effectName.endswith('Power') ][0]
                    if slotsLeft[slotType]:
                        sm.RemoteSvc('slash').SlashCmd('/fit me %s' % rec.typeID)
                        t.remove(item)
                        flag = slotsLeft[slotType].pop(0)
                        module = []
                        while not module:
                            blue.pyos.synchro.SleepWallclock(500)
                            module = [ x for x in sm.GetService('godma').GetItem(session.shipid).modules if x.flagID == flag ]

                        if slotsLeft.values() == [[], [], []]:
                            break
                except UserError as e:
                    errors.append((rec.typeID, str(e)))
                    sys.exc_clear()
                except IndexError:
                    sys.exc_clear()

        sm.GetService('slash').SlashCmd('/unload me all')
        sm.GetService('station').LoadSvc(None, close=True)

    def bm_MapPerformance(self):
        import mapcommon
        sm.GetService('viewState').ActivateView('starmap')
        try:
            bm = self.Benchmark(None, 'MapPerformance1', 'Map Stuff', self.runID)
            for i in range(3):
                sm.GetService('starmap').SetStarColorMode(mapcommon.STARMODE_PLAYERCOUNT)
                SleepSim(2000)
                sm.GetService('starmap').SetStarColorMode(mapcommon.STARMODE_SHIPKILLS24HR)
                SleepSim(2000)
                sm.GetService('starmap').SetStarColorMode(mapcommon.STARMODE_REAL)
                SleepSim(2000)

            SleepSim(2000)
            bm.CaptureEnd()
        finally:
            sm.GetService('viewState').CloseSecondaryView()
            self.SlashCmd('/tr me home')

    def connectionTest(self, *args):
        timeperiod = prefs.GetValue('csduration')
        count = prefs.GetValue('cscount')
        if count > 0:
            count -= 1
            prefs.SetValue('bmnextrun', count)
            prefs.SetValue('cscount', count)
            for a in xrange(timeperiod, -1, -1):
                SleepSim(1000)
                sm.GetService('gameui').Say('Connection test in progress.<br>%s seconds until restart, %s runs left.' % (a, count))

            sm.GetService('gameui').Say('Connection test in progress.<br>Current cycle complete, rebooting!')
            completedsofar = prefs.GetValue('cscompleted', 0)
            prefs.SetValue('cscompleted', completedsofar + 1)
            SleepSim(2000)
            text = 'Client Stats test, %s runs left' % count
            appUtils.Reboot(text)

    def Test(self):
        self.bm_MapPerformance()

    def TestParticular(self, test):
        self.platform = self.GetPlatform()
        self.platformID = self.Platform()
        if not self.runID:
            self.runID = self.GenerateRunID()
        Try(test)
        Try(self.Save)

    def Station(self):
        self.TestParticular(self.bm_StationPerformance)

    def Space(self):
        self.TestParticular(self.bm_SpacePerformance)

    def Autopilot(self):
        self.TestParticular(self.bm_AutopilotPerformance)

    def NPC(self):
        self.TestParticular(self.bm_RattingPerformance)

    def Map(self):
        self.TestParticular(self.bm_MapPerformance)

    def All(self):
        self.TestParticular(self.bm_StationPerformance)
        self.TestParticular(self.bm_SpacePerformance)
        self.TestParticular(self.bm_AutopilotPerformance)
        self.TestParticular(self.bm_RattingPerformance)
        self.TestParticular(self.bm_MapPerformance)

    def Go(self):
        testList = self.ParseFromYAML()
        try:
            server, user, password, character = prefs.GetValue('bmaccount', None).split(':')
        except:
            sys.exc_clear()
            server = user = password = character = ''
            Quit('Incorrect or invalid connection details')

        blue.os.sleeptime = 0
        self.WaitForEula()
        conntest = prefs.GetValue('csloopenabled', 0)
        conncount = prefs.GetValue('cscount', 0)
        if conntest and conncount:
            uicore.Say("Connection test in progress, logging into '%s' with '%s'.<br>%s runs left." % (server, user, conncount))
            self.LoginUser(server, user, password)
            self.SelectCharacter(character)
            self.connectionTest()
            return
        uicore.Say('Benchmarking in progress!')
        self.platform = self.GetPlatform()
        self.platformID = self.Platform()
        self.runID = self.GenerateRunID()
        Log('Measuring login framerate')
        self.Benchmark(10000, 'LoginState2', '15 seconds of framerate measurement at logon', self.runID)
        self.LoginUser(server, user, password)
        filename = settings.public.generic.Get('eveBenchmarkFileName', None)
        if filename:
            settings.public.generic.Set('eveBenchmarkFileName', None)
        self.Benchmark(None, 'LoginState1', 'A snapshot of the machine state after login', self.runID, snapShot=True)
        self.bm_CharSel()
        self.Save
        pcUnLocked = prefs.GetValue('bmreslock', 0)
        triapp = trinity.app
        Log('Running at resolution: %s x %s (fullscreen: %s)' % (uicore.desktop.width, uicore.desktop.height, triapp.fullscreen))
        if pcUnLocked:
            Log('Client resolutions unlocked')
            if self.defDB and self.dbsess:
                displayList = {}
                resInfo = self.dbsess.Execute('dbo.bm2Resolution_Get', [self.platformID])[0][1]
                for position in range(0, len(resInfo)):
                    resID, windowed, fullscreen = resInfo[position]
                    h, w = self.dbsess.Execute('dbo.bm2Resolution_GetByID', [resID])[0][1][0]
                    if windowed:
                        displayList[position] = [w, h, False]
                    if fullscreen:
                        displayList[position + len(resInfo)] = [w, h, True]

        self.SelectCharacter(character)
        sm.GetService('slash').SlashCmd('/unload me all')
        try:
            if pcUnLocked:
                if self.defDB and self.dbsess:
                    for w, h, fullscreen in displayList.values():
                        Log('%s, %s, %s' % (w, h, fullscreen))
                        self.ChangeScreenMode(w, h, fullscreen)
                        Log('Changing resolution to: %s x %s (fullscreen: %s)' % (w, h, fullscreen))
                        for benchmark in testList:
                            e, m, d, s = benchmark
                            Try((m, d, s), e)
                            SleepSim(5000)
                            Try(self.Save)

                else:
                    for w, h, fullscreen in ((1024, 768, False),
                     (1280, 1024, False),
                     (1024, 768, True),
                     (1280, 1024, True)):
                        self.ChangeScreenMode(w, h, fullscreen)
                        Log('Changing resolution to: %s x %s (fullscreen: %s)' % (w, h, fullscreen))
                        for benchmark in testList:
                            e, m, d, s = benchmark
                            Try((m, d, s), e)
                            SleepSim(5000)
                            Try(self.Save)

            else:
                for benchmark in testList:
                    e, m, d, s = benchmark
                    Try((m, d, s), e)
                    SleepSim(5000)
                    Try(self.Save)

            Try(self.Dock)
        finally:
            if pcUnLocked:
                self.ChangeScreenMode()

        Quit('done')

    def GetIDs(self, *args):
        self.ids = {4: [self.bm_StationPerformance, 'Station'],
         8: [self.bm_SpacePerformance, 'Space'],
         16: [self.bm_AutopilotPerformance, 'Autopilot'],
         32: [self.bm_RattingPerformance, 'Ratting'],
         64: [self.bm_MapPerformance, 'Map']}
        return self.ids

    def ParseFromYAML(self, *args):
        default = [[0,
          self.bm_StationPerformance,
          1,
          1],
         [0,
          self.bm_SpacePerformance,
          1,
          1],
         [0,
          self.bm_AutopilotPerformance,
          1,
          1],
         [0,
          self.bm_RattingPerformance,
          1,
          1],
         [0,
          self.bm_MapPerformance,
          1,
          1]]
        lookup = self.GetIDs()
        DIR = GetDirectory()
        NAME = prefs.GetValue('bmyamlname', os.path.join(DIR, OUTPUT_FILE))
        TARGET = os.path.join(DIR, NAME)
        if not os.path.exists(TARGET):
            Log('Could not find %s. Using default configuration.' % TARGET)
            return default
        f = blue.classes.CreateInstance('blue.ResFile')
        if not f.Open(TARGET, 0):
            f.Open(TARGET, 0)
        Log('Using YAML data file: %s' % TARGET)
        yamldict = yaml.load(f)
        f.Close()
        key = str(prefs.GetValue('bmyamlkey', None))
        if key is None or key not in yamldict:
            Log('key %s is None or is not in the specified file %s' % (key, TARGET))
            return default
        use = yamldict[key]
        loaded = []
        order = use.keys()
        order.sort()
        for k in order:
            dictionary = use[k]
            eventID = dictionary['type']
            if eventID == 0:
                Log('%s %s %s %s' % (eventID,
                 lookup[dictionary['id']][0],
                 dictionary['duration'],
                 dictionary['scale']))
                loaded.append([eventID,
                 lookup[dictionary['id']][0],
                 dictionary['duration'],
                 dictionary['scale']])
            elif eventID == 1:
                Log('%s %s %s %s' % (eventID,
                 self.DoSettingsModify,
                 dictionary['id'],
                 dictionary['setting']))
                loaded.append([eventID,
                 self.DoSettingsModify,
                 dictionary['id'],
                 dictionary['setting']])

        return loaded

    def DoSettingsModify(self, var, state, *args):
        prior = settings.user.ui.Get(var, None)
        Log("Setting '%s' to %s (prior state: '%s')" % (var, state, prior))
        settings.user.ui.Set(var, state)


def GetDirectory():
    return os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'insider')


def GetBenchmarkDirectory():
    return os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'logs', 'Benchmarks')


def CloseXML(*args):
    BENCHMARKDIR = GetBenchmarkDirectory()
    dbop = fiop = 0
    try:
        outputMethods = prefs.GetValue('bmoutput', '0:0')
        dbop, fiop = outputMethods.split(':')
    except:
        sys.exc_clear()

    if fiop:
        Log('Attempting to terminate XML...')
        try:
            filename = settings.public.generic.Get('eveBenchmarkFileName', None)
            TARGET = os.path.join(BENCHMARKDIR, filename)
        except:
            sys.exc_clear()
            filename = 0

        if filename:
            f = blue.classes.CreateInstance('blue.ResFile')
            if not f.Open(TARGET, 0):
                if f.FileExists(TARGET):
                    f.Open(TARGET, 0)
                    f.read()
                    f.Write('</eveBenchmarking>')
                    f.Close()
            else:
                f.Open(TARGET, 0)
                f.read()
                f.Write('</eveBenchmarking>')
                f.Close()
            Log('XML closed.')
        else:
            Log('Could not attach to XML.')


def ScriptWrapper(methodName):
    Log('Starting Script')
    try:
        getattr(Script(), methodName)()
    except Quitter as e:
        CloseXML()
        Log('Quitting: %s' % e)
        bluepy.Terminate(str(e))
        sys.exc_clear()
    except:
        CloseXML()
        LogException()
        sys.exc_clear()
        Log('Quitting!')
        if methodName != 'Test':
            bluepy.Terminate('Yikes!')

    CloseXML()
    Log('Finished Script')


def Run():
    blue.pyos.CreateTasklet(ScriptWrapper, ('Go',), {})


def Test():
    blue.pyos.CreateTasklet(ScriptWrapper, ('Test',), {})


def Station():
    settings.public.generic.Set('eveBenchmarkFileName', None)
    blue.pyos.CreateTasklet(ScriptWrapper, ('Station',), {})


def Space():
    settings.public.generic.Set('eveBenchmarkFileName', None)
    blue.pyos.CreateTasklet(ScriptWrapper, ('Space',), {})


def Autopilot():
    settings.public.generic.Set('eveBenchmarkFileName', None)
    blue.pyos.CreateTasklet(ScriptWrapper, ('Autopilot',), {})


def NPC():
    settings.public.generic.Set('eveBenchmarkFileName', None)
    blue.pyos.CreateTasklet(ScriptWrapper, ('NPC',), {})


def Map():
    settings.public.generic.Set('eveBenchmarkFileName', None)
    blue.pyos.CreateTasklet(ScriptWrapper, ('Map',), {})


def All():
    settings.public.generic.Set('eveBenchmarkFileName', None)
    blue.pyos.CreateTasklet(ScriptWrapper, ('All',), {})


def connectionTest():
    return getattr(Script(), 'connectionTest')()


def GetIDs():
    return getattr(Script(), 'GetIDs')()


def DoSettingsModify():
    return getattr(Script(), 'DoSettingsModify')()


def GetPlatform():
    return getattr(Script(), 'GetPlatform')()


def GetState():
    return getattr(Script(), 'GetState')()


exports = {'benchmark1.Run': Run,
 'benchmark1.Test': Test,
 'benchmark1.Station': Station,
 'benchmark1.Space': Space,
 'benchmark1.Autopilot': Autopilot,
 'benchmark1.NPC': NPC,
 'benchmark1.Map': Map,
 'benchmark1.All': All,
 'benchmark1.GetPlatform': GetPlatform,
 'benchmark1.GetState': GetState,
 'benchmark1.ConnectionTest': connectionTest,
 'benchmark1.GetIDs': GetIDs}