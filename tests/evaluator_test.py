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

    def test_iterate_over_cons(self):

        expression = cons(1, cons(2, cons(3, cons(4, cons(5, 6)))))

        self.assertEquals([1,2,3,4,5], list(expression))
        self.assertEquals(6, expression.terminal())
        self.assertEquals(5, len(expression))
        self.assertEquals(1, expression[0])
        self.assertEquals(2, expression[1])
        self.assertEquals(3, expression[2])
        self.assertEquals(4, expression[3])
        self.assertEquals(5, expression[4])

    def test_evaluate_expressions(self):

        result = evaluator.evaluate("(+ 1 2 3)")
        self.assertEquals(6, result[0].value)

        result = evaluator.evaluate("(let ((x 10) (y 20)) (+ x y))")
        self.assertEquals(30, result[0].value)

        result = evaluator.evaluate("(let ((inc (lambda (x) (+ x 1)))) (inc 40))")
        self.assertEquals(41, result[0].value)

        result = evaluator.evaluate("(let ((inc (lambda (x) (+ x 1)))) (if (= (inc 40) 41) 3 4))")
        self.assertEquals(3, result[0].value)

        result = evaluator.evaluate("(+ 'a 'b)")
        self.assertEquals('ab', result[0].value)

        result = evaluator.evaluate("(let ((x '(+ 1 2))) (car x))")
        self.assertEquals('+', result[0].value)

        result = evaluator.evaluate("(let ((x '(+ 1 2))) (len x))")
        self.assertEquals(3, result[0].value)

        result = evaluator.evaluate("(let ((x '(+ 1 2))) (len (cdr x)))")
        self.assertEquals(2, result[0].value)

        result = evaluator.evaluate("(len ())")
        self.assertEquals(0, result[0].value)

        result = evaluator.evaluate("(len nil)")
        self.assertEquals(0, result[0].value)

