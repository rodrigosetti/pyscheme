#! /usr/bin/env python
# coding: utf-8

from evaluator import Evaluator
from environment import make_global_environment

if __name__ == "__main__":

    evaluator = Evaluator(make_global_environment())
    while True:

        try:
            print evaluator.evaluate_str(raw_input("> "))
        except EOFError:
            print "\nexiting..."
            break
        except Exception as e:
            print e.message

