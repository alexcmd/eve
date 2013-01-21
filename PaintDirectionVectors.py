# Credits to ferox2552@gmail.com
# Played around with this some time ago, painted direction vectors in the tactical overlay

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
	import spaceObject
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
			blue.pyos.synchro.Sleep(5000)
			bp = sm.GetService('michelle').GetBallpark()
		return bp	
	@safetycheck
	
	@safetycheck
	def LogMessage(Message_Text):
		sm.GetService('gameui').Say(Message_Text)
	
	@safetycheck
	def UpdateDirectionVector():
		bp = GetBallPark()
		myball = bp.GetBall(eve.session.shipid)	
		if not myball:
			LogMessage("ball doesnt exist")
			return
		if bp:
			balls = copy.copy(bp.balls)
			#\LogMessage("Copied Ballpark")
		else:
			LogMessage("Invalid Ballpark")
		
		tacticalSvc = sm.GetService("tactical")
		tacticalSvc.circles.ClearLines()
		color = (0.25,0.25,0.25,1)
		
		i = 0
		while (i < 50):
			blue.pyos.synchro.Sleep(500)
			tacticalSvc.circles.ClearLines()
			for ballid in balls.iterkeys():
				ball = bp.GetBall(ballid)
				slimItem = bp.GetInvItem(ballid)
				if (ball.maxVelocity != 0):
					currentDirection = ball.GetQuaternionAt(blue.os.GetTime())
					d = trinity.TriVector(0,0,1)
					d.TransformQuaternion(currentDirection)
					LogMessage(str(d.x) + " " + str(d.y) + "  " + str(d.z))
					d.x = d.x*10000
					d.y = d.y*10000
					d.z = d.z*10000
					tacticalSvc.circles.AddLine((ball.x-myball.x,ball.y-myball.y,ball.z-myball.z),color,(d.x+ball.x-myball.x,d.y+ball.y-myball.y,d.z+ball.z-myball.z),color)
					tacticalSvc.circles.SubmitChanges()
			i=i+1	
	
	@safetycheck
	def ShowMyPath():
		bp = GetBallPark()
		myball = bp.GetBall(eve.session.shipid)	
		if not myball:
			LogMessage("ball doesnt exist")
			return
		if bp:
			balls = copy.copy(bp.balls)
			#\LogMessage("Copied Ballpark")
		else:
			LogMessage("Invalid Ballpark")
		
		tacticalSvc = sm.GetService("tactical")
		tacticalSvc.circles.ClearLines()
		color = (0.25,0.25,0.25,1)
		
		i = 0
		while (i < 50):
			blue.pyos.synchro.Sleep(500)
			tacticalSvc.circles.ClearLines()
			#slimItem = bp.GetInvItem(ballid)
			if (myball.maxVelocity != 0):
				currentDirection = myball.GetQuaternionAt(blue.os.GetTime())
				d = trinity.TriVector(0,0,1)
				d.TransformQuaternion(currentDirection)
				
				d.x = d.x*100
				d.y = d.y*100
				d.z = d.z*100
				LogMessage(str(d.x) + " " + str(d.y) + "  " + str(d.z))
				#tacticalSvc.circles.AddLine((0,0,0),color,(d.x,0,d.z),color)
				for q in range(100):
					tacticalSvc.circles.AddLine(((0+d.x*q/10)*q,(d.y*q/10*q),(0+d.z*q/10)*q),color,((-d.z+d.x*q/10)*q,(d.y*q/10)*q,(d.x+d.z*q/10)*q),color)
					tacticalSvc.circles.AddLine(((0+d.x*q/10)*q,(d.y*q/10*q),(0+d.z*q/10)*q),color,((d.z+d.x*q/10)*q,(d.y*q/10)*q,(-d.x+d.z*q/10)*q),color)
				tacticalSvc.circles.SubmitChanges()
			i=i+1	
	
	@safetycheck
	def ShowPathOfSelectedShipOnMyShip():
		tacticalSvc = sm.GetService("tactical")
		tacticalSvc.circles.ClearLines()
		color = (0.25,0.25,0.25,1)
		
		i = 0
		while (i < 50):
			blue.pyos.synchro.Sleep(500)
			currItem = eve.LocalSvc("registry").GetWindow("selecteditemview").itemIDs[0]
			bp = GetBallPark()
			currSelectedBall = bp.GetBall(currItem)	
			if not currSelectedBall:
				LogMessage("ball doesnt exist")
				return
			if bp:
				balls = copy.copy(bp.balls)
				LogMessage("Copied Ballpark")
			else:
				LogMessage("Invalid Ballpark")
			
			tacticalSvc.circles.ClearLines()
			currentDirection = currSelectedBall.GetQuaternionAt(blue.os.GetTime())
			d = trinity.TriVector(0,0,1)
			d.TransformQuaternion(currentDirection)
			
			d.x = d.x*1000
			d.y = d.y*1000
			d.z = d.z*1000
			LogMessage(str(d.x) + " " + str(d.y) + "  " + str(d.z))
			tacticalSvc.circles.AddLine((0,0,0),color,(d.x,d.y,d.z),color)
			tacticalSvc.circles.SubmitChanges()
			i=i+1	
			
	@safetycheck
	def ShowAllPaths():
		bp = GetBallPark()
		myball = bp.GetBall(eve.session.shipid)	
		if not myball:
			LogMessage("ball doesnt exist")
			return
		if bp:
			balls = copy.copy(bp.balls)
			LogMessage("Copied Ballpark")
		else:
			LogMessage("Invalid Ballpark")
		
		
		tacticalSvc = sm.GetService("tactical")
		tacticalSvc.circles.ClearLines()
		color = (0.25,0.25,0.25,1)
		
		i = 0
		for qq in range(50):
			blue.pyos.synchro.Sleep(500)
			tacticalSvc.circles.ClearLines()
			for ballid in balls.iterkeys():
				ball = bp.GetBall(ballid)
				slimItem = bp.GetInvItem(ballid) 
				if (ball.maxVelocity != 0):
					currentDirection = ball.GetQuaternionAt(blue.os.GetTime())
					d = trinity.TriVector(0,0,1)
					d.TransformQuaternion(currentDirection)
					#LogMessage(str(d.x) + " " + str(d.y) + "  " + str(d.z))
					d.x = d.x*10000
					d.y = d.y*10000
					d.z = d.z*10000
					LogMessage(str(d.x) + " " + str(d.y) + "  " + str(d.z))
					RelPosBallX = (ball.x-myball.x)
					RelPosBallY = (ball.y-myball.y)
					RelPosBallZ = (ball.z-myball.z)
					
					tacticalSvc.circles.AddLine((RelPosBallX,RelPosBallY,RelPosBallZ),color,(RelPosBallX+d.x,RelPosBallY+d.y,RelPosBallZ+d.z),color)
					tacticalSvc.circles.SubmitChanges()
		i=i+1
			
	@safetycheck			
	def ShowMyPathCompletely():
		bp = GetBallPark()
		myball = bp.GetBall(eve.session.shipid)	
		if not myball:
			LogMessage("ball doesnt exist")
			return
		if bp:
			balls = copy.copy(bp.balls)
			#\LogMessage("Copied Ballpark")
		else:
			LogMessage("Invalid Ballpark")
		
		tacticalSvc = sm.GetService("tactical")
		tacticalSvc.circles.ClearLines()
		color = (0.25,0.25,0.25,1)
		
		i = 0
		oldx = 0
		oldy = 0
		oldz = 0
		tacticalSvc.circles.ClearLines()
		now = blue.os.GetTime()
		while (i < 50):
			
			currentDirection = myball.GetQuaternionAt(blue.os.TimeAddSec(now, i))
			d = trinity.TriVector(0,0,1)
			d.TransformQuaternion(currentDirection)
			
			d.x = d.x*1000
			d.y = d.y*1000
			d.z = d.z*1000
			
			tacticalSvc.circles.AddLine((oldx,oldy,oldz),color,(d.x+oldx,d.y+oldy,d.z+oldz),color)
			oldx = d.x+oldx
			oldy = d.y+oldy
			oldz = d.z+oldz
			
			i=i+1	
		tacticalSvc.circles.SubmitChanges()
	
		
	try:
		uthread.new(ShowAllPaths)

		#foundballID = FindWarpDestinationBall()
		#findRange(foundballID)
		#sm.GetService('FxSequencer').LogError(dir(GetBallPark()))
	except:
		LogMessage("error")


except:
	print "ProbeHelper broken."