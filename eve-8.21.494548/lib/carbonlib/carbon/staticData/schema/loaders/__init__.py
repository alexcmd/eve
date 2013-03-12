#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\carbon\staticData\schema\loaders\__init__.py
import ctypes
import collections

class VectorLoader(object):

    def __init__(self, data, offset, schema, extraState):
        self.data = data
        self.offset = offset
        self.schema = schema
        schemaType = schema['type']
        if schemaType == 'vector4':
            self.itemCount = 4
        elif schemaType == 'vector3':
            self.itemCount = 3
        else:
            self.itemCount = 2
        self.vectorType = ctypes.c_float * self.itemCount

    def __getitem__(self, key):
        if 'aliases' in self.schema:
            if key in self.schema['aliases']:
                return ctypes.cast(ctypes.byref(self.data, self.offset), ctypes.POINTER(self.vectorType)).contents[self.schema['aliases'][key]]
        if type(key) is int and key >= 0 and key <= self.itemCount:
            return ctypes.cast(ctypes.byref(self.data, self.offset), ctypes.POINTER(self.vectorType)).contents[key]
        raise IndexError('Invalid index %s' % key)

    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except IndexError as e:
            raise AttributeError(str(e))


def Vector4FromBinaryString(data, offset, schema, extraState):
    if 'aliases' in schema:
        return VectorLoader(data, offset, schema, extraState)
    t = ctypes.c_float * 4
    castPointer = ctypes.cast(ctypes.byref(data, offset), ctypes.POINTER(t))
    return (castPointer.contents[0],
     castPointer.contents[1],
     castPointer.contents[2],
     castPointer.contents[3])


def Vector3FromBinaryString(data, offset, schema, extraState):
    if 'aliases' in schema:
        return VectorLoader(data, offset, schema, extraState)
    t = ctypes.c_float * 3
    castPointer = ctypes.cast(ctypes.byref(data, offset), ctypes.POINTER(t))
    return (castPointer.contents[0], castPointer.contents[1], castPointer.contents[2])


def Vector2FromBinaryString(data, offset, schema, extraState):
    if 'aliases' in schema:
        return VectorLoader(data, offset, schema, extraState)
    t = ctypes.c_float * 2
    castPointer = ctypes.cast(ctypes.byref(data, offset), ctypes.POINTER(t))
    return (castPointer.contents[0], castPointer.contents[1])


def StringFromBinaryString(data, offset, schema, extraState):
    count = ctypes.cast(ctypes.byref(data, offset), ctypes.POINTER(ctypes.c_uint32)).contents.value
    stringPtr = ctypes.cast(ctypes.byref(data, offset + 4), ctypes.POINTER(ctypes.c_char * count))
    return stringPtr.contents.value


def EnumFromBinaryString(data, offset, schema, extraState):
    dataValue = ctypes.cast(ctypes.byref(data, offset), ctypes.POINTER(schema['enumType'])).contents.value
    if schema.get('readEnumValue', False):
        return dataValue
    for k, v in schema['values'].iteritems():
        if v == dataValue:
            return k


def BoolFromBinaryString(data, offset, schema, extraState):
    return ctypes.cast(ctypes.byref(data, offset), ctypes.POINTER(ctypes.c_ubyte)).contents.value == 255


def IntFromBinaryString(data, offset, schema, extraState):
    intType = ctypes.c_int32
    if 'min' in schema and schema['min'] >= 0 or 'exclusiveMin' in schema and schema['exclusiveMin'] >= -1:
        intType = ctypes.c_uint32
    return ctypes.cast(ctypes.byref(data, offset), ctypes.POINTER(intType)).contents.value


def FloatFromBinaryString(data, offset, schema, extraState):
    return ctypes.cast(ctypes.byref(data, offset), ctypes.POINTER(ctypes.c_float)).contents.value