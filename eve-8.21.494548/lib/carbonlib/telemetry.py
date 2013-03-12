#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\telemetry.py
import blue
import sys
import types
if blue.pyos.markupZonesInPython:

    def ZONE_FUNCTION(func):

        def wrapper(*args, **kwargs):
            try:
                blue.statistics.EnterZone(func.__name__)
                res = func(*args, **kwargs)
            finally:
                blue.statistics.LeaveZone()

            return res

        return wrapper


    def ZONE_METHOD(method):
        zoneName = method.__name__

        def wrapper(self, *args, **kwargs):
            try:
                blue.statistics.EnterZone(zoneName)
                res = method(self, *args, **kwargs)
            finally:
                blue.statistics.LeaveZone()

            return res

        return wrapper


    def ZONE_METHOD_IN_WAITING(name, method):
        zoneName = name + '::' + method.__name__

        def wrapper(self, *args, **kwargs):
            try:
                blue.statistics.EnterZone(zoneName)
                res = method(self, *args, **kwargs)
            finally:
                blue.statistics.LeaveZone()

            return res

        return wrapper


    class ZONE_PER_METHOD(type):

        def __new__(cls, name, bases, dct):
            print 'Marking up class', name
            for key in dct:
                if isinstance(dct[key], types.FunctionType):
                    print 'Method', dct[key].__name__
                    dct[key] = ZONE_METHOD_IN_WAITING(name, dct[key])

            return type.__new__(cls, name, bases, dct)


    def APPEND_TO_ZONE(label):
        blue.statistics.AppendToZone(str(label))


else:

    def ZONE_FUNCTION(func):
        return func


    def ZONE_METHOD(method):
        return method


    class ZONE_PER_METHOD(type):
        pass


    def APPEND_TO_ZONE(label):
        pass


class StatisticsProfiler(object):

    def trace_dispatch_call(self, frame, arg):
        fcode = frame.f_code
        fn = '%s:%d %s' % (fcode.co_filename, fcode.co_firstlineno, fcode.co_name)
        blue.statistics.EnterZone(fn)

    def trace_dispatch_c_call(self, frame, arg):
        blue.statistics.EnterZone(arg.__name__)

    def trace_dispatch_return(self, frame, t):
        blue.statistics.LeaveZone()

    dispatch = {'call': trace_dispatch_call,
     'exception': trace_dispatch_return,
     'return': trace_dispatch_return,
     'c_call': trace_dispatch_c_call,
     'c_exception': trace_dispatch_return,
     'c_return': trace_dispatch_return}

    def dispatcher(self, frame, event, arg):
        self.dispatch[event](self, frame, arg)

    @classmethod
    def Start(cls):
        sys.setprofile(cls().dispatcher)

    @classmethod
    def Stop(cls):
        sys.setprofile(None)