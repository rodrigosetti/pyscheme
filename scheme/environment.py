# coding: utf-8

import codecs
import operator
import sys

from cons import *
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
            if self.parent:
                return self.parent[name]
            else:
                raise KeyError("Unbound variable %s" % name)

    def exists(self, name):
        return name in self or (self.parent and self.parent.exists(name))

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

    def define(env, args):
        name = car(args)
        if not is_symbol(name):
            raise ValueError("define name should evaluate to symbol")
        env[name] = cadr(args)
        return name

    def is_defined(env, args):
        "Check if name is bound in current or outer environments"
        name = car(args)
        if not is_symbol(name):
            raise ValueError("defined? name should evaluate to symbol")
        return bool(env.exists(name))

    def set_(env, args):
        name = car(args)
        if not is_symbol(name):
            raise ValueError("set! name should evaluate to symbol")
        env.change(name, cadr(args))
        return name

    def is_set(env, args):
        "Check if name is bound in the current environment"
        name = car(args)
        if not is_symbol(name):
            raise ValueError("set? name should evaluate to symbol")
        return name in env

    env.update({
            # built-in symbols
            'nil' : None,
            '#t'  : True,
            '#f'  : False,

            # symbolic tests
            'procedure?' : BuiltinProcedure(lambda env, args: is_procedure(car(args)), 'procedure?', 1, 1),
            'macro?' : BuiltinProcedure(lambda env, args: is_macro(car(args)), 'macro?', 1, 1),
            'symbol?': BuiltinProcedure(lambda env, args: is_symbol(car(args)), 'symbol?', 1, 1),
            'atom?'  : BuiltinProcedure(lambda env, args: is_atom(car(args)), 'atom?', 1, 1),
            'pair?'  : BuiltinProcedure(lambda env, args: is_pair(car(args)), 'pair?', 1, 1),
            'nil?'   : BuiltinProcedure(lambda env, args: is_nil(car(args)), 'nil?', 1, 1),
            'eq?':     BuiltinProcedure(lambda env, args: car(args) is cadr(args), 'eq?', 2, 2),
            '=':       BuiltinProcedure(lambda env, args: car(args) == cadr(args), '=', 2, 2),

            # basic forms
            'define'   : BuiltinProcedure(define, 'define', 2, 2),
            'defined?' : BuiltinProcedure(is_defined, 'defined?', 1, 1),
            'set!' : BuiltinProcedure(set_, 'set!', 2, 2),
            'set?' : BuiltinProcedure(is_set, 'set?', 1, 1),

            # symbolic manipulation
            'explode': BuiltinProcedure(lambda env, args: make_list(list(car(args))), 'explode', 1, 1),
            'implode': BuiltinProcedure(lambda env, args: ''.join(iter(args)), 'implode', 1),

            # basic data manipulation
            'car':   BuiltinProcedure(lambda env, args: caar(args), 'car', 1, 1),
            'cdr':   BuiltinProcedure(lambda env, args: cdar(args), 'cdr', 1, 1),
            'cons':  BuiltinProcedure(lambda env, args: cons(car(args), cadr(args)), 'cons', 2, 2),

            # I/O operations
            'write': BuiltinProcedure(lambda env, args: stdout.write(car(args).encode('utf-8').decode('string_escape')), 'write', 1, 1),
            'read' : BuiltinProcedure(lambda env, args: stdin.read(1), 'read', 0, 0),
            'file-open' : BuiltinProcedure(lambda env, args: codecs.open(car(args), cadr(args), 'utf-8'), 'file-open', 2, 2),
            'file-close': BuiltinProcedure(lambda env, args: car(args).close(), 'file-close', 1, 1),
            'file-write': BuiltinProcedure(lambda env, args: car(args).write(cadr(args).encode('utf-8').decode('string_escape').decode('utf-8')), 'file-write', 2, 2),
            'file-read' : BuiltinProcedure(lambda env, args: car(args).read(1), 'file-read', 1, 1),

            # arithmetic operations
            '+':   BuiltinProcedure(lambda env, args: reduce(operator.add, args), '+', 2),
            '-':   BuiltinProcedure(lambda env, args: reduce(operator.sub, args), '-', 2),
            '*':   BuiltinProcedure(lambda env, args: reduce(operator.mul, args), '*', 2),
            '/':   BuiltinProcedure(lambda env, args: reduce(operator.div, args), '/', 2),
            'mod': BuiltinProcedure(lambda env, args: reduce(operator.mod, args), 'mod', 2),
            '<' :  BuiltinProcedure(lambda env, args: car(args) <  cadr(args), '<',  2),
            '>' :  BuiltinProcedure(lambda env, args: car(args) >  cadr(args), '>',  2),
            '<=':  BuiltinProcedure(lambda env, args: car(args) <= cadr(args), '<=', 2),
            '>=':  BuiltinProcedure(lambda env, args: car(args) >= cadr(args), '>=', 2),
            })
    return env

def make_default_environment():

    from evaluator import string_to_scheme, EXPRESSION

    s = lambda x: string_to_scheme(x, start_parsing=EXPRESSION)

    env = make_minimum_environment()
    env.update({
            'len':   BuiltinProcedure(lambda env, args: 0 if is_nil(car(args)) else len(car(args)), 'len', 1, 1),
            '!=':    BuiltinProcedure(lambda env, args: car(args) != cadr(args), '!=', 2, 2),
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
                           (s('(_ (e1 e2 ...))'), s('(if e1 (begin e2 ...) ())')),
                           (s('(_ (e1 e2 ...1) c1 ...2)'), s('(if e1 (begin e2 ...1) (cond c1 ...2))')),),
                            reserved_words=set(('else',))),
        })
    return env

