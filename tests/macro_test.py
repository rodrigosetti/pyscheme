#! /usr/bin/env python
#! coding: utf-8

import unittest

from scheme.evaluator import string_to_scheme as s
from scheme.evaluator import evaluate
from scheme.cons import *
from scheme.macro import *

class TestMacro(unittest.TestCase):

    def compare_result(self, expected, actual):
        if is_pair(expected):
            self.assertTrue(is_pair(actual))
            self.compare_result(car(expected), car(actual))
            self.compare_result(cdr(expected), cdr(actual))
        else:
            self.assertEquals(expected, actual)

    def test_simple_macros(self):

        # very simple macro
        macro = Macro([ (s('(_ x)'),
                         s('(set! x ())')), ])
        result = macro.transform(s('(nil! foo)'))
        self.compare_result(s('(set! foo ())'), result)

        # using ellipsis ...
        macro = Macro([ (s('(_ pred b1 ...)'),
                         s('(if pred (begin b1 ...))')), ])
        result = macro.transform(s('(when (> x y) A B C)'))
        self.compare_result(s('(if (> x y) (begin A B C))'), result)

        # macro of macro, no problem
        macro = Macro([ (s('(_ pred b1 ...)'),
                         s('(let loop () (when pred b1 ... (loop)))')), ])
        result = macro.transform(s('(while (< i 10) A B (set! i (+ i 1)))'))
        self.compare_result(s('(let loop () (when (< i 10) A B (set! i (+ i 1))))'), result)

        # little bit more complicated
        macro = Macro([ (s('(_ (i from to) b1 ...)'),
                         s('(let loop((i from)) (when (< i to)  b1 ... (loop (1+ i))))')), ])
        result = macro.transform(s('(for (i 0 10) (display i) (display " "))'))
        self.compare_result(s('(let loop((i 0)) (when (< i 10) (display i) (display " ")))'), result)

    def test_several_patterns(self):

        macro = Macro([ (s('(_ x)'),
                         s('(begin (set! x (+ x 1)) x)')),
                        (s('(_ x i)'),
                         s('(begin (set! x (+ x i)) x)')), ])
        result = macro.transform(s('(incf i)'))
        self.compare_result(s('(begin (set! i (+ i 1)) i)'), result)

        result = macro.transform(s('(incf j 3)'))
        self.compare_result(s('(begin (set! j (+ j 3)) j)'), result)

    def test_recursive_definition(self):

        # recursive transformation is not implemented in the macro itself, but
        # it's supposed to happen as the result expression is re-evaluated

        macro = Macro([ (s('(_)'),
                         s('#t')),
                        (s('(_ e)'),
                         s('e')),
                        (s('(_ e1 e2 ...)'),
                         s('(if e1 (my-and e2 ...) #f)')), ])
        result = macro.transform(s('(my-and)'))
        self.compare_result(s('#t'), result)

        result = macro.transform(s('(my-and x)'))
        self.compare_result(s('x'), result)

        result = macro.transform(s('(my-and x y)'))
        self.compare_result(s('(if x (my-and y) #f)'), result)

        result = macro.transform(s('(my-and x y z)'))
        self.compare_result(s('(if x (my-and y z) #f)'), result)

        # a useful macro: let
        macro = Macro([ (s('(_ ((n v)) e)'),
                         s('((lambda (n) e) v)')),
                        (s('(_ ((n v) ...) e)'),
                         s('(let (...) ((lambda (n) e) v))')), ])

        # we apply twice to get the full expanded form
        result = macro.transform(macro.transform(s('(let ((x a) (y (+ b c))) (display x y))')))
        self.compare_result(s('((lambda (y) ((lambda (x) (display x y)) a)) (+ b c))'),
                            result)

    def test_using_reseved_words(self):

        macro = Macro([ (s('(_ (else e1 ...))'),
                         s('(begin e1 ...)')),
                        (s('(_ (e1 e2 ...))'),
                         s('(when e1 e2 ...)')),
                        (s('(_ (e1 e2 ...1) c1 ...2)'),
                         s('(if e1 (begin e2 ...1) (cond c1 ...2))')), ],
                        reserved_words=['else'])

        result = macro.transform(s('(cond (else A B C))'))
        self.compare_result(s('(begin A B C)'), result)

        result = macro.transform(s('(cond (x A B C))'))
        self.compare_result(s('(when x A B C)'), result)

        result = macro.transform(s('(cond (x A B) (y C D) (z E F))'))
        self.compare_result(s('(if x (begin A B) (cond (y C D) (z E F)))'), result)



    def test_macro_usage(self):

        string = """
                ; define macro in the environment
                (define my-let (macro ()
                                      ((_ ((n v)) e)
                                       ((lambda (n) e) v))
                                      ((_ ((n v) ...) e)
                                       (my-let (...) ((lambda (n) e) v)))))

                ; now using the macro
                (my-let ((x 10) (y 20))
                         (+ x y))
        """
        result = evaluate(string)
        self.assertEquals(30, result)

if __name__ == '__main__':
    unittest.main()

