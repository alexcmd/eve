# Credits to ferox2552@gmail.com
# Prints warp destination of every warping ball in a file, needs some proper visualizing of it..

try:
	from log import LogError
	import uix
	import uiutil
	import mathUtil
	import xtriui
	import uthread
	import form
	import blue
	import util
	import trinity
	import service
	import destiny
	import listentry
	import base
	import math
	import sys
	import geo2
	import maputils
	import copy
	from math import pi, cos, sin, sqrt, floor
	from foo import Vector3
	from mapcommon import SYSTEMMAP_SCALE
	from traceback import format_exception
	import functools
	import uiconst
	import uicls
	import listentry
	import state
	import localization
	import localizationUtil
	
	def safetycheck(func):
		def wrapper(*args, **kwargs):
			try:
				return func(*args, **kwargs)
			except:
				try:
					print "exception in " + func.__name__
					(exc, e, tb,) = sys.exc_info()
					result2 = (''.join(format_exception(exc, e, tb)) + '\n').replace('\n', '<br>')
					#sm.GetService('gameui').MessageBox(result2, "ProbeHelper Exception")
					sm.GetService('FxSequencer').LogError(result2)
				except:
					print "exception in safetycheck"
		return wrapper
	@safetycheck
	def WarpToStuff(ItemID):
		sm.services["michelle"].GetRemotePark().CmdWarpToStuff("item", ItemID, 50000)	
		
	@safetycheck
	def GetBallPark():
		bp = sm.GetService('michelle').GetBallpark()
		while(not bp):
			blue.pyos.synchro.Sleep(500)
			bp = sm.GetService('michelle').GetBallpark()
		return bp	
	@safetycheck
	def LogMessage(Message_Text):
		sm.GetService('gameui').Say(Message_Text)
	
	@safetycheck
	def DistanceMyGotoBall(ball):
		bp = sm.StartService('michelle').GetBallpark()
		myball = bp.GetBall(eve.session.shipid)		
		distance = sqrt((myball.gotoX-ball.gotoX)*(myball.gotoX-ball.gotoX)+(myball.gotoY-ball.gotoY)*(myball.gotoY-ball.gotoY)+(myball.gotoZ-ball.gotoZ)*(myball.gotoZ-ball.gotoZ))
		return distance
	
	@safetycheck
	def FindClosestMoon(playerballID):
		bp = sm.StartService('michelle').GetBallpark()
		dist = 1e+100
		closestMoonID = None
		for (ballID, slimItem,) in bp.slimItems.iteritems():
			if (slimItem.groupID == const.groupPlanet) or (slimItem.groupID == const.groupMoon) or (slimItem.groupID == const.groupStation) or (slimItem.groupID == const.groupStargate):
				test = bp.DistanceBetween(playerballID, ballID)
				if test < dist:
					dist = test
					closestMoonID = ballID
		slimItem2 = bp.GetInvItem(closestMoonID)
		return uix.GetSlimItemName(slimItem2)

	@safetycheck
	def FindClosestDestinationCelestial(playerballID):
		bp = sm.StartService('michelle').GetBallpark()
		playerball = bp.GetBall(playerballID)
		dist2 = 1e+100
		closestcelestialID = None
		for (ballID, slimItem,) in bp.slimItems.iteritems():
			if (slimItem.groupID == const.groupPlanet) or (slimItem.groupID == const.groupMoon) or (slimItem.groupID == const.groupStation) or (slimItem.groupID == const.groupStargate):
				ballcelestial = bp.GetBall(ballID)
				test = sqrt((playerball.gotoX-ballcelestial.x)*(playerball.gotoX-ballcelestial.x)+(playerball.gotoY-ballcelestial.y)*(playerball.gotoY-ballcelestial.y)+(playerball.gotoZ-ballcelestial.z)*(playerball.gotoZ-ballcelestial.z))
				if test < dist2:
					dist2 = test
					closestcelestialID = ballID
		slimItem3 = bp.GetInvItem(closestcelestialID)
		return uix.GetSlimItemName(slimItem3)

	@safetycheck
	def FindWarpDestinationBall():
		bp = GetBallPark()
		if bp:
			balls = copy.copy(bp.balls)
			LogMessage("Copied Ballpark")
		else:
			LogMessage("Invalid Ballpark")
		FILE = open("D://EvE Programming/ineve/dump.txt","wt")
		#ballself2 = bp.GetBall(eve.session.shipid)
		#slimitemself2 = bp.GetInvItem(eve.session.shipid)
		#FILE.write(str(uix.GetSlimItemName(slimitemself2)) + "	" + str(FindClosestMoon(eve.session.shipid)) + str(ballself2.surfaceDist) + "	" + str(ballself2.gotoX) + "\n")
		foundBallID = None
		for ballID in balls.iterkeys():
			ball = bp.GetBall(ballID)
			slimItem = bp.GetInvItem(ballID)
			if (slimItem and ball.__guid__ == "spaceObject.Ship" and ball.mode == destiny.DSTBALL_WARP):
				LogMessage(str(ballID) + "	" + str(ball.__guid__) + "	" + str(ball.surfaceDist) + str(uix.GetSlimItemName(slimItem)))  
				#FILE.write(str(FindClosestDestinationCelestial(ballID)) + "	" + str(FindClosestDestinationCelestial(eve.session.shipid)) + str(uix.GetSlimItemName(slimItem)) + "	" + str(FindClosestMoon(ballID)) + "	" + str(ball.surfaceDist) + "\n")
				FILE.write(str(FindClosestDestinationCelestial(ballID)) + "          " + str(uix.GetSlimItemName(slimItem)) + "              " + str(DistanceMyGotoBall(ball)) + "\n")
		FILE.write("Done. \n")
		FILE.close()
		return foundBallID
	
	@safetycheck
	def findRange(foundballID):
		bp = GetBallPark()
		if bp:
			balls = copy.copy(bp.balls)
			LogMessage("Copied Ballpark")
		else:
			LogMessage("Invalid Ballpark")
				
		foundball = bp.GetBall(foundballID)
		if (DistanceMyGotoBall(foundball) < 150000):
			uthread.new(WarpToStuff(foundballID))
		else:
			uthread.new(WarpToStuff(foundballID))
			uthread.new(uicore.cmd.CmdStopShip)

	try:
		
		#foundballID = FindWarpDestinationBall()
		#findRange(foundballID)
		sm.GetService('FxSequencer').LogError(testfunc())
	except:
		LogError("error")


except:
	print "ProbeHelper broken."
