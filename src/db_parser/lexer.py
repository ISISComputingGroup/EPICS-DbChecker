import re
from collections import OrderedDict

from src.db_parser.common import DbSyntaxError
from src.db_parser.tokens import TokenTypes


class Token(object):
    """
    Class representing a lexer token. Tokens are considered equal if their types are equal.
    Args:
        type: the type of this token. Should be one of TokenTypes
        linenum: the line number this token was found on
        colnum: the column number this token was found on
        contents: the original text that this token was parsed from
    """

    def __init__(self, type, linenum, colnum, contents=None):
        self.type = type
        self.contents = contents

        self.line = linenum
        self.col = colnum

    def __str__(self):
        return "{} (contents={})".format(self.type, self.contents)

    __repr__ = __str__

    def __eq__(self, other):
        try:
            return self.type == other.type
        except AttributeError:
            return False


def _escape(var):
    """
    Returns the input variable escaped and wrapped in a regex capture group.
    """
    return f"({re.escape(var)})"


class Lexer:
    """
    Lexer, tokenises the database file into
    """

    """
    Tokens to ignore. These are never returned from __next__
    """
    IGNORED_TOKENS = [TokenTypes.WHITESPACE]

    """
    This provides a mapping between regexes and lexer tokens.

    The regexes are tried in order, the first one that matches get's it's token produced.
    """
    TOKEN_MAPPING = OrderedDict(
        [
            (
                _escape("$("),  # Macro start with brackets $(MACRO=VALUE)
                TokenTypes.BRACKET_MACRO_START,
            ),
            (
                _escape("${"),  # Macro start with curly braces ${MACRO=VALUE}
                TokenTypes.BRACE_MACRO_START,
            ),
            (_escape("record"), TokenTypes.RECORD),
            (_escape("grecord"), TokenTypes.RECORD),
            (_escape("field"), TokenTypes.FIELD),
            (_escape("info"), TokenTypes.INFO),
            (_escape("alias"), TokenTypes.ALIAS),
            (_escape("("), TokenTypes.L_BRACKET),
            (_escape(")"), TokenTypes.R_BRACKET),
            (_escape("{"), TokenTypes.L_BRACE),
            (_escape("}"), TokenTypes.R_BRACE),
            (_escape(","), TokenTypes.COMMA),
            (_escape("="), TokenTypes.EQUALS),
            (
                # Ignore escaped quotes within a string. Add special case for empty string
                r"(\".*?[^\\]\"|\"\")",
                TokenTypes.QUOTED_STRING,
            ),
            (r"(\s+)", TokenTypes.WHITESPACE),
            (
                r"([a-zA-Z0-9\-\_\.\:]+)",  # Alphanumeric, -, _, ., :
                TokenTypes.LITERAL,
            ),
            (
                _escape("#"),  # Mostly comments,
                # but also things like $(MACRO=#) field(INPA, "blah") are valid...
                TokenTypes.HASH,
            ),
            (
                # Matches absolutely anything (as a last resort, for comment contents for example).
                r"(.+)",
                TokenTypes.UNKNOWN,
            ),
        ]
    )

    # Change to keep track of macro
    def __init__(self, file_contents):
        self.file_contents = file_contents
        self.gen = None

    def token_generator(self):
        """
        Token generator function.
        yields:
            Tokens corresponding to the lexed input.
        """
        lines = self.file_contents.split("\n")
        for linenum, line in enumerate(lines, 1):
            column = 0
            while column < len(line):
                for regexp in Lexer.TOKEN_MAPPING:
                    match_text = self._text_matches_regex(line[column:], regexp)
                    if match_text is not None:
                        yield Token(Lexer.TOKEN_MAPPING[regexp], linenum, column, match_text)
                        column += len(match_text)
                        break
                else:
                    raise DbSyntaxError(
                        "No matching rules found at {}:{}. Line contents: '{}'".format(
                            linenum, column, line
                        )
                    )

        yield Token(TokenTypes.EOF, len(lines), len(lines[len(lines) - 1]))

    def __next__(self):
        """
        Generator of this Lexer's tokens
        """
        if self.gen is None:
            self.gen = self.token_generator()

        tok = next(self.gen)
        while tok.type in self.IGNORED_TOKENS:
            tok = next(self.gen)
        return tok

    @staticmethod
    def _text_matches_regex(text, rx):
        """
        Attempts to match the given text with a given regex.

        Args:
            text:
            rx: the regex to apply
        Returns:
             The text of the match if the match succeeded, None otherwise
        """
        match = re.match(rx, text)
        if match:
            return match.group(1)
        return None
