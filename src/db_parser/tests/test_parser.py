import unittest

from src.db_parser.common import DbSyntaxError
from src.db_parser.lexer import Token
from src.db_parser.parser import Parser
from src.db_parser.tokens import TokenTypes


class MockLexer():
    """
    Mocked lexer builder.
    """

    EOF_TOKEN = Token(TokenTypes.EOF, linenum=0, colnum=0)

    def __init__(self):
        self.tokens = []
        self.gen = None

    def add_token(self, token_type, contents=None):
        self.tokens.append(Token(type=token_type, linenum=0, colnum=0, contents=contents))
        return self

    def add_key_value_pair(self, key, value):
        """
        Adds a bracketed key-value pair to the mocked lexer. Key is a literal, value is a quoted string.
        """
        return self \
            .add_token(TokenTypes.L_BRACKET) \
            .add_token(TokenTypes.LITERAL, '{}'.format(key)) \
            .add_token(TokenTypes.COMMA) \
            .add_token(TokenTypes.QUOTED_STRING, '"{}"'.format(value)) \
            .add_token(TokenTypes.R_BRACKET)

    def add_field(self, field_name, field_value):
        return self.add_token(TokenTypes.FIELD).add_key_value_pair(field_name, field_value)

    def add_info_field(self, field_name, field_value):
        return self.add_token(TokenTypes.INFO).add_key_value_pair(field_name, field_value)

    def add_alias_field(self, value):
        return self \
            .add_token(TokenTypes.ALIAS) \
            .add_token(TokenTypes.L_BRACKET) \
            .add_token(TokenTypes.QUOTED_STRING, '"{}"'.format(value)) \
            .add_token(TokenTypes.R_BRACKET)

    def add_alias(self, record_name, alias_name):
        return self.add_token(TokenTypes.ALIAS).add_key_value_pair(record_name, alias_name)

    def add_record_header(self, record_type, record_name):
        return self.add_token(TokenTypes.RECORD).add_key_value_pair(record_type, record_name)

    def add_macro(self):
        return self.add_token(TokenTypes.BRACKET_MACRO_START)\
            .add_token(TokenTypes.LITERAL)\
            .add_token(TokenTypes.R_BRACKET)

    def __next__(self):
        if self.gen is None:
            def gen():
                for t in self.tokens:
                    yield t
                yield MockLexer.EOF_TOKEN

            self.gen = gen()

        return next(self.gen)


class ParserTests(unittest.TestCase):
    def test_WHEN_parser_given_no_tokens_THEN_raises_parse_error(self):
        lexer = (i for i in [])  # No tokens

        with self.assertRaises(DbSyntaxError):
            Parser(lexer).db()

    def test_WHEN_parser_given_only_an_end_of_file_token_while_parsing_db_THEN_no_parse_error(self):
        lexer = MockLexer()

        Parser(lexer).db()

    def test_WHEN_parser_given_a_quoted_string_THEN_parser_can_extract_the_value(self):
        val = "HELLO"

        lexer = MockLexer() \
            .add_token(TokenTypes.QUOTED_STRING, '"{}"'.format(val))

        self.assertEqual(Parser(lexer).value(), val)

    def test_WHEN_parser_given_a_string_literal_THEN_parser_can_extract_the_value(self):
        val = "TESTVALUE"

        lexer = MockLexer() \
            .add_token(TokenTypes.LITERAL, '{}'.format(val))

        self.assertEqual(Parser(lexer).value(), val)

    def test_GIVEN_a_token_that_does_not_represent_a_value_WHEN_parse_value_THEN_parser_error(self):
        lexer = MockLexer() \
            .add_token(TokenTypes.RECORD)

        with self.assertRaises(DbSyntaxError):
            Parser(lexer).value()

    def test_GIVEN_a_bracketed_key_value_pair_where_both_values_are_quoted_WHEN_parse_key_value_pair_THEN_can_extract_key_and_value(
            self):
        key, value = "Key", "Value"

        # ("KEY", "VALUE")
        lexer = MockLexer() \
            .add_token(TokenTypes.L_BRACKET) \
            .add_token(TokenTypes.QUOTED_STRING, '"{}"'.format(key)) \
            .add_token(TokenTypes.COMMA) \
            .add_token(TokenTypes.QUOTED_STRING, '"{}"'.format(value)) \
            .add_token(TokenTypes.R_BRACKET, '"{}"'.format(value))

        parsed_key, parsed_value = Parser(lexer).key_value_pair()

        self.assertEqual(parsed_key, key)
        self.assertEqual(parsed_value, value)

    def test_GIVEN_a_bracketed_key_value_pair_where_first_value_is_literal_and_second_value_is_quoted_WHEN_parse_key_value_pair_THEN_can_extract_key_and_value(
            self):
        key, value = "Key", "Value"

        # (KEY, "VALUE")
        lexer = MockLexer().add_key_value_pair(key, value)

        parsed_key, parsed_value = Parser(lexer).key_value_pair()

        self.assertEqual(parsed_key, key)
        self.assertEqual(parsed_value, value)

    def test_GIVEN_a_bracketed_key_value_pair_where_both_values_are_literal_WHEN_parse_key_value_pair_THEN_can_extract_key_and_value(
            self):
        key, value = "Key", "Value"

        # (KEY, VALUE)
        lexer = MockLexer() \
            .add_token(TokenTypes.L_BRACKET) \
            .add_token(TokenTypes.LITERAL, '{}'.format(key)) \
            .add_token(TokenTypes.COMMA) \
            .add_token(TokenTypes.LITERAL, '{}'.format(value)) \
            .add_token(TokenTypes.R_BRACKET, '"{}"'.format(value))

        parsed_key, parsed_value = Parser(lexer).key_value_pair()

        self.assertEqual(parsed_key, key)
        self.assertEqual(parsed_value, value)

    def test_GIVEN_a_bracketed_key_value_pair_where_comma_is_missing_WHEN_parse_key_value_pair_THEN_raises_error(self):
        key, value = "Key", "Value"

        # (KEY VALUE)
        lexer = MockLexer() \
            .add_token(TokenTypes.L_BRACKET) \
            .add_token(TokenTypes.LITERAL, '{}'.format(key)) \
            .add_token(TokenTypes.LITERAL, '{}'.format(value)) \
            .add_token(TokenTypes.R_BRACKET, '"{}"'.format(value))

        with self.assertRaises(DbSyntaxError):
            Parser(lexer).key_value_pair()

    def test_GIVEN_a_field_declaration_WHEN_parse_field_THEN_can_extract_key_and_value(self):
        key, value = "PINI", "YES"

        # field(PINI, "YES")
        lexer = MockLexer() \
            .add_token(TokenTypes.FIELD) \
            .add_key_value_pair(key, value)

        parsed_field = Parser(lexer).field()
        parsed_key = parsed_field.name
        parsed_value = parsed_field.value

        self.assertEqual(parsed_key, key)
        self.assertEqual(parsed_value, value)

    def test_GIVEN_an_empty_record_declaration_WHEN_parse_record_THEN_parser_can_extract_the_information(self):
        rec_type, rec_name = "ai", "$(P)TEST"

        # record(ai, "$(P)TEST") {}

        lexer = MockLexer() \
            .add_record_header(rec_type, rec_name) \
            .add_token(TokenTypes.L_BRACE) \
            .add_token(TokenTypes.R_BRACE)

        parsed_record = Parser(lexer).record()

        self.assertEqual(parsed_record.pv, rec_name)
        self.assertEqual(parsed_record.get_type(), rec_type)
        self.assertEqual(parsed_record.fields, [])
        self.assertEqual(parsed_record.infos, [])
        self.assertEqual(parsed_record.aliases, [])

    def test_GIVEN_a_record_declaration_containing_a_field_and_an_info_WHEN_parse_record_THEN_parser_can_extract_the_information(
            self):
        rec_type, rec_name = "ai", "$(P)TEST"
        field_name, field_val = "PINI", "YES"
        info_name, info_val = "alarm", "TEST_01"

        # record(ai, "$(P)TEST") {
        #     field(PINI, "YES")
        #     info(alarm, "TEST_01")
        # }
        lexer = MockLexer() \
            .add_record_header(rec_type, rec_name) \
            .add_token(TokenTypes.L_BRACE) \
            .add_field(field_name, field_val) \
            .add_info_field(info_name, info_val) \
            .add_token(TokenTypes.R_BRACE)

        parsed_record = Parser(lexer).record()

        self.assertEqual(parsed_record.pv, rec_name)
        self.assertEqual(parsed_record.get_type(), rec_type)
        self.assertEqual([field.unpack() for field in parsed_record.fields], [(field_name, field_val)])
        self.assertEqual([field.unpack() for field in parsed_record.infos], [(info_name, info_val)])
        self.assertEqual(parsed_record.aliases, [])

    def test_GIVEN_a_record_declaration_containing_an_alias_WHEN_parse_record_THEN_parser_can_extract_the_information(
            self):
        rec_type, rec_name = "ai", "$(P)TEST"
        alias_name = "$(P)ALIAS"

        # record(ai, "$(P)TEST") {
        #     alias("$(P)ALIAS")
        # }
        lexer = MockLexer() \
            .add_record_header(rec_type, rec_name) \
            .add_token(TokenTypes.L_BRACE) \
            .add_alias_field(alias_name) \
            .add_token(TokenTypes.R_BRACE)

        parsed_record = Parser(lexer).record()

        self.assertEqual(parsed_record.pv, rec_name)
        self.assertEqual(parsed_record.get_type(), rec_type)
        self.assertEqual(parsed_record.fields, [])
        self.assertEqual(parsed_record.infos, [])
        self.assertEqual(parsed_record.aliases, [alias_name])

    def test_GIVEN_a_record_declaration_with_a_separate_alias_WHEN_parse_record_THEN_parser_can_extract_the_information(
            self):
        rec_type, rec_name = "ai", "$(P)TEST"
        alias_name = "$(P)ALIAS"

        # record(ai, "$(P)TEST") {
        # }
        # alias("$(P)TEST", "$(P)ALIAS")
        lexer = MockLexer() \
            .add_record_header(rec_type, rec_name) \
            .add_token(TokenTypes.L_BRACE) \
            .add_token(TokenTypes.R_BRACE) \
            .add_alias(rec_name, alias_name)

        parsed_db = Parser(lexer).db()

        self.assertEqual(len(parsed_db), 1)
        parsed_record = parsed_db.records[0]

        self.assertEqual(parsed_record.pv, rec_name)
        self.assertEqual(parsed_record.get_type(), rec_type)
        self.assertEqual(parsed_record.fields, [])
        self.assertEqual(parsed_record.infos, [])
        self.assertEqual(parsed_record.aliases, [alias_name])

    def test_GIVEN_multiple_records_WHEN_parse_as_db_THEN_parser_can_extract_the_information(self):
        rec_type_1 = "ai"
        rec_type_2 = "bi"
        rec_name_1 = "$(P)TEST1"
        rec_name_2 = "$(P)TEST2"

        # record(ai, "$(P)TEST1") {
        # }
        # record(bi, "$(P)TEST2") {
        # }
        lexer = MockLexer() \
            .add_record_header(rec_type_1, rec_name_1) \
            .add_token(TokenTypes.L_BRACE) \
            .add_token(TokenTypes.R_BRACE) \
            .add_record_header(rec_type_2, rec_name_2) \
            .add_token(TokenTypes.L_BRACE) \
            .add_token(TokenTypes.R_BRACE)

        parsed_db = Parser(lexer).db()

        self.assertEqual(len(parsed_db), 2)
        rec1, rec2 = parsed_db.records

        self.assertEqual(rec1.get_type(), rec_type_1)
        self.assertEqual(rec2.get_type(), rec_type_2)
        self.assertEqual(rec1.pv, rec_name_1)
        self.assertEqual(rec2.pv, rec_name_2)

    def test_GIVEN_multiple_records_with_no_bodies_WHEN_parse_as_db_THEN_parser_can_extract_the_information(self):
        rec_type_1 = "ai"
        rec_type_2 = "bi"
        rec_name_1 = "$(P)TEST1"
        rec_name_2 = "$(P)TEST2"

        # record(ai, "$(P)TEST1")
        # record(bi, "$(P)TEST2")
        lexer = MockLexer().add_record_header(rec_type_1, rec_name_1).add_record_header(rec_type_2, rec_name_2)
        parsed_db = Parser(lexer).db()

        self.assertEqual(len(parsed_db), 2)
        rec1, rec2 = parsed_db.records

        self.assertEqual(rec1.get_type(), rec_type_1)
        self.assertEqual(rec2.get_type(), rec_type_2)
        self.assertEqual(rec1.pv, rec_name_1)
        self.assertEqual(rec2.pv, rec_name_2)

    def test_GIVEN_record_containing_macros_WHEN_parse_record_THEN_parser_can_find_fields_with_starting_macro(self):
        rec_type = "ai"
        rec_name = "$(P)TEST1"
        field_name_1, field_val_1 = "HASMACRO", "YES"
        field_name_2, field_val_2 = "NOMACRO", "YES"

        lexer = MockLexer() \
            .add_record_header(rec_type, rec_name) \
            .add_token(TokenTypes.L_BRACE) \
            .add_macro() \
            .add_field(field_name_1, field_val_1) \
            .add_field(field_name_2, field_val_2) \
            .add_token(TokenTypes.R_BRACE)

        parsed_record = Parser(lexer).record()
        self.assertTrue(parsed_record.fields[0].has_macro)
        self.assertFalse(parsed_record.fields[1].has_macro)

    def test_GIVEN_nested_macros_THEN_parsed_correctly(self):
        lexer = MockLexer() \
            .add_token(TokenTypes.BRACKET_MACRO_START) \
            .add_token(TokenTypes.LITERAL) \
            .add_token(TokenTypes.BRACKET_MACRO_START) \
            .add_token(TokenTypes.LITERAL) \
            .add_token(TokenTypes.R_BRACKET) \
            .add_token(TokenTypes.R_BRACKET)

        parsed_macro = Parser(lexer).macro()
        self.assertEquals(parsed_macro, "")
