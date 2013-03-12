#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/util/animUtils_unittest.py
import unittest
import entities
import geo2
import math
import blue

class TestAnimUtils(unittest.TestCase):

    def setUp(self):
        mock.SetUp(self, globals(), doNotMock=['test',
         'const',
         'entities',
         'geo2',
         'mathCommon',
         'math',
         'blue'])

    def tearDown(self):
        mock.TearDown(self)

    def _GetAnimInfoWithFixedMoveInfo(self, name):
        animInfo = {}
        animInfo[name] = {}
        animInfo[name][const.animation.METADATA_END_OFFSET] = 0
        animInfo[name][const.animation.METADATA_YAW] = 0
        return animInfo

    def testIsFixedMoveAnimation(self):
        animInfo = self._GetAnimInfoWithFixedMoveInfo(const.animation.ATTACKER_NAME)
        self.assertTrue(IsFixedMoveAnimation(animInfo, const.animation.ATTACKER_NAME) == True, 'IsFixedMoveAnimation should have returned True with an animInfo given to it that has an offset.')
        animInfo = {}
        self.assertTrue(IsFixedMoveAnimation(animInfo, const.animation.ATTACKER_NAME) == False, 'IsFixedMoveAnimation should have returned False with an animInfo given to it that has no offsets.')

    def _CreateMovementEntity(self, pos, rot):
        entity = mock.Mock('GameComponent')
        entity.movement = mock.Mock('Movement')
        entity.position = mock.Mock('Position')
        entity.position.position = pos
        entity.position.rotation = rot

        def mockGetComponent(componentName):
            if componentName == 'position':
                return entity.position

        entity.GetComponent = mockGetComponent
        return entity

    def testGetSynchedAnimStartLocation(self):
        sourceEnt = self._CreateMovementEntity(geo2.Vector(0.0, 0.0, 0.0), geo2.Vector(0.0, 0.0, 0.0, 1.0))
        targetEnt = self._CreateMovementEntity(geo2.Vector(0.0, 0.0, 2.0), geo2.Vector(0.0, 0.0, 0.0, 1.0))
        animInfo = {const.animation.METADATA_START_DISTANCE: 1.0}
        newSourcePos, newSourceRot, newTargetPos, newTargetRot = GetSynchedAnimStartLocation(sourceEnt.GetComponent('position').position, sourceEnt.GetComponent('position').rotation, targetEnt.GetComponent('position').position, targetEnt.GetComponent('position').rotation, animInfo)
        self.assertTrue(mathCommon.VectorCloseEnough(newSourcePos, geo2.Vector(0.0, 0.0, 1.0)), "newSourcePos doesn't match expected value")
        self.assertTrue(mathCommon.VectorCloseEnough(newSourceRot, geo2.Vector(0.0, 0.0, 0.0, 1.0)), "newSourceRot doesn't match expected value")
        self.assertTrue(mathCommon.VectorCloseEnough(newTargetPos, geo2.Vector(0.0, 0.0, 2.0)), "newTargetPos doesn't match expected value")
        self.assertTrue(mathCommon.VectorCloseEnough(newTargetRot, geo2.Vector(0.0, 1.0, 0.0, 0.0)), "newTargetRot doesn't match expected value")

    def testTransformAccumulatedAnimFromEnt(self):
        ent = self._CreateMovementEntity(geo2.Vector(0.0, 0.0, 0.0), geo2.Vector(0.0, 0.0, 0.0, 1.0))
        animInfo = {}
        animInfo[const.animation.ATTACKER_NAME] = {}
        animInfo[const.animation.ATTACKER_NAME][const.animation.METADATA_END_OFFSET] = (1.0, 2.0)
        animInfo[const.animation.ATTACKER_NAME][const.animation.METADATA_YAW] = 90.0
        newPos, newRot = TransformAccumulatedAnimFromEnt(ent, animInfo, const.animation.ATTACKER_NAME)
        expectedNewPos = geo2.Vector(0.01, 0.0, 0.02)
        self.assertTrue(mathCommon.VectorCloseEnough(newPos, expectedNewPos), 'newPos value of ' + str(newPos) + " doesn't match expected value of " + str(expectedNewPos))
        expectedNewRot = geo2.Vector(0.0, 0.707107, -0.0, 0.707107)
        self.assertTrue(mathCommon.VectorCloseEnough(newRot, expectedNewRot), 'newRot value of ' + str(newRot) + " doesn't match expected value of " + str(expectedNewRot))