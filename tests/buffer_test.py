#! /usr/bin/env python
#! coding: utf-8

import unittest

import scheme.buffer as buffer

class TestBuffer(unittest.TestCase):

    def test_buffer_without_marking(self):

        buf = buffer.Buffer(xrange(1,11))

        expectation = [1,2,3,4,5,6,7,8,9,10]

        count = 0
        for expected, value in zip(expectation, buf):
            self.assertEquals(expected, value)
            count += 1

        self.assertEquals(10, count)

    def test_buffer_with_one_mark(self):

        buf = buffer.Buffer(xrange(1,11))

        i = iter(buf)

        self.assertEquals(1, next(i))
        self.assertEquals(2, next(i))
        self.assertEquals(3, next(i))

        with buf.mark() as markedBuffer:

            mi = iter(markedBuffer)

            self.assertEquals(4, next(mi))
            self.assertEquals(5, next(mi))
            self.assertEquals(6, next(mi))


        self.assertEquals(7, next(i))
        self.assertEquals(8, next(i))
        self.assertEquals(9, next(i))
        self.assertEquals(10, next(i))

    def test_buffer_with_restore(self):

        buf = buffer.Buffer(xrange(1,11))

        i = iter(buf)

        self.assertEquals(1, next(i))
        self.assertEquals(2, next(i))
        self.assertEquals(3, next(i))

        with buf.mark() as markedBuffer:

            mi = iter(markedBuffer)

            self.assertEquals(4, next(mi))
            self.assertEquals(5, next(mi))
            self.assertEquals(6, next(mi))

            markedBuffer.restore()

        self.assertEquals(4, next(i))
        self.assertEquals(5, next(i))
        self.assertEquals(6, next(i))
        self.assertEquals(7, next(i))
        self.assertEquals(8, next(i))
        self.assertEquals(9, next(i))
        self.assertEquals(10, next(i))

    def test_buffer_with_inner_restore(self):

        buf = buffer.Buffer(xrange(1,11))

        i = iter(buf)

        self.assertEquals(1, next(i))
        self.assertEquals(2, next(i))
        self.assertEquals(3, next(i))

        with buf.mark() as markedBuffer:

            mi = iter(markedBuffer)

            self.assertEquals(4, next(mi))
            self.assertEquals(5, next(mi))
            self.assertEquals(6, next(mi))

            with markedBuffer.mark() as markedBuffer2:
                mi2 = iter(markedBuffer2)

                self.assertEquals(7, next(mi2))
                self.assertEquals(8, next(mi2))
                self.assertEquals(9, next(mi2))

                markedBuffer2.restore()

            self.assertEquals(7, next(mi))
            self.assertEquals(8, next(mi))

        self.assertEquals(9, next(i))
        self.assertEquals(10, next(i))

    def test_buffer_with_two_inner_restores(self):

        buf = buffer.Buffer(xrange(1,11))

        i = iter(buf)

        self.assertEquals(1, next(i))
        self.assertEquals(2, next(i))
        self.assertEquals(3, next(i))

        with buf.mark() as markedBuffer:

            mi = iter(markedBuffer)

            self.assertEquals(4, next(mi))
            self.assertEquals(5, next(mi))
            self.assertEquals(6, next(mi))

            with markedBuffer.mark() as markedBuffer2:
                mi2 = iter(markedBuffer2)

                self.assertEquals(7, next(mi2))
                self.assertEquals(8, next(mi2))
                self.assertEquals(9, next(mi2))

                markedBuffer2.restore()

            self.assertEquals(7, next(mi))
            self.assertEquals(8, next(mi))
            self.assertEquals(9, next(mi))

            markedBuffer.restore()

        self.assertEquals(4, next(i))
        self.assertEquals(5, next(i))
        self.assertEquals(6, next(i))
        self.assertEquals(7, next(i))
        self.assertEquals(8, next(i))
        self.assertEquals(9, next(i))
        self.assertEquals(10, next(i))

if __name__ == '__main__':
    unittest.main()

