import unittest

import six

from src.db_parser.common import DbSyntaxError
from src.db_parser.lexer import Lexer, Token
from src.db_parser.tokens import TokenTypes


def get_tokens_list(lexer):
    tokens = []
    while True:
        try:
            tokens.append(six.advance_iterator(lexer))
        except StopIteration:
            break
    return tokens


def token_from_type(token_type):
    return Token(token_type, 0, 0)


class LexerTests(unittest.TestCase):
    def test_WHEN_lexer_lexes_empty_file_THEN_produces_an_EOF_token(self):
        tokens = get_tokens_list(Lexer(""))

        expected_tokens = [
            token_from_type(TokenTypes.EOF)
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_WHEN_lexer_lexes_a_record_literal_THEN_produces_a_record_token(self):
        tokens = get_tokens_list(Lexer("record"))

        expected_tokens = [
            token_from_type(TokenTypes.RECORD),
            token_from_type(TokenTypes.EOF)
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_WHEN_lexer_lexes_a_literal_THEN_produces_a_literal_token(self):
        tokens = get_tokens_list(Lexer("HI_THIS_IS_A_LITERAL"))

        expected_tokens = [
            token_from_type(TokenTypes.LITERAL),
            token_from_type(TokenTypes.EOF)
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_WHEN_lexer_lexes_whitespace_THEN_whitespace_is_ignored(self):
        tokens = get_tokens_list(Lexer("      "))

        expected_tokens = [
            token_from_type(TokenTypes.EOF)
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_WHEN_lexer_lexes_a_comment_THEN_comment_is_ignored(self):
        tokens = get_tokens_list(Lexer("# Hello this is a comment"))

        expected_tokens = [
            token_from_type(TokenTypes.EOF)
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_WHEN_lexer_lexes_a_macro_THEN_macro_is_ignored(self):
        tokens = get_tokens_list(Lexer("$(MACRO=VALUE)"))

        expected_tokens = [
            token_from_type(TokenTypes.EOF)
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_WHEN_lexer_lexes_brackets_THEN_returns_bracket_tokens(self):
        tokens = get_tokens_list(Lexer("()"))

        expected_tokens = [
            token_from_type(TokenTypes.L_BRACKET),
            token_from_type(TokenTypes.R_BRACKET),
            token_from_type(TokenTypes.EOF),
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_WHEN_lexer_lexes_braces_THEN_returns_brace_tokens(self):
        tokens = get_tokens_list(Lexer("{}"))

        expected_tokens = [
            token_from_type(TokenTypes.L_BRACE),
            token_from_type(TokenTypes.R_BRACE),
            token_from_type(TokenTypes.EOF),
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_WHEN_lexer_lexes_a_quoted_string_THEN_returns_quoted_string_token(self):
        tokens = get_tokens_list(Lexer(r'"This is a quoted string"'))

        expected_tokens = [
            token_from_type(TokenTypes.QUOTED_STRING),
            token_from_type(TokenTypes.EOF),
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_WHEN_lexer_lexes_a_quoted_string_containing_escaped_quotes_THEN_returns_a_single_quoted_string_token(self):
        tokens = get_tokens_list(Lexer(r'"This \"is\" a quoted string"'))

        expected_tokens = [
            token_from_type(TokenTypes.QUOTED_STRING),
            token_from_type(TokenTypes.EOF),
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_WHEN_lexer_lexes_a_quoted_string_containing_comment_syntax_THEN_returns_a_single_quoted_string_token(self):
        tokens = get_tokens_list(Lexer(r'"This # is a quoted string"'))

        expected_tokens = [
            token_from_type(TokenTypes.QUOTED_STRING),
            token_from_type(TokenTypes.EOF),
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_WHEN_lexer_lexes_an_empty_quoted_string_THEN_returns_a_quoted_string_token(self):
        tokens = get_tokens_list(Lexer(r'""'))

        expected_tokens = [
            token_from_type(TokenTypes.QUOTED_STRING),
            token_from_type(TokenTypes.EOF),
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_WHEN_lexer_lexes_a_string_with_missing_end_quote_THEN_raises_syntax_error(self):
        with self.assertRaises(DbSyntaxError):
            get_tokens_list(Lexer(r'"This is a quoted string without a closing quote'))

    def test_WHEN_lexer_lexes_a_minimal_record_declaration_THEN_returns_an_appropriate_set_of_tokens(self):
        tokens = get_tokens_list(Lexer(r'record(ai, "$(P)TEST"){}'))

        expected_tokens = [
            token_from_type(TokenTypes.RECORD),
            token_from_type(TokenTypes.L_BRACKET),
            token_from_type(TokenTypes.LITERAL),
            token_from_type(TokenTypes.COMMA),
            token_from_type(TokenTypes.QUOTED_STRING),
            token_from_type(TokenTypes.R_BRACKET),
            token_from_type(TokenTypes.L_BRACE),
            token_from_type(TokenTypes.R_BRACE),
            token_from_type(TokenTypes.EOF),
        ]

        self.assertListEqual(tokens, expected_tokens)

    def test_GIVEN_content_on_multiple_lines_WHEN_lexed_THEN_line_numbers_are_correct(self):

        content = """
        
        record"""

        tokens = get_tokens_list(Lexer(content))

        expected_tokens = [
            token_from_type(TokenTypes.RECORD),
            token_from_type(TokenTypes.EOF),
        ]

        self.assertListEqual(tokens, expected_tokens)

        self.assertEqual(tokens[0].line, 3)  # The record token should be on line 3

    def test_GIVEN_content_WHEN_lexed_THEN_column_number_is_correct(self):
        indentation_level = 4
        tokens = get_tokens_list(Lexer("{}record".format(" " * indentation_level)))

        expected_tokens = [
            token_from_type(TokenTypes.RECORD),
            token_from_type(TokenTypes.EOF),
        ]

        self.assertListEqual(tokens, expected_tokens)

        self.assertEqual(tokens[0].col, indentation_level)  # The record token should start on the specified column

    def test_GIVEN_comment_on_previous_line_WHEN_lexed_THEN_next_line_is_lexed_properly(self):
        content = """
        # Hi this is a comment on one line
        record
        """
        tokens = get_tokens_list(Lexer(content))

        expected_tokens = [
            token_from_type(TokenTypes.RECORD),
            token_from_type(TokenTypes.EOF),
        ]

        self.assertListEqual(tokens, expected_tokens)
