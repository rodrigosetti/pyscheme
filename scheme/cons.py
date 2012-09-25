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
        elements = []
        current = self
        while is_pair(current):
            val = car(current)
            if type(val) == unicode:
                val = val.encode('utf-8')

            elements.append(pretty_print(val))
            current = cdr(current)

        return "(%s%s)" % (' '.join(elements),
                           ' . %s' % current if not is_nil(current) else '')

    def __iter__(self):
        current = self
        while is_pair(current):
            yield car(current)
            current = cdr(current)

    def terminal(self):
        current = self
        while is_pair(current):
            current = cdr(current)
        return current

    def __len__(self):
        return len(list(iter(self)))

def car(pair):
    if not is_pair(pair):
        raise ValueError("Not a cons")
    return pair.first

def cdr(pair):
    if not is_pair(pair):
        raise ValueError("Not a cons")
    return pair.second

caar   = lambda x: car(car(x))
cddr   = lambda x: cdr(cdr(x))
cdar   = lambda x: cdr(car(x))
cadr   = lambda x: car(cdr(x))
caddr  = lambda x: car(cdr(cdr(x)))
cadddr = lambda x: car(cdr(cdr(cdr(x))))

#: atom is everything which is not nil and not pair
is_atom   = lambda x: not is_nil(x) and not is_pair(x)
is_symbol = lambda x: type(x) in (str, unicode)
is_pair   = lambda x: type(x) == cons
is_nil    = lambda x: x is None

def make_list(iterable):
    """
    Build a cons list using the elements from a iterable
    """
    result = None
    for e in reversed(iterable):
        result = cons(e, result)
    return result

def pretty_print(exp):
    """
    Return a scheme like representation string of a python object
    """

    if exp is None:
        return '()'
    elif exp is True:
        return '#t'
    elif exp is False:
        return '#f'
    else:
        return str(exp)

