# coding: utf-8

from cons import *
from environment import Environment, make_default_environment
from macro import Macro
from parser import Element, Parser
from procedure import Procedure
import lexer

__all__ = ["evaluate"]

#: Lex states constants enum
(START, COMMENT, QUOTE, LPAREN, RPAREN, MAYBE_DOT, MAYBE_INTEGER, STRING_OPEN,
        STRING_BODY, STRING_CLOSE, SCAPE_CHAR, SYMBOL,) = xrange(12)

#: Grammar non-terminal constants enum
(EXPRESSION, QUOTED_EXPRESSION, UNQUOTED_EXPRESSION, LIST, DOTED_EXPRESSION,
        ATOM,) = xrange(6)

#: Rules for the scheme lexical analyzer
SCHEME_LEX_RULES = {START: lexer.State([(r"\s", START),
                                        (r";",  COMMENT),
                                        (r"'",  QUOTE),
                                        (r"\(", LPAREN),
                                        (r"\)", RPAREN),
                                        (r"\.", MAYBE_DOT),
                                        (r'"',  STRING_OPEN),
                                        (r".",  SYMBOL)], discard=True),
                    COMMENT: lexer.State([(r"\n",  START),
                                            (r".", COMMENT)], discard=True),
                    QUOTE: lexer.State(token='QUOTE'),
                    LPAREN: lexer.State(token='LPAREN'),
                    RPAREN: lexer.State(token='RPAREN'),
                    MAYBE_DOT: lexer.State([(r"[^\(\)\s;]", SYMBOL)], token='DOT'),
                    STRING_OPEN: lexer.State([(r'[^"\\]', STRING_BODY),
                                                 (r'\\', SCAPE_CHAR)], discard=True),
                    STRING_BODY: lexer.State([(r'[^"\\]', STRING_BODY),
                                                 (r'\\', SCAPE_CHAR),
                                                 (r'"', STRING_CLOSE)]),
                    SCAPE_CHAR: lexer.State([(r'.', STRING_BODY)]),
                    STRING_CLOSE: lexer.State(token='SYMBOL', discard=True),
                    SYMBOL: lexer.State([(r"[^\(\)\s;]", SYMBOL)], token='SYMBOL')}

#: The scheme tokenizer
SCHEME_TOKENIZER = lexer.Tokenizer(SCHEME_LEX_RULES, start=START)

#: The scheme parser
SCHEME_PARSER = Parser(start=EXPRESSION)

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

                      ATOM:                p.token('SYMBOL')}

SCHEME_PARSER.grammar = SCHEME_GRAMMAR

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
    return tree_to_scheme(SCHEME_PARSER.parse(SCHEME_TOKENIZER.tokens(string)))

def evaluate(string, environment=None):
    """
    evaluate a string in the scheme evaluator, and return the result as a scheme
    object.
    """
    evaluator = Evaluator(make_default_environment() if environment is None else environment)
    return evaluator.evaluate_str(string)

class Evaluator(object):
    """
    The scheme evaluator. It's a register machine implementation of the
    Explicit-Control Evaluator from the book Structure and Interpretation of
    Computer Programs. Extended with some stuff.
    """

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
        if is_atom(self.exp): # is a not-nil and not-pair value?

            # if it's a number, try to evaluate to the numeric value. like the
            # environment has the numeric
            try:
                self.val = int(self.exp)
            except ValueError:
                try:
                    self.val = float(self.exp)
                except ValueError:
                    self.val = self.env[self.exp]
            return self.continue_
        if is_nil(self.exp):  # is nil, evaluate to itself
            self.val = self.exp
            return self.continue_
        elif car(self.exp) == 'quote':
            self.val = cadr(self.exp) # the quoted text
            return self.continue_
        elif car(self.exp) == 'lambda':
            self.val = Procedure(cadr(self.exp), # the lambda parameters
                                 cddr(self.exp), # the lambda body
                                 self.env)
            return self.continue_
        elif car(self.exp) == 'set!':
            self.stack.append(cadr(self.exp))  # the assignment variable
            self.exp = caddr(self.exp) # the assignment body
            self.stack.append(self.env)
            self.stack.append(self.continue_)
            self.continue_ = self._ev_assignment_1
            return self._eval_dispatch
        elif car(self.exp) == 'macro':
            self.val = Macro( [(car(e), cadr(e)) for e in cddr(self.exp)],
                              [] if not cadr(self.exp) else set(iter(cadr(self.exp))) )
            return self.continue_
        elif car(self.exp) == 'eval':
            self.exp = cadr(self.exp)
            self.stack.append(self.continue_)
            self.continue_ = self._ev_eval_1
            return self._eval_dispatch
        elif car(self.exp) == 'define':
            self.unev = cadr(self.exp) # the definition variable

            # check the case where the the define is using the lambda syntatic
            # sugar: (define (<symbol> <param> ...) <body>)
            if is_pair(self.unev):
                self.env[car(self.unev)] = Procedure(cdr(self.unev), # parameters
                                                     cddr(self.exp), # body
                                                     self.env)
                self.val = car(self.unev)
                return self.continue_
            else:
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
        else: # assume it's a procedure or macro application
            self.stack.append(self.continue_)
            self.stack.append(self.env)
            self.stack.append(cdr(self.exp)) # the operands of the application
            self.exp = car(self.exp) # the operator of the application
            self.continue_ = self._ev_appl_did_operator
            return self._eval_dispatch

    def _ev_eval_1(self):
        self.continue_ = self.stack.pop()
        self.exp = self.val
        return self._eval_dispatch

    def _ev_assignment_1(self):
        self.continue_ = self.stack.pop()
        self.env = self.stack.pop()
        self.unev = self.stack.pop()
        self.env.change(self.unev, self.val)
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
        self.unev = cdr(self.stack.pop()) # get the rest of expressions list
        return self._ev_sequence

    def _ev_appl_did_operator(self):
        self.unev = self.stack.pop() # the operands
        self.env = self.stack.pop()
        self.proc = self.val # the operator

        # if it's a macro
        if type(self.proc) == Macro:
            self.unev = cons('_', self.unev)
            self.exp = self.proc.transform(self.unev)
            self.continue_ = self.stack.pop()
            return self._eval_dispatch
        else:
            # not a macro... must evaluate operands
            self.argl = [] # the empty argument list
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

            # if the lambda parameters is not in the format ( () [. <symbol>] )
            # for taking zero or more arguments
            if len(self.proc.parameters) != 1 or not is_nil(self.proc.parameters[0]):
                for name in self.proc.parameters:
                    try:
                        self.env[name] = self.argl.pop(0)
                    except IndexError:
                        raise ValueError("Insuficient parameters for procedure %s. It should be at least %d" %
                                         (self.proc, len(self.proc.parameters)))
            if not is_nil(self.proc.optional):
                self.env[self.proc.optional] = make_list(self.argl)
            elif self.argl:
                raise ValueError("Too much parameters for procedure %s. It should be %d." %
                                 (self.proc, len(self.proc.parameters)))

            self.unev = self.proc.body
            return self._ev_sequence
        else:
            raise ValueError("Cannot apply procedure %s" % self.proc)


