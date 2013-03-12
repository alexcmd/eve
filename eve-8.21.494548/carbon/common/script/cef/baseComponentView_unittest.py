#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/cef/baseComponentView_unittest.py
import unittest
MOCK_TYPE_1 = -9999
MOCK_TYPE_2 = -9998
MOCK_TYPE_3 = -9997
UNUSED_COMPONENT_ID_1 = -999
UNUSED_COMPONENT_ID_2 = -998

def MakeMockComponentViews():

    class MockComponentView1(BaseComponentView):
        __COMPONENT_ID__ = UNUSED_COMPONENT_ID_1
        __COMPONENT_DISPLAY_NAME__ = 'Unit Test Component'
        __COMPONENT_CODE_NAME__ = None
        MOCK_INPUT_1 = 'mockInput1_1'
        MOCK_INPUT_2 = 'mockInput1_2'

        @classmethod
        def SetupInputs(cls):
            cls.RegisterComponent(cls)
            cls._AddInput(cls.MOCK_INPUT_1, 0.0, cls.RECIPE, MOCK_TYPE_1)
            cls._AddInput(cls.MOCK_INPUT_2, 0.0, cls.RECIPE, MOCK_TYPE_2)

    class MockComponentView2(BaseComponentView):
        __COMPONENT_ID__ = UNUSED_COMPONENT_ID_2
        __COMPONENT_DISPLAY_NAME__ = 'Unit Test Component'
        __COMPONENT_CODE_NAME__ = None
        MOCK_INPUT_1 = 'mockInput2_1'
        MOCK_INPUT_2 = 'mockInput2_2'

        @classmethod
        def SetupInputs(cls):
            cls.RegisterComponent(cls)
            cls._AddInput(cls.MOCK_INPUT_1, 0.0, cls.RECIPE, MOCK_TYPE_2)
            cls._AddInput(cls.MOCK_INPUT_2, 0.0, cls.RECIPE, MOCK_TYPE_3)

    MockComponentView1.SetupInputs()
    MockComponentView2.SetupInputs()
    return (MockComponentView1, MockComponentView2)


class CefUtilTests(unittest.TestCase):

    def setUp(self):
        mock.SetUp(self, globals(), doNotMock=['collections'])
        self.MockComponentView1Type, self.MockComponentView2Type = MakeMockComponentViews()

    def tearDown(self):
        mock.TearDown(self)
        del BaseComponentView.__COMPONENT_CLASS_BY_ID__[UNUSED_COMPONENT_ID_1]
        del BaseComponentView.__COMPONENT_CLASS_BY_ID__[UNUSED_COMPONENT_ID_2]

    def testGetComponentViewsWithDatatype(self):
        searchResults = BaseComponentView.GetComponentsWithDatatype(MOCK_TYPE_1)
        self.assertTrue(len(searchResults) == 1)
        searchResults = BaseComponentView.GetComponentsWithDatatype(MOCK_TYPE_2)
        self.assertTrue(len(searchResults) == 2)
        searchResults = BaseComponentView.GetComponentsWithDatatype(MOCK_TYPE_3)
        self.assertTrue(len(searchResults) == 1)