# coding: utf-8

import operator
from lexer import Token
from parser import Element
import lexer, parser

__all__ = ["evaluate"]

#: Lex states constants enum
(START, COMMENT, QUOTE, LPAREN, RPAREN, MAYBE_DOT, INTEGER_OR_SYMBOL,
MAYBE_INTEGER, MAYBE_STRING, SCAPE_CHAR, STRING, MAYBE_FLOAT, SYMBOL,) = xrange(13)

#: Grammar non-terminal constants enum
EXPRESSION = 'expression'
QUOTED_EXPRESSION = "quoted-expression"
UNQUOTED_EXPRESSION = "unquoted-expression"
LIST = "list"
DOTED_EXPRESSION = 'doted-expression'
ATOM = 'atom'

#: reserved words are for special forms. they cannot name anything
RESERVED_WORDS = ('quote', 'if', 'let', 'lambda')

#: Rules for the scheme lexical analyzer
SCHEME_LEX_RULES = {START: lexer.State([(r"\s",   START),
                                        (r";",  COMMENT),
                                        (r"'",  QUOTE),
                                        (r"\(", LPAREN),
                                        (r"\)", RPAREN),
                                        (r"\.", MAYBE_DOT),
                                        (r"-",  INTEGER_OR_SYMBOL),
                                        (r"\d", MAYBE_INTEGER),
                                        (r'"',  MAYBE_STRING),
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
                    MAYBE_STRING: lexer.State([(r'[^"\\]', MAYBE_STRING),
                                                 (r'\\', SCAPE_CHAR),
                                                 (r'"', STRING)]),
                    SCAPE_CHAR: lexer.State([(r'.', MAYBE_STRING)]),
                    STRING: lexer.State(token='STRING'),
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
                                           p.token('FLOAT')   |
                                           p.token('STRING')}

SCHEME_PARSER.grammar = SCHEME_GRAMMAR

class Pair(object):
    """
    Implementation of the fundamental scheme data structure
    """

    def __init__(self, first, second):
        "Create a pair with values"
        self.first = first
        self.second = second

    def __repr__(self):
        return "(%s . %s)" % (str(self.first), str(self.second))

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

# predicates
is_atom = lambda x: type(x) == Token
is_symbol = lambda x: is_atom(x) and x.type == 'SYMBOL'
is_pair  = lambda x: type(x) == Pair

cons = lambda a,b: Pair(a,b)
car = lambda x: x.first
cdr = lambda x: x.second

def create_list(expressions):
    if len(expressions) == 0:
        return None
    else:
        return cons(expressions[0], create_list(expressions[1:]))

def tree_to_scheme(tree):
    "Transforms a parsed tree to scheme"

    if type(tree) == Element:
        if tree.name == ATOM:
            tok = tree.value[0].value
            if tok.type == 'SYMBOL' and tok.value == 'nil':
                return None
            else:
                return tok
        elif tree.name == QUOTED_EXPRESSION:
            return cons(Token('quote', 'SYMBOL'), cons(tree_to_scheme(tree.value[0]), None))
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
    else:
        raise ValueError("Invalid parsed tree")

def string_to_scheme(string):
    "Transforms a string input into a pair lisp's structure"
    global SCHEME_PARSER, SCHEME_TOKENIZER

    return tree_to_scheme(SCHEME_PARSER.parse(SCHEME_TOKENIZER.tokens(string)))

def evaluate(string):
    """
    Evaluate program string, returning a s-expression result
    """
    unevaluated_exprs = string_to_scheme(string)
    return [evaluate_sexpression(e, DEFAULT_ENVIRONMENT) for e in unevaluated_exprs]

class Procedure(object):

    def __init__(self, params_names, variable_param, expression, environment):
        self.params_names = params_names
        self.variable_param = variable_param
        self.expression = expression
        self.environment = environment

    def __call__(self, arguments):

        # create a sub-environment
        procedure_env = Environment(self.environment)

        cur_arg = arguments
        for name in self.params_names:
            if not is_pair(cur_arg):
                raise SyntaxError("Invalid number of arguments for procedure. should be at least %d" % len(self.params_names))

            # name unevaluated expression argument in procedure environment
            procedure_env[name] = cur_arg.first

            cur_arg = cur_arg.second

        # if there is a variable param name, name it to the rest of arguments
        if self.variable_param:
            procedure_env[self.variable_param] = cur_arg

        # evaluate procedure expression with the local environment populated
        # with parameters
        return evaluate_sexpression(self.expression, procedure_env)

class Environment(dict):
    """
    Hierarchical dictionary
    """

    def __init__(self, parent=None):
        self.parent = parent

    def __getitem__(self, x):
        try:
            return super(Environment, self).__getitem__(x)
        except KeyError as e:
            if self.parent:
                return self.parent[x]
            else:
                raise e

def evaluate_sexpression(expression, environment):

    if is_pair(expression):
        # evaluate head
        head = evaluate_sexpression(expression.first, environment)
        if type(head) == Token:
            if head.type == 'SYMBOL':
                if head.value == 'quote':
                    # return the quoted expression unevaluated
                    quoted = expression.second
                    if not is_pair(quoted) or len(quoted) != 1:
                        SyntaxError("quote expression should have two parts at line %d, column %d" % (head.line, head.column))

                    return quoted.first
                elif head.value == 'let':
                    # evaluate let expression:
                    # (let ( (<symbol> <expression>)* ) <expression>)
                    if len(expression) != 3:
                        raise SyntaxError("Let expression should have three parts at line %d, column %d" % (head.line, head.column))

                    # create an empty sub-environment, child of the current environment
                    sub_environment = Environment(environment)

                    for n, definition in enumerate(expression[1], 1):
                        if not is_pair(definition):
                            raise SyntaxError("The definition number %d of let expression is not a list. At line %d, column %d" % (n, head.line, head.column))
                        if len(definition) != 2:
                            raise SyntaxError("The definition number %d of let expression should have two parts. At line %d, column %d" % (n, head.line, head.column))
                        if not is_symbol(definition[0]):
                            raise SyntaxError("The first part of definition number %d of let expression should be a symbol. At line %d, column %d" % (n, head.line, head.column))

                        # name evaluated expression in current sub-environment
                        sub_environment[definition[0].value] = evaluate_sexpression(definition[1], sub_environment)

                    # finally, evaluate the let expression with the populated sub-environment
                    return evaluate_sexpression(expression[2], sub_environment)

                elif head.value == 'lambda':
                    # evalualte lambda expression
                    # (lambda ( <symbol>* ) <expression>)
                    if len(expression) != 3:
                        raise SyntaxError("Lambda expression should have three parts at line %d, column %d" % (head.line, head.column))

                    params = expression[1]
                    lambda_expr = expression[2]

                    if (not is_pair(params) or not all(is_symbol(e) for e in params)) and params is not None:
                        raise SyntaxError("Lambda parameters should be a list of symbols at line %d, column %d" % (head.line, head.column))

                    params_names = [e.value for e in params]
                    last = params.terminal()

                    if last is not None and not is_symbol(last):
                        raise SyntaxError("Variable parameter of lambda should be symbol at line %d, column %d" % (head.line, head.column))

                    variable_param = last.value if last is not None else None

                    # return a procedure with formal parameters name, an
                    # optional variable formal parameter; the expression and
                    # the current environment in which lambda was evaluated
                    return Procedure(params_names, variable_param, lambda_expr, environment)

                elif head.value == 'if':
                    # evaluate if expression
                    # (if <expression> <expression> <expression>)
                    if len(expression) != 4:
                        raise SyntaxError("If expression should have four parts at line %d, column %d" % (head.line, head.column))

                    condition = evaluate_sexpression(expression[1], environment)
                    if type(condition) != Token:
                        raise SyntaxError("Condition of if expression didn't evaluate to token at line %d, column %d" % (head.line, head.column))

                    # return the consequence or alternative depending on the thruth value of condition
                    return evaluate_sexpression(expression[2], environment) if condition.value else evaluate_sexpression(expression[3], environment)
                else:
                    raise SyntaxError("Could not call symbol head of s-expression at line %d, column %d" % (head.line, head.column))
            else:
                # head of s-expression is not a symbol (i.e. a number, string, etc.)
                raise SyntaxError("Could not call non-symbol head of s-expression at line %d, column %d" % (head.line, head.column))
        elif callable(head):
            # it's a procedure (evaluated from lambda) or a built-in

            # evaluate arguments before calling
            if is_pair(expression.second):
                arguments = create_list([evaluate_sexpression(e, environment) for e in expression.second])
            else:
                arguments = expression.second

            # call procedure with evaluated arguments
            return head(arguments)
        else:
            # head of s-expression is not an atom
            raise SyntaxError("Could not call non-atom head of s-expression at line %d, column %d" % (head.line, head.column))

    elif type(expression) == Token:
        # expression is atom

        if expression.type == 'SYMBOL':
            if expression.value not in RESERVED_WORDS:
                # read (and evaluate, if not) from environment

                try:
                    return environment[expression.value]
                except KeyError:
                    raise SyntaxError("Symbols %s is not defined in this environment, at line %d, column %d" %
                                      (expression.value, expression.line, expression.column))

        # return unevaluated token of the special form
        # or the numeric value
        return expression

    elif expression is None or callable(expression):
        # return the unevaluated procedure or None (nil)
        return expression
    else:
        # expression is not a token, pair, nil or procedure (???)
        raise ValueError("Invalid expression: %s" % expression)

# define the DEFAULT_ENVIRONMENT
DEFAULT_ENVIRONMENT = Environment()
DEFAULT_ENVIRONMENT.update({
    '+': lambda args:    Token(reduce(operator.add,  (e.value for e in args))),
    '-': lambda args:    Token(reduce(operator.sub,  (e.value for e in args))),
    '*': lambda args:    Token(reduce(operator.mul,  (e.value for e in args))),
    '/': lambda args:    Token(reduce(operator.div,  (e.value for e in args))),
    'mod': lambda args:  Token(reduce(operator.mod,  (e.value for e in args))),
    'or': lambda args:   Token(reduce(operator.or_,  (e.value for e in args)),  'BOOLEAN'),
    'and': lambda args:  Token(reduce(operator.and_, (e.value for e in args)),  'BOOLEAN'),
    'not': lambda args:  Token(reduce(operator.not_, (e.value for e in args)),  'BOOLEAN'),
    'eq?': lambda args:  Token(reduce(operator.eq,   (e.value for e in args)),  'BOOLEAN'),
    '=': lambda args:    Token(reduce(operator.eq,   (e.value for e in args)),  'BOOLEAN'),
    '<': lambda args:    Token(reduce(operator.lt,   (e.value for e in args)),  'BOOLEAN'),
    '>': lambda args:    Token(reduce(operator.gt,   (e.value for e in args)),  'BOOLEAN'),
    '<=': lambda args:   Token(reduce(operator.le,   (e.value for e in args)),  'BOOLEAN'),
    '>=': lambda args:   Token(reduce(operator.ge,   (e.value for e in args)),  'BOOLEAN'),
    'nil?': lambda args: Token(car(args) == None, 'BOOLEAN'),
    'atom?': lambda args: Token(is_atom(car(args)), 'BOOLEAN'),
    'len': lambda args:  Token(len(car(args)) if car(args) is not None else 0, 'INTEGER'),
    'list': lambda args: args,
    'cons': lambda args: cons(car(args), car(cdr(args))),
    'car': lambda args:  car(car(args)),
    'cdr': lambda args:  cdr(car(args))})

