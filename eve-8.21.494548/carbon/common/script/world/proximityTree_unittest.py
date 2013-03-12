#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/world/proximityTree_unittest.py
import unittest
import GameWorld

class TestProximityTree(unittest.TestCase):

    def setUp(self):
        initData = {'Gravity': (0.0, -9.80665, 0.0),
         'WorldSize': 10000.0}
        self.instanceID = 9876543210L
        self.gw = GameWorld.GameWorld()
        self.gw.InitWorld('TestCase_GameWorld', initData, False)
        self.gw.instanceID = self.instanceID
        GameWorld.Manager.AddGameWorld(self.gw)
        self.gw.grid = GameWorld.ProximityTree()
        self.gw.grid.Initialize(2000, 0.35, 32)
        boundingVolume = GameWorld.BoundingVolumeComponent()
        boundingVolume.minExtends = (-1e-05, -1e-05, -1e-05)
        boundingVolume.maxExtends = (1e-05, 1e-05, 1e-05)
        self.me = GameWorld.PositionComponent()
        self.me.position = (0.0, 0.0, 0.0)
        self.l1 = GameWorld.PositionComponent()
        self.l1.position = (10.0, 10.0, 10.0)
        self.gw.grid.AddFromComponents(1, self.me, boundingVolume)
        self.gw.grid.AddFromComponents(666, self.l1, boundingVolume)

    def tearDown(self):
        self.gw.grid.Delete(1)
        self.gw.grid.Delete(666)
        GameWorld.Manager.DeleteGameWorld(self.instanceID)
        del self.me
        del self.l1

    def testSelfInResults(self):
        res = []
        self.gw.grid.GetEntitiesAtPosition(self.me.position, 1.0, res, 100)
        found = False
        atDistance = -1
        for e, d in res:
            if e == 1:
                found = True
                atDistance = d
                break

        self.assertTrue(found)
        self.assertTrue(atDistance < 1e-05, 'atDistance should have been 0.0, but it was %f' % atDistance)

    def testCanFindEntityInRange(self):
        res = []
        self.gw.grid.GetEntitiesAtPosition(self.me.position, 20.0, res, 100)
        found = False
        atDistance = -1
        for e, d in res:
            if e == 666:
                found = True
                atDistance = d
                break

        self.assertTrue(found)
        self.assertTrue(atDistance == 300.0, 'atDistance should have been 300.0, but it was %.2f' % atDistance)

    def testDoesNotFindEntitiesOutOfRange(self):
        res = []
        self.gw.grid.GetEntitiesAtPosition(self.me.position, 17.3, res, 100)
        found = False
        for e, d in res:
            if e == 666:
                found = True
                atDistance = d
                break

        self.assertFalse(found)
        self.assertTrue(len(res) == 1)