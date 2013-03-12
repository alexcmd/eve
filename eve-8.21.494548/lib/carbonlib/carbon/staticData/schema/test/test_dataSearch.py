#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\carbon\staticData\schema\test\test_dataSearch.py
if __name__ == '__main__':
    import sys, os
    carbonLibPath = os.path.abspath(os.path.join(__file__, '../../../../../'))
    sys.path.append(carbonLibPath)
import unittest
from carbon.staticData.schema.dataSearch import Search

class DataSearchTest(unittest.TestCase):

    def testSimpleIntDataSearch(self):
        schema = {'type': 'int'}
        data = 5
        searchResult = Search(data, schema, dataQuery={'root': 5})
        self.assertEquals(data, searchResult)
        searchResult = Search(data, schema, dataQuery={'root': 'this will not be found'})
        self.assertNotEqual(data, searchResult)

    def testSimpleFloatDataSearch(self):
        schema = {'type': 'float'}
        data = 5.0
        searchResult = Search(data, schema, dataQuery={'root': 5.0})
        self.assertEquals(data, searchResult)
        searchResult = Search(data, schema, dataQuery={'root': 'this will not be found'})
        self.assertNotEqual(data, searchResult)

    def testSimpleStringDataSearch(self):
        schema = {'type': 'string'}
        data = 'Hello world'
        searchResult = Search(data, schema, dataQuery={'root': 'Hello world'})
        self.assertEquals(data, searchResult)
        searchResult = Search(data, schema, dataQuery={'root': 'this will not be found'})
        self.assertNotEqual(data, searchResult)

    def testSimpleSchemaSearch(self):
        schema = {'type': 'int'}
        data = 5
        searchResult = Search(data, schema, schemaQuery={'root': {'type': 'int'}})
        self.assertEquals(data, searchResult)
        searchResult = Search(data, schema, schemaQuery={'root': {'type': 'string'}})
        self.assertNotEqual(data, searchResult)

    def testObjectDataSearch(self):
        schema = {'type': 'object',
         'attributes': {'name': {'type': 'string'}}}
        data = {'name': 'Oli'}
        searchResult = Search(data, schema, dataQuery={'root.name': 'Oli'})
        self.assertEqual(1, len(searchResult))
        self.assertEquals(data, searchResult)

    def testObjectSchemaSearch(self):
        schema = {'type': 'object',
         'attributes': {'name': {'type': 'string'}}}
        data = {'name': 'Oli'}
        searchResult = Search(data, schema, schemaQuery={'root.name': {'type': 'string'}})
        self.assertEqual(1, len(searchResult))
        self.assertEquals(data, searchResult)

    def testListDataSearch(self):
        schema = {'type': 'list',
         'itemTypes': {'type': 'string'}}
        data = ['a', 'ble', 'flu']
        searchResult = Search(data, schema, dataQuery={'root\\[.*\\]': 'ble'})
        self.assertEqual(1, len(searchResult))
        self.assertEquals(data[1], searchResult[0])

    def testDictDataSearch(self):
        schema = {'type': 'dict',
         'keyTypes': {'type': 'int'},
         'valueTypes': {'type': 'int'}}
        data = {1: 10,
         2: 20,
         3: 25}
        searchResult = Search(data, schema, dataQuery={'root\\[2\\]': 20})
        self.assertEqual(1, len(searchResult))
        self.assertEquals({2: 20}, searchResult)

    def testComplexObjectDataSearch(self):
        schema = {'type': 'object',
         'attributes': {'name': {'type': 'string'},
                        'object': {'type': 'object',
                                   'attributes': {'nestedName': {'type': 'string'}}}}}
        data = {'name': 'Oli',
         'object': {'nestedName': 'Some nested Name'}}
        searchResult = Search(data, schema, dataQuery={'root\\.object\\.nestedName': 'Some nested Name'})
        self.assertEquals(data, searchResult)

    def testComplexObjectWithListDataSearch(self):
        schema = {'type': 'object',
         'attributes': {'name': {'type': 'string'},
                        'object': {'type': 'object',
                                   'attributes': {'nestedName': {'type': 'string'},
                                                  'somelist': {'type': 'list',
                                                               'itemTypes': {'type': 'string'}}}}}}
        data = {'name': 'Oli',
         'object': {'nestedName': 'Some nested Name',
                    'somelist': ['fle', 'flu', 'fleeee']}}
        searchResult = Search(data, schema, dataQuery={'root\\.object\\.somelist': 'flu'})
        self.assertEquals(data, searchResult)
        searchResult = Search(data, schema, dataQuery={'root\\.object\\.somelist': 'flasdfasdfasdfu'})
        self.assertEqual(0, len(searchResult))

    def testComplexObjectWithDictionaryDataSearch(self):
        schema = {'type': 'object',
         'attributes': {'name': {'type': 'string'},
                        'object': {'type': 'object',
                                   'attributes': {'nestedName': {'type': 'string'},
                                                  'somedict': {'type': 'dict',
                                                               'keyTypes': {'type': 'int'},
                                                               'valueTypes': {'type': 'string'}}}}}}
        data = {'name': 'Oli',
         'object': {'nestedName': 'Some nested Name',
                    'somedict': {10: 'fle',
                                 100: 'flu',
                                 1000: 'fleeee'}}}
        searchResult = Search(data, schema, dataQuery={'root\\.object\\.somedict\\[100\\]': 'flu'})
        self.assertEqual(data, searchResult)
        searchResult = Search(data, schema, dataQuery={'root\\.object\\.somedict\\[100000000\\]': 'flasdfasdfasdfu'})
        self.assertNotEqual(data, searchResult)

    def testWildcardDataSearch(self):
        schema = {'type': 'object',
         'attributes': {'name': {'type': 'string'},
                        'object': {'type': 'object',
                                   'attributes': {'nestedName': {'type': 'string'}}}}}
        data = {'name': 'Oli',
         'object': {'nestedName': 'Some nested Name'}}
        searchResult = Search(data, schema, dataQuery={'root.*': 'Some nested Name'})
        self.assertEquals(data, searchResult)
        searchResult = Search(data, schema, dataQuery={'root.*\\.nestedName': 'Some nested Name'})
        self.assertEquals(data, searchResult)

    def testSimpleFloatIgnoreCaseDataSearch(self):
        schema = {'type': 'float'}
        data = 5.0
        searchResult = Search(data, schema, dataQuery={'root': 5.0}, ignoreCase=True)
        self.assertEquals(data, searchResult)
        searchResult = Search(data, schema, dataQuery={'root': 'this will not be found'}, ignoreCase=True)
        self.assertNotEqual(data, searchResult)

    def testSimpleStringIgnoreCaseDataSearch(self):
        schema = {'type': 'string'}
        data = 'Hello world'
        searchResult = Search(data, schema, dataQuery={'root': 'hello wORLd'}, ignoreCase=True)
        self.assertEquals(data, searchResult)
        searchResult = Search(data, schema, dataQuery={'root': 'this will not be found'}, ignoreCase=True)
        self.assertEqual(0, len(searchResult))

    def testSimpleIntRegularExpressionDataSearch(self):
        schema = {'type': 'int'}
        data = 100
        searchResult = Search(data, schema, dataQuery={'root': '10.*'}, ignoreCase=True, regularExpression=True)
        self.assertNotEqual(0, searchResult)

    def testSimpleStringRegularExpressionDataSearch(self):
        schema = {'type': 'string'}
        data = 'Hello world'
        searchResult = Search(data, schema, dataQuery={'root': 'Hello .*'}, ignoreCase=True, regularExpression=True)
        self.assertEquals(data, searchResult)
        searchResult = Search(data, schema, dataQuery={'root': 'Hallo .*'}, ignoreCase=True, regularExpression=True)
        self.assertEqual(0, len(searchResult))

    def testDictKeyDataSearch(self):
        schema = {'type': 'dict',
         'keyTypes': {'type': 'int'},
         'valueTypes': {'type': 'int'}}
        data = {1: 10,
         2: 20,
         3: 25}
        searchResult = Search(data, schema, dataQuery={'root<.*>': 2})
        self.assertEqual(1, len(searchResult))
        self.assertEquals({2: 20}, searchResult)


if __name__ == '__main__':
    import sys
    suite = unittest.TestLoader().loadTestsFromTestCase(DataSearchTest)
    unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)