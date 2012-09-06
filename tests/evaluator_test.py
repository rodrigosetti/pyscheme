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

        expected_structure = cons(('SYMBOL', 'a'),
                              cons(('SYMBOL', 'b'),
                               cons(('SYMBOL', 'c'),
                                cons(('SYMBOL', 'd'), None))))

        result = evaluator.string_to_scheme(string)

        self.compare_result(expected_structure, result)

    def test_dot_notation(self):

        string = "(a b c . d)"

        expected_structure = cons(('SYMBOL', 'a'),
                              cons(('SYMBOL', 'b'),
                               cons(('SYMBOL', 'c'), ('SYMBOL', 'd'))))

        result = evaluator.string_to_scheme(string)

        self.compare_result(expected_structure, result)

    def test_quote_notation(self):

        expected_structure = cons(('SYMBOL', 'quote'),
                              cons(
                               cons(('SYMBOL', 'a'),
                                cons(
                                 cons(('SYMBOL', 'quote'),
                                  cons(('SYMBOL', 'b'), None)),
                                   cons(('SYMBOL', 'c'), None))), None))

        string = "'(a 'b c)"

        result = evaluator.string_to_scheme(string)

        self.compare_result(expected_structure, result)

    def test_nil_value(self):

        # using nil
        result = evaluator.evaluate('nil')
        self.compare_result(None, result)

        # using the () notation
        result = evaluator.evaluate('()')
        self.compare_result(None, result)

        # using the (list) notation
        result = evaluator.evaluate('(list)')
        self.compare_result(None, result)

        # using the () notation
        result = evaluator.evaluate("(len ())")
        self.assertEquals(0, result.value)

        # using nil
        result = evaluator.evaluate("(len nil)")
        self.assertEquals(0, result.value)

        # using empty list
        result = evaluator.evaluate("(len (list ))")
        self.assertEquals(0, result.value)

        # using the () notation
        result = evaluator.evaluate("(nil? ())")
        self.assertEquals(True, result.value)

        # using nil
        result = evaluator.evaluate("(nil? nil)")
        self.assertEquals(True, result.value)

        # using empty list
        result = evaluator.evaluate("(nil? (list ))")
        self.assertEquals(True, result.value)


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

        # built-in procedure application
        result = evaluator.evaluate("(+ 1 2 3)")
        self.assertEquals(6, result.value)

        # let special form, environment
        result = evaluator.evaluate("(let ((x 10) (y 20)) (+ x y))")
        self.assertEquals(30, result.value)

        # creating and calling procedures
        result = evaluator.evaluate("(let ((inc (lambda (x) (+ x 1)))) (inc 40))")
        self.assertEquals(41, result.value)

        # if form
        result = evaluator.evaluate("(let ((inc (lambda (x) (+ x 1)))) (if (= (inc 40) 41) 3 4))")
        self.assertEquals(3, result.value)

        # quoting symbols
        result = evaluator.evaluate("(+ 'a 'b)")
        self.assertEquals('ab', result.value)

        # quoting lists
        result = evaluator.evaluate("(let ((x '(+ 1 2))) (car x))")
        self.assertEquals('+', result.value)

        # length of a list
        result = evaluator.evaluate("(let ((x '(+ 1 2))) (len x))")
        self.assertEquals(3, result.value)

        # using cdr
        result = evaluator.evaluate("(let ((x '(+ 1 2))) (len (cdr x)))")
        self.assertEquals(2, result.value)

        # using cons
        result = evaluator.evaluate("(let ((x (cons 1 2))) (car x))")
        self.assertEquals(1, result.value)

        # using cons
        result = evaluator.evaluate("(let ((x (cons 1 2))) (cdr x))")
        self.assertEquals(2, result.value)

        # variable arguments
        result = evaluator.evaluate("(let ((n-of-args (lambda (a . b) (+ (len b) a)))) (n-of-args 1 2 3 4 5))")
        self.assertEquals(5, result.value)

        # variable arguments as optional
        result = evaluator.evaluate("(let ((n-of-args (lambda (a . b) (+ (len b) a)))) (n-of-args 1))")
        self.assertEquals(1, result.value)

        # nested environments in let
        result = evaluator.evaluate("(let ((x 7) (y (let ((x 20)) (+ x 1)))) (+ x y))")
        self.assertEquals(28, result.value)

        # nested environments in lambdas
        result = evaluator.evaluate("(let ((x 100) (inc (lambda (x) (+ 1 x)))) (+ (inc 7) x))")
        self.assertEquals(108, result.value)

        # atom?
        result = evaluator.evaluate("(atom? 'x)")
        self.assertEquals(True, result.value)

        # atom?
        result = evaluator.evaluate("(atom? '(1 2 3 4 5))")
        self.assertEquals(False, result.value)

    def test_quicksort(self):

        string = """
            (let ((filter (lambda (f l)
                                  (if (nil? l)
                                      nil
                                      (if (f (car l))
                                          (cons (car l) (filter f (cdr l)))
                                          (filter f (cdr l))))))

                  (join (lambda (x y)
                                (if (nil? x)
                                    y
                                    (cons (car x) (join (cdr x) y)))))

                  (sort (lambda (l)
                                (if (nil? l)
                                    nil
                                    (let ((pivot (car l)))
                                         (join (sort (filter (lambda (e) (<= e pivot)) (cdr l)))
                                               (cons pivot
                                                     (sort (filter (lambda (e) (> e pivot)) (cdr l))))))))))

                 (sort (list 8 6 0 1 5 2 9 3 4 7)))
        """

        result = evaluator.evaluate(string)

        self.assertEquals(10, len(result))
        self.assertEquals([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [e.value for e in result])

    def test_tail_call_optimization(self):

        string = """
            (let ((inc-to-5000 (lambda ()
                                       (let ((iter (lambda (x)
                                                           (if (>= x 5000)
                                                                x
                                                                (iter (+ 1 x))))))
                                            (iter 1)))))
                 (inc-to-5000))
        """

        # without tail-call this should reach maximum recursion depth
        result = evaluator.evaluate(string)
        self.assertEquals(5000, result.value)

