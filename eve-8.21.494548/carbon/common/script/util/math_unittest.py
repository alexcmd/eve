#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/util/math_unittest.py
import unittest
import blue

class MathTestCollection(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testCalcScaledValueOverInterval(self):
        args = {'startVal': 0,
         'targetVal': 20,
         'intervalLength': 0,
         'intervalRemaining': 10}
        result = CalcScaledValueOverInterval(**args)
        self.assertTrue(result == args['targetVal'], 'Edge case test: intervalLength == 0; ' + str(args))
        args = {'startVal': 0,
         'targetVal': 20,
         'intervalLength': 10,
         'intervalRemaining': 10}
        result = CalcScaledValueOverInterval(**args)
        self.assertTrue(result == args['startVal'], 'Edge case test: intervalLength == intervalRemaining; ' + str(args))
        args = {'startVal': 0,
         'targetVal': 20,
         'intervalLength': 10,
         'intervalRemaining': 0}
        result = CalcScaledValueOverInterval(**args)
        self.assertTrue(result == args['targetVal'], 'Edge case test: intervalRemaining == 0; ' + str(args))
        args = {'startVal': 10,
         'targetVal': 20,
         'intervalLength': 10,
         'intervalRemaining': 5}
        result = CalcScaledValueOverInterval(**args)
        self.assertTrue(result == 15, 'Normal case: intervalRemaining > 0 and < intervalLength; ' + str(args))
        args = {'startVal': 10,
         'targetVal': 20,
         'intervalLength': 10,
         'intervalRemaining': 5,
         'minFactor': 0.6}
        result = CalcScaledValueOverInterval(**args)
        self.assertTrue(result == 16, 'Test that the factor minimum is respected;(%s) ' % result + str(args))
        args = {'startVal': 0,
         'targetVal': 20,
         'intervalLength': 10,
         'intervalRemaining': 5,
         'maxFactor': 0.3}
        result = CalcScaledValueOverInterval(**args)
        self.assertTrue(result == 6.0, 'Test that the factor maximum is respected; ' + str(args))

    def testCalcLinearIntpValue(self):
        START_SPEED = 0
        END_SPEED = 10
        START_TIME = 0
        END_TIME = 10
        TIME_TAKEN = END_TIME - START_TIME
        MID_TIME = 0.5 * TIME_TAKEN
        ret = CalcLinearIntpValue(START_SPEED, END_SPEED, START_TIME, START_TIME, TIME_TAKEN)
        self.assertTrue(ret == START_SPEED, 'The calculated speed (%s) was expected to be the starting speed (%s)' % (ret, START_SPEED))
        ret = CalcLinearIntpValue(START_SPEED, END_SPEED, START_TIME, MID_TIME, TIME_TAKEN)
        self.assertTrue(START_SPEED < ret < END_SPEED, 'The calculated speed (%s) was expected to be between the start speed (%s) and the end speed (%s)' % (ret, START_SPEED, END_SPEED))
        ret = CalcLinearIntpValue(START_SPEED, END_SPEED, START_TIME, END_TIME, TIME_TAKEN)
        self.assertTrue(ret == END_SPEED, 'The calculated speed (%s) was expected to be the final speed (%s)' % (ret, END_SPEED))
        ret = CalcLinearIntpValue(START_SPEED, END_SPEED, START_TIME, TIME_TAKEN * 2, TIME_TAKEN)
        self.assertTrue(ret == END_SPEED, 'The calculated speed after the end time (%s) was expected to be the final speed (%s)' % (ret, END_SPEED))
        ret = CalcLinearIntpValue(START_SPEED, END_SPEED, START_TIME, END_TIME, 0)
        self.assertTrue(ret == END_SPEED, 'The calculated speed (%s) when there is no time taken for a movement is bad' % ret)
        ret = CalcLinearIntpValue(START_SPEED, END_SPEED, START_TIME, END_TIME, -1)
        self.assertTrue(ret == END_SPEED, 'The calculated speed (%s) when there is negative time taken for a movement is bad' % ret)
        ret = CalcLinearIntpValue(START_SPEED, END_SPEED, START_TIME, START_TIME - 1, 0)
        self.assertTrue(ret == START_SPEED, 'The calculated speed (%s) when the current time is strangely earlier than the start time is bad' % ret)

    def testGetLesserAngleBetweenYaws(self):
        self.assertTrue(GetLesserAngleBetweenYaws(1, 3) == CalculateShortestRotation(2), "Somehow we've managed to decouple CalculateShortestRotation from GetLesserAngleBetweenYaws")
        self.assertTrue(GetLesserAngleBetweenYaws(3, 1) == CalculateShortestRotation(-2), "Somehow we've managed to decouple CalculateShortestRotation from GetLesserAngleBetweenYaws")

    def testCalculateShortestRotation(self):
        self.assertTrue(CalculateShortestRotation(math.pi - 1) == math.pi - 1, 'Changes angle even though angle is between 0 and pi')
        self.assertTrue(CalculateShortestRotation(-math.pi + 1) == -math.pi + 1, 'Changes angle even though angle is between 0 and -pi')
        self.assertTrue(CalculateShortestRotation(math.pi + 1) == -math.pi + 1, 'Angle is changed incorrectly when between pi and 2pi')
        self.assertTrue(CalculateShortestRotation(-math.pi - 1) == math.pi - 1, 'Angle is changed incorrectly when between -pi and -2pi')
        self.assertTrue(CalculateShortestRotation(1 + 2 * math.pi) == CalculateShortestRotation(1), 'Angle + 2pi is not equal to angle')
        self.assertTrue(CalculateShortestRotation(1 - 2 * math.pi) == CalculateShortestRotation(1), 'Angle - 2pi is not equal to angle')

    def testFloatCloseEnough(self):
        self.assertTrue(FloatCloseEnough(1.0 + const.FLOAT_TOLERANCE / 2.0, 1.0))
        self.assertTrue(not FloatCloseEnough(1.0 + const.FLOAT_TOLERANCE * 2.0, 1.0))
        self.assertTrue(FloatCloseEnough(1.0, 1.0 + const.FLOAT_TOLERANCE / 2.0))
        self.assertTrue(not FloatCloseEnough(1.0, 1.0 + const.FLOAT_TOLERANCE * 2.0))

    def testBoundedRotateQuatByYaw(self):
        testQuaternion = geo2.Vector(0, 0, 0, 1.0)
        testString = 'angle to rotate is larger than the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, 1)
        testQuatOne = BoundedRotateQuatByYaw(testQuaternion, 2, 1)
        testQuatTwo = BoundedRotateQuatByYaw(testQuaternion, 2, -1)
        self.assertTrue(testQuatOne == testQuatControl, testString + ':' + str(testQuatOne) + ',' + str(testQuatControl))
        self.assertTrue(testQuatTwo == testQuatControl, testString + ':' + str(testQuatTwo) + ',' + str(testQuatControl))
        testString = 'angle to rotate is smaller than the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, 1)
        testQuatOne = BoundedRotateQuatByYaw(testQuaternion, 1, 3)
        testQuatTwo = BoundedRotateQuatByYaw(testQuaternion, 1, -3)
        self.assertTrue(testQuatOne == testQuatControl, testString + ':' + str(testQuatOne) + ',' + str(testQuatControl))
        self.assertTrue(testQuatTwo == testQuatControl, testString + ':' + str(testQuatTwo) + ',' + str(testQuatControl))
        testString = 'angle to rotate is equal to the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, 2.8)
        testQuatOne = BoundedRotateQuatByYaw(testQuaternion, 2.8, 2.8)
        testQuatTwo = BoundedRotateQuatByYaw(testQuaternion, 2.8, -2.8)
        self.assertTrue(testQuatOne == testQuatControl, testString + ':' + str(testQuatOne) + ',' + str(testQuatControl))
        self.assertTrue(testQuatTwo == testQuatControl, testString + ':' + str(testQuatTwo) + ',' + str(testQuatControl))
        testString = 'angle to rotate is larger than the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, 1)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, 2 + 2 * math.pi, 1)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is smaller than the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, 1)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, 1 + 2 * math.pi, 3)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is equal to the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, 2.8)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, 2.8 + 2 * math.pi, 2.8)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is larger than the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, -1)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, -2, 1)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is smaller than the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, -1)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, -1, 3)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is equal to the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, -2.8)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, -2.8, 2.8)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is larger than the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, -1)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, -2 - 2 * math.pi, 1)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is smaller than the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, -1)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, -1 - 2 * math.pi, 3)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is equal to the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, -2.8)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, -2.8 - 2 * math.pi, 2.8)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is larger than the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, -1)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, 2 * math.pi - 2, 1)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is smaller than the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, -1)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, 2 * math.pi - 1, 3)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is equal to the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, -2.8)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, 2 * math.pi - 2.8, 2.8)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is larger than the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, 1)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, -2 * math.pi + 2, 1)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is smaller than the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, 1)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, -2 * math.pi + 1, 3)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))
        testString = 'angle to rotate is equal to the bounding angle'
        testQuatControl = RotateQuatByYaw(testQuaternion, 2.8)
        testQuat = BoundedRotateQuatByYaw(testQuaternion, -2 * math.pi + 2.8, 2.8)
        self.assertTrue(testQuat == testQuatControl, testString + ':' + str(testQuat) + ',' + str(testQuatControl))

    def testLineIntersectVerticalPlaneWithTwoPoints(self):
        lineV1 = geo2.Vector(-1, 1, 1)
        lineV2 = geo2.Vector(1, 3, 1)
        planeV1 = geo2.Vector(0, 1, 29)
        planeV2 = geo2.Vector(0, 13, -9)
        intersectionPoint = LineIntersectVerticalPlaneWithTwoPoints(lineV1, lineV2, planeV1, planeV2)
        self.assertTrue(VectorCloseEnough(intersectionPoint, geo2.Vector(0, 2, 1)), 'LineIntersectVerticalPlaneWithTwoPoints did not return the correct intersection point')

    def testGetPitchAngleFromDirectionVector(self):
        testVector = geo2.Vector(5, 3, 4)
        pitch = GetPitchAngleFromDirectionVector(testVector)
        self.assertTrue(FloatCloseEnough(pitch, 0.4381), 'GetPitchAngleFromDirectionVector did not return the expected result.')


class GetDeltaAngleToFaceTargetTests(unittest.TestCase):

    def setUp(self):
        self.pos = geo2.Vector(0.0, 0.0, 0.0)
        self.rot = geo2.Vector(0.0, 0.0, 0.0, 1.0)

    def tearDown(self):
        pass

    def AnglesFairlyClose(self, angle1, angle2):
        diff = angle1 - angle2
        diff /= 2.0 * math.pi
        diff -= int(diff)
        return 0.01 - math.fabs(diff) > 0

    def testGreater(self):
        theta = 0.0
        while theta < 1000.0 * math.pi:
            oldTheta = theta
            theta += 1.0
            thetaVector = CreateDirectionVectorFromYawAngle(theta)
            getFace = GetDeltaAngleToFaceTarget(self.pos, self.rot, thetaVector)
            self.assertTrue(self.AnglesFairlyClose(theta - oldTheta, getFace), 'The small angle returned did not match the angle given.' + str(theta - oldTheta) + str(getFace))
            self.rot = geo2.QuaternionRotationSetYawPitchRoll(theta, 0.0, 0.0)

    def testLesser(self):
        theta = 0.0
        while theta > -1000.0 * math.pi:
            oldTheta = theta
            theta -= 1.0
            thetaVector = CreateDirectionVectorFromYawAngle(theta)
            getFace = GetDeltaAngleToFaceTarget(self.pos, self.rot, thetaVector)
            self.assertTrue(self.AnglesFairlyClose(theta - oldTheta, getFace), 'The small angle returned did not match the angle given.' + str(theta - oldTheta) + str(getFace))
            self.rot = geo2.QuaternionRotationSetYawPitchRoll(theta, 0.0, 0.0)


class YawAngleDirectionVectorTests(unittest.TestCase):

    def SameAngles(self, angle1, angle2):
        diff = angle1 - angle2
        diff /= 2.0 * math.pi
        diff -= int(diff)
        return FloatCloseEnough(diff, 0.0)

    def CheckDirectionYawEquivalence(self, direction, yaw):
        testVector = CreateDirectionVectorFromYawAngle(yaw)
        testYaw = GetYawAngleFromDirectionVector(direction)
        cosTheta = geo2.Vec3Dot(direction, testVector) / geo2.Vec3Length(direction)
        self.assertTrue(FloatCloseEnough(cosTheta, 1.0), 'The two vectors should be co-linear ' + str(direction) + ' ' + str(testVector))
        self.assertTrue(self.SameAngles(yaw, testYaw), 'The yaw should be equivalent to the testYaw ' + str(yaw / math.pi) + ' ' + str(testYaw / math.pi))

    def testSouth(self):
        direction = (0, 0, -1)
        yaw = math.pi
        self.CheckDirectionYawEquivalence(direction, yaw)

    def testSouthWest(self):
        direction = (-1, 0, -1)
        yaw = 5.0 * math.pi / 4.0
        self.CheckDirectionYawEquivalence(direction, yaw)

    def testWest(self):
        direction = (-1, 0, 0)
        yaw = 3.0 * math.pi / 2.0
        self.CheckDirectionYawEquivalence(direction, yaw)

    def testNorthWest(self):
        direction = (-1, 0, 1)
        yaw = 7.0 * math.pi / 4.0
        self.CheckDirectionYawEquivalence(direction, yaw)

    def testNorth(self):
        direction = (0, 0, 1)
        yaw = 0.0
        self.CheckDirectionYawEquivalence(direction, yaw)

    def testNorthEast(self):
        direction = (1, 0, 1)
        yaw = math.pi / 4.0
        self.CheckDirectionYawEquivalence(direction, yaw)

    def testEast(self):
        direction = (1, 0, 0)
        yaw = math.pi / 2.0
        self.CheckDirectionYawEquivalence(direction, yaw)

    def testSouthEast(self):
        direction = (1, 0, -1)
        yaw = 3.0 * math.pi / 4.0
        self.CheckDirectionYawEquivalence(direction, yaw)