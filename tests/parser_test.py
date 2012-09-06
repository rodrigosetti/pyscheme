#! coding: utf-8

import unittest
import scheme.lexer as lexer
import scheme.parser as parser

class TestParser(unittest.TestCase):

    def setUp(self):

        lex_rules = {'START': lexer.State([(r"\s", 'START'),
                                           (r";", 'COMMENT'),
                                           (r"'", 'QUOTE'),
                                           (r"\(", 'LPAREN'),
                                           (r"\)", 'RPAREN'),
                                           (r"\.", 'MAYBE-DOT'),
                                           (r"-", 'INTEGER-OR-SYMBOL'),
                                           (r"[0-9]", 'MAYBE-INTEGER'),
                                           (r'"', 'MAYBE-STRING'),
                                           (r"[^\(\)\s;]", 'SYMBOL')], discard=True),
                     'COMMENT': lexer.State([(r"\n", 'START'),
                                             (r".", 'COMMENT')], discard=True),
                     'QUOTE': lexer.State(token='QUOTE'),
                     'LPAREN': lexer.State(token='LPAREN'),
                     'RPAREN': lexer.State(token='RPAREN'),
                     'MAYBE-DOT': lexer.State([(r"[0-9]", 'MAYBE-FLOAT'),
                                               (r"[^\(\)\s;]", 'SYMBOL')], token='DOT'),
                     'INTEGER-OR-SYMBOL': lexer.State([(r"[0-9]", 'MAYBE-INTEGER'),
                                                       (r"[^\(\)\s;]", 'SYMBOL')], token='SYMBOL'),
                     'MAYBE-INTEGER': lexer.State([(r"[0-9]", 'MAYBE-INTEGER'),
                                                   (r"\.", 'MAYBE-FLOAT'),
                                                   (r"[^\(\)\s;]", 'SYMBOL')], token='INTEGER'),
                     'MAYBE-STRING': lexer.State([(r'[^"\\]', 'MAYBE-STRING'),
                                                  (r'\\', 'SCAPE-CHAR'),
                                                  (r'"', 'STRING')]),
                     'SCAPE-CHAR': lexer.State([(r'.', 'MAYBE-STRING')]),
                     'STRING': lexer.State(token='STRING'),
                     'MAYBE-FLOAT': lexer.State([(r"[0-9]", 'MAYBE-FLOAT'),
                                                 (r"[^\(\)\s;]", 'SYMBOL')], token='FLOAT'),
                     'SYMBOL': lexer.State([(r"[^\(\)\s;]", 'SYMBOL')], token='SYMBOL')}

        self.tokenizer = lexer.Tokenizer(lex_rules, start='START')

        p = parser.Parser(start='expression')

        grammar = {'expression': ~p.token('QUOTE') &
                                 (p.expression('atom') |
                                  (p.token('LPAREN') &
                                   p.zeroOrMore(~p.token('DOT') &
                                                     p.expression('expression')) &
                                   p.token('RPAREN'))),
                   'atom': p.token('SYMBOL')  |
                           p.token('INTEGER') |
                           p.token('FLOAT')   |
                           p.token('STRING')}

        p.grammar = grammar
        self.parser = p

    def test_parse(self):

        string = """
            (let
                ; definition of foo:
                ((foo (lambda (x . y)
                            (bar x y "hello")))) ;bar is something I made up ;

                ; displaying something...
                (display '(foo -15
                                7
                                10.
                                20.5
                                .30)))
        """
        expected_tree = [{'expression': [("LPAREN", "("),
                                         {'expression': [{'atom': [("SYMBOL", "let")]}]},
                                         {'expression': [("LPAREN", "("),
                                                         {'expression': [("LPAREN", "("),
                                                                         {'expression': [{'atom': [("SYMBOL", "foo")]}]},
                                                                         {'expression': [("LPAREN", "("),
                                                                                         {'expression': [{'atom': [("SYMBOL", "lambda")]}]},
                                                                                         {'expression': [("LPAREN", "("),
                                                                                                         {'expression': [{'atom': [("SYMBOL", "x")]}]},
                                                                                                         ("DOT", "."),
                                                                                                         {'expression': [{'atom': [("SYMBOL", "y")]}]},
                                                                                                         ("RPAREN", ")")]},
                                                                                         {'expression': [("LPAREN", "("),
                                                                                                         {'expression': [{'atom': [("SYMBOL", "bar")]}]},
                                                                                                         {'expression': [{'atom': [("SYMBOL", "x")]}]},
                                                                                                         {'expression': [{'atom': [("SYMBOL", "y")]}]},
                                                                                                         {'expression': [{'atom': [("STRING", "hello")]}]},
                                                                                                         ("RPAREN", ")")]},
                                                                                         ("RPAREN", ")")]},
                                                                         ("RPAREN", ")")]},
                                                         ("RPAREN", ")")]},
                                         {'expression': [("LPAREN", "("),
                                                         {'expression': [{'atom': [("SYMBOL", "display")]}]},
                                                         {'expression': [("QUOTE", "'"),
                                                                         ("LPAREN", "("),
                                                                         {'expression': [{'atom': [("SYMBOL", "foo")]}]},
                                                                         {'expression': [{'atom': [("INTEGER", -15)]}]},
                                                                         {'expression': [{'atom': [("INTEGER", 7)]}]},
                                                                         {'expression': [{'atom': [("FLOAT", 10.)]}]},
                                                                         {'expression': [{'atom': [("FLOAT", 20.5)]}]},
                                                                         {'expression': [{'atom': [("FLOAT", .3)]}]},
                                                                         ("RPAREN", ")")]},
                                                         ("RPAREN", ")")]},
                                         ("RPAREN", ")")]}]

        tree = self.parser.parse(self.tokenizer.tokens(string))

        def compare(expected, actual):
            if type(expected) == dict:
                name, sub_expected = expected.items()[0]

                self.assertFalse(actual.is_terminal)
                self.assertEquals(name, actual.name)
                self.assertEquals(len(sub_expected), len(actual.value))

                compare(sub_expected, actual.value)
            elif type(expected) == list:
                self.assertEquals(len(expected), len(actual))

                for exp, act in zip(expected, actual):
                    compare(exp, act)
            else:
                tok_type, tok_value = expected

                self.assertTrue(actual.is_terminal)
                self.assertEquals(tok_type, actual.name)
                self.assertEquals(tok_type, actual.value.type)
                self.assertEquals(tok_value, actual.value.value)

        compare(expected_tree, tree)

    def test_parse_error(self):

        try:
            self.parser.parse(self.tokenizer.tokens("(add foo bar"))
        except SyntaxError as s:
            self.assertEquals("Unexpected end of input. Expecting RPAREN", s.message)

        try:
            self.parser.parse(self.tokenizer.tokens("(add foo bar))"))
        except SyntaxError as s:
            self.assertEquals("Unexpected ) at line 1, column 15. Expecting end of tokens", s.message)

