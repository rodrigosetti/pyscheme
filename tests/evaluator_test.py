#! coding: utf-8

import unittest
from scheme.lexer import Token
import scheme.evaluator as evaluator
from scheme.evaluator import cons

class TestEvaluator(unittest.TestCase):

    def compare_result(self, expected, actual):
        if evaluator.is_pair(expected):
            self.assertTrue(evaluator.is_pair(actual))
            self.compare_result(expected.first, actual.first)
            self.compare_result(expected.second, actual.second)
        else:
            self.assertEquals(expected, actual)


    def test_cons_car_and_cdr(self):

        p = evaluator.cons('A', 'B')

        self.assertTrue(evaluator.is_pair(p))
        self.assertTrue('A', evaluator.car(p))
        self.assertTrue('B', evaluator.cdr(p))

    def test_string_to_scheme_simple_list(self):

        string = "(a b c d)"

        expected_structure = cons(
                              cons('a',
                               cons('b',
                                cons('c',
                                 cons('d', None)))), None)

        result = evaluator.string_to_scheme(string)

        self.compare_result(expected_structure, result)

    def test_string_to_scheme_two_expressions(self):

        string = "(a b c) (d e f)"

        expected_structure = cons(
                              cons('a',
                               cons('b',
                                cons('c', None))),
                               cons(
                                cons('d',
                                 cons('e',
                                  cons('f', None))), None))

        result = evaluator.string_to_scheme(string)

        self.compare_result(expected_structure, result)


    def test_dot_notation(self):

        string = "(a b c . d)"

        expected_structure = cons(
                              cons('a',
                                cons('b',
                                 cons('c', 'd'))), None)

        result = evaluator.string_to_scheme(string)

        self.compare_result(expected_structure, result)

    def test_quote_notation(self):

        expected_structure = cons(
                              cons('quote',
                               cons(
                                cons('a',
                                 cons(
                                  cons('quote',
                                   cons('b', None)),
                                    cons('c', None))), None)), None)

        string = "'(a 'b c)"

        result = evaluator.string_to_scheme(string)

        self.compare_result(expected_structure, result)


    def test_self_eval(self):

        result = evaluator.evaluate('10')
        self.compare_result(10, result)

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
        self.assertEquals(0, result)

        # using nil
        result = evaluator.evaluate("(len nil)")
        self.assertEquals(0, result)

        # using empty list
        result = evaluator.evaluate("(len (list ))")
        self.assertEquals(0, result)

        # using the () notation
        result = evaluator.evaluate("(nil? ())")
        self.assertEquals(True, result)

        # using nil
        result = evaluator.evaluate("(nil? nil)")
        self.assertEquals(True, result)

        # using empty list
        result = evaluator.evaluate("(nil? (list ))")
        self.assertEquals(True, result)


    def test_iterate_over_cons(self):

        expression = cons(1, cons(2, cons(3, cons(4, cons(5, 6)))))

        self.assertEquals([1,2,3,4,5], list(expression))
        self.assertEquals(6, expression.terminal())
        self.assertEquals(5, len(expression))

    def test_evaluate_expressions(self):

        # built-in procedure application
        result = evaluator.evaluate("(+ 1 2 3)")
        self.assertEquals(6, result)

        # define special forms, environment
        result = evaluator.evaluate("(define x 10) (define y 20) (+ x y)")
        self.assertEquals(30, result)

        # creating and calling procedures
        result = evaluator.evaluate("(let ((inc (lambda (x) (+ x 1)))) (inc 40))")
        self.assertEquals(41, result)

        # if form
        result = evaluator.evaluate("(define inc (lambda (x) (+ x 1))) (if (= (inc 40) 41) 3 4)")
        self.assertEquals(3, result)

        # quoting symbols
        result = evaluator.evaluate("(+ 'a 'b)")
        self.assertEquals('ab', result)

        # quoting lists
        result = evaluator.evaluate("(let ((x '(+ 1 2))) (car x))")
        self.assertEquals('+', result)

        # length of a list
        result = evaluator.evaluate("(define x '(+ 1 2)) (len x)")
        self.assertEquals(3, result)

        # using cdr
        result = evaluator.evaluate("(let ((x '(+ 1 2))) (len (cdr x)))")
        self.assertEquals(2, result)

        # using cons
        result = evaluator.evaluate("(define x (cons 1 2)) (car x)")
        self.assertEquals(1, result)

        # using cons
        result = evaluator.evaluate("(let ((x (cons 1 2))) (cdr x))")
        self.assertEquals(2, result)

        # variable arguments
        result = evaluator.evaluate("(define n-of-args (lambda (a . b) (+ (len b) 1))) (n-of-args 1 2 3 4 5)")
        self.assertEquals(5, result)

        # variable arguments as optional
        result = evaluator.evaluate("(let ((n-of-args (lambda (a . b) (+ (len b) 1)))) (n-of-args 1))")
        self.assertEquals(1, result)

        # zero or more arguments
        result = evaluator.evaluate("(define n-of-args (lambda (() . b) (len b))) (n-of-args 1 2 3 4 5)")
        self.assertEquals(5, result)

        # nested environments in let (using macro)
        result = evaluator.evaluate("(let ((x 7) (y (let ((x 20)) (+ x 1)))) (+ x y))")
        self.assertEquals(28, result)

        # nested environments in lambdas
        result = evaluator.evaluate("(define x 100) (define inc (lambda (x) (+ 1 x))) (+ (inc 7) x)")
        self.assertEquals(108, result)

        # atom?
        result = evaluator.evaluate("(atom? 'x)")
        self.assertEquals(True, result)

        # atom?
        result = evaluator.evaluate("(atom? '(1 2 3 4 5))")
        self.assertEquals(False, result)

    def test_quicksort(self):

        string = """
            (define filter
                    (lambda (f l)
                            (cond ((nil? l) nil)
                                  ((f (car l)) (cons (car l) (filter f (cdr l))))
                                  (else (filter f (cdr l))))))

             (define join
                     (lambda (x y)
                             (if (nil? x)
                                 y
                                 (cons (car x) (join (cdr x) y)))))

             (define sort
                     (lambda (l cmp)
                             (if (nil? l)
                                 nil
                                 (let ((pivot (car l)))
                                        (join (sort (filter (lambda (e) (not (cmp e pivot))) (cdr l)) cmp)
                                              (cons pivot
                                                    (sort (filter (lambda (e) (cmp e pivot)) (cdr l)) cmp)))))))

            ; This procedure is useful to evaluate all lazy values from the
            ; list, by using the full-evaluating form cons'
            (define eval-list
                    (lambda (l)
                            (if (nil? l)
                                nil
                                (cons' (car l) (eval-list (cdr l))))))

            (eval-list (sort (list 8 6 0 1 5 2 9 3 4 7) >))
        """

        result = evaluator.evaluate(string)

        self.assertEquals(10, len(result))
        self.assertEquals([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], list(iter(result)))

    def test_tail_call_optimization(self):

        string = """
            (define inc-to-5000
                    (lambda ()
                       (let ((iter (lambda (x)
                                           (if (>= x 5000)
                                               x
                                               (iter (+ 1 x))))))
                            (iter 1))))
            (inc-to-5000)
        """

        # without tail-call this should reach maximum recursion depth
        result = evaluator.evaluate(string)
        self.assertEquals(5000, result)

    def test_lazy_evaluation(self):

        string = """
            (define count
                    (lambda (n)
                            (cons n (count (+ n 1)))))

            (define take-n
                    (lambda (n l)
                            (if (= n 0)
                                nil
                                (cons (car l)
                                      (take-n (- n 1)
                                            (cdr l))))))

            ; This procedure is useful to evaluate all lazy values from the
            ; list, by using the full-evaluating form cons'
            (define eval-list
                    (lambda (l)
                            (if (nil? l)
                                nil
                                (cons' (car l) (eval-list (cdr l))))))

            (eval-list (take-n 40 (count 1)))
        """
        result = evaluator.evaluate(string)
        self.assertEquals(range(1,41), list(iter(result)))

        string = """
            (define f
                    (lambda (x y z)
                            (if x
                                y
                                z)))

            (f #f (/ 1 0) 30)
        """
        result = evaluator.evaluate(string)
        self.assertEquals(30, result)

