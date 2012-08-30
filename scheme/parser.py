#coding: utf-8

from buffer import Buffer
import lexer

__all__ = ["Parser"]

class Expression(object):

    def __init__(self, name, parser):
        self.name = name
        self.parser = parser

    def __or__(self, other):
        return Or(self, other)

    def __and__(self, other):
        return And(self, other)

    def __invert__(self):
        return Optional(self)

    def match(self, tokens, mandatory=False):
        result = self.parser.grammar[self.name].match(tokens, mandatory)
        return Result(True, [Element(result.tree, self.name)]) if result.matches else Result(False)

    def __repr__(self):
        return self.name

class Optional(Expression):

    def __init__(self, expression):
        self.expression = expression

    def match(self, tokens, mandatory=False):
        result = self.expression.match(tokens, False)
        return result if result.matches else Result(True)

    def __repr__(self):
        return '~%s' % self.expression

class Or(Expression):

    def __init__(self, *expressions):
        self.expressions = expressions

    def match(self, tokens, mandatory=False):
        for n, expression in enumerate(self.expressions, 1):
            result = expression.match(tokens, n == len(self.expressions) and mandatory)
            if result.matches:
                return result
        return Result(False)

    def __or__(self, other):
        return Or(*(self.expressions + (other,)))

    def __repr__(self):
        return '(%s)' % ' | '.join([str(e) for e in self.expressions])

class And(Expression):

    def __init__(self, *expressions):
        self.expressions = expressions

    def match(self, tokens, mandatory=False):
        matches = []

        with tokens.mark() as m_tokens:
            for expression in self.expressions:
                result = expression.match(m_tokens, mandatory)
                if result.matches:
                    matches.extend(result.tree)
                else:
                    tokens.restore()
                    return Result(False)

        return Result(True, matches)

    def __and__(self, other):
        return And(*(self.expressions + (other,)))

    def __repr__(self):
        return '(%s)' % ' & '.join([str(e) for e in self.expressions])

class ZeroOrMore(Expression):

    def __init__(self, expression):
        self.expression = expression

    def match(self, tokens, mandatory=False):
        matches = []
        while True:
            result = self.expression.match(tokens, False)
            if result.matches:
                matches.extend(result.tree)
            else:
                break

        return Result(True, matches)

    def __repr__(self):
        return '%s*' % self.expression

class OneOrMore(Expression):

    def __init__(self, expression):
        self.expression = expression

    def match(self, tokens, mandatory=False):
        matches = []
        is_first = True
        while True:
            result = self.expression.match(tokens, is_first and mandatory)
            is_first = False
            if result.matches:
                matches.extend(result.tree)
            else:
                break

        return Result(True, matches) if matches else Result(False)

    def __repr__(self):
        return '%s+' % self.expression

class Token(Expression):

    def __init__(self, type):
        self.type = type

    def match(self, tokens, mandatory=False):
        matches = []
        next_token = None

        with tokens.mark() as m_tokens:
            try:
                next_token = next(iter(m_tokens))
                if next_token.type == self.type:
                    return Result(True, [Element(next_token)])
            except StopIteration:
                pass
            tokens.restore()

        if mandatory:
            if next_token:
                raise SyntaxError('Expecting %s, but found %s. At line %d, column %d' % (self, next_token.value, next_token.line, next_token.column))
            else:
                raise SyntaxError('Unexpected end of input. Expecting %s' % self)

        return Result(False)

    def __repr__(self):
        return self.type

class Parser(object):

    def __init__(self, start, grammar=None):
        self.grammar = grammar if grammar else {}
        self.start = self.expression(start)

    def token(self, type):
        return Token(type)

    def expression(self, name):
        return Expression(name, parser=self)

    def zeroOrMore(self, expression):
        return ZeroOrMore(expression)

    def oneOrMore(self, expression):
        return OneOrMore(expression)

    def parse(self, tokens):
        tokensBuffer = Buffer(tokens)
        result = self.start.match(tokensBuffer, True)

        # raise exception if there's something left in the buffer
        for token in tokens:
            raise SyntaxError("Unexpected %s at line %d, column %d. Expecting end of tokens" % (token.value, token.line, token.column))

        if result.matches == True:
            return result.tree
        else:
            return None

class Result(object):

    def __init__(self, matches, tree=None):
        self.matches = matches
        self.tree = tree if tree else []

class Element(object):

    def __init__(self, value, name=None):
        if type(value) == lexer.Token:
            self.name = name if name else value.type
            self.is_terminal = True
        else:
            self.name = name
            self.is_terminal = False
        self.value = value

    def __repr__(self):
        return repr(self.value) if self.is_terminal else "<%s: %s>" % (self.name, repr(self.value))

