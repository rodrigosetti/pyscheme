# coding: utf-8

import codecs
import operator
import sys

from cons import *
from thunk import is_thunk
from macro import Macro, is_macro
from procedure import Procedure, BuiltinProcedure, is_procedure

class Environment(dict):
    """
    Hierarchical dictionary. This object serves as a frame in the scheme
    evaluation model, which can point to a higher scope environment.
    """

    def __init__(self, parent=None):
        """
        Creates a new environment frame , optionaly, pointing to a parent
        frame.
        """
        super(Environment, self).__init__()
        self.parent = parent

    def __getitem__(self, name):
        """
        Get the value from the name in this frame or higher scope ones.
        """
        try:
            return super(Environment, self).__getitem__(name)
        except KeyError as e:
            # should stop only is parent is None, {} is acceptable, as it
            # could have other parents (grandparents)
            if self.parent is not None:
                return self.parent[name]
            else:
                raise KeyError("Unbound variable %s" % name)

    def truncated_repr(self):
        if len(self.keys()) > 6:
            current = "%s ..." % dict(self.items()[:5])
        else:
            current = str(dict(self.items()))

        if self.parent is not None:
            return "%s, parent=%s" % (current,
                                      self.parent.truncated_repr())
        else:
            return current

    def __repr__(self):
        return "<environment %s>" % self.truncated_repr()

class NumericEnvironment(Environment):

    def __getitem__(self, name):
        # try to transform to numeric forms
        try:
            return int(name)
        except ValueError:
            try:
                return float(name)
            except ValueError:
                try:
                    return complex(name)
                except ValueError:
                    return super(NumericEnvironment, self).__getitem__(name)


def make_minimum_environment():
    env = NumericEnvironment()

    # utf-8 stdin and out
    stdin = codecs.getreader('utf-8')(sys.stdin)
    stdout = codecs.getreader('utf-8')(sys.stdout)

    env.update({
            # built-in symbols
            'nil' : None,
            '#t'  : True,
            '#f'  : False,

            # symbolic tests
            'procedure?' : BuiltinProcedure(lambda args: is_procedure(car(args)), 'procedure?', 1, 1),
            'macro?' : BuiltinProcedure(lambda args: is_macro(car(args)), 'macro?', 1, 1),
            'thunk?' : BuiltinProcedure(lambda args: is_thunk(car(args)), 'thunk?', 1, 1),
            'symbol?': BuiltinProcedure(lambda args: is_symbol(car(args)), 'symbol?', 1, 1),
            'atom?'  : BuiltinProcedure(lambda args: is_atom(car(args)), 'atom?', 1, 1),
            'pair?'  : BuiltinProcedure(lambda args: is_pair(car(args)), 'pair?', 1, 1),
            'nil?'   : BuiltinProcedure(lambda args: is_nil(car(args)), 'nil?', 1, 1),
            'eq?':     BuiltinProcedure(lambda args: car(args) is cadr(args), 'eq?', 2, 2),
            '=':       BuiltinProcedure(lambda args: car(args) == cadr(args), '=', 2, 2),

            # symbolic manipulation
            'explode': BuiltinProcedure(lambda args: make_list(list(car(args))), 'explode', 1, 1),
            'implode': BuiltinProcedure(lambda args: ''.join(iter(args)), 'implode', 1),

            # basic data manipulation
            'car' :   BuiltinProcedure(lambda args: caar(args), 'car', 1, 1),
            "cdr'":   BuiltinProcedure(lambda args: cdar(args), "cdr'", 1, 1),
            "cons'":  BuiltinProcedure(lambda args: cons(car(args), cadr(args)), "cons'", 2, 2),

            # I/O operations
            'write': BuiltinProcedure(lambda args: stdout.write(unicode(car(args)).encode('utf-8').decode('string_escape')), 'write', 1, 1),
            'read' : BuiltinProcedure(lambda args: stdin.read(1), 'read', 0, 0),
            'file-open' : BuiltinProcedure(lambda args: codecs.open(car(args), cadr(args), 'utf-8'), 'file-open', 2, 2),
            'file-close': BuiltinProcedure(lambda args: car(args).close(), 'file-close', 1, 1),
            'file-write': BuiltinProcedure(lambda args: car(args).write(unicode(cadr(args)).encode('utf-8').decode('string_escape').decode('utf-8')), 'file-write', 2, 2),
            'file-read' : BuiltinProcedure(lambda args: car(args).read(1), 'file-read', 1, 1),

            # arithmetic operations
            '+':   BuiltinProcedure(lambda args: reduce(operator.add, args), '+', 2),
            '-':   BuiltinProcedure(lambda args: reduce(operator.sub, args), '-', 2),
            '*':   BuiltinProcedure(lambda args: reduce(operator.mul, args), '*', 2),
            '/':   BuiltinProcedure(lambda args: reduce(operator.div, args), '/', 2),
            'mod': BuiltinProcedure(lambda args: reduce(operator.mod, args), 'mod', 2),
            '<' :  BuiltinProcedure(lambda args: car(args) <  cadr(args), '<',  2),
            '>' :  BuiltinProcedure(lambda args: car(args) >  cadr(args), '>',  2),
            '<=':  BuiltinProcedure(lambda args: car(args) <= cadr(args), '<=', 2),
            '>=':  BuiltinProcedure(lambda args: car(args) >= cadr(args), '>=', 2),
            })
    return env

def make_default_environment():

    from evaluator import string_to_scheme, EXPRESSION

    s = lambda x: string_to_scheme(x, start_parsing=EXPRESSION)

    env = make_minimum_environment()
    env.update({
            'len':   BuiltinProcedure(lambda args: 0 if is_nil(car(args)) else len(car(args)), 'len', 1, 1),
            '!=':    BuiltinProcedure(lambda args: car(args) != cadr(args), '!=', 2, 2),
            'not':   Macro(((s('(_ e)'), s('(if e #f #t)')),),
                           name='not'),
            'cons':  Macro(((s('(_ x y)'), s("(cons' x (delay y))")),),
                           name='cons'),
            'cdr':   Macro(((s('(_ x)'), s("(if (thunk? (cdr' x)) (eval (cdr' x)) (cdr' x))")),),
                           name='cdr'),
            'list':  Macro(((s('(_)'), s('()')),
                            (s('(_ e ...)'), s('(cons e (list ...))')),),
                           name='list'),
            'begin': Macro(((s('(_ ...)'), s('((lambda () ...))')),),
                           name='begin'),
            'and':   Macro(((s('(_)'), s('#t')),
                            (s('(_ e)'), s('e')),
                            (s('(_ e1 e2 ...)'), s('(if e1 (and e2 ...) #f)')),),
                           name='and'),
            'or':    Macro(((s('(_)'), s('#f')),
                            (s('(_ e)'), s('e')),
                            (s('(_ e1 e2 ...)'), s('(let ((t e1)) (if t t (or e2 ...)))')),),
                           name='or'),
            'let':   Macro(((s('(_ ((n v)) e ...)'), s('((lambda () (define n v) e ...))')),
                            (s('(_ ((n v) ...1) e ...2)'), s('((lambda () (define n v) (let (...1) e ...2)))')),),
                           name='let'),
            'cond': Macro(((s('(_ (else e))'), s('e')),
                           (s('(_ (e1 e2))'), s('(if e1 e2 ())')),
                           (s('(_ (e1 e2 ) c1 ...)'), s('(if e1 e2 (cond c1 ...))')),),
                          reserved_words=set(('else',)),
                          name='cond'),
        })
    return env

