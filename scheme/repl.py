#! /usr/bin/env python
# coding: utf-8

from evaluator import evaluate, to_str, make_global_environment

if __name__ == "__main__":

    environment = make_global_environment()
    while True:

        try:
            print to_str(evaluate(raw_input("> "), environment))
        except EOFError:
            print "\nexiting..."
            break
        except Exception as e:
            print e.message

