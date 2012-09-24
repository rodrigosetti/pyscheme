# coding: utf-8

class cons(object):
    """
    Implementation of the fundamental scheme data structure
    """

    def __init__(self, first, second):
        "Create a pair with values"
        self.first = first
        self.second = second

    def __repr__(self):
        if self.second == None:
            # the end of the list
            second_str = ''
        elif is_atom(self.second):
            # a non null terminator
            second_str = ' .  %s' % str(self.second)
        else:
            # the continuation of the list
            second_str = str(self.second)

        return "(%s%s)" % (str(self.first), second_str)

    def __iter__(self):
        "iterator over the list structure"
        cur = self
        while is_pair(cur):
            yield cur.first
            cur = cur.second

    def terminal(self):
        "return the last non-Pair element of the list"
        cur = self
        while is_pair(cur):
            cur = cur.second
        return cur

    def __len__(self):
        return len(list(iter(self)))

    def __getitem__(self, idx):
        for i, x in enumerate(self):
            if i == idx:
                return x
        raise IndexError("Index out of range")

car = lambda x: x.first
cdr = lambda x: x.second
is_atom  = lambda x: x is not None and not is_pair(x)
is_pair  = lambda x: type(x) == cons

