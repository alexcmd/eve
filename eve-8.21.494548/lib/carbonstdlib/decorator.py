#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\stdlib\decorator.py
__version__ = '3.3.2'
__all__ = ['decorator', 'FunctionMaker', 'partial']
import sys, re, inspect
try:
    from functools import partial
except ImportError:

    class partial(object):

        def __init__(self, func, *args, **kw):
            self.func = func
            self.args = args
            self.keywords = kw

        def __call__(self, *otherargs, **otherkw):
            kw = self.keywords.copy()
            kw.update(otherkw)
            return self.func(*(self.args + otherargs), **kw)


if sys.version >= '3':
    from inspect import getfullargspec
else:

    class getfullargspec(object):

        def __init__(self, f):
            self.args, self.varargs, self.varkw, self.defaults = inspect.getargspec(f)
            self.kwonlyargs = []
            self.kwonlydefaults = None
            self.annotations = getattr(f, '__annotations__', {})

        def __iter__(self):
            yield self.args
            yield self.varargs
            yield self.varkw
            yield self.defaults


DEF = re.compile('\\s*def\\s*([_\\w][_\\w\\d]*)\\s*\\(')

class FunctionMaker(object):

    def __init__(self, func = None, name = None, signature = None, defaults = None, doc = None, module = None, funcdict = None):
        self.shortsignature = signature
        if func:
            self.name = func.__name__
            if self.name == '<lambda>':
                self.name = '_lambda_'
            self.doc = func.__doc__
            self.module = func.__module__
            if inspect.isfunction(func):
                argspec = getfullargspec(func)
                for a in ('args', 'varargs', 'varkw', 'defaults', 'kwonlyargs', 'kwonlydefaults', 'annotations'):
                    setattr(self, a, getattr(argspec, a))

                for i, arg in enumerate(self.args):
                    setattr(self, 'arg%d' % i, arg)

                self.signature = inspect.formatargspec(formatvalue=(lambda val: ''), *argspec)[1:-1]
                allargs = list(self.args)
                if self.varargs:
                    allargs.append('*' + self.varargs)
                if self.varkw:
                    allargs.append('**' + self.varkw)
                try:
                    self.shortsignature = ', '.join(allargs)
                except TypeError:
                    self.shortsignature = self.signature

                self.dict = func.__dict__.copy()
        if name:
            self.name = name
        if signature is not None:
            self.signature = signature
        if defaults:
            self.defaults = defaults
        if doc:
            self.doc = doc
        if module:
            self.module = module
        if funcdict:
            self.dict = funcdict
        if not hasattr(self, 'signature'):
            raise TypeError('You are decorating a non function: %s' % func)

    def update(self, func, **kw):
        func.__name__ = self.name
        func.__doc__ = getattr(self, 'doc', None)
        func.__dict__ = getattr(self, 'dict', {})
        func.func_defaults = getattr(self, 'defaults', ())
        func.__kwdefaults__ = getattr(self, 'kwonlydefaults', None)
        callermodule = sys._getframe(3).f_globals.get('__name__', '?')
        func.__module__ = getattr(self, 'module', callermodule)
        func.__dict__.update(kw)

    def make(self, src_templ, evaldict = None, addsource = False, **attrs):
        src = src_templ % vars(self)
        evaldict = evaldict or {}
        mo = DEF.match(src)
        if mo is None:
            raise SyntaxError('not a valid function template\n%s' % src)
        name = mo.group(1)
        names = set([name] + [ arg.strip(' *') for arg in self.shortsignature.split(',') ])
        for n in names:
            if n in ('_func_', '_call_'):
                raise NameError('%s is overridden in\n%s' % (n, src))

        if not src.endswith('\n'):
            src += '\n'
        try:
            code = compile(src, '<string>', 'single')
            exec code in evaldict
        except:
            print >> sys.stderr, 'Error in generated code:'
            print >> sys.stderr, src
            raise 

        func = evaldict[name]
        if addsource:
            attrs['__source__'] = src
        self.update(func, **attrs)
        return func

    @classmethod
    def create(cls, obj, body, evaldict, defaults = None, doc = None, module = None, addsource = True, **attrs):
        if isinstance(obj, str):
            name, rest = obj.strip().split('(', 1)
            signature = rest[:-1]
            func = None
        else:
            name = None
            signature = None
            func = obj
        self = cls(func, name, signature, defaults, doc, module)
        ibody = '\n'.join(('    ' + line for line in body.splitlines()))
        return self.make(('def %(name)s(%(signature)s):\n' + ibody), evaldict, addsource, **attrs)


def decorator(caller, func = None):
    if func is not None:
        evaldict = func.func_globals.copy()
        evaldict['_call_'] = caller
        evaldict['_func_'] = func
        return FunctionMaker.create(func, 'return _call_(_func_, %(shortsignature)s)', evaldict, undecorated=func, __wrapped__=func)
    elif isinstance(caller, partial):
        return partial(decorator, caller)
    else:
        first = inspect.getargspec(caller)[0][0]
        evaldict = caller.func_globals.copy()
        evaldict['_call_'] = caller
        evaldict['decorator'] = decorator
        return FunctionMaker.create('%s(%s)' % (caller.__name__, first), 'return decorator(_call_, %s)' % first, evaldict, undecorated=caller, __wrapped__=caller, doc=caller.__doc__, module=caller.__module__)