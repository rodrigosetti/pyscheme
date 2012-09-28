#! /usr/bin/env python
# coding: utf-8

import atexit
import os
import readline
import sys

from evaluator import evaluate
from environment import make_default_environment
from cons import pretty_print

def repl():
    #: the built-in scheme forms
    SCHEME_KEYWORDS = ('lambda', 'macro', 'if', 'quote', 'eval', 'define', 'delay')

    # the scheme auto-completer
    def completer(text, state):
        # look through SCHEME_KEYWORDS
        for w in SCHEME_KEYWORDS:
            if w.startswith(text):
                if state <= 0:
                    return w
                state -= 1

        # look through the environment names
        for w in environment.iterkeys():
            if w.startswith(text):
                if state <= 0:
                    return w
                state -= 1

    histfile = os.path.join(os.path.expanduser("~"), ".pyscheme-hist")
    try:
        readline.read_history_file(histfile)
    except IOError:
        pass
    atexit.register(readline.write_history_file, histfile)

    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer)

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

if __name__ == "__main__":
    if len(sys.argv) == 1:
        repl()
    elif len(sys.argv) == 2:
        with open(sys.argv[1]) as f:
            evaluate(unicode(f.read(), 'utf-8'))
    else:
        sys.stderr.write("Usage: %s [FILE]\nif FILE is not provided, scheme runs in eval-print-loop mode.\n" %
                         sys.argv[0])
        sys.exit(1)

