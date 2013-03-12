#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\carbon\staticData\schema\test\test_validator.py
if __name__ == '__main__':
    import sys, os
    carbonLibPath = os.path.abspath(os.path.join(__file__, '../../../../../'))
    sys.path.append(carbonLibPath)
import unittest
import carbon.staticData.schema.validator as validator

def Validate(data, schema):
    errors = validator.Validate(schema, data)
    return errors


class StaticDataValidationTest(unittest.TestCase):

    def assertValidationPasses(self, validationErrors):
        self.assertEquals(len(validationErrors), 0)

    def assertValidationFailedWithError(self, validationErrors, expectedValidationError):
        validationErrorTypes = [ type(error) for error in validationErrors ]
        self.assertIn(expectedValidationError, validationErrorTypes)

    def testIntRepresentation(self):
        schema = {'type': 'int'}
        self.assertValidationFailedWithError(Validate('This is not a int', schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(4.0, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationPasses(Validate(1, schema))

    def testTypeIDRepresentation(self):
        schema = {'type': 'typeID'}
        self.assertValidationFailedWithError(Validate('This is not a typeId', schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(4.0, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(-1, schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationPasses(Validate(1, schema))

    def testFloatRepresentation(self):
        schema = {'type': 'float'}
        self.assertValidationFailedWithError(Validate('This is not a float', schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(1, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationPasses(Validate(4.0, schema))

    def testVector2Representation(self):
        schema = {'type': 'vector2'}
        self.assertValidationFailedWithError(Validate('This is not a vector2', schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(1, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(0.0, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate((0.0, 0.0, 0.0), schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate((0.0, 0.0, 0.0, 0.0), schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate((0.0, 'This is not a valid vector value', 0.0), schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(('This is not a valid vector value', 0.0), schema), validator.SchemaComparisonError)
        self.assertValidationPasses(Validate((0.0, 2.0), schema))
        self.assertValidationPasses(Validate((0, 2), schema))
        self.assertValidationPasses(Validate((long(0), long(0)), schema))

    def testVector3Representation(self):
        schema = {'type': 'vector3'}
        self.assertValidationFailedWithError(Validate('This is not a vector3', schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(1, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(0.0, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate((0.0, 0.0), schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate((0.0, 0.0, 0.0, 0.0), schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(('This is not a valid vector value', 0.0), schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate((0.0, 'This is not a valid vector value', 0.0), schema), validator.SchemaComparisonError)
        self.assertValidationPasses(Validate((0.0, 0.0, 2.0), schema))
        self.assertValidationPasses(Validate((0, 0, 2), schema))
        self.assertValidationPasses(Validate((long(0), long(0), long(0)), schema))

    def testVector4Representation(self):
        schema = {'type': 'vector4'}
        self.assertValidationFailedWithError(Validate('This is not a vector4', schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(1, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(0.0, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate((0.0, 0.0), schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate((0.0, 0.0, 0.0), schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(('This is not a valid vector value', 0.0), schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate((0.0, 0.0, 'This is not a valid vector value', 0.0), schema), validator.SchemaComparisonError)
        self.assertValidationPasses(Validate((0.0, 0.0, 0.0, 2.0), schema))
        self.assertValidationPasses(Validate((0, 0, 0, 2), schema))
        self.assertValidationPasses(Validate((long(0),
         long(0),
         long(0),
         long(0)), schema))

    def testStringRepresentation(self):
        schema = {'type': 'string'}
        self.assertValidationFailedWithError(Validate(1, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(('this is a tuple, not a string', 'still a tuple'), schema), validator.SchemaTypeError)
        self.assertValidationPasses(Validate('This is a string', schema))

    def testResPathRepresentation(self):
        schema = {'type': 'resPath',
         'extensions': ['red', 'dds']}
        self.assertValidationFailedWithError(Validate(1, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(('this is a tuple, not a string', 'still a tuple'), schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate('This is a string, not a respath', schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate('r:/has/to/start/with/res.red', schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate('res:/no\\backslashes.red', schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate('res:/some space.red', schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate('res:/wrongextension.txt', schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate('res:/path/somerespath.blue', schema), validator.SchemaComparisonError)
        self.assertValidationPasses(Validate('res:/somerespath.red', schema))
        self.assertValidationPasses(Validate('res:/path/path/path/somerespath.red', schema))
        self.assertValidationPasses(Validate('res:/yes/dds/is/allowed/pic.dds', schema))

    def testBoolRepresentation(self):
        schema = {'type': 'bool'}
        self.assertValidationFailedWithError(Validate(0, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(1, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationPasses(Validate(True, schema))
        self.assertValidationPasses(Validate(False, schema))

    def testDictRepresentation(self):
        schema = {'type': 'dict',
         'keyTypes': {'type': 'int'},
         'valueTypes': {'type': 'int'}}
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate({'not int': 'not int'}, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate({1: 'not int'}, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate({'not int': 1}, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate({2.0: 2.0}, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate({2: 2.0}, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate({2.0: 2}, schema), validator.SchemaTypeError)
        self.assertValidationPasses(Validate({}, schema))
        self.assertValidationPasses(Validate({3: 4}, schema))
        self.assertValidationPasses(Validate({3: 4,
         5: 3,
         10: 10,
         1000: 1000}, schema))

    def testListRepresentation(self):
        schema = {'type': 'list',
         'itemTypes': {'type': 'string'}}
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate([1, 2.0], schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(['list Value', 'another list value'], schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(['z', 'r', 'a'], schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(['z', 'r', 1], schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(['z', 'r', 1], schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate([0, 'r', 'a'], schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate([0, 'r', 'a'], schema), validator.SchemaTypeError)
        self.assertValidationPasses(Validate([], schema))
        self.assertValidationPasses(Validate(['list Value'], schema))
        self.assertValidationPasses(Validate(['another list value', 'list Value'], schema))

    def testEnumRepresentation(self):
        schema = {'type': 'enum',
         'values': {'VALUE1': 1,
                    'VALUE2': 2,
                    'VALUE3': 3}}
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(1, schema), validator.SchemaTypeError)
        self.assertValidationPasses(Validate('VALUE1', schema))
        self.assertValidationPasses(Validate('VALUE2', schema))
        self.assertValidationPasses(Validate('VALUE3', schema))

    def testUnionRepresentation(self):
        schema = {'type': 'union',
         'optionTypes': [{'type': 'string'}, {'type': 'int'}]}
        self.assertEquals(1, len(Validate(1.0, schema)))
        self.assertValidationFailedWithError(Validate(1.0, schema), validator.SchemaTypeError)
        self.assertValidationPasses(Validate('This is valid', schema))
        self.assertValidationPasses(Validate(1, schema))
        self.assertValidationPasses(Validate(0, schema))
        self.assertValidationPasses(Validate(-1, schema))

    def testObjectData(self):
        schema = {'type': 'object',
         'attributes': {'a': {'type': 'int'},
                        'b': {'type': 'float'},
                        'c': {'type': 'vector4'}}}
        validValue = {'a': 19,
         'b': 0.5,
         'c': (2.0, 3.0, 4.0, 5.0)}
        invalidValue1 = {'a': 0.5,
         'b': 0.5,
         'c': 1}
        invalidValue2 = 3
        self.assertValidationFailedWithError(Validate(invalidValue1, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(invalidValue2, schema), validator.SchemaTypeError)
        self.assertValidationPasses(Validate(validValue, schema))

    def testComplexInt(self):
        schema = {'type': 'int',
         'min': 10,
         'max': 100}
        self.assertValidationFailedWithError(Validate('This is not a int', schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(4.0, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(0, schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(101, schema), validator.SchemaComparisonError)
        self.assertValidationPasses(Validate(10, schema))
        self.assertValidationPasses(Validate(50, schema))
        self.assertValidationPasses(Validate(10, schema))

    def testIntExclusiveMinMax(self):
        schema = {'type': 'int',
         'exclusiveMax': 10,
         'exclusiveMin': 5}
        self.assertValidationFailedWithError(Validate('This is not an int', schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(4.0, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(0, schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(5, schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(10, schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(101, schema), validator.SchemaComparisonError)
        self.assertValidationPasses(Validate(6, schema))
        self.assertValidationPasses(Validate(7, schema))
        self.assertValidationPasses(Validate(9, schema))

    def testFloatExclusiveMinMax(self):
        schema = {'type': 'float',
         'exclusiveMax': 10.0,
         'exclusiveMin': 5.0}
        self.assertValidationFailedWithError(Validate('This is not a float', schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(4, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(0.0, schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(5.0, schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(10.0, schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(101.0, schema), validator.SchemaComparisonError)
        self.assertValidationPasses(Validate(6.0, schema))
        self.assertValidationPasses(Validate(7.0, schema))
        self.assertValidationPasses(Validate(9.0, schema))

    def testComplexTypeID(self):
        schema = {'type': 'typeID',
         'min': 10,
         'max': 100}
        self.assertValidationFailedWithError(Validate('This is not a typeID', schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(4.0, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(101, schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(0, schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate(-1, schema), validator.SchemaComparisonError)
        self.assertValidationPasses(Validate(10, schema))
        self.assertValidationPasses(Validate(50, schema))
        self.assertValidationPasses(Validate(100, schema))

    def testComplexStringWithLengthCondition(self):
        schema = {'type': 'string',
         'length': 10}
        self.assertValidationFailedWithError(Validate(1, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(4.0, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(('this is a tuple, not a string', 'still a tuple'), schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate('This is a string of wrong length', schema), validator.SchemaComparisonError)
        self.assertValidationPasses(Validate('0123456789', schema))

    def testComplexStringWithMinMaxCondition(self):
        schema = {'type': 'string',
         'minLength': 5,
         'maxLength': 10}
        self.assertValidationFailedWithError(Validate(1, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(('this is a tuple, not a string', 'still a tuple'), schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate('This is a string of wrong length', schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate('a', schema), validator.SchemaComparisonError)
        self.assertValidationPasses(Validate('01234', schema))
        self.assertValidationPasses(Validate('0123456', schema))
        self.assertValidationPasses(Validate('0123456789', schema))

    def testComplexStringWithMinMaxRegExCondition(self):
        schema = {'type': 'string',
         'minLength': 5,
         'maxLength': 10,
         'regex': '.*egg.*'}
        self.assertValidationFailedWithError(Validate(1, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(('this is a tuple, not a string', 'still a tuple'), schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate('spamspamspamspamspambakedbeans-eggandspam', schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate("This is a string of wrong length and doesn't match the regex", schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate('egg', schema), validator.SchemaComparisonError)
        self.assertValidationPasses(Validate('spam-egg', schema))

    def testComplexRegexWithMinMaxRegExCondition(self):
        schema = {'type': 'resPath',
         'minLength': 10,
         'maxLength': 20,
         'regex': '.*egg.*'}
        self.assertValidationFailedWithError(Validate(1, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(None, schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate(('this is a tuple, not a string', 'still a tuple'), schema), validator.SchemaTypeError)
        self.assertValidationFailedWithError(Validate('notrespathegg', schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate('spam-egg', schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate("This is a string of wrong length and doesn't match the regex and isn't a res path", schema), validator.SchemaComparisonError)
        self.assertValidationFailedWithError(Validate('a', schema), validator.SchemaComparisonError)
        self.assertValidationPasses(Validate('res:/spamegg.fle', schema))

    def testComplexObjectData(self):
        schema = {'type': 'object',
         'attributes': {'name': {'type': 'string'},
                        'boundingBox': {'type': 'object',
                                        'isOptional': True,
                                        'attributes': {'min': {'type': 'vector3'},
                                                       'max': {'type': 'vector3'}}}}}
        validDataWithBB = {'name': 'SomeGrandAwesomeShip',
         'boundingBox': {'min': (-100, -100, -100),
                         'max': (100, 100, 100)}}
        validDataWithoutBB = {'name': 'SomeGrandAwesomeShip'}
        invalidDataWithBB1 = {'name': 'SomeGrandAwesomeShip',
         'boundingBox': {'min': (-100, -100, -100)}}
        invalidDataWithBB2 = {'name': 'SomeGrandAwesomeShip',
         'boundingBox': {'max': (-100, -100, -100)}}
        invalidDataWithBB3 = {'name': 'SomeGrandAwesomeShip',
         'boundingBox': {}}
        invalidDataWithBB4 = {'name': 'SomeGrandAwesomeShip',
         'boundingBox': {'invalidAttribute': 'this does not belong here'}}
        self.assertValidationFailedWithError(Validate(invalidDataWithBB1, schema), validator.SchemaObjectAttributeMissingError)
        self.assertValidationFailedWithError(Validate(invalidDataWithBB2, schema), validator.SchemaObjectAttributeMissingError)
        self.assertValidationFailedWithError(Validate(invalidDataWithBB3, schema), validator.SchemaObjectAttributeMissingError)
        self.assertValidationFailedWithError(Validate(invalidDataWithBB4, schema), validator.SchemaObjectAttributeMissingError)
        self.assertValidationFailedWithError(Validate(invalidDataWithBB4, schema), validator.SchemaObjectAttributeNotInSchemaError)
        self.assertValidationPasses(Validate(validDataWithoutBB, schema))
        self.assertValidationPasses(Validate(validDataWithBB, schema))


if __name__ == '__main__':
    import sys
    suite = unittest.TestLoader().loadTestsFromTestCase(StaticDataValidationTest)
    unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)