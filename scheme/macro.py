# coding: utf-8

from cons import *

__all__ = ['Macro']

class Macro(object):

    def __init__(self, rules, reserved_words=None):
        self.rules = rules
        self.reserved_words = set() if not reserved_words else reserved_words

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
        raise ValueError("Expression %s does not match macro" % expression)

    def __repr__(self):
        return "<%d-rule macro>" % len(self.rules)

def match_pattern(pattern, expression, reserved_words):

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

