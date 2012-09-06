#! /usr/bin/env python
# coding: utf-8

from evaluator import evaluate, to_str, DEFAULT_ENVIRONMENT

if __name__ == "__main__":

    environment = DEFAULT_ENVIRONMENT
    while True:

        try:
            print to_str(evaluate(raw_input("> "), environment))
        except EOFError:
            print "\nexiting..."
            break
        except SyntaxError as e:
            print e.message

