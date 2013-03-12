#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/util/inspect_unittest.py
import unittest

class ClassWithMethods(object):

    def NormalMethod(self):
        return 'Normal method for ' + self.__class__.__name__

    @classmethod
    def ClassMethod(cls):
        return 'Class method for ' + cls.__name__

    @staticmethod
    def StaticMethod():
        return 'Static method'


class _TestMethodInspectors(unittest.TestCase):

    def testClassMethod(self):
        obj = ClassWithMethods()
        self.assertTrue(IsClassMethod(ClassWithMethods.ClassMethod), 'ClassMethod from class not a class method!')
        self.assertTrue(IsClassMethod(obj.ClassMethod), 'ClassMethod from object not a class method!')
        self.assertTrue(not IsClassMethod(ClassWithMethods.StaticMethod), 'StaticMethod from class is a class method???')
        self.assertTrue(not IsClassMethod(ClassWithMethods.NormalMethod), 'NormalMethod from class is a class method???')

    def testStaticMethod(self):
        obj = ClassWithMethods()
        self.assertTrue(IsStaticMethod(ClassWithMethods.StaticMethod), 'StaticMethod from class not a static method!')
        self.assertTrue(IsStaticMethod(obj.StaticMethod), 'StaticMethod from object not a static method!')
        self.assertTrue(not IsStaticMethod(ClassWithMethods.ClassMethod), 'ClassMethod from class is a static method???')
        self.assertTrue(not IsStaticMethod(ClassWithMethods.NormalMethod), 'NormalMethod from class is a static method???')

    def testNormalMethod(self):
        obj = ClassWithMethods()
        self.assertTrue(IsNormalMethod(ClassWithMethods.NormalMethod), 'NormalMethod from class not a normal method!')
        self.assertTrue(IsNormalMethod(obj.NormalMethod), 'NormalMethod from object not a normal method!')
        self.assertTrue(not IsNormalMethod(ClassWithMethods.ClassMethod), 'ClassMethod from class is a normal method???')
        self.assertTrue(not IsNormalMethod(ClassWithMethods.StaticMethod), 'StaticMethod from class is a normal method???')