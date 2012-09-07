# coding: utf-8

import operator
from lexer import Token
from parser import Element
import lexer, parser

__all__ = ["evaluate", "to_str"]

#: Lex states constants enum
(START, COMMENT, QUOTE, LPAREN, RPAREN, MAYBE_DOT, INTEGER_OR_SYMBOL,
MAYBE_INTEGER, MAYBE_STRING, SCAPE_CHAR, STRING, MAYBE_FLOAT, SYMBOL,) = xrange(13)

#: Grammar non-terminal constants enum
(EXPRESSION, QUOTED_EXPRESSION, UNQUOTED_EXPRESSION,
 LIST, DOTED_EXPRESSION, ATOM,) = xrange(6)

#: reserved words are for special forms. they cannot name anything
RESERVED_WORDS = ('quote', 'if', 'let', 'lambda', 'define')

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
                    STRING: lexer.State(token='SYMBOL'),
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
is_atom = lambda x: x is None or type(x) == Token
is_symbol = lambda x: x is not None and is_atom(x) and x.type == 'SYMBOL'
is_pair  = lambda x: type(x) == Pair

cons = lambda a,b: Pair(a,b)
car = lambda x: x.first
cdr = lambda x: x.second

class SymbolData(object):
    """
    Represent a piece of information associated to a symbol in the environment
    """
    def __init__(self, expression, environment, is_evaluated=False):
        self.expression = expression
        self.environment = environment
        self.is_evaluated = is_evaluated

    def evaluate(self):
        self.expression = evaluate_sexpression(self.expression, self.environment)
        self.is_evaluated = True
        return self

class Environment(dict):
    """
    Hierarchical dictionary
    """

    def __init__(self, parent=None):
        self.parent = parent

    def add(self, name, expression, environment=None, is_evaluated=False):
        """
        Adds an expression and the environment it's supposed to be
        evaluated
        """
        if name in self:
            raise RuntimeError("Symbol %s already defined in environment" % name)
        super(Environment, self).__setitem__(name, SymbolData(expression, environment, is_evaluated))

    def __setitem__(self, *args):
        raise ValueError("Please use .add method to add stuff to environment")

    def __getitem__(self, name):
        """
        Get expression evaluated from the hierarchy
        """
        try:
            symbol_data = super(Environment, self).__getitem__(name)
            if type(symbol_data) == SymbolData:
                if not symbol_data.is_evaluated:
                    super(Environment, self).__setitem__(name, symbol_data.evaluate())
                return symbol_data.expression
            else:
                return symbol_data
        except KeyError as e:
            if self.parent is not None:
                return self.parent[name]
            else:
                raise e

def create_list(expressions):
    if len(expressions) == 0:
        return None
    else:
        return cons(expressions[0], create_list(expressions[1:]))

def tree_to_scheme(tree):
    "Transforms a parsed tree to scheme"

    if type(tree) == Element:
        if tree.name == ATOM:
            return tree.value[0].value
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
    elif tree is None:
        return None
    else:
        raise ValueError("Invalid parsed tree")

def string_to_scheme(string):
    "Transforms a string input into a pair lisp's structure"
    global SCHEME_PARSER, SCHEME_TOKENIZER

    return tree_to_scheme(SCHEME_PARSER.parse(SCHEME_TOKENIZER.tokens(string)))

def to_str(expression):
    "Trasforms a s-expression into a string"
    if expression is None:
        return 'nil'
    elif is_atom(expression):
        if expression.type == 'BOOLEAN':
            return '#t' if expression.value else '#f'
        else:
            return str(expression.value)
    elif callable(expression):
        return "<procedure>"
    elif is_pair(expression):
        s = "(" + ' '.join([to_str(e) for e in expression])
        t = expression.terminal()
        if t is not None:
            s += " . %s" % to_str(t)
        return s + ")"
    else:
        raise ValueError("Invalid expression: %s" % expression)

def evaluate(string, environment=None):
    """
    Evaluate program string, returning a s-expression result
    """
    if environment is None:
        environment = make_global_environment()

    return evaluate_sexpression(string_to_scheme(string), environment)

class TailCall(Exception):

    def __init__(self, arguments, caller_environment):
        super(TailCall, self).__init__()
        self.arguments = arguments
        self.caller_environment = caller_environment

class Procedure(object):

    def __init__(self, params_names, variable_param, expression, environment):
        self.params_names = params_names
        self.variable_param = variable_param
        self.expression = expression
        self.environment = environment

    def __call__(self, arguments, caller_environment):

        while True:
            # create a sub-environment
            procedure_env = Environment(self.environment)

            cur_arg = arguments
            for name in self.params_names:
                if not is_pair(cur_arg):
                    raise RuntimeError("Too few arguments for procedure. should be at least %d" %
                                        len(self.params_names))

                # name unevaluated expression argument in procedure environment
                procedure_env.add(name, cur_arg.first, caller_environment)

                cur_arg = cur_arg.second

            # if there is a variable param name, name it to the rest of arguments
            if self.variable_param:
                variable = cons(lambda args,env: args, cur_arg)
                procedure_env.add(self.variable_param, variable, caller_environment)
            elif cur_arg is not None:
                # there's no variable params and there still arguments (too much arguments)
                raise RuntimeError("Too much arguments for procedure. should be %d" %
                                   len(self.params_names))

            # evaluate procedure expression with the local environment populated
            # with parameters
            try:
                return evaluate_sexpression(self.expression, procedure_env, procedure_context=self)
            except TailCall as t:
                arguments = t.arguments
                caller_environment = t.caller_environment
                continue

            break

def evaluate_sexpression(expression, environment, procedure_context=None):

    if is_pair(expression):

        # evaluate head
        head = expression.first
        if not is_atom(head) or head.value not in RESERVED_WORDS:
            head = evaluate_sexpression(head, environment)

        if is_atom(head):
            if is_symbol(head):
                if head.value == 'quote':
                    # return the quoted expression unevaluated
                    quoted = expression.second
                    if not is_pair(quoted) or len(quoted) != 1:
                        SyntaxError("quote form should have one part %s" %
                                    head.location_str())

                    return quoted.first
                elif head.value == 'define':
                    # this is mostly to be used in REPL
                    # (define <symbol> <expression>)
                    if len(expression) != 3:
                        raise SyntaxError("Define form should have two parts %s" %
                                          head.location_str())
                    if not is_symbol(expression[1]):
                        raise SyntaxError("The first part of define form should be a symbol %s" %
                                          head.location_str())

                    environment.add(expression[1].value, expression[2], environment)
                    return expression[1]
                elif head.value == 'let':
                    # evaluate let expression:
                    # (let ( (<symbol> <expression>)* ) <expression>)
                    if len(expression) != 3:
                        raise SyntaxError("Let form should have three parts %s" %
                                          head.location_str())

                    # create an empty sub-environment, child of the current environment
                    sub_environment = Environment(environment)

                    for n, definition in enumerate(expression[1], 1):
                        if not is_pair(definition):
                            raise SyntaxError("The definition number %d of let form is not a list %s" %
                                              (n, head.location_str()))
                        if len(definition) != 2:
                            raise SyntaxError("The definition number %d of let form should have two parts %s" %
                                              (n, head.location_str()))
                        if not is_symbol(definition[0]):
                            raise SyntaxError("The first part of definition number %d of let form should be a symbol %s" %
                                              (n, head.location_str()))

                        # name evaluated expression in current sub-environment
                        sub_environment.add(definition[0].value, definition[1], sub_environment)

                    # finally, evaluate the let expression with the populated sub-environment
                    return evaluate_sexpression(expression[2], sub_environment, procedure_context)

                elif head.value == 'lambda':
                    # evalualte lambda expression
                    # (lambda ( <symbol>* ) <expression>)
                    if len(expression) != 3:
                        raise SyntaxError("Lambda form should have two parts %s" %
                                          head.location_str())

                    params = expression[1]
                    lambda_expr = expression[2]

                    if (not is_pair(params) or not all(is_symbol(e) for e in params)) and params is not None:
                        raise SyntaxError("Lambda parameters should be a list of symbols %s" %
                                          head.location_str())

                    if params is not None:
                        params_names = [e.value for e in params]
                        last = params.terminal()
                    else:
                        params_names = []
                        last = None

                    if last is not None and not is_symbol(last):
                        raise SyntaxError("Variable parameter of lambda should be symbol %s" %
                                          head.location_str())

                    variable_param = last.value if last is not None else None

                    # return a procedure with formal parameters name, an
                    # optional variable formal parameter; the expression and
                    # the current environment in which lambda was evaluated
                    return Procedure(params_names, variable_param, lambda_expr, environment)

                elif head.value == 'if':
                    # evaluate if expression
                    # (if <expression> <expression> <expression>)
                    if len(expression) != 4:
                        raise SyntaxError("If form should have three parts %s" %
                                          head.location_str())

                    condition = evaluate_sexpression(expression[1], environment)
                    if type(condition) != Token:
                        raise RuntimeError("Condition of if form didn't evaluate to token %s" %
                                           head.location_str())

                    # return the consequence or alternative depending on the thruth value of condition
                    if condition.value:
                        return evaluate_sexpression(expression[2], environment, procedure_context)
                    else:
                        return evaluate_sexpression(expression[3], environment, procedure_context)
                else:
                    raise RuntimeError('Symbolic value "%s" is not a procedure, line %d, column %d' %
                                       (to_str(head), head.line, head.column))
            else:
                # head of s-expression is not a symbol (i.e. a number, etc.)
                raise SyntaxError('Non-symbolic value "%s" is not a procedure %s' %
                                  (to_str(head), head.location_str()))
        elif callable(head):
            # it's a procedure (evaluated from lambda) or a built-in

            arguments = expression.second

            # call procedure with evaluated arguments
            if head == procedure_context:
                # tail call
                raise TailCall(arguments, environment)

            return head(arguments, environment)
        else:
            # head of s-expression is not an atom
            raise RuntimeError('Non-atom "%s" is not a procedure.' % to_str(head))

    elif is_atom(expression):
        # expression is atom

        if is_symbol(expression):

            try:
                return environment[expression.value]
            except KeyError:
                raise SyntaxError('Unbound symbol "%s" at current environment %s' %
                                  (expression.value, expression.location_str()))

        # return unevaluated token of numeric or None value
        return expression

    elif callable(expression):
        # return the unevaluated procedure
        return expression
    else:
        # expression is not a token, pair, nil or procedure (???)
        raise ValueError("Invalid expression: %s" % expression)

def evaluate_args(procedure):
    "evaluate arguments decorator"

    def eval_arg_procedure(arguments, environment):
        if is_pair(arguments):
            arguments = create_list([evaluate_sexpression(e, environment) for e in arguments])
        else:
            arguments = evaluate_sexpression(arguments, environment)

        return procedure(arguments, environment)

    return eval_arg_procedure

def min_args(n, procedure):
    "check for a minimum number of arguments"

    def decorated(arguments, environment):
        if len(arguments) < n:
            raise RuntimeError("procedure should have at least %d arguments" % n)
        return procedure(arguments, environment)

    return procedure

def fix_args(n, procedure):
    "check for a fixed number of arguments"

    def decorated(arguments, environment):
        if len(arguments) != n:
            raise RuntimeError("procedure should have %d arguments" % n)
        return procedure(arguments, environment)

    return procedure

def make_global_environment():
    """
    Return the default global environment, with built-in procedures and values
    """
    environment = Environment()
    environment.update({
        'nil':   None,
        '#t':    Token(True, 'BOOLEAN'),
        '#f':    Token(False, 'BOOLEAN'),
        '+':     min_args(2, evaluate_args(lambda args, env: Token(reduce(operator.add, (e.value for e in args))))),
        '-':     min_args(2, evaluate_args(lambda args, env: Token(reduce(operator.sub, (e.value for e in args))))),
        '*':     min_args(2, evaluate_args(lambda args, env: Token(reduce(operator.mul, (e.value for e in args))))),
        '/':     min_args(2, evaluate_args(lambda args, env: Token(reduce(operator.div, (e.value for e in args))))),
        'not':   fix_args(1, evaluate_args(lambda args, env: Token(not args[0].value, 'BOOLEAN'))),
        'mod':   fix_args(2, evaluate_args(lambda args, env: Token(reduce(operator.mod,  (e.value for e in args))))),
        'eq?':   fix_args(2, evaluate_args(lambda args, env: Token(args[0].value is args[1].value,  'BOOLEAN'))),
        '=':     fix_args(2, evaluate_args(lambda args, env: Token(args[0].value == args[1].value,  'BOOLEAN'))),
        '<':     fix_args(2, evaluate_args(lambda args, env: Token(args[0].value <  args[1].value,  'BOOLEAN'))),
        '>':     fix_args(2, evaluate_args(lambda args, env: Token(args[0].value >  args[1].value,  'BOOLEAN'))),
        '<=':    fix_args(2, evaluate_args(lambda args, env: Token(args[0].value <= args[1].value,  'BOOLEAN'))),
        '>=':    fix_args(2, evaluate_args(lambda args, env: Token(args[0].value >= args[1].value,  'BOOLEAN'))),
        'and':   min_args(2, evaluate_args(lambda args, env: Token(all(e.value for e in args),  'BOOLEAN'))),
        'or':    min_args(2, lambda args, env: Token(any(bool(evaluate_sexpression(e, env)) for e in args),  'BOOLEAN')),
        'nil?':  fix_args(1, evaluate_args(lambda args, env: Token(car(args) == None,  'BOOLEAN'))),
        'atom?': fix_args(1, evaluate_args(lambda args, env: Token(is_atom(car(args)), 'BOOLEAN'))),
        'len':   fix_args(1, evaluate_args(lambda args, env: Token(len(car(args)) if car(args) is not None else 0, 'INTEGER'))),
        'car':   fix_args(1, evaluate_args(lambda args, env: car(car(args)))),
        'cdr':   fix_args(1, evaluate_args(lambda args, env: cdr(car(args)))),
        'cons':  fix_args(2, evaluate_args(lambda args, env: cons(car(args), car(cdr(args))))),
        'eval':  lambda args, env: evaluate_sexpression(args, env),
        'list':  evaluate_args(lambda args, env: args),
    })
    return environment

