# coding: utf-8

import operator
from lexer import Token
from parser import Element
import lexer, parser
from cons import *
from procedure import Procedure
from environment import Environment, make_global_environment

__all__ = ["evaluate", "to_str"]

#: Lex states constants enum
(START, COMMENT, QUOTE, LPAREN, RPAREN, MAYBE_DOT, INTEGER_OR_SYMBOL,
MAYBE_INTEGER, STRING_OPEN, STRING_BODY, STRING_CLOSE, SCAPE_CHAR, MAYBE_FLOAT, SYMBOL,) = xrange(14)

#: Grammar non-terminal constants enum
(EXPRESSION, QUOTED_EXPRESSION, UNQUOTED_EXPRESSION,
 LIST, DOTED_EXPRESSION, ATOM,) = xrange(6)

#: reserved words are for special forms. they cannot name anything
RESERVED_WORDS = ('quote', 'define', 'let', 'lambda', 'λ',)

#: Rules for the scheme lexical analyzer
SCHEME_LEX_RULES = {START: lexer.State([(r"\s", START),
                                        (r";",  COMMENT),
                                        (r"'",  QUOTE),
                                        (r"\(", LPAREN),
                                        (r"\)", RPAREN),
                                        (r"\.", MAYBE_DOT),
                                        (r"-",  INTEGER_OR_SYMBOL),
                                        (r"\d", MAYBE_INTEGER),
                                        (r'"',  STRING_OPEN),
                                        (r".",  SYMBOL)], discard=True),
                    COMMENT: lexer.State([(r"\n",  START),
                                            (r".", COMMENT)], discard=True),
                    QUOTE: lexer.State(token='QUOTE'),
                    LPAREN: lexer.State(token='LPAREN'),
                    RPAREN: lexer.State(token='RPAREN'),
                    MAYBE_DOT: lexer.State([(r"\d", MAYBE_FLOAT),
                                              (r"[^\(\)\s;]", SYMBOL)], token='DOT'),
                    INTEGER_OR_SYMBOL: lexer.State([(r"\d", MAYBE_INTEGER),
                                                      (r"[^\(\)\s;]", SYMBOL)], token='SYMBOL'),
                    MAYBE_INTEGER: lexer.State([(r"\d", MAYBE_INTEGER),
                                                  (r"\.", MAYBE_FLOAT),
                                                  (r"[^\(\)\s;]", SYMBOL)], token='INTEGER'),
                    STRING_OPEN: lexer.State([(r'[^"\\]', STRING_BODY),
                                                 (r'\\', SCAPE_CHAR)], discard=True),
                    STRING_BODY: lexer.State([(r'[^"\\]', STRING_BODY),
                                                 (r'\\', SCAPE_CHAR),
                                                 (r'"', STRING_CLOSE)]),
                    SCAPE_CHAR: lexer.State([(r'.', STRING_BODY)]),
                    STRING_CLOSE: lexer.State(token='SYMBOL', discard=True),
                    MAYBE_FLOAT: lexer.State([(r"\d", MAYBE_FLOAT),
                                                (r"[^\(\)\s;]", SYMBOL)], token='FLOAT'),
                    SYMBOL: lexer.State([(r"[^\(\)\s;]", SYMBOL)], token='SYMBOL')}

#: The scheme tokenizer
SCHEME_TOKENIZER = lexer.Tokenizer(SCHEME_LEX_RULES, start=START)

#: The scheme parser
SCHEME_PARSER = parser.Parser(start=EXPRESSION)

with SCHEME_PARSER as p:
    #: The scheme grammar for the parser
    SCHEME_GRAMMAR = {EXPRESSION:          p.expression(QUOTED_EXPRESSION) |
                                           p.expression(ATOM) |
                                           p.expression(LIST),

                      QUOTED_EXPRESSION:   p.token('QUOTE', discard=True) &
                                           (p.expression(ATOM) |
                                            p.expression(LIST)),

                      LIST:                p.token('LPAREN', discard=True) &
                                           p.zeroOrMore(p.expression(EXPRESSION)) &
                                           ~p.expression(DOTED_EXPRESSION) &
                                           p.token('RPAREN', discard=True),

                      DOTED_EXPRESSION:    p.token('DOT', discard=True) &
                                           p.expression(EXPRESSION),

                      ATOM:                p.token('SYMBOL')  |
                                           p.token('INTEGER') |
                                           p.token('FLOAT')}

SCHEME_PARSER.grammar = SCHEME_GRAMMAR

def create_list(expressions):
    if len(expressions) == 0:
        return None
    else:
        return cons(expressions[0], create_list(expressions[1:]))

def tree_to_scheme(tree):
    "Transforms a parsed tree to scheme"

    if type(tree) == Element:
        if tree.name == ATOM:
            return tree.value[0].value.value
        elif tree.name == QUOTED_EXPRESSION:
            return cons('quote', cons(tree_to_scheme(tree.value[0]), None))
        elif tree.name == LIST:
            return tree_to_scheme(tree.value)
        elif tree.name == EXPRESSION:
            return tree_to_scheme(tree.value[0])
        else:
            raise ValueError("Invalid parsed tree element: %s" % tree)
    elif type(tree) == list:
        if len(tree) == 0:
            return None
        elif len(tree) == 1 and type(tree[0]) == Element and tree[0].name == DOTED_EXPRESSION:
            return tree_to_scheme(tree[0].value[0])
        else:
            return cons(tree_to_scheme(tree[0]), tree_to_scheme(tree[1:]))
    elif tree is None:
        return None
    else:
        raise ValueError("Invalid parsed tree")

def string_to_scheme(string):
    "Transforms a string input into a pair lisp's structure"
    global SCHEME_PARSER, SCHEME_TOKENIZER

    return tree_to_scheme(SCHEME_PARSER.parse(SCHEME_TOKENIZER.tokens(string)))

def evaluate(string, environment=None):
        evaluator = Evaluator(make_global_environment() if environment is None else environment)
        return evaluator.evaluate_str(string)

class Evaluator(object):

    def __init__(self, environment):
        # initialize registers
        self.exp = None
        self.env = environment
        self.val = None
        self.continue_ = None
        self.proc = None
        self.argl = None
        self.unev = None

        # initialize stack
        self.stack = []

    def evaluate_str(self, expression_str):
        """
        Evaluate program string, returning a s-expression result
        """
        return self.evaluate(string_to_scheme(expression_str))

    def evaluate(self, expression):
        """
        Evaluate program s-expression, returning a s-expression result
        """
        # feed expression
        self.exp = expression

        # start with eval-dispatch
        continuation = self._eval_dispatch()

        # the continuation loop
        while continuation:
            continuation = continuation()

        return self.val

    def _eval_dispatch(self):
        if is_symbol(self.exp): # is variable?
            self.val = self.env[self.exp]
            return self.continue_
        if is_atom(self.exp) or is_nil(self.exp):  # self evaluating?
            self.val = self.exp
            return self.continue_
        elif car(self.exp) == 'quote':
            self.val = cadr(self.exp) # the quoted text
            return self.continue_
        elif car(self.exp) in ('lambda', 'λ'):
            self.unev = cadr(self.exp) # the lambda parameters
            self.exp = cddr(self.exp) # the lambda body (not atom, for implicit sequence)
            self.val = Procedure(self.unev, self.exp, self.env)
            return self.continue_
        elif car(self.exp) == 'set!':
            self.unev = cadr(self.exp) # the assignment variable
            self.stack.append(self.unev)
            self.exp = caddr(self.exp) # the assignment body
            self.stack.append(self.env)
            self.stack.append(self.continue_)
            self.continue_ = self._ev_assignment_1
            return self._eval_dispatch
        elif car(self.exp) == 'define':
            self.unev = cadr(self.exp) # the definition variable
            self.stack.append(self.unev)
            self.exp = caddr(self.exp) # the definition body
            self.stack.append(self.env)
            self.stack.append(self.continue_)
            self.continue_ = self._ev_definition_1
            return self._eval_dispatch
        elif car(self.exp) == 'if':
            self.stack.append(self.exp)
            self.stack.append(self.env)
            self.stack.append(self.continue_)
            self.continue_ = self._ev_if_decide
            self.exp = cadr(self.exp) # the if predicate
            return self._eval_dispatch
        elif car(self.exp) == 'begin':
            self.unev = cdr(self.exp) # the begin actions
            self.stack.append(self.continue_)
            return self._ev_sequence
        else: # assume it's an application
            self.stack.append(self.continue_)
            self.stack.append(self.env)
            self.unev = cdr(self.exp) # the operands of the application
            self.stack.append(self.unev)
            self.exp = car(self.exp) # the operator of the application
            self.continue_ = self._ev_appl_did_operator
            return self._eval_dispatch

    def _ev_assignment_1(self):
        self.continue_ = self.stack.pop()
        self.env = self.stack.pop()
        self.unev = self.stack.pop()
        self.env.change(self.unev, self.val)
        self.val = self.val
        return self.continue_

    def _ev_definition_1(self):
        self.continue_ = self.stack.pop()
        self.env = self.stack.pop()
        self.unev = self.stack.pop()
        self.env[self.unev] = self.val
        self.val = self.unev
        return self.continue_

    def _ev_if_decide(self):
        self.continue_ = self.stack.pop()
        self.env = self.stack.pop()
        self.exp = self.stack.pop()
        if self.val: # if evaluated predicate is true
            self.exp = caddr(self.exp) # evaluates the if consequent
        else:
            self.exp = cadddr(self.exp) # evaluates the if alternative
        return self._eval_dispatch

    def _ev_sequence(self):
        self.exp = car(self.unev) # get the first expression of the list
        if is_nil(cdr(self.unev)): # if this is the last expression
            self.continue_ = self.stack.pop()
            return self._eval_dispatch
        else:
            self.stack.append(self.unev)
            self.stack.append(self.env)
            self.continue_ = self._ev_sequence_continue
            return self._eval_dispatch

    def _ev_sequence_continue(self):
        self.env = self.stack.pop()
        self.unev = self.stack.pop()
        self.unev = cdr(self.unev) # get the rest of expressions list
        return self._ev_sequence

    def _ev_appl_did_operator(self):
        self.unev = self.stack.pop() # the operands
        self.env = self.stack.pop()
        self.argl = [] # the empty argument list
        self.proc = self.val # the operator
        if is_nil(self.unev): # if there's no operands
            return self._apply_dispatch
        self.stack.append(self.proc)
        return self._ev_appl_operand_loop

    def _ev_appl_operand_loop(self):
        self.stack.append(self.argl)
        self.exp = car(self.unev) # the first operand
        if is_nil(cdr(self.unev)): # if this is the last operand
            self.continue_ = self._ev_appl_accum_last_arg
            return self._eval_dispatch
        else:
            self.stack.append(self.env)
            self.stack.append(self.unev)
            self.continue_ = self._ev_appl_accumulate_arg
            return self._eval_dispatch

    def _ev_appl_accumulate_arg(self):
        self.unev = self.stack.pop()
        self.env = self.stack.pop()
        self.argl = self.stack.pop()
        self.argl.append(self.val) # accumulate the evaluated operand
        self.unev = cdr(self.unev) # the rest of operands
        return self._ev_appl_operand_loop

    def _ev_appl_accum_last_arg(self):
        self.argl = self.stack.pop()
        self.argl.append(self.val) # accumulate the evaluated operand
        self.proc = self.stack.pop()
        return self._apply_dispatch

    def _apply_dispatch(self):
        if callable(self.proc): # primitive application
            self.val = self.proc(make_list(self.argl))
            self.continue_ = self.stack.pop()
            return self.continue_
        elif type(self.proc) == Procedure: # compound procedure
            # extends environment:
            self.env = Environment(parent=self.proc.environment)
            for name in self.proc.parameters:
                self.env[name] = self.argl.pop(0)
            if not is_nil(self.proc.optional):
                self.env[self.proc.optional] = make_list(self.argl)

            self.unev = self.proc.body
            return self._ev_sequence
        else:
            raise ValueError("Cannot apply procedure %s" % self.proc)


