# coding: utf-8

from cons import *

__all__ = ['Macro', 'is_macro']

class Macro(object):
    """
    A macro is an object that hold transformation rules which change an input
    expression into another. The rules are a list of pattern/form pairs. The
    expression is transformed into the form associated with the first pattern
    matched from the rules. In case none of the pattern matches, an error is
    raised.
    """

    def __init__(self, rules, reserved_words=None, name=''):
        """
        Creates a new macro using the given rules, and optionaly, a set of
        reserved words. This words will be used to match with the symbols
        itself (i.e. not variable placeholders).
        """
        self.rules = rules
        self.reserved_words = set() if not reserved_words else reserved_words
        self.name = name

    def transform(self, expression):
        """
        Applies the macro in the expression, and return the transformed
        expression. This method assumes that the expression head matches
        the macro
        """
        for pattern, form in self.rules:
            # match_pattern retuns a dictionary of variables and matched
            # expression, or None if there's no match.
            variables = match_pattern(pattern, expression, self.reserved_words)
            if variables is not None:
                return substitute(variables, form)

        # no matching
        raise ValueError("Expression %s does not match macro %s" %
                         (expression, self.name))

    def __repr__(self):
        return "<%d-rule macro>" % len(self.rules)

def match_pattern(pattern, expression, reserved_words=set()):
    """
    Return a dictionary of matched variables if the pattern matches the
    expression.  An optional reserverd words set might be used to let these
    words be matched exactly in the pattern.
    """

    if is_atom(pattern):
        if pattern in reserved_words:
            return {} if expression == pattern else None
        elif pattern == '_':
            return {}
        elif is_symbol(pattern) and pattern.startswith('...'):
            return {pattern: expression}
        else:
            return {pattern: expression}
    elif is_nil(pattern) and is_nil(expression):
        return {}
    elif is_pair(pattern):

        if is_symbol(car(pattern)) and car(pattern).startswith('...'):
            return {car(pattern): expression}
        elif is_pair(expression):
            matched_car = match_pattern(car(pattern), car(expression), reserved_words)
            if matched_car is not None:
                matched_cdr = match_pattern(cdr(pattern), cdr(expression), reserved_words)
                if matched_cdr is not None:
                    matched_cdr.update(matched_car)
                    return matched_cdr

    return None

def substitute(variables, expression):
    """
    Substitute an expression using the symbols in it as variables to be
    looked-up in the variables dictionary - if they exists.
    """

    if is_atom(expression):
        return variables.get(expression, expression)
    elif is_pair(expression):
        if is_symbol(car(expression)) and car(expression).startswith('...'):
            return substitute(variables, car(expression))
        else:
            return cons(substitute(variables, car(expression)),
                        substitute(variables, cdr(expression)))
    else:
        return expression

is_macro = lambda x: isinstance(x, Macro)

