#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\carbon\staticData\schema\test\test_dataWalker.py
if __name__ == '__main__':
    import sys, os
    carbonLibPath = os.path.abspath(os.path.join(__file__, '../../../../../'))
    sys.path.append(carbonLibPath)
import unittest
import carbon.staticData.schema.dataWalker as dataWalker

class DataWalkerCallback:

    def __init__(self):
        self.dataCheckList = []
        self.schemaCheckList = []
        self.pathList = []
        self.rootObj = None

    def continueWalkingFunction(self, rootObj, obj, schemaNode, path):
        if schemaNode not in self.schemaCheckList:
            self.schemaCheckList.append(schemaNode)
        self.dataCheckList.append(obj)
        self.pathList.append(path)
        self.rootObj = rootObj
        return True


class DataWalkerTest(unittest.TestCase):

    def testSimpleDataWalk(self):
        dataWalkerCallback = DataWalkerCallback()
        schema = {'type': 'int'}
        data = 5
        dataWalker.Walk(data, schema, continueWalkingFunction=dataWalkerCallback.continueWalkingFunction)
        self.assertEquals(1, len(dataWalkerCallback.dataCheckList))
        self.assertEquals(1, len(dataWalkerCallback.schemaCheckList))
        self.assertEquals(1, len(dataWalkerCallback.pathList))
        self.assertEquals(data, dataWalkerCallback.dataCheckList[0])
        self.assertEquals(schema, dataWalkerCallback.schemaCheckList[0])
        self.assertEquals('root', dataWalkerCallback.pathList[0])
        self.assertEquals(data, dataWalkerCallback.rootObj)

    def testSimpleListDataWalk(self):
        dataWalkerCallback = DataWalkerCallback()
        schema = {'type': 'list',
         'itemTypes': {'type': 'string'}}
        data = ['a', 'ble', 'flu']
        dataWalker.Walk(data, schema, continueWalkingFunction=dataWalkerCallback.continueWalkingFunction)
        expectedSchemaCheckedList = [schema, {'type': 'string'}]
        expectedData = [data,
         data[0],
         data[1],
         data[2]]
        self.assertEquals(4, len(dataWalkerCallback.dataCheckList))
        self.assertEquals(2, len(dataWalkerCallback.schemaCheckList))
        self.assertEquals(4, len(dataWalkerCallback.pathList))
        for index, item in enumerate(expectedData):
            self.assertEquals(item, dataWalkerCallback.dataCheckList[index])

        self.assertEquals(expectedSchemaCheckedList, dataWalkerCallback.schemaCheckList)
        self.assertEquals(['root',
         'root[0]',
         'root[1]',
         'root[2]'], dataWalkerCallback.pathList)
        self.assertEquals(data, dataWalkerCallback.rootObj)

    def testSimpleObjectDataWalk(self):
        dataWalkerCallback = DataWalkerCallback()
        schema = {'type': 'object',
         'attributes': {'a': {'type': 'int'},
                        'b': {'type': 'string'}}}
        data = {'a': 19,
         'b': 'Whoop whoop'}
        dataWalker.Walk(data, schema, continueWalkingFunction=dataWalkerCallback.continueWalkingFunction)
        expectedSchemaCheckedList = [schema, schema['attributes']['a'], schema['attributes']['b']]
        expectedData = [data, data['a'], data['b']]
        self.assertEquals(3, len(dataWalkerCallback.dataCheckList))
        self.assertEquals(3, len(dataWalkerCallback.schemaCheckList))
        self.assertEquals(3, len(dataWalkerCallback.pathList))
        for index, item in enumerate(expectedData):
            self.assertEquals(item, dataWalkerCallback.dataCheckList[index])

        self.assertEquals(expectedSchemaCheckedList, dataWalkerCallback.schemaCheckList)
        self.assertEquals(['root', 'root.a', 'root.b'], dataWalkerCallback.pathList)
        self.assertEquals(data, dataWalkerCallback.rootObj)

    def testSimpleDictDataWalk(self):
        dataWalkerCallback = DataWalkerCallback()
        schema = {'type': 'dict',
         'keyTypes': {'type': 'int'},
         'valueTypes': {'type': 'int'}}
        data = {1: 10,
         2: 20,
         3: 25}
        dataWalker.Walk(data, schema, continueWalkingFunction=dataWalkerCallback.continueWalkingFunction)
        expectedDataList = [data,
         1,
         10,
         2,
         20,
         3,
         25]
        expectedSchemaCheckedList = [schema, schema['valueTypes']]
        expectedData = [data,
         data[1],
         data[2],
         data[3]]
        self.assertEquals(7, len(dataWalkerCallback.dataCheckList))
        self.assertEquals(2, len(dataWalkerCallback.schemaCheckList))
        self.assertEquals(7, len(dataWalkerCallback.pathList))
        self.assertEquals(expectedDataList, dataWalkerCallback.dataCheckList)
        self.assertEquals(expectedSchemaCheckedList, dataWalkerCallback.schemaCheckList)
        self.assertEquals(['root',
         'root<1>',
         'root[1]',
         'root<2>',
         'root[2]',
         'root<3>',
         'root[3]'], dataWalkerCallback.pathList)
        self.assertEquals(data, dataWalkerCallback.rootObj)


if __name__ == '__main__':
    import sys
    suite = unittest.TestLoader().loadTestsFromTestCase(DataWalkerTest)
    unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)