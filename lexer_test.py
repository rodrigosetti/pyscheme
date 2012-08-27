#! coding: utf-8

import unittest
import lexer

class TestLexer(unittest.TestCase):

    def test_lexer(self):

        rules = {'START': lexer.State([(r"\s", 'START'),
                                       (r";", 'COMMENT'),
                                       (r"'", 'QUOTE'),
                                       (r"\(", 'LPAREN'),
                                       (r"\)", 'RPAREN'),
                                       (r"\.", 'MAYBE-DOT'),
                                       (r"-", 'INTEGER-OR-SYMBOL'),
                                       (r"[0-9]", 'MAYBE-INTEGER'),
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
                 'MAYBE-FLOAT': lexer.State([(r"[0-9]", 'MAYBE-FLOAT'),
                                             (r"[^\(\)\s;]", 'SYMBOL')], token='FLOAT'),
                 'SYMBOL': lexer.State([(r"[^\(\)\s]", 'SYMBOL')], token='SYMBOL')}

        tokenizer = lexer.Tokenizer(rules, start='START')

        string = """
            ; definition of foo:
            (define foo (lambda (x . y)
                        (bar x y)))

            ; displaying something...
            (display '(foo -15
                            7
                            10.
                            20.5
                            .30))
        """
        expected_tokens = [('LPAREN', '('),
                           ('SYMBOL', 'define'),
                           ('SYMBOL', 'foo'),
                           ('LPAREN', '('),
                           ('SYMBOL', 'lambda'),
                           ('LPAREN', '('),
                           ('SYMBOL', 'x'),
                           ('DOT', '.'),
                           ('SYMBOL', 'y'),
                           ('RPAREN', ')'),
                           ('LPAREN', '('),
                           ('SYMBOL', 'bar'),
                           ('SYMBOL', 'x'),
                           ('SYMBOL', 'y'),
                           ('RPAREN', ')'),
                           ('RPAREN', ')'),
                           ('RPAREN', ')'),
                           ('LPAREN', '('),
                           ('SYMBOL', 'display'),
                           ('QUOTE', "'"),
                           ('LPAREN', '('),
                           ('SYMBOL', 'foo'),
                           ('INTEGER', '-15'),
                           ('INTEGER', '7'),
                           ('FLOAT', '10.'),
                           ('FLOAT', '20.5'),
                           ('FLOAT', '.30'),
                           ('RPAREN', ')'),
                           ('RPAREN', ')') ]

        tokens = list(tokenizer.parse(string))

        self.assertEquals(len(expected_tokens), len(tokens))

        for expected, token in zip(expected_tokens, tokens):
            self.assertEquals(expected, (token.type, token.value))

