#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\stdlib\stacklesslib\util.py
import sys
import stackless
import contextlib
import weakref
import collections
from . import main
import threading
if hasattr(threading, 'real_threading'):
    _realthreading = threading.realthreading
    _RealThread = threading.realthreading.Thread
else:
    _realthreading = threading
    _RealThread = threading.Thread
del threading

@contextlib.contextmanager
def atomic():
    c = stackless.getcurrent()
    old = c.set_atomic(True)
    try:
        yield
    finally:
        c.set_atomic(old)


@contextlib.contextmanager
def block_trap(trap = True):
    c = stackless.getcurrent()
    old = c.block_trap
    c.block_trap = trap
    try:
        yield
    finally:
        c.block_trap = old


@contextlib.contextmanager
def ignore_nesting(flag = True):
    c = stackless.getcurrent()
    old = c.set_ignore_nesting(flag)
    try:
        yield
    finally:
        c.set_ignore_nesting(old)


class local(object):

    def __init__(self):
        object.__getattribute__(self, '__dict__')['_tasklets'] = weakref.WeakKeyDictionary()

    def get_dict(self):
        d = object.__getattribute__(self, '__dict__')['_tasklets']
        try:
            a = d[stackless.getcurrent()]
        except KeyError:
            a = {}
            d[stackless.getcurrent()] = a

        return a

    def __getattribute__(self, name):
        a = object.__getattribute__(self, 'get_dict')()
        if name == '__dict__':
            return a
        elif name in a:
            return a[name]
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        a = object.__getattribute__(self, 'get_dict')()
        a[name] = value

    def __delattr__(self, name):
        a = object.__getattribute__(self, 'get_dict')()
        try:
            del a[name]
        except KeyError:
            raise AttributeError, name


class WaitTimeoutError(RuntimeError):
    pass


def channel_wait(chan, timeout = None):
    if timeout is None:
        return chan.receive()
    waiting_tasklet = stackless.getcurrent()

    def break_wait():
        with atomic():
            if waiting_tasklet and waiting_tasklet.blocked:
                waiting_tasklet.raise_exception(WaitTimeoutError)

    with atomic():
        try:
            main.event_queue.push_after(break_wait, timeout)
            return chan.receive()
        finally:
            waiting_tasklet = None


class ValueEvent(stackless.channel):

    def __new__(cls, timeout = None, timeoutException = None, timeoutExceptionValue = None):
        obj = super(ValueEvent, cls).__new__(cls)
        obj.timeout = timeout
        if timeout > 0.0:
            if timeoutException is None:
                timeoutException = WaitTimeoutError
                timeoutExceptionValue = 'Event timed out'

            def break_wait():
                if not obj.closed:
                    obj.abort(timeoutException, timeoutExceptionValue)

            main.event_queue.push_after(break_wait, timeout)
        return obj

    def __repr__(self):
        return '<ValueEvent object at 0x%x, balance=%s, queue=%s, timeout=%s>' % (id(self),
         self.balance,
         self.queue,
         self.timeout)

    def set(self, value = None):
        if self.closed:
            raise RuntimeError('ValueEvent object already signaled or aborted.')
        while self.queue:
            self.send(value)

        self.close()
        self.exception, self.value = RuntimeError, ('Already resumed',)

    def abort(self, exception = None, *value):
        if self.closed:
            raise RuntimeError('ValueEvent object already signaled or aborted.')
        if exception is None:
            exception, value = self.exception, self.value
        else:
            self.exception, self.value = exception, value
        while self.queue:
            self.send_exception(exception, *value)

        self.close()

    def wait(self):
        if self.closed:
            raise self.exception(*self.value)
        return self.receive()


def send_throw(channel, exc, val = None, tb = None):
    if hasattr(channel, 'send_throw'):
        return channel.send_throw(exc, val, tb)
    if exc is None:
        if val is None:
            val = sys.exc_info()[1]
        exc = val.__class__
    elif val is None:
        if isinstance(type, exc):
            exc, val = exc, ()
        else:
            exc, val = exc.__class__, exc
    if not isinstance(val, tuple):
        val = val.args
    channel.send_exception(exc, *val)


class qchannel(stackless.channel):

    def __init__(self):
        self.data_queue = collections.deque()
        self.preference = 1

    @property
    def balance(self):
        if self.data_queue:
            return len(self.data_queue)
        return super(qchannel, self).balance

    def send(self, data):
        sup = super(qchannel, self)
        with atomic():
            if sup.balance >= 0 and not sup.closing:
                self.data_queue.append((True, data))
            else:
                sup.send(data)

    def send_exception(self, exc, *args):
        self.send_throw(exc, args)

    def send_throw(self, exc, value = None, tb = None):
        sup = super(qchannel, self)
        with atomic():
            if sup.balance >= 0 and not sup.closing:
                self.data_queue.append((False, (exc, value, tb)))
            else:
                send_throw(sup, exc, value, tb)

    def receive(self):
        with atomic():
            if not self.data_queue:
                return super(qchannel, self).receive()
            ok, data = self.data_queue.popleft()
            if ok:
                return data
            exc, value, tb = data
            try:
                raise exc, value, tb
            finally:
                tb = None

    def send_sequence(self, sequence):
        for i in sequence:
            self.send(i)

    def __next__(self):
        return self.receive()


def call_async(dispatcher, function, args = (), kwargs = {}, timeout = None, timeout_exception = WaitTimeoutError):
    chan = qchannel()

    def helper():
        try:
            try:
                result = function(*args, **kwargs)
            except Exception:
                chan.send_throw(*sys.exc_info())
            else:
                chan.send(result)

            main.mainloop.interrupt_wait()
        except StopIteration:
            pass

    dispatcher(helper)
    with atomic():
        try:
            return channel_wait(chan, timeout)
        finally:
            chan.close()


@contextlib.contextmanager
def released(lock):
    lock.release()
    try:
        yield
    finally:
        lock.acquire()


class dummy_threadpool(object):

    def __init__(self, stack_size = None):
        self.stack_size = stack_size

    def stop(self):
        pass

    def start_thread(self, target):
        stack_size = self.stack_size
        if stack_size is not None:
            prev_stacksize = _realthreading.stack_size()
            _realthreading.stack_size(stack_size)
        try:
            thread = _RealThread(target=target)
            thread.start()
            return thread
        finally:
            if stack_size is not None:
                _realthreading.stack_size(prev_stacksize)

    def submit(self, job):
        self.start_thread(job)


class simple_threadpool(dummy_threadpool):

    def __init__(self, stack_size = None, n_threads = 1):
        super(simple_threadpool, self).__init__(stack_size)
        self.threads_max = n_threads
        self.threads_n = 0
        self.threads_executing = 0
        self.cond = _realthreading.Condition()
        self.queue = collections.deque()

    def stop(self):
        with self.cond:
            self.threads_max = 0
            self.cond.notify_all()

    def submit(self, job):
        with self.cond:
            ready = self.threads_n - self.threads_executing
            if not ready and self.threads_n < self.threads_max:
                self.threads_n += 1
                try:
                    self.start_thread(self._threadfunc)
                except:
                    self.threads_n -= 1
                    raise 

            self.queue.append(job)
            self.cond.notify()

    def _threadfunc(self):

        def predicate():
            return self.threads_n > self.threads_max or self.queue

        with self.cond:
            try:
                while True:
                    self.cond.wait_for(predicate)
                    if self.threads_n > self.threads_max:
                        return
                    job = self.queue.popleft()
                    self.threads_executing += 1
                    try:
                        with released(self.cond):
                            job()
                    finally:
                        self.threads_executing -= 1
                        job = None

            finally:
                self.threads_n -= 1


def call_on_thread(function, args = (), kwargs = {}, stack_size = None, threadpool = None, timeout = None):
    if not threadpool:
        threadpool = dummy_threadpool(stack_size)
    return call_async(threadpool.submit, function, args, kwargs, timeout=timeout)