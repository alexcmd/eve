#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/sys/locks_unittest.py
from __future__ import with_statement
import unittest
import random
import stackless
import blue
from contextlib import contextmanager
from locks import *

@contextmanager
def AllowBlock():
    old = stackless.getcurrent().block_trap = False
    try:
        yield ()
    finally:
        stackless.getcurrent().block_trap = old


def Run():

    def watcher(old):
        while stackless.getruncount() > 1:
            stackless.schedule()

        old.insert()

    with AllowBlock():
        stackless.tasklet(watcher)(stackless.getcurrent())
        stackless.schedule_remove()


class TestLockCommon(object):

    def setUp(self):
        self.lock = self.lockType()

    def tearDown(self):
        del self.lock

    def test_exclusive(self):
        have = []

        def func(n, counter):
            for i in range(n):
                with self.lock:
                    counter[0] += 1
                    self.assertEqual(have, [])
                    have.append(stackless.getcurrent())
                    for i in xrange(random.randint(1, 5)):
                        stackless.schedule()

                    self.assertEqual(have, [stackless.getcurrent()])
                    have.remove(stackless.getcurrent())
                stackless.schedule()

        c0 = [0]
        c1 = [0]
        n = 10
        stackless.tasklet(func)(n, c0)
        stackless.tasklet(func)(n, c1)
        Run()
        self.assertEqual(c0[0], n)
        self.assertEqual(c1[0], n)

    def test_try_acquire(self):
        have = []

        def func(n, counter):
            successes = 0
            while successes < n:
                if self.lock.try_acquire():
                    try:
                        successes += 1
                        counter[0] += 1
                        self.assertEqual(have, [])
                        have.append(stackless.getcurrent())
                        for i in xrange(random.randint(1, 5)):
                            stackless.schedule()

                        self.assertEqual(have, [stackless.getcurrent()])
                        have.remove(stackless.getcurrent())
                    finally:
                        self.lock.release()

                else:
                    counter[1] += 1
                stackless.schedule()

        c0 = [0, 0]
        c1 = [0, 0]
        n = 10
        stackless.tasklet(func)(n, c0)
        stackless.tasklet(func)(n, c1)
        Run()
        self.assertEqual(c0[0], n)
        self.assertEqual(c1[0], n)
        self.assertTrue(c0[1] > 0)
        self.assertTrue(c1[1] > 0)


class TestLockOnly(object):

    def testHolding(self):
        with self.lock:
            self.assertEqual(self.lock.HoldingTasklets(), [stackless.getcurrent()])
        self.assertEqual(self.lock.HoldingTasklets(), [])

    def testWaiting(self):
        with self.lock:

            def f():
                with self.lock:
                    stackless.schedule()

            t0 = stackless.tasklet(f)()
            t1 = stackless.tasklet(f)()
            Run()
            self.assertTrue(t0 in self.lock.WaitingTasklets())
            self.assertTrue(t1 in self.lock.WaitingTasklets())
            self.assertEqual(len(self.lock.WaitingTasklets()), 2)
        Run()
        self.assertEqual(self.lock.WaitingTasklets(), [])

    def testIsCool(self):
        with self.lock:
            self.assertFalse(self.lock.IsCool())
        self.assertTrue(self.lock.IsCool())

        def f():
            with self.lock:
                stackless.schedule()

        with self.lock:
            stackless.tasklet(f)()
            Run()
            self.assertFalse(self.lock.IsCool())
        self.assertFalse(self.lock.IsCool())
        Run()
        self.assertTrue(self.lock.IsCool())


class TestLock(TestLockCommon, TestLockOnly, unittest.TestCase):
    lockType = Lock

    def testBlock(self):

        def f(where):
            where[0] = 0
            with self.lock:
                where[0] = 1
                self.assertFalse(self.lock.try_acquire())
                self.assertFalse(self.lock.acquire(False))
                self.lock.acquire()
                where[0] = 2
            where[0] = 3

        w = [-1]
        t = stackless.tasklet(f)(w)
        Run()
        self.assertEqual(w[0], 1)
        self.assertEqual(self.lock.WaitingTasklets(), [t])
        self.assertEqual(self.lock.WaitingTasklets(), [t])
        self.assertFalse(self.lock.IsCool())
        self.lock.release()
        Run()
        self.assertEqual(w[0], 3)
        self.assertEqual(self.lock.WaitingTasklets(), [])
        self.assertEqual(self.lock.WaitingTasklets(), [])
        self.assertTrue(self.lock.IsCool())


class TestRLock(TestLockCommon, TestLockOnly, unittest.TestCase):
    lockType = RLock

    def testRecursion(self):

        def f(where):
            where[0] = 0
            with self.lock:
                where[0] = 1
                with self.lock:
                    where[0] = 2
                    self.assertTrue(self.lock.try_acquire())
                    self.assertEqual(len(self.lock.HoldingTasklets()), 3)
                    self.lock.release()
            where[0] = 3

        w = [-1]
        t = stackless.tasklet(f)(w)
        Run()
        self.assertEqual(w[0], 3)
        self.assertEqual(self.lock.WaitingTasklets(), [])
        self.assertEqual(self.lock.WaitingTasklets(), [])
        self.assertTrue(self.lock.IsCool())

    def testRecursionInheritance(self):

        def f(where, parent):
            with Inheritance(parent):
                where[0] = 0
                with self.lock:
                    where[0] = 1
                    with self.lock:
                        where[0] = 2
                        self.assertTrue(self.lock.try_acquire())
                        self.assertEqual(len(self.lock.HoldingTasklets()), 4)
                        self.lock.release()
                where[0] = 3

        w = [-1]
        t = stackless.tasklet(f)(w, stackless.getcurrent())
        with self.lock:
            Run()
        self.assertEqual(w[0], 3)
        self.assertEqual(self.lock.WaitingTasklets(), [])
        self.assertEqual(self.lock.WaitingTasklets(), [])
        self.assertTrue(self.lock.IsCool())


class TestRWLock(TestRLock):
    lockType = RWLock

    def testMultiReader(self):

        def f(lock):
            with self.lock.acquired_read():
                with lock:
                    pass

        lock = Lock()
        with lock:
            stackless.tasklet(f)(lock)
            stackless.tasklet(f)(lock)
            stackless.tasklet(f)(lock)
            Run()
            self.assertEqual(len(self.lock.HoldingTasklets()), 3)
        Run()
        self.assertEqual(len(self.lock.HoldingTasklets()), 0)

    def testReaderWriter(self):
        stats = []
        inlock = []

        def reader(n):
            for i in range(n):
                with self.lock.acquired_read():
                    inlock.append(stackless.getcurrent())
                    for j in xrange(random.randint(1, 3)):
                        stackless.schedule()

                    stats.append(inlock[:])
                    inlock.remove(stackless.getcurrent())

        def writer(n):
            for i in range(n):
                with self.lock.acquired():
                    inlock.append(stackless.getcurrent())
                    for j in xrange(random.randint(1, 3)):
                        stackless.schedule()

                    stats.append(inlock[:])
                    inlock.remove(stackless.getcurrent())

        readers = [ stackless.tasklet(reader)(4) for i in xrange(3) ]
        writers = [ stackless.tasklet(writer)(4) for i in xrange(3) ]
        Run()
        self.assertTrue(len(stats) > 0)
        multi = 0
        writer = 0
        for s in stats:
            self.assertTrue(len(s) > 0)
            t = s[0]
            if t in readers:
                if len(s) > 1:
                    multi += 1
                for o in s[1:]:
                    self.assertTrue(o in readers)

            else:
                writer += 1
                self.assertEqual(len(s), 1)

        self.assertTrue(multi)
        self.assertTrue(writer)


class TestCondition(TestLockCommon, unittest.TestCase):
    lockType = Condition

    def testProducerConsumer(self):

        def producer(n, slot):
            for i in xrange(n):
                while True:
                    with self.lock:
                        if not slot:
                            slot.append(i)
                            self.lock.notify()
                            break
                    stackless.schedule()

        def consumer(n, slot, result):
            for i in xrange(n):
                with self.lock:
                    while not slot:
                        self.lock.wait()

                    result.append(slot[0])
                    del slot[:]

        theslot = []
        result = []
        n = 5
        stackless.tasklet(producer)(n, theslot)
        stackless.tasklet(consumer)(n, theslot, result)
        Run()
        self.assertEqual(result, range(n))

    def testProducerConsumer2(self):
        lock = RLock()
        producerReady = Condition(lock)
        consumerReady = Condition(lock)

        def producer(n, slot):
            for i in xrange(n):
                with producerReady:
                    while slot:
                        producerReady.wait()

                    slot.append(i)
                    consumerReady.notify()

        def consumer(n, slot, result):
            for i in xrange(n):
                with consumerReady:
                    while not slot:
                        consumerReady.wait()

                    result.append(slot[0])
                    del slot[:]
                    producerReady.notify()

        theslot = []
        result = []
        n = 5
        stackless.tasklet(producer)(n, theslot)
        stackless.tasklet(consumer)(n, theslot, result)
        Run()
        self.assertEqual(result, range(n))