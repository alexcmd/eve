#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/parklife/autopilot.py
import util
import destiny
import base
import service
import sys
import uthread
import blue
import log
import localization
import uiconst
from collections import defaultdict
AUTO_NAVIGATION_LOOP_INTERVAL_MS = 2000

class AutoPilot(service.Service):
    __guid__ = 'svc.autoPilot'
    __exportedcalls__ = {'SetOn': [],
     'SetOff': [],
     'GetState': []}
    __notifyevents__ = ['OnBallparkCall', 'OnSessionChanged', 'OnRemoteMessage']
    __dependencies__ = ['michelle', 'starmap']

    def __init__(self):
        service.Service.__init__(self)
        self.updateTimer = None
        self.autopilot = 0
        self.ignoreTimerCycles = 0
        self.isOptimizing = False
        self.approachAndTryTarget = None
        self.warpAndTryTarget = None
        self.__navigateSystemDestinationItemID = None
        self.__navigateSystemThread = None
        uthread.new(self.UpdateWaypointsThread).context = 'autoPilot::UpdateWaypointsThread'

    def UpdateWaypointsThread(self):
        blue.pyos.synchro.SleepWallclock(2000)
        starmapSvc = sm.GetService('starmap')
        waypoints = starmapSvc.GetWaypoints()
        if len(waypoints):
            starmapSvc.SetWaypoints(waypoints)

    def Run(self, memStream = None):
        service.Service.Run(self, memStream)
        self.StartTimer()

    def SetOn(self):
        if self.autopilot == 1:
            return
        self.autopilot = 1
        if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
            self.CancelSystemNavigation()
        else:
            self.AbortApproachAndTryCommand()
            self.AbortWarpAndTryCommand()
        sm.ScatterEvent('OnAutoPilotOn')
        eve.Message('AutoPilotEnabled')
        self.KillTimer()
        self.StartTimer()
        self.LogNotice('Autopilot Enabled')

    def OnSessionChanged(self, isremote, session, change):
        self.KillTimer()
        self.ignoreTimerCycles = 3
        self.StartTimer()
        sm.GetService('starmap').UpdateRoute(fakeUpdate=True)

    def SetOff(self, reason = ''):
        if self.autopilot == 0:
            self.KillTimer()
            return
        sm.ScatterEvent('OnAutoPilotOff')
        self.autopilot = 0
        if reason == '  - waypoint reached':
            eve.Message('AutoPilotWaypointReached')
        elif reason == '  - no destination path set':
            eve.Message('AutoPilotDisabledNoPathSet')
        else:
            eve.Message('AutoPilotDisabled')
        self.LogNotice('Autopilot Disabled', reason)

    def OnRemoteMessage(self, msgID, *args, **kwargs):
        if msgID == 'FleetWarp':
            self.LogInfo('Canceling auto navigation due to fleet warp detected')
            self.CancelSystemNavigation()

    def OnBallparkCall(self, functionName, args):
        functions = ['GotoDirection', 'GotoPoint']
        if args[0] != eve.session.shipid:
            return
        if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
            cancelAutoNavigation = False
            if self.__navigateSystemDestinationItemID is None:
                pass
            elif functionName in {'GotoDirection', 'GotoPoint', 'Orbit'}:
                cancelAutoNavigation = True
            elif functionName == 'FollowBall' and self.__navigateSystemDestinationItemID != args[1]:
                cancelAutoNavigation = True
            if cancelAutoNavigation:
                self.LogInfo('Canceling auto navigation to', self.__navigateSystemDestinationItemID, 'as a respons to OnBallparkCall:', functionName, args)
                self.CancelSystemNavigation()
        else:
            approachAndTryFunctions = ['GotoDirection',
             'GotoPoint',
             'FollowBall',
             'Orbit',
             'WarpTo']
            warpAndTryFunctions = ['GotoDirection',
             'GotoPoint',
             'FollowBall',
             'Orbit']
            if functionName in approachAndTryFunctions:
                if functionName != 'FollowBall' or self.approachAndTryTarget != args[1]:
                    self.AbortApproachAndTryCommand()
            if functionName in warpAndTryFunctions:
                self.AbortWarpAndTryCommand()
        if functionName in functions:
            if functionName == 'GotoDirection' and self.gotoCount > 0:
                self.gotoCount = 0
                self.LogInfo('Autopilot gotocount set to 0')
                return
            if self.gotoCount == 0:
                waypoints = sm.GetService('starmap').GetWaypoints()
                if waypoints and util.IsStation(waypoints[-1]):
                    return
            self.SetOff(functionName + str(args))
            self.LogInfo('Autopilot stopped gotocount is ', self.gotoCount)

    def GetState(self):
        return self.autopilot

    def Stop(self, stream):
        self.KillTimer()
        service.Service.Stop(self)

    def KillTimer(self):
        self.updateTimer = None

    def StartTimer(self):
        self.gotoCount = 0
        self.updateTimer = base.AutoTimer(2000, self.Update)

    def Update(self):
        if self.autopilot == 0:
            self.KillTimer()
            return
        elif self.ignoreTimerCycles > 0:
            self.ignoreTimerCycles = self.ignoreTimerCycles - 1
            return
        elif not session.IsItSafe():
            self.LogInfo('returning as it is not safe')
            return
        elif not session.rwlock.IsCool():
            self.LogInfo("returning as the session rwlock isn't cool")
            return
        else:
            starmapSvc = sm.GetService('starmap')
            destinationPath = starmapSvc.GetDestinationPath()
            if len(destinationPath) == 0:
                self.SetOff('  - no destination path set')
                return
            elif destinationPath[0] == None:
                self.SetOff('  - no destination path set')
                return
            bp = sm.GetService('michelle').GetBallpark()
            if not bp:
                return
            elif sm.GetService('jumpQueue').IsJumpQueued():
                return
            ship = bp.GetBall(session.shipid)
            if ship is None:
                return
            elif ship.mode == destiny.DSTBALL_WARP:
                return
            destID = None
            destItem = None
            for ballID in bp.balls.iterkeys():
                slimItem = bp.GetInvItem(ballID)
                if slimItem == None:
                    continue
                if slimItem.groupID == const.groupStargate and destinationPath[0] in map(lambda x: x.locationID, slimItem.jumps):
                    destID = ballID
                    destItem = slimItem
                    break
                elif destinationPath[0] == slimItem.itemID:
                    destID = ballID
                    destItem = slimItem
                    break

            if destID is None:
                return
            jumpingToCelestial = not util.IsSolarSystem(destinationPath[0])
            theJump = None
            if not jumpingToCelestial:
                for jump in destItem.jumps:
                    if destinationPath[0] == jump.locationID:
                        theJump = jump
                        break

            if theJump is None and not jumpingToCelestial:
                return
            approachObject = bp.GetBall(destID)
            if approachObject is None:
                return
            if jumpingToCelestial:
                jumpToLocationName = cfg.evelocations.Get(destinationPath[0]).name
            else:
                jumpToLocationName = cfg.evelocations.Get(theJump.locationID).name
            shipDestDistance = bp.GetSurfaceDist(ship.id, destID)
            if shipDestDistance < const.maxStargateJumpingDistance and not jumpingToCelestial:
                if ship.isCloaked:
                    return
                if session.mutating:
                    self.LogInfo('session is mutating')
                    return
                if session.changing:
                    self.LogInfo('session is changing')
                    return
                if bp.solarsystemID != session.solarsystemid:
                    self.LogInfo('bp.solarsystemid is not solarsystemid')
                    return
                if sm.GetService('michelle').GetRemotePark()._Moniker__bindParams != session.solarsystemid:
                    self.LogInfo('remote park moniker bindparams is not solarsystemid')
                    return
                try:
                    self.LogNotice('Autopilot jumping from', destID, 'to', theJump.toCelestialID, '(', jumpToLocationName, ')')
                    sm.GetService('sessionMgr').PerformSessionChange('autopilot', sm.GetService('michelle').GetRemotePark().CmdStargateJump, destID, theJump.toCelestialID, session.shipid)
                    eve.Message('AutoPilotJumping', {'what': jumpToLocationName})
                    sm.ScatterEvent('OnAutoPilotJump')
                    self.ignoreTimerCycles = 5
                except UserError as e:
                    if e.msg == 'SystemCheck_JumpFailed_Stuck':
                        self.SetOff()
                        raise 
                    elif e.msg.startswith('SystemCheck_JumpFailed_'):
                        eve.Message(e.msg, e.dict)
                    elif e.msg == 'NotCloseEnoughToJump':
                        park = sm.GetService('michelle').GetRemotePark()
                        park.CmdSetSpeedFraction(1.0)
                        shipui = uicore.layer.shipui
                        if shipui.isopen:
                            shipui.SetSpeed(1.0)
                        park.CmdFollowBall(destID, 0.0)
                        self.LogWarn("Autopilot: I thought I was close enough to jump, but I wasn't.")
                    sys.exc_clear()
                    self.LogError('Autopilot: jumping to ' + jumpToLocationName + ' failed. Will try again')
                    self.ignoreTimerCycles = 5
                except:
                    sys.exc_clear()
                    self.LogError('Autopilot: jumping to ' + jumpToLocationName + ' failed. Will try again')
                    self.ignoreTimerCycles = 5

                return
            elif jumpingToCelestial and util.IsStation(destID) and shipDestDistance < const.maxDockingDistance:
                if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
                    if self.__navigateSystemDestinationItemID != destID:
                        if shipDestDistance > 2500:
                            sm.GetService('audio').SendUIEvent('wise:/msg_AutoPilotApproachingStation_play')
                        sm.GetService('menu').Dock(destID)
                        self.ignoreTimerCycles = 5
                else:
                    if shipDestDistance > 2500 and self.approachAndTryTarget != destID:
                        sm.GetService('audio').SendUIEvent('wise:/msg_AutoPilotApproachingStation_play')
                    sm.GetService('menu').Dock(destID)
                return
            elif shipDestDistance < const.minWarpDistance:
                if ship.mode == destiny.DSTBALL_FOLLOW and ship.followId == destID:
                    return
                self.CancelSystemNavigation()
                park = sm.GetService('michelle').GetRemotePark()
                park.CmdSetSpeedFraction(1.0)
                shipui = uicore.layer.shipui
                if shipui.isopen:
                    shipui.SetSpeed(1.0)
                park.CmdFollowBall(destID, 0.0)
                eve.Message('AutoPilotApproaching')
                if not (jumpingToCelestial and util.IsStation(destID)):
                    sm.GetService('audio').SendUIEvent('wise:/msg_AutoPilotApproaching_play')
                self.LogInfo('Autopilot: approaching')
                self.ignoreTimerCycles = 2
                return
            try:
                sm.GetService('space').WarpDestination(destID, None, None)
                sm.GetService('michelle').GetRemotePark().CmdWarpToStuffAutopilot(destID)
                eve.Message('AutoPilotWarpingTo', {'what': jumpToLocationName})
                if jumpingToCelestial:
                    if util.IsStation(destID):
                        sm.GetService('audio').SendUIEvent('wise:/msg_AutoPilotWarpingToStation_play')
                    self.LogInfo('Autopilot: warping to celestial object', destID)
                else:
                    sm.GetService('audio').SendUIEvent('wise:/msg_AutoPilotWarpingTo_play')
                    self.LogInfo('Autopilot: warping to gate')
                sm.ScatterEvent('OnAutoPilotWarp')
                self.ignoreTimerCycles = 2
            except UserError as e:
                sys.exc_clear()
                item = sm.GetService('godma').GetItem(session.shipid)
                if item.warpScrambleStatus > 0:
                    self.SetOff('Autopilot cannot warp while warp scrambled.')
                if 'WarpDisrupted' in e.msg:
                    self.SetOff('Autopilot cannot warp while warp scrambled by bubble.')
            except Exception as e:
                self.SetOff('Unknown error')

            return

    def NavigateSystemTo(self, itemID, interactionRange, commandFunc, *args, **kwargs):
        self.LogInfo('Navigate to item', itemID, 'range', interactionRange, 'and execute', commandFunc)
        self.__navigateSystemDestinationItemID = itemID
        self.__navigateSystemThread = base.AutoTimer(50, self.__NavigateSystemTo, itemID, interactionRange, commandFunc, *args, **kwargs)

    def CancelSystemNavigation(self):
        self.LogInfo('Cancel system navigation')
        self.__navigateSystemDestinationItemID = None
        self.__navigateSystemThread = None
        self.AbortApproachAndTryCommand()
        self.AbortWarpAndTryCommand()

    def __NavigateSystemTo(self, itemID, interactionRange, commandFunc, *args, **kwargs):
        try:
            if self.InWarp():
                pass
            elif self.InInteractionRange(itemID, interactionRange) and not self.IsCloaked():
                self.LogInfo('System navigation: at target location. Triggering action')
                try:
                    commandFunc(*args, **kwargs)
                except UserError:
                    raise 
                finally:
                    self.CancelSystemNavigation()

            elif self.InWarpRange(itemID):
                self.LogInfo('System navigation: warping to target', itemID, interactionRange)
                sm.GetService('menu').WarpToItem(itemID, warpRange=const.minWarpEndDistance, cancelAutoNavigation=False)
            elif self.IsApproachable(itemID):
                sm.GetService('menu').Approach(itemID, cancelAutoNavigation=False)
            else:
                self.LogInfo('Unable to resolve the proper navigation action. Aborting.', itemID, interactionRange, commandFunc)
                self.CancelSystemNavigation()
            if self.__navigateSystemThread:
                self.__navigateSystemThread.interval = AUTO_NAVIGATION_LOOP_INTERVAL_MS
        except UserError as e:
            self.LogInfo('User error detected', e.msg, itemID, interactionRange, commandFunc)
            raise 
        except:
            self.LogError('Problem while navigating system', itemID, interactionRange, commandFunc)
            log.LogException(channel=self.__guid__)

    def IsApproachable(self, itemID):
        destBall = self.michelle.GetBall(itemID)
        if destBall is not None and destBall.surfaceDist < const.minWarpDistance:
            return True
        return False

    def InInteractionRange(self, itemID, interactionRange):
        destBall = self.michelle.GetBall(itemID)
        if destBall is not None and destBall.surfaceDist < interactionRange:
            return True
        return False

    def InWarp(self):
        shipBall = self.michelle.GetBall(session.shipid)
        if shipBall is not None and shipBall.mode == destiny.DSTBALL_WARP:
            return True
        return False

    def InWarpRange(self, itemID):
        destBall = self.michelle.GetBall(itemID)
        if destBall is not None and destBall.surfaceDist > const.minWarpDistance:
            return True
        return False

    def IsCloaked(self):
        shipBall = self.michelle.GetBall(session.shipid)
        if shipBall is not None:
            return bool(shipBall.isCloaked)
        return False

    def WarpAndTryCommand(self, id, cmdMethod, args, interactionRange):
        bp = sm.StartService('michelle').GetRemotePark()
        if not bp:
            return
        if sm.StartService('space').CanWarp() and self.warpAndTryTarget != id:
            self.approachAndTryTarget = None
            self.warpAndTryTarget = id
            try:
                michelle = sm.StartService('michelle')
                shipBall = michelle.GetBall(session.shipid)
                if shipBall is None:
                    return
                if shipBall.mode != destiny.DSTBALL_WARP:
                    bp.CmdWarpToStuff('item', id)
                    sm.StartService('space').WarpDestination(id, None, None)
                while self.warpAndTryTarget == id and shipBall.mode != destiny.DSTBALL_WARP:
                    blue.pyos.synchro.SleepWallclock(500)

                while shipBall.mode == destiny.DSTBALL_WARP:
                    blue.pyos.synchro.SleepWallclock(500)

                counter = 3
                while self.warpAndTryTarget == id and counter > 0:
                    destBall = michelle.GetBall(id)
                    if not destBall or destBall.surfaceDist > const.minWarpDistance:
                        break
                    destBall.GetVectorAt(blue.os.GetSimTime())
                    if destBall.surfaceDist < interactionRange:
                        cmdMethod(*args)
                        break
                    blue.pyos.synchro.SleepWallclock(500)
                    counter -= 1

            finally:
                if self.warpAndTryTarget == id:
                    self.warpAndTryTarget = None

    def ApproachAndTryCommand(self, id, cmdMethod, args, interactionRange):
        bp = sm.StartService('michelle').GetRemotePark()
        if not bp:
            return
        if self.approachAndTryTarget != id and not self.warpAndTryTarget:
            self.warpAndTryTarget = None
            self.approachAndTryTarget = id
            localbp = sm.StartService('michelle').GetBallpark()
            if not localbp:
                return
            try:
                sm.GetService('menu').Approach(id)
                michelle = sm.StartService('michelle')
                while self.approachAndTryTarget == id:
                    ball = localbp.GetBall(id)
                    if not ball:
                        break
                    ball.GetVectorAt(blue.os.GetSimTime())
                    shipBall = localbp.GetBall(session.shipid)
                    if ball.surfaceDist < interactionRange and not shipBall.isCloaked:
                        cmdMethod(*args)
                        break
                    blue.pyos.synchro.SleepWallclock(500)

            finally:
                if self.approachAndTryTarget == id:
                    self.approachAndTryTarget = False

    def AbortApproachAndTryCommand(self, nextID = None):
        if nextID != self.approachAndTryTarget:
            self.approachAndTryTarget = None
            self.CancelSystemNavigation()

    def AbortWarpAndTryCommand(self, nextID = None):
        if nextID != self.warpAndTryTarget:
            self.warpAndTryTarget = None
            self.CancelSystemNavigation()

    def OptimizeRoute(self, *args):
        if self.isOptimizing:
            return
        try:
            self.isOptimizing = True
            starmapSvc = sm.GetService('starmap')
            waypoints = list(starmapSvc.GetWaypoints())
            originalWaypointsLen = len(waypoints)
            isReturnTrip = False
            for idx in reversed(xrange(len(waypoints))):
                if waypoints[idx] == eve.session.solarsystemid2:
                    del waypoints[idx]
                    isReturnTrip = True
                    break

            solarSystemToStations = defaultdict(list)
            for i, waypoint in enumerate(waypoints):
                if util.IsStation(waypoint):
                    solarSystemID = cfg.stations.Get(waypoint).solarSystemID
                    solarSystemToStations[solarSystemID].append(waypoint)
                    waypoints[i] = solarSystemID

            waypoints = list(set(waypoints))
            if session.solarsystemid2 in waypoints:
                waypoints.remove(session.solarsystemid2)
            numWaypoints = len(waypoints)
            if numWaypoints == 0:
                return
            msg = None
            if numWaypoints > 12:
                msg = 'UI/Map/MapPallet/msgOptimizeQuestion1'
            elif numWaypoints > 10:
                msg = 'UI/Map/MapPallet/msgOptimizeQuestion2'
            if msg:
                yesNo = eve.Message('AskAreYouSure', {'cons': localization.GetByLabel(msg, numWaypoints=originalWaypointsLen)}, uiconst.YESNO)
                if yesNo != uiconst.ID_YES:
                    return
            distance = {}
            waypoints.append(eve.session.solarsystemid2)
            for fromID in waypoints:
                distance[fromID] = {}
                for toID in waypoints:
                    if fromID == toID:
                        continue
                    distance[fromID][toID] = sm.GetService('pathfinder').GetJumpCountFromCurrent(toID, fromID)

            waypoints.pop()
            startTime = blue.os.GetWallclockTimeNow()
            prefix = [None]
            _push = prefix.append
            _pop = prefix.pop

            def FindShortestRoute(prefix, distanceSoFar, toID):
                distanceTo = distance[toID]
                prefix[-1] = toID
                shortestDist = shortestRouteSoFar[0]
                if len(prefix) < numWaypoints:
                    _push(None)
                    for i in indexes:
                        toID = waypoints[i]
                        if not toID:
                            continue
                        candidateDist = distanceSoFar + distanceTo[toID]
                        if candidateDist >= shortestDist:
                            continue
                        waypoints[i] = None
                        FindShortestRoute(prefix, candidateDist, toID)
                        waypoints[i] = toID

                    _pop()
                else:
                    for i in indexes:
                        toID = waypoints[i]
                        if not toID:
                            continue
                        candidateDist = distanceSoFar + distanceTo[toID]
                        if candidateDist < shortestDist:
                            shortestRouteSoFar[:] = [candidateDist, prefix[:], toID]
                            shortestDist = candidateDist

            shortestRouteSoFar = [999999999, None, None]
            indexes = range(len(waypoints))
            FindShortestRoute(prefix, 0, eve.session.solarsystemid2)
            distance, waypoints, last = shortestRouteSoFar
            blue.pyos.synchro.SleepWallclock(1)
            endTime = blue.os.GetWallclockTimeNow()
            if waypoints is None:
                raise UserError('AutoPilotDisabledUnreachable')
            waypoints.append(last)
            waypointsWithStations = []
            for waypoint in waypoints:
                if waypoint in solarSystemToStations:
                    waypointsWithStations.extend(solarSystemToStations[waypoint])
                else:
                    waypointsWithStations.append(waypoint)

            if isReturnTrip == True:
                sm.GetService('starmap').SetWaypoints(waypointsWithStations + [session.solarsystemid2])
            else:
                sm.GetService('starmap').SetWaypoints(waypointsWithStations)
        finally:
            self.isOptimizing = False