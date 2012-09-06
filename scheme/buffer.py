# coding: utf-8

class Buffer(object):
    """
    A marked Buffer is an iterable object that support marking
    through the "with" statement. By such, one can restore the
    buffer up to the point where it was marked, and also, nest
    marks and restore
    """

    def __init__(self, iterable):
        "Creates a marked buffer from any iterable object"
        self.iterable = iterable
        self.iterator = iter(iterable)
        self.idx = 0
        self.buffer = []
        self.marks = []

    def __iter__(self):
        while True:
            self.idx += 1
            if self.idx-1 < len(self.buffer):
                yield self.buffer[self.idx-1]
            else:
                value = next(self.iterator)
                self.buffer.append(value)
                yield value

    def __nonzero__(self):
        if self.buffer:
            return True
        else:
            try:
                value = next(self.iterator)
                self.buffer.append(value)
                return True
            except StopIteration:
                return False

    def mark(self):
        return self

    def __enter__(self):
        self.marks.append(self.idx)
        return self

    def __exit__(self, type, value, traceback):
        self.marks.pop()

    def restore(self):
        "Restore buffer up to the last mark"
        self.idx = self.marks[-1]

