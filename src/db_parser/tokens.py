class TokenTypes(object):
    # Special tokens
    EOF = "EOF"

    # Common literals
    RECORD = "RECORD"
    FIELD = "FIELD"
    INFO = "INFO"
    ALIAS = "ALIAS"
    INCLUDE = "INCLUDE"

    # Delimeters, separators
    L_BRACKET = "L_BRACKET"
    R_BRACKET = "R_BRACKET"
    L_BRACE = "L_BRACE"
    R_BRACE = "R_BRACE"
    COMMA = "COMMA"

    # Values
    QUOTED_STRING = "QUOTED_STRING"
    LITERAL = "LITERAL"
    COMMENT = "COMMENT"
    MACRO = "MACRO"
    WHITESPACE = "WHITESPACE"
