# coding: utf-8

import codecs

from cons import *
from thunk import Thunk, is_thunk
from environment import Environment, make_default_environment
from macro import Macro, is_macro
from parser import Element, Parser
from procedure import Procedure, is_procedure
import lexer

__all__ = ["evaluate"]

#: Lex states constants enum
(START, COMMENT, QUOTE, LPAREN, RPAREN, MAYBE_DOT, MAYBE_INTEGER, STRING_OPEN,
        STRING_BODY, STRING_CLOSE, SCAPE_CHAR, SYMBOL,) = xrange(12)

#: Grammar non-terminal constants enum
(EXPRESSION, QUOTED_EXPRESSION, UNQUOTED_EXPRESSION, LIST, DOTED_EXPRESSION,
        ATOM, PROGRAM) = xrange(7)

class FileStream(object):

    def __init__(self, file):
        self.file = file

    def __iter__(self):
        for chunk in self.file:
            for char in chunk:
                yield char

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
        elif tree.name == PROGRAM:
            return tree_to_scheme(tree.value)
        else:
            raise ValueError("Invalid parsed tree element: %s" % tree)
    elif hasattr(tree, 'next'): # is an iterator
        try:
            e = next(tree)
            if type(e) == Element and e.name == DOTED_EXPRESSION:
                return tree_to_scheme(e.value[0])
            else:
                return cons(tree_to_scheme(e),
                            tree_to_scheme(tree))
        except StopIteration:
            return None
    elif hasattr(tree, '__iter__'): # is iterable
        return tree_to_scheme(iter(tree))
    elif tree is None:
        return None
    else:
        raise ValueError("Invalid parsed tree")

def string_to_scheme(input, start_parsing=PROGRAM):
    """
    Transforms a string or file input into a pair lisp's structure.
    """

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
    tokenizer = lexer.Tokenizer(SCHEME_LEX_RULES, start=START)

    #: The scheme parser
    parser = Parser(start=start_parsing)

    with parser as p:
        #: The scheme grammar for the parser
        SCHEME_GRAMMAR = {PROGRAM:             p.oneOrMore(p.expression(EXPRESSION)) &
                                               p.end(),

                          EXPRESSION:          p.expression(QUOTED_EXPRESSION) |
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

    parser.grammar = SCHEME_GRAMMAR

    # wraps input into a file-stream if it's a file object
    if input.__class__ in (codecs.StreamReaderWriter, file):
        input = FileStream(input)
    elif hasattr(input, 'iter'):
        raise ValueError("Invalid input object")

    return tree_to_scheme(parser.parse(tokenizer.tokens(input)))

def evaluate(input, environment=None):
    """
    evaluate a string or file object in the scheme evaluator as a program, and
    return the result as a scheme object.
    """
    environment = make_default_environment() if environment is None else environment
    expressions = string_to_scheme(input)

    for expression in expressions:
        result = full_evaluate(expression, environment)
    return result

def full_evaluate(expression, environment):
    """
    Fully evaluate an expression until its basic representation
    """

    while True:
        if is_thunk(expression):
            if not expression.is_evaluated:
                expression.is_evaluated = True
                expression.expression = full_evaluate(expression.expression,
                                                      expression.environment)
            return expression.expression
        elif is_symbol(expression):
            expression = environment[expression]
            continue
        elif (is_atom(expression) or is_nil(expression) or
              is_procedure(expression) or is_macro(expression) or
              callable(expression)):
            return expression
        elif car(expression) == 'delay':
            return Thunk(cadr(expression), environment)
        elif car(expression) == 'define':
            name = cadr(expression)
            environment[name] = Thunk(caddr(expression), environment)
            return name
        elif car(expression) == 'quote':
            return cadr(expression)
        elif car(expression) == 'eval':
            expression = full_evaluate(cadr(expression), environment)
            continue
        elif car(expression) == 'if':
            condition = full_evaluate(cadr(expression), environment)
            expression = caddr(expression) if condition else cadddr(expression)
            continue
        elif car(expression) == 'lambda':
            return Procedure(cadr(expression), # parameters
                             cddr(expression), # body (list of expressions)
                             environment)
        elif car(expression) == 'macro':
            return Macro( [(car(e), cadr(e)) for e in cddr(expression)], # rules
                          [] if not cadr(expression) else set(iter(cadr(expression))) ) # reserved words
        else:
            # application of procedure or macro
            operator = full_evaluate(car(expression), environment)
            unev_operands = cdr(expression)
            if is_macro(operator):
                expression = operator.transform(cons('_', unev_operands))
                continue
            else:
                if callable(operator):
                    # evaluate each operand recursively
                    operands = [full_evaluate(e, environment) for e in unev_operands] if unev_operands else []
                    # return the application of the built-in procedure
                    return operator(make_list(operands))
                elif is_procedure(operator):
                    # create Thunks (promisse to evaluate) for each operand
                    thunks = [Thunk(e, environment) for e in unev_operands] if unev_operands else []
                    proc_environment = Environment(parent=operator.environment)
                    # if the lambda parameters is not in the format ( () [. <symbol>] )
                    # for taking zero or more arguments
                    if len(operator.parameters) != 1 or not is_nil(operator.parameters[0]):
                        for name in operator.parameters:
                            try:
                                # take next argument
                                proc_environment[name] = thunks.pop(0)
                            except IndexError:
                                raise ValueError("Insuficient parameters for procedure %s. It should be at least %d" %
                                                 (operator, len(operator.parameters)))
                    if not is_nil(operator.optional):
                        proc_environment[operator.optional] = cons('quote', cons(make_list(thunks), None))
                    elif thunks:
                        raise ValueError("Too much parameters for procedure %s. It should be %d." %
                                         (operator, len(operator.parameters)))

                    # evaluate recursively only the inner procedure expressions
                    # (not the last)
                    current = operator.body
                    while cdr(current) is not None:
                        full_evaluate(car(current), proc_environment)
                        current = cdr(current)

                    environment = proc_environment
                    expression = car(current)
                    # continue not-recursively to evaluate the procedure's body
                    # in the extended environment
                    continue
                else:
                    raise ValueError("Not an operator: %s" % operator)

