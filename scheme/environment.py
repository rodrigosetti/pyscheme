# coding: utf-8

import codecs
import operator
import sys

from cons import *
from macro import Macro
from procedure import BuiltinProcedure

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
            if self.parent is not None:
                return self.parent[name]
            else:
                raise KeyError("Unbound variable %s" % name)

    def change(self, name, value):
        if name in self:
            self[name] = value
        elif self.parent is None:
            raise KeyError("Unbound variable %s" % name)
        else:
            self.parent.change(name, value)

def make_minimum_environment():
    env = Environment()

    # utf-8 stdin and out
    stdin = codecs.getreader('utf-8')(sys.stdin)
    stdout = codecs.getreader('utf-8')(sys.stdout)

    env.update({
            # built-in symbols
            'nil' : None,
            '#t'  : True,
            '#f'  : False,

            # symbolic tests
            'atom?': BuiltinProcedure(lambda args: is_atom(car(args)), 'atom?', 1, 1),
            'pair?': BuiltinProcedure(lambda args: is_pair(car(args)), 'pair?', 1, 1),
            'nil?' : BuiltinProcedure(lambda args: is_nil(car(args)), 'nil?', 1, 1),
            'eq?':   BuiltinProcedure(lambda args: car(args) is cadr(args), 'eq?', 2, 2),
            '=':     BuiltinProcedure(lambda args: car(args) == cadr(args), '=', 2, 2),

            # basic data manipulation
            'car':   BuiltinProcedure(lambda args: caar(args), 'car', 1, 1),
            'cdr':   BuiltinProcedure(lambda args: cdar(args), 'cdr', 1, 1),
            'cons':  BuiltinProcedure(lambda args: cons(car(args), cadr(args)), 'cons', 2, 2),

            # I/O operations
            'write': BuiltinProcedure(lambda args: stdout.write(car(args).encode('utf-8').decode('string_escape')), 'write', 1, 1),
            'read' : BuiltinProcedure(lambda args: stdin.read(1), 'read', 0, 0),
            'file-open' : BuiltinProcedure(lambda args: codecs.open(car(args), cadr(args), 'utf-8'), 'file-open', 2, 2),
            'file-close': BuiltinProcedure(lambda args: car(args).close(), 'file-close', 1, 1),
            'file-write': BuiltinProcedure(lambda args: car(args).write(cadr(args).encode('utf-8').decode('string_escape').decode('utf-8')), 'file-write', 2, 2),
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

    from evaluator import string_to_scheme as s

    env = make_minimum_environment()
    env.update({
            'len':   BuiltinProcedure(lambda args: 0 if is_nil(car(args)) else len(car(args)), 'len', 1, 1),
            '!=':    BuiltinProcedure(lambda args: car(args) != cadr(args), '!=', 2, 2),
            'not':   Macro(((s('(_ e)'), s('(if e #f #t)')),)),
            'begin': Macro(((s('(_ e ...)'), s('((lambda () e ...))')),)),
            'list':  Macro(((s('(_)'), s('()')),
                            (s('(_ e ...)'), s('(cons e (list ...))')),)),
            'and':   Macro(((s('(_)'), s('#t')),
                            (s('(_ e)'), s('e')),
                            (s('(_ e1 e2 ...)'), s('(if e1 (and e2 ...) #f)')),)),
            'or':    Macro(((s('(_)'), s('#f')),
                            (s('(_ e)'), s('e')),
                            (s('(_ e1 e2 ...)'), s('(let ((t e1)) (if t t (or e2 ...)))')),)),
            'let':   Macro(((s('(_ ((n v)) e1 ...)'), s('((lambda (n) e1 ...) v)')),
                            (s('(_ ((n v) ...d) e1 ...e)'), s('(let (...d) ((lambda (n) e1 ...e) v))')),)),
            'cond': Macro(((s('(_ (else e1 ...))'), s('(begin e1 ...)')),
                           (s('(_ (e1 e2 ...))'), s('(when e1 e2 ...)')),
                           (s('(_ (e1 e2 ...1) c1 ...2)'), s('(if e1 (begin e2 ...1) (cond c1 ...2))')),),
                            reserved_words=set(('else',))),
        })
    return env

