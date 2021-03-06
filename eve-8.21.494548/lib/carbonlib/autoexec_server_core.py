#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\autoexec_server_core.py
import sys
import log
import autoexec_common
import const
import util
import bluepy
LOG_CONNECTIVITY_ERROR_TIME = const.SEC * 120

def Startup(servicesToRun, startInline = [], serviceManagerClass = 'ServiceManager'):
    import blue
    args = blue.pyos.GetArg()[1:]
    autoexec_common.LogStarting('Server')
    import nasty
    additionalScriptDirs = ['script:/../../../carbon/backend/script/', 'script:/../../backend/script/']
    telemetryStarted = False
    for argument in args:
        if argument.startswith('/telemetryServer='):
            tmServer = str(argument[17:])
            print 'Telemetry starting up on %s (from cmdline)' % tmServer
            blue.statistics.StartTelemetry(tmServer)
            blue.pyos.taskletTimer.telemetryOn = 1
            telemetryStarted = True

    if not telemetryStarted:
        telemetryServer = prefs.GetValue('startupTelemetryServer', None)
        if telemetryServer is not None:
            print 'Telemetry starting up on %s (from prefs)' % telemetryServer
            blue.statistics.StartTelemetry(telemetryServer)
            blue.pyos.taskletTimer.telemetryOn = 1
            telemetryStarted = True
    if '/jessica' in args:
        additionalScriptDirs.extend(['script:/../../../carbon/tools/jessica/script/'])
        useExtensions = '/noJessicaExtensions' not in args
        if useExtensions:
            additionalScriptDirs.extend(['script:/../../../carbon/tools/jessicaExtensions/script/', 'script:/../../tools/jessicaExtensions/script/'])
    nasty.Startup(additionalScriptDirs)
    import util
    import types
    print 'Nasty was started @ -', strx(util.FmtTimeIntervalEng(blue.os.GetWallclockTimeNow() - nastyStarted))
    import localization
    localization.LoadLanguageData()
    t0 = blue.os.GetWallclockTimeNow()
    t00 = t0
    import gc
    gc.disable()
    autoexec_common.LogStarted('Server')
    for i in args:
        if len(i) > 0 and i[0] != '-' and i[0] != '/':
            print 'Executing', strx(i)
            blue.pyos.ExecFile(i, globals())

    import service
    smClass = getattr(service, serviceManagerClass)
    srvMng = smClass(startInline=['DB2', 'machoNet'] + startInline)
    log.general.Log('Startup:  Starting Core Services...', log.LGNOTICE)
    print 'Core Services Starting @', strx(util.FmtTimeIntervalEng(blue.os.GetWallclockTimeNow() - t0))
    startServices = ('machoNet', 'alert', 'objectCaching', 'debug')
    srvMng.Run(startServices)
    macho = sm.services['machoNet']
    DB2 = sm.services['DB2']
    dbzcluster = DB2.GetSchema('zcluster')
    dbzsystem = DB2.GetSchema('zsystem')
    while True:
        r = macho.AreTheseServicesRunning(startServices)
        if r is None:
            break
        log.general.Log('Startup:  Waiting for %s' % r, log.LGNOTICE)
        print 'Startup:  Waiting for', strx(r)
        blue.pyos.synchro.SleepWallclock(3000)

    print 'Database: ' + DB2.GetConnectionString()
    blue.os.SetAppTitle('[%s %s.%s] %s %s %s.%s pid=%s' % (macho.GetNodeID(),
     macho.GetBasePortNumber(),
     boot.region.upper(),
     boot.codename,
     boot.role,
     boot.version,
     boot.build,
     blue.os.pid))
    startupInfo = dbzcluster.Cluster_StartupInfo()[0]
    dbClusterMode = startupInfo.clusterMode
    if dbClusterMode != prefs.clusterMode:
        s = 'DB / Server disagree on cluster mode.  Server says %s, but DB says %s' % (prefs.clusterMode, dbClusterMode)
        log.general.Log('###', log.LGERR)
        log.general.Log('### ' + s, log.LGERR)
        log.general.Log('###', log.LGERR)
        log.Quit(s)
    print '...'
    log.general.Log('Server Configuration:', log.LGNOTICE)
    log.general.Log(' NodeID: %s' % macho.GetNodeID(), log.LGNOTICE)
    log.general.Log(' NodeName: %s' % macho.GetNodeName(), log.LGNOTICE)
    log.general.Log(' Base Port: %s' % macho.GetBasePortNumber(), log.LGNOTICE)
    log.general.Log(' Region: %s' % boot.region.upper(), log.LGNOTICE)
    log.general.Log(' CodeName: %s' % boot.codename, log.LGNOTICE)
    log.general.Log(' Role: %s' % boot.role, log.LGNOTICE)
    log.general.Log(' Version: %s.%s' % (boot.version, boot.build), log.LGNOTICE)
    log.general.Log(' ProcessID: %s' % blue.os.pid, log.LGNOTICE)
    log.general.Log(' clusterMode: %s' % startupInfo.clusterMode, log.LGNOTICE)
    log.general.Log(' Host: %s' % blue.pyos.GetEnv().get('COMPUTERNAME', '?'), log.LGNOTICE)
    log.general.Log('Startup:  Synchronizing Clock with DB...', log.LGNOTICE)
    originalNow = blue.os.GetWallclockTimeNow()
    timediff = 0
    for i in xrange(20):
        now1 = blue.os.GetWallclockTimeNow()
        dbnow = dbzsystem.DateTime()[0].dateTime
        now2 = blue.os.GetWallclockTimeNow()
        now = (now1 + now2) / 2
        if abs(dbnow - now) < (i + 1) * const.SEC:
            break
        reason = 'DB / Server time horribly out of synch, DB says now=%s but server thinks now=%s' % (util.FmtDateEng(dbnow), util.FmtDateEng(now))
        log.general.Log(reason, 2)
        if prefs.clusterMode != 'LIVE':
            newnow = dbnow + (now2 - now1) / 2
            log.general.Log('Resetting clock, setting time: ' + util.FmtDateEng(newnow), log.LGNOTICE)
            print 'Correcting clock to match DB ... advancing ', float(newnow - now2) / float(const.SEC), ' secs'
            t0 += newnow - now2
            blue.pyos.synchro.ResetClock(newnow)
        elif i < 10:
            log.general.Log('Retrying clock check to prevent node death', log.LGERR)
            continue
        else:
            log.Quit('DB / Server time horriby out of synch on live cluster.  Please perform a manual time synch.')

    finalNow = blue.os.GetWallclockTimeNow()
    sm.ScatterEvent('OnTimeReset', originalNow, finalNow)
    nasty.nasty.OnTimeReset(originalNow, finalNow)
    log.general.Log('Startup:  Marking myself as ready for connectivity establishment in zcluster.nodes', log.LGNOTICE)
    print 'Server Ready @', strx(util.FmtTimeIntervalEng(blue.os.GetWallclockTimeNow() - t0))
    dbzcluster.Nodes_SetStatus(macho.GetNodeID(), -4)
    macho.SetStatusKeyValuePair('clusterStatus', -400)
    macho.SetStatusKeyValuePair('clusterStatusText', 'Ready for connectivity establishment')
    log.general.Log('Startup:  Establishing Connectivity...', log.LGNOTICE)
    print 'Establishing Connectivity @', strx(util.FmtTimeIntervalEng(blue.os.GetWallclockTimeNow() - t0))
    if prefs.GetValue('skipConnectivity', 0):
        log.general.Log('Startup:  skipConnectivity has been set, skipping connectivity tests...')
    if not macho.IsResurrectedNode() and not prefs.GetValue('skipConnectivity', 0):
        offsetClock = None
        if macho.GetNodeID() == macho.GetNodeFromAddress(const.cluster.SERVICE_POLARIS, 0):
            offsetClock = t0 - t00
        macho.readyToConnect = True
        startConnectivityCheck = blue.os.GetWallclockTime()
        while 1:
            try:
                log.general.Log('Startup:  Refreshing Connectivity...', log.LGINFO)
                macho.RefreshConnectivity()
            except StandardError:
                log.general.Log('Startup:  Error refreshing connectivity...', log.LGWARN)
                log.LogException(toConsole=1, toLogServer=1, severity=log.LGWARN)
                sys.exc_clear()

            blue.pyos.synchro.SleepWallclock(500)
            try:
                log.general.Log('Startup:  Performing cluster readiness test...', log.LGINFO)
                now = blue.os.GetWallclockTimeNow()
                if now > startConnectivityCheck + LOG_CONNECTIVITY_ERROR_TIME:
                    log.general.Log('I have been checking the network connectivity for a long time.... Should we go and check out why?', log.LGERR)
                    startConnectivityCheck = now
                ready = dbzcluster.Cluster_Ready(-4)
                if type(ready) == types.IntType:
                    if not ready:
                        print 'More Nodes Starting, pausing and retrying'
                        log.general.Log('Startup:  More nodes starting', log.LGNOTICE)
                        blue.pyos.synchro.SleepWallclock(5000)
                        continue
                elif ready[0].readyWhen is None:
                    log.Quit('The DB says that even I am not ready, but I have already passed my ready marker!  Shutting down.')
                else:
                    ready = ready[0]
                    until = ready.readyWhen + const.SEC * 70 * 5
                    if until > now:
                        s = min(70000 / 4, (until - now) / const.SEC * 1000 + 1000)
                        log.general.Log('Startup:  Last startup was at %s.  Waiting %s before retrying, now=%s' % (util.FmtDateEng(ready.readyWhen), util.FmtDateEng(until), util.FmtDateEng(now)), log.LGWARN)
                    else:
                        print 'Only %d nodes have registered themselves in zcluster.nodes and the safetytime has been passed by far...' % ready.nodeCount
                        log.general.Log('Startup:  Only %d nodes have registered in zcluster.nodes, but the safetytime has been passed by far...' % ready.nodeCount, log.LGERR)
                        s = 70000
                    print 'Waiting ', s, ' millisecs prior to rechecking'
                    blue.pyos.synchro.SleepWallclock(s)
                    continue
                startupInfo = dbzcluster.Cluster_StartupInfo()[0]
                log.general.Log('Startup:  Connectivity test - calling all proxies...', log.LGINFO)
                p = macho.session.ConnectToAllProxyServerServices('machoNet').ConnectivityTest(offsetClock, startupInfo.proxyNodeCount - 1, startupInfo.serverNodeCount - startupInfo.unexpectServerNodeCount, uberMachoRaise=True)
                if len(p) != startupInfo.proxyNodeCount:
                    log.general.Log('Startup:  %d proxy nodes available, %d proxy nodes expected...' % (len(p), startupInfo.proxyNodeCount), log.LGINFO)
                    print '%d proxy nodes available, %d proxy nodes expected...' % (len(p), startupInfo.proxyNodeCount)
                    blue.pyos.synchro.SleepWallclock(500)
                    continue
                for isexception, nodeID, ret in p:
                    if not ret:
                        log.general.Log('Startup:  Proxy %d failed its connectivity test' % nodeID, log.LGINFO)
                        raise UberMachoException('Proxy failed connectivity test')

                minimumProxyCount = prefs.GetValue('machoNet.minimumProxyCount', 0) or max(1, int(startupInfo.proxyNodeCount * 0.8))
                if len(p) < minimumProxyCount:
                    print 'Too few proxy nodes succeeded in starting to make this run worthwhile'
                    log.general.Log('Too few proxy nodes succeeded in starting to make this run worthwhile', log.LGERR)
                    log.general.Log('Minimum=%d, Actual=%d' % (minimumProxyCount, len(p)), log.LGERR)
                    blue.pyos.synchro.SleepWallclock(10000)
                    continue
                log.general.Log('Startup:  Connectivity test - calling all sols...', log.LGINFO)
                s = macho.session.ConnectToAllSolServerServices('machoNet').ConnectivityTest(offsetClock, startupInfo.proxyNodeCount, startupInfo.serverNodeCount - 1 - startupInfo.unexpectServerNodeCount, uberMachoRaise=True)
                if len(s) != startupInfo.serverNodeCount - startupInfo.unexpectServerNodeCount:
                    log.general.Log('Startup:  %d server nodes available, %d server nodes expected...' % (len(s), startupInfo.serverNodeCount), log.LGINFO)
                    print '%d server nodes available, %d server nodes expected...' % (len(s), startupInfo.serverNodeCount)
                    blue.pyos.synchro.SleepWallclock(500)
                    continue
                for isexception, nodeID, ret in s:
                    if not ret:
                        log.general.Log('Startup:  Server %d failed its connectivity test' % nodeID, log.LGINFO)
                        raise UberMachoException('Server failed connectivity test')

                minimumSolCount = prefs.GetValue('machoNet.minimumSolCount', 0) or max(1, int(startupInfo.serverNodeCount * 0.8))
                if len(s) < minimumSolCount:
                    print 'Too few sol nodes succeeded in starting to make this run worthwhile'
                    log.general.Log('Too few sol nodes succeeded in starting to make this run worthwhile', log.LGERR)
                    log.general.Log('Minimum=%d, Actual=%d' % (minimumSolCount, len(s)), log.LGERR)
                    blue.pyos.synchro.SleepWallclock(10000)
                    continue
                break
            except UberMachoException as e:
                log.general.Log('Startup:  network connectivity not achieved', log.LGINFO)
                sys.exc_clear()
            except UnMachoDestination as e:
                log.general.Log('Startup:  network connectivity not yet achieved (%s)' % e.payload, 2)
                sys.exc_clear()
            except:
                log.LogException('Exception while pinging all proxies and sols')
                sys.exc_clear()

        print 'Connectivity achieved @', strx(util.FmtTimeIntervalEng(blue.os.GetWallclockTimeNow() - t0))
    if 'waitForPremapping' in startupInfo.__columns__ and int(startupInfo.waitForPremapping) == 1:
        polarisID = macho.GetNodeFromAddress(const.cluster.SERVICE_POLARIS, 0)
        while macho.GetNodeID() != polarisID and dbzcluster.Nodes_Status(polarisID) < -3:
            print 'Waiting for Polaris to reach premapping stage.. sleeping 5 seconds..'
            blue.pyos.synchro.SleepWallclock(5000)

    if prefs.clusterMode in ('TEST', 'LIVE'):
        if macho.GetNodeID() == macho.GetNodeFromAddress(const.cluster.SERVICE_POLARIS, 0):
            if not macho.IsResurrectedNode():
                dbzcluster.Cluster_PreMap()
    log.general.Log('Startup:  Marking myself as ready for distributed startup phase in zcluster.nodes', log.LGNOTICE)
    dbzcluster.Nodes_SetStatus(macho.GetNodeID(), -3)
    macho.SetStatusKeyValuePair('clusterStatus', -300)
    macho.SetStatusKeyValuePair('clusterStatusText', 'Ready for distributed setup')
    log.general.Log('Startup:  Priming address cache...', log.LGNOTICE)
    while 1:
        try:
            if macho.IsResurrectedNode():
                print 'Priming address cache directly @', strx(util.FmtTimeIntervalEng(blue.os.GetWallclockTimeNow() - t0))
                log.general.Log('Startup:  Priming address cache directly...', log.LGINFO)
                macho.PrimeAddressCache(dbzcluster.Addresses_PrimeCache())
            elif macho.GetNodeID() == macho.GetNodeFromAddress(const.cluster.SERVICE_POLARIS, 0):
                print 'Orchestrating priming of address cache @', strx(util.FmtTimeIntervalEng(blue.os.GetWallclockTimeNow() - t0))
                log.general.Log('Startup:  Orchestrating priming of address cache...', log.LGINFO)
                macho.session.ConnectToAllSolServerServices('machoNet').PrimeAddressCache(dbzcluster.Addresses_PrimeCache(), uberMachoRaise=True)
            else:
                print 'Waiting for completion of priming of address cache @', strx(util.FmtTimeIntervalEng(blue.os.GetWallclockTimeNow() - t0))
                if macho.GetNodeID() == macho.GetNodeFromAddress(const.cluster.SERVICE_POLARIS, 0):
                    print "Polaris has died, and I have resumed it's responsibilities"
                    log.general.Log("Polaris has died, and I have resumed it's responsibilities", log.LGERR)
                    continue
            break
        except:
            print 'Priming address cache failure, retrying...'
            log.LogException('Exception while priming address cachep.  I am%s Polaris' % [' NOT', ''][macho.GetNodeID() == macho.GetNodeFromAddress(const.cluster.SERVICE_POLARIS, 0)])
            sys.exc_clear()

    log.general.Log('Startup:  Marking myself as ready for starting user service phase in zcluster.nodes', log.LGNOTICE)
    dbzcluster.Nodes_SetStatus(macho.GetNodeID(), -2)
    macho.SetStatusKeyValuePair('clusterStatus', -200)
    macho.SetStatusKeyValuePair('clusterStatusText', 'Starting user services')
    log.general.Log('Startup:  Starting User Services...', log.LGNOTICE)
    print 'User Services Starting @', strx(util.FmtTimeIntervalEng(blue.os.GetWallclockTimeNow() - t0))
    blue.pyos.taskletTimer.Reset()
    sys.clearmemcontexts()
    blue.pyos.taskletTimer.active = 1
    srvMng.Run(servicesToRun)
    import ttimerutil
    timers = ttimerutil.TaskletSnapshot()
    blue.pyos.taskletTimer.active = 0
    sys.setmemcontextsactive(False)
    sys.clearmemcontexts()
    totalCPUTime = 0
    totalWallClockTime = 0
    for timer in timers:
        if timer.startswith('StartService::ServiceStartRun::') and timer.find('^') == -1:
            serviceName = timer[31:]
            if serviceName in srvMng.startupTimes:
                serviceWallClockTime = srvMng.startupTimes[serviceName]
                totalWallClockTime += serviceWallClockTime
            else:
                serviceWallClockTime = -1
            serviceCPUTime = timers[timer].GetTime()
            totalCPUTime += serviceCPUTime
            log.general.Log('Startup: Service %s took %.4fs wallclock and %.4fs cpu time to startup' % (serviceName, serviceWallClockTime, serviceCPUTime), log.LGNOTICE)

    log.general.Log('Startup: Estimated serial execution time: %.4fs Total CPU time spent %.4fs ' % (totalWallClockTime, totalCPUTime), log.LGNOTICE)
    log.general.Log('Startup:  Marking myself as ready for cluster startup tests in zcluster.nodes', log.LGNOTICE)
    dbzcluster.Nodes_SetStatus(macho.GetNodeID(), -1)
    macho.SetStatusKeyValuePair('clusterStatus', -100)
    macho.SetStatusKeyValuePair('clusterStatusText', 'Startup test phase')
    if macho.IsResurrectedNode():
        loop = True
        while loop:
            loop = False
            try:
                ret = macho.AreTheseServicesRunning(startServices)
                if ret:
                    log.general.Log('Startup:  Waiting for %s' % ret, log.LGERR)
                    print 'Startup:  Waiting for %s' % strx(ret)
                    loop = True
            except:
                log.LogException('Exception while performing distributed startup.  I am%s Polaris' % [' NOT', ''][macho.GetNodeID() == macho.GetNodeFromAddress(const.cluster.SERVICE_POLARIS, 0)])
                sys.exc_clear()
                log.Quit('Failed to determine service running state')

            if loop:
                blue.pyos.synchro.SleepWallclock(3000)

        macho.readyToConnect = True
        try:
            log.general.Log('Startup:  Refreshing Connectivity...', log.LGNOTICE)
            macho.RefreshConnectivity()
        except StandardError:
            log.general.Log('Startup:  Error refreshing connectivity...', log.LGWARN)
            log.LogException(toConsole=1, toLogServer=1, severity=log.LGWARN)
            sys.exc_clear()

        sm.ScatterEvent('OnClusterStarting', macho.GetNodeFromAddress(const.cluster.SERVICE_POLARIS, 0))
    else:
        sent = False
        while not macho.clusterStartupPhase:
            if not sent and macho.GetNodeID() == macho.GetNodeFromAddress(const.cluster.SERVICE_POLARIS, 0):
                print 'Cluster User Service Startup tests beginning @', strx(util.FmtTimeIntervalEng(blue.os.GetWallclockTimeNow() - t0))
                loop = True
                while loop:
                    loop = False
                    r = macho.session.ConnectToAllSolServerServices('machoNet').AreTheseServicesRunning(startServices, uberMachoRaise=True)
                    for isexception, nodeID, ret in r:
                        if ret:
                            log.general.Log('Startup:  Node %d waiting for %s' % (nodeID, ret), log.LGERR)
                            print 'Startup:  Node %d waiting for %s' % (nodeID, strx(ret))
                            loop = True
                            break

                    if loop:
                        blue.pyos.synchro.SleepWallclock(3000)
                    if len(r) < minimumSolCount:
                        print 'Too few sol nodes succeeded in starting to make this run worthwhile'
                        raise UberMachoException('Too few sol nodes succeeded in starting to make this run worthwhile')

                print 'Broadcasting OnClusterStarting'
                log.general.Log('Startup:  Broadcasting OnClusterStarting', log.LGNOTICE)
                macho.ClusterBroadcast('OnClusterStarting', macho.GetNodeID())
                sent = True
                blue.pyos.synchro.SleepWallclock(1000)
            else:
                print 'Waiting for OnClusterStarting...'
                log.general.Log('Startup:  Waiting for OnClusterStarting...', log.LGNOTICE)
                blue.pyos.synchro.SleepWallclock(3000)

    log.general.Log("Startup:  Marking myself as ready to rock'n'roll in zcluster.nodes", log.LGNOTICE)
    dbzcluster.Nodes_SetStatus(macho.GetNodeID(), 0)
    macho.SetStatusKeyValuePair('clusterStatus', -50)
    macho.SetStatusKeyValuePair('clusterStatusText', 'Ready in DB')
    print '--------------------------------------------------------------'
    if macho.GetNodeID() == macho.GetNodeFromAddress(const.cluster.SERVICE_POLARIS, 0):
        print 'Polaris - Cluster ready @', strx(util.FmtTimeIntervalEng(blue.os.GetWallclockTimeNow() - t0))
    else:
        print 'Not Polaris - Server ready @', strx(util.FmtTimeIntervalEng(blue.os.GetWallclockTimeNow() - t0))
    ram = blue.win32.GetProcessMemoryInfo()['PagefileUsage'] / 1024 / 1024
    msg = 'Memory Usage (virtual mem) : %sMb upon startup' % ram
    macho.LogNotice(msg)
    print msg
    sm.ScatterEvent('OnServerStartupCompleted')
    macho.SetStatusKeyValuePair('clusterStatus', 0)
    macho.SetStatusKeyValuePair('clusterStatusText', 'Ready')
    if bluepy.IsRunningStartupTest():
        bluepy.TerminateStartupTest()


def StartServer(servicesToRun, startInline = [], serviceManagerClass = 'ServiceManager'):
    import blue
    t = blue.pyos.CreateTasklet(Startup, (servicesToRun, startInline, serviceManagerClass), {})
    t.context = '^boot::autoexec_server'