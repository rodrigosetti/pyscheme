# coding: utf-8

"""
Lexical Analyzer. Generates a list of Tokens from an input text, given a set of
rules
"""

import re

__all__ = ["State", "Tokenizer"]

class State(object):
    """
    Represents a state in the Tokenizer finite automata
    """

    def __init__(self, transitions=None, token=None, discard=False):
        """
        Creates a new state, with transition rules given by a list of tuples in
        the format (<regexp>, <next state>); a token name, if this state is
        final; and whether it discard matched chars in token buffer (default
        False)
        """
        # compile all regexp
        self.transitions = [(re.compile(key), value) for key,value in transitions] if transitions else []
        self.token=token
        self.discard=discard

    def match(self, char):
        """
        Try to match the char with any of the transition rules,
        return the next state name, or None, if none matches
        """
        for regexp, next_state in self.transitions:
            if regexp.match(char):
                return next_state
        return None

    def __repr__(self):
        return '<State "%s">' % self.token

class Token(object):
    """
    A representation of a Token.
    """

    def __init__(self, value, type='ANY', line=None, column=None):
        if type == 'STRING':
            self.value = eval(value)
        elif type == 'INTEGER':
            self.value = int(value)
        elif type == 'FLOAT':
            self.value = float(value)
        else:
            self.value = value

        self.type = type
        self.line = line
        self.column = column

    def __repr__(self):
        return '<Token %s "%s">' % (self.type, self.value)

class Tokenizer(object):
    """
    The finite state automata machine.
    """

    def __init__(self, states, start):
        """
        Creates a new tokenizer with the given states and the name of the
        initial state. States must be a dictionary of <state name>: <State
        object>
        """
        self.states = states
        self.start = self.states[start]

    def tokens(self, text):
        """
        Analizes the input text and returns a generator that one can iterate over
        the matched tokens. Raises a SyntaxError if the machine encouters an
        unexpected character.
        """
        current = self.start

        token_buffer = []
        line = 1
        column = 1

        for char in text:
            # while matching with the same char...
            while True:
                next_state = current.match(char)

                # if no next state matches
                if next_state is None:
                    # if current state is final
                    if current.token:
                        # yield the token accumulated in buffer and clear buffer
                        yield Token(''.join(token_buffer), current.token, line, column)
                        token_buffer = []

                        # restart automata
                        current = self.start

                        # matching this char again
                        consume = False
                    else:
                        # current token is not final, and char doesn't match!
                        raise SyntaxError('unexpected char at line: %d, column: %d: "%s"' % (line, column, char))
                else:
                    # goto next state and acumulated token buffer
                    current = self.states[next_state]
                    if not current.discard:
                        token_buffer.append(char)

                    # consume char - match next char
                    consume = True

                if consume:
                    break

            # count lines and columns
            if char == '\n':
                line += 1
                column = 1
            else:
                column += 1

        # try to recognize the last token, if there's buffer
        if token_buffer:
            if current.token:
                # yield the token accumulated in buffer
                yield Token(''.join(token_buffer), current.token, line, column)
            else:
                raise SyntaxError('unexpected end of stream line: %d, column: %d' % (line, column))

