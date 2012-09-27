#! /usr/bin/env python
# coding: utf-8

import os
import readline
import atexit

from evaluator import evaluate, string_to_scheme
from environment import make_default_environment
from cons import pretty_print

#: the built-in scheme forms
SCHEME_KEYWORDS = ('lambda', 'macro', 'if', 'quote', 'eval',)

if __name__ == "__main__":

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

