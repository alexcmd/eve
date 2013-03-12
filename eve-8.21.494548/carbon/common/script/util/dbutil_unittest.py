#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/util/dbutil_unittest.py
import unittest

class _TestStringManipulation(unittest.TestCase):

    def testSQLStringify(self):
        observed = SQLStringify(9)
        expected = '9'
        self.assertTrue(expected == observed, 'SQLStringify failed on an integer')
        observed = SQLStringify('hello')
        expected = "'hello'"
        self.assertTrue(expected == observed, 'SQLStringify failed on a simple string')
        observed = SQLStringify("it's me")
        expected = "'it''s me'"
        self.assertTrue(expected == observed, 'SQLStringify failed on a string with a single quote')

    def testSQLStringifyUnicode(self):
        observed = SQLStringify(u"it's me")
        expected = u"'it''s me'"
        self.assertTrue(expected == observed, 'SQLStringify failed on a unicode string')