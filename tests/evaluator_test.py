#! coding: utf-8

import unittest
from scheme.lexer import Token
import scheme.evaluator as evaluator
from scheme.evaluator import cons

class TestEvaluator(unittest.TestCase):

    def compare_result(self, expected, actual):
        if expected is None:
            self.assertEquals(None, actual)
        elif type(expected) == tuple:
            tok_type, tok_val = expected
            self.assertEquals(Token, type(actual))
            self.assertEquals(tok_type, actual.type)
            self.assertEquals(tok_val, actual.value)
        elif evaluator.is_pair(expected):
            self.assertTrue(evaluator.is_pair(actual))
            self.compare_result(expected.first, actual.first)
            self.compare_result(expected.second, actual.second)


    def test_cons_car_and_cdr(self):

        p = evaluator.cons('A', 'B')

        self.assertTrue(evaluator.is_pair(p))
        self.assertTrue('A', evaluator.car(p))
        self.assertTrue('B', evaluator.cdr(p))

    def test_string_to_scheme_simple_list(self):

        string = "(a b c d)"

        expected_structure = cons(
                              cons(('SYMBOL', 'a'),
                                cons(('SYMBOL', 'b'),
                                 cons(('SYMBOL', 'c'),
                                  cons(('SYMBOL', 'd'), None)))), None)

        result = evaluator.string_to_scheme(string)

        self.compare_result(expected_structure, result)

    def test_dot_notation(self):

        string = "(a b c . d)"

        expected_structure = cons(
                              cons(('SYMBOL', 'a'),
                                cons(('SYMBOL', 'b'),
                                 cons(('SYMBOL', 'c'), ('SYMBOL', 'd')))), None)

        result = evaluator.string_to_scheme(string)

        self.compare_result(expected_structure, result)

    def test_quote_notation(self):

        expected_structure = cons(
                              cons(('SYMBOL', 'quote'),
                               cons(
                                cons(('SYMBOL', 'a'),
                                 cons(
                                  cons(('SYMBOL', 'quote'),
                                   cons(('SYMBOL', 'b'), None)),
                                    cons(('SYMBOL', 'c'), None))), None)), None)

        string = "'(a 'b c)"

        result = evaluator.string_to_scheme(string)

        self.compare_result(expected_structure, result)

    def test_nil_value(self):

        result = evaluator.string_to_scheme('nil')
        self.compare_result(cons(None, None), result)

        result = evaluator.string_to_scheme('()')
        self.compare_result(cons(None, None), result)

