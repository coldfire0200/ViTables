from qtpy.QtCore import QRegExp
from qtpy.QtGui import (QColor, QTextCharFormat, QFont, QSyntaxHighlighter)

import keyword

import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': format('blue', 'bold'),
    'operator': format('red'),
    'brace': format('darkGray'),
    'defclass': format('black', 'bold'),
    'function': format('black', 'bold'),
    'string': format('magenta'),
    'string2': format('darkMagenta'),
    'comment': format('darkGreen', 'italic'),
    'self': format('black', 'italic'),
    'numbers': format('brown'),
    'inprompt': format('darkBlue', 'bold'),
    'outprompt': format('darkRed', 'bold'),
    'default': format('black'),
    'output': format('black'),
    'output-error': format('red', 'bold'),
    'output-trace': format('#03f4fc', 'bold')
}


class PromptHighlighter(object):

    def __init__(self, formats=None):
        self.styles = styles = dict(STYLES, **(formats or {}))
        self.rules = [
            # Match the prompt incase of a console
            (QRegExp(r'IN[^\:]*'), 0, styles['inprompt']),
            (QRegExp(r'OUT[^\:]*'), 0, styles['outprompt']),
            # Numeric literals
            (QRegExp(r'\b[+-]?[0-9]+\b'), 0, styles['numbers']),
        ]        

    def highlight(self, text):
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)
            while index >= 0:
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                yield (index, length, format)
                index = expression.indexIn(text, index + length)

    def default_format(self):
        return self.styles['default']

class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = keyword.kwlist
    # Python operators
    operators = [
            '=',
            # Comparison
            '==', '!=', '<', '<=', '>', '>=',
            # Arithmetic
            r'\+', r'-', r'\*', r'/', r'//', r'\%', r'\*\*',
            # In-place
            r'\+=', r'-=', r'\*=', r'/=', r'\%=',
            # Bitwise
            r'\^', r'\|', r'\&', r'\~', '>>', '<<',
    ]
    # Python braces
    braces = [
            r'\{', r'\}', r'\(', r'\)', r'\[', r'\]',
    ]

    def __init__(self, document, input_valid, formats=None):
        QSyntaxHighlighter.__init__(self, document)

        self.styles = styles = dict(STYLES, **(formats or {}))
        self.input_valid = input_valid

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, styles['string2'])
        self.tri_double = (QRegExp('"""'), 2, styles['string2'])

        rules = []


        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, styles['keyword'])
                  for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, styles['operator'])
                  for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, styles['brace'])
                  for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, styles['self']),

            # function
            (r'\b\s*(\w+)\s*\(', 1, styles['function']),
            # decorator
            (r'^\s*(@\s*\w+)\s*', 1, styles['function']),
            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, styles['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, styles['defclass']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, styles['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, styles['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0,
             styles['numbers']),
            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, styles['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, styles['string']),
            # From '#' until a newline
            (r'#[^\n]*', 0, styles['comment']),
        ]

        # output rules
        output_rules = []
        output_rules += [
            (r'^(\w*Error)', 0, styles['output-error']),
            (r'^(Exception)\:*', 0, styles['output-error']),
            (r'^(Traceback)\b', 0, styles['output-trace'])
        ]
        
        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]
        self.output_rules = [(QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in output_rules]

    def default_format(self):
        return self.styles['default']

    def apply_syntax_formating(self, text, rules, default):
        self.setFormat(0, len(text), default)
        for expression, nth, format in rules:
            index = expression.indexIn(text, 0)
            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        if self.input_valid(self.currentBlock().firstLineNumber()):
            self.apply_syntax_formating(text, self.rules, self.styles['default'])
        else:
            self.apply_syntax_formating(text, self.output_rules, self.styles['output'])

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        return self.currentBlockState() == in_state
