# coding: utf-8

from parser import Element
from lexer import Token
import lexer, parser

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

is_pair  = lambda x: type(x) == Pair
cons = lambda a,b: Pair(a,b)
car = lambda x: x.first
cdr = lambda x: x.second

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

