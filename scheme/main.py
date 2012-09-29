#! /usr/bin/env python
# coding: utf-8

import atexit
import codecs
import os
import readline
import re
import sys

from cons import pretty_print, quote
from environment import make_global_environment
from evaluator import evaluate, evaluate_expression

def identation_position(text):
    """
    Returns the number of space characters to indent in the next line, if
    the expression in text is given in the previous line.
    """
    # The identation position is right under the beginning of the last expression

    # iterate over text from end to begining
    for i in xrange(len(text)-1, -1, -1):
        # find the first non-whitespace char
        if not re.match('[\s(]', text[i]):
            if text[i] == ')':
                # expression: find the beginning of this expression
                nesting = 1
                for j in xrange(i-1, -1, -1):
                    if text[j] == '(':
                        nesting -= 1
                        if nesting == 0:
                            return j
                    elif text[j] == ')':
                        nesting += 1
            else:
                # symbol: find the beginning of this symbol
                for j in xrange(i-1, -1, -1):
                    if re.match('[\s(]', text[j]):
                        return j+1
    return 0

class InterpreterInput(object):
    """
    Gets more raw_input while characters are needed by the parser
    """

    def __init__(self, input_text=''):
        self.input_text = input_text
        self.input_buffer = list(input_text) + ['\n']

    def __iter__(self):
        if self.input_text:
            self.prompt = '... ' + (' ' * identation_position(self.input_text))
        else:
            self.prompt = '>> '
        return self

    def next(self):
        if self.input_buffer:
            return self.input_buffer.pop(0)
        else:
            identation = ' ' * identation_position(self.input_text)
            self.prompt = '... ' + identation

            self.input_text = identation + unicode(raw_input(self.prompt), 'utf-8')
            self.input_buffer = list(self.input_text)

            if not self.input_buffer:
                raise StopIteration()

            self.input_buffer.append('\n')
            return next(self)

def repl():
    #: the built-in scheme forms and special repl commands
    KEYWORDS = ('lambda', 'macro', 'if', 'quote', 'eval', 'define', 'delay',
                '.reset', '.exit', '.quit', '.help')

    # the scheme auto-completer
    def completer(text, state):
        # look through SCHEME_KEYWORDS
        for w in KEYWORDS:
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
    readline.parse_and_bind("set blink-matching-paren on")
    readline.set_completer(completer)

    environment = make_global_environment()
    while True:

        try:
            text = raw_input(">>  ")

            # test for special commands
            if text == '.reset':
                print "reseting environment..."
                environment = make_global_environment()
                continue
            elif text == '.help':
                print "Just type scheme expression and have fun."
                continue
            elif text in ('.exit', '.quit'):
                break

            result = evaluate_expression(InterpreterInput(text),
                                         environment)

            print "=>", pretty_print(result)

            # set % as the last evaluated expression in environment
            environment['%'] = quote(result)
        except EOFError:
            break
        except KeyboardInterrupt:
            print "\ninterrupt."
        except Exception as e:
            print "error:", e.message

    print "\nexiting..."

if __name__ == "__main__":
    if len(sys.argv) == 1:
        repl()
    elif len(sys.argv) == 2:
        with codecs.open(sys.argv[1], 'r', 'utf-8') as f:
            evaluate(f,make_minimum_environment())
    else:
        sys.stderr.write("Usage: %s [FILE]\nif FILE is not provided, scheme runs in eval-print-loop mode.\n" %
                         sys.argv[0])
        sys.exit(1)

