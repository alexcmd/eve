#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/localization/localizationParser_unittest.py
import unittest

class TokenizerUnitTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testDateTime(self):
        result = _Tokenize('{[datetime]foo}')
        expectedResult = {'{[datetime]foo}': {'conditionalValues': [],
                             'variableType': 6,
                             'propertyName': None,
                             'args': 0,
                             'kwargs': {},
                             'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, time=long}')
        expectedResult = {'{[datetime]foo, time=long}': {'conditionalValues': [],
                                        'variableType': 6,
                                        'propertyName': None,
                                        'args': 0,
                                        'kwargs': {'format': u'%H:%M:%S'},
                                        'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, time=none}')
        expectedResult = {'{[datetime]foo, time=none}': {'conditionalValues': [],
                                        'variableType': 6,
                                        'propertyName': None,
                                        'args': 0,
                                        'kwargs': {},
                                        'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, date=short}')
        expectedResult = {'{[datetime]foo, date=short}': {'conditionalValues': [],
                                         'variableType': 6,
                                         'propertyName': None,
                                         'args': 0,
                                         'kwargs': {'format': u'%Y.%m.%d'},
                                         'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, date=none}')
        expectedResult = {'{[datetime]foo, date=none}': {'conditionalValues': [],
                                        'variableType': 6,
                                        'propertyName': None,
                                        'args': 0,
                                        'kwargs': {},
                                        'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, date=none, time=none}')
        expectedResult = {'{[datetime]foo, date=none, time=none}': {'conditionalValues': [],
                                                   'variableType': 6,
                                                   'propertyName': None,
                                                   'args': 0,
                                                   'kwargs': {},
                                                   'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, time=short}')
        expectedResult = {'{[datetime]foo, time=short}': {'conditionalValues': [],
                                         'variableType': 6,
                                         'propertyName': None,
                                         'args': 0,
                                         'kwargs': {'format': u'%H:%M'},
                                         'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, time=medium}')
        expectedResult = {'{[datetime]foo, time=medium}': {'conditionalValues': [],
                                          'variableType': 6,
                                          'propertyName': None,
                                          'args': 0,
                                          'kwargs': {'format': u'%H:%M:%S'},
                                          'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, time=long}')
        expectedResult = {'{[datetime]foo, time=long}': {'conditionalValues': [],
                                        'variableType': 6,
                                        'propertyName': None,
                                        'args': 0,
                                        'kwargs': {'format': u'%H:%M:%S'},
                                        'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, time=full}')
        expectedResult = {'{[datetime]foo, time=full}': {'conditionalValues': [],
                                        'variableType': 6,
                                        'propertyName': None,
                                        'args': 0,
                                        'kwargs': {'format': u'%H:%M:%S'},
                                        'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, date=short}')
        expectedResult = {'{[datetime]foo, date=short}': {'conditionalValues': [],
                                         'variableType': 6,
                                         'propertyName': None,
                                         'args': 0,
                                         'kwargs': {'format': u'%Y.%m.%d'},
                                         'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, date=medium}')
        expectedResult = {'{[datetime]foo, date=medium}': {'conditionalValues': [],
                                          'variableType': 6,
                                          'propertyName': None,
                                          'args': 0,
                                          'kwargs': {'format': u'%b %d, %Y'},
                                          'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, date=long}')
        expectedResult = {'{[datetime]foo, date=long}': {'conditionalValues': [],
                                        'variableType': 6,
                                        'propertyName': None,
                                        'args': 0,
                                        'kwargs': {'format': u'%B %d, %Y'},
                                        'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, date=full}')
        expectedResult = {'{[datetime]foo, date=full}': {'conditionalValues': [],
                                        'variableType': 6,
                                        'propertyName': None,
                                        'args': 0,
                                        'kwargs': {'format': u'%#x'},
                                        'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, date=full, time=full}')
        expectedResult = {'{[datetime]foo, date=full, time=full}': {'conditionalValues': [],
                                                   'variableType': 6,
                                                   'propertyName': None,
                                                   'args': 0,
                                                   'kwargs': {'format': u'%#c'},
                                                   'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, date=full, time=short}')
        expectedResult = {'{[datetime]foo, date=full, time=short}': {'conditionalValues': [],
                                                    'variableType': 6,
                                                    'propertyName': None,
                                                    'args': 0,
                                                    'kwargs': {'format': u'%#x %H:%M'},
                                                    'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))
        result = _Tokenize('{[datetime]foo, date=short, time=short}')
        expectedResult = {'{[datetime]foo, date=short, time=short}': {'conditionalValues': [],
                                                     'variableType': 6,
                                                     'propertyName': None,
                                                     'args': 0,
                                                     'kwargs': {'format': u'%Y.%m.%d %H:%M'},
                                                     'variableName': 'foo'}}
        self.assertTrue(result == expectedResult, 'Result did not match input: %s != %s' % (result, expectedResult))