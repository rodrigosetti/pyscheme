#! /usr/bin/env python
# coding: utf-8

from evaluator import evaluate, string_to_scheme
from environment import make_default_environment
from cons import pretty_print

if __name__ == "__main__":

    environment = make_default_environment()
    while True:

        try:
            result = evaluate(unicode(raw_input("> "), 'utf-8'), environment)
            print "=>", pretty_print(result)
        except EOFError:
            print "\nexiting..."
            break
        except Exception as e:
            print "error:", e.message

