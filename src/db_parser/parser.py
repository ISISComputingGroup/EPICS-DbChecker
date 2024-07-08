from contextlib import contextmanager

from src.db_parser.common import DbSyntaxError
from src.db_parser.epics_collections import Db, Field, Record
from src.db_parser.tokens import TokenTypes


class Parser(object):
    """
    Main db_parser. Takes input tokens from the given lexer and builds an EPICS DB out of them.
    """

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = None
        self.next_token()

    def next_token(self):
        """
        Call to advance the lexer by one token.
        """
        try:
            # Ignore macros and comments wherever they occur
            self.current_token = next(self.lexer)
        except StopIteration:
            self.raise_error("Next token was requested, but none exists.")

    def consume(self, token_type):
        """
        Verifies that the lexer's current token is of the given type, and then advances the lexer
        by one token.

        Args:
            token_type: the expected type of the current token.
        """
        if self.current_token.type == token_type:
            value = self.current_token.contents
            self.next_token()
            return value
        else:
            self.raise_error("Expected '{}'.".format(token_type))

    def raise_error(self, message):
        """
        Error function if an unexpected token was encountered. Line numbers and current token
        information will be added.

        Args:
            message: A message to add to the error
        """
        if self.current_token is None:
            raise DbSyntaxError("No tokens found.")
        else:
            raise DbSyntaxError(
                "Unexpected token '{}' encountered at {}:{}: {}".format(
                    self.current_token, self.current_token.line, self.current_token.col, message
                )
            )

    @contextmanager
    def delimited_block(self, start, end):
        """
        Context manager to surround a given block with a given start and end token.
        Args:
            start: The type of token to expect at the start of the block
            end: The type of token to expect at the end of the block
        """
        self.consume(start)
        yield
        self.consume(end)

    def bracket_delimited_block(self):
        """
        Context manager to surround a block with brackets
        """
        return self.delimited_block(start=TokenTypes.L_BRACKET, end=TokenTypes.R_BRACKET)

    def brace_delimited_block(self):
        """
        Context manager to surround a block with braces
        """
        return self.delimited_block(start=TokenTypes.L_BRACE, end=TokenTypes.R_BRACE)

    def literal_or_macro(self):
        ret = ""
        while self.current_token.type == TokenTypes.LITERAL or self.next_token_is_macro():
            if self.current_token.type == TokenTypes.LITERAL:
                ret += self.consume(TokenTypes.LITERAL)
            else:
                self.macro()
        return ret

    def value(self):
        """
        Handler for values which are allowed to be quoted or not.
        Examples:
            HELLO
            "HELLO"
        Returns:
            The value with quotes stripped (if applicable)
        """
        if self.current_token.type == TokenTypes.QUOTED_STRING:
            return self.consume(TokenTypes.QUOTED_STRING)[1:-1]  # Strip quotes
        elif self.current_token.type == TokenTypes.LITERAL or self.next_token_is_macro():
            return self.literal_or_macro()
        else:
            self.raise_error("Expected either a literal or a string literal.")

    def key_value_pair(self):
        """
        Handler for key value pairs surrounded by brackets.
        Both the key and value are allowed to be quoted or not.
        Examples:
            (ONVL, "1")
            ("HELLO", bonjour)
        Returns:
            tuple of (key, value)
        """
        with self.bracket_delimited_block():
            key = self.value()
            self.consume(TokenTypes.COMMA)
            value = self.value()
        return key, value

    def field(self, has_macro=False):
        """
        Handler for an EPICS DB field.
        Examples:
             field(PINI, "YES")
        Returns:
            tuple of (key, value)
        """
        self.consume(TokenTypes.FIELD)
        return Field(*self.key_value_pair(), has_macro=has_macro)

    def info(self):
        """
        Handler for an EPICS DB info field.
        Example:
             info(alarm, "SIMPLE_01")
        Returns:
            tuple of (key, value)
        """
        self.consume(TokenTypes.INFO)
        return Field(*self.key_value_pair())

    def alias_field(self):
        """
        Handler for an EPICS alias within a DB record
        Example:
            alias("$(P)RECORD1")
        Returns:
             value of the alias
        """
        self.consume(TokenTypes.ALIAS)
        with self.bracket_delimited_block():
            return self.value()

    def next_token_is_macro(self):
        return self.current_token.type in [
            TokenTypes.BRACE_MACRO_START,
            TokenTypes.BRACKET_MACRO_START,
        ]

    def macro(self):
        if not self.next_token_is_macro():
            self.raise_error("Expected start of macro")

        end = (
            TokenTypes.R_BRACE
            if self.current_token.type == TokenTypes.BRACE_MACRO_START
            else TokenTypes.R_BRACKET
        )
        self.consume(self.current_token.type)

        while self.current_token.type != end and self.current_token.type != TokenTypes.EQUALS:
            if self.current_token.type == TokenTypes.LITERAL:
                self.consume(TokenTypes.LITERAL)
            elif self.next_token_is_macro():
                self.macro()
            else:
                self.raise_error("Expected macro or literal")

        if self.current_token.type == TokenTypes.EQUALS:
            self.consume(TokenTypes.EQUALS)
            while self.current_token.type != end:
                if self.current_token.type == TokenTypes.LITERAL:
                    self.consume(TokenTypes.LITERAL)
                elif self.next_token_is_macro():
                    self.macro()
                elif self.current_token.type == TokenTypes.HASH:
                    # Bit of a special case,
                    # HASH in this context is not a comment but an allowable macro value
                    self.consume(TokenTypes.HASH)
                else:
                    self.raise_error("Expected macro or literal")

        self.consume(end)
        return ""  # Assume all macros expand to empty string

    def record(self):
        """
        Handler for an EPICS DB record.
        Example:
            record(ai, "$(P)RECORDNAME") {
                field(PINI, "YES")
                field(VAL, "0")
                info(alarm, "SIMPLE_01")
                alias("$(P)ALIASRECORDNAME")
            }
        Returns:
            dict:
                "type": record type, e.g. "ai"
                "name": record name, e.g. "$(P)RECORDNAME"
                "fields": list of fields. Each item in the list is a (key, value) tuple
                "infos": list of info fields. Each item in the list is a (key, value) tuple
                "aliases": list of record names aliased to this record
        """
        fields = []
        infos = []
        aliases = []
        previous_token_macro = False
        self.consume(TokenTypes.RECORD)
        record_type, record_name = self.key_value_pair()

        # Handle Macro before opening brace
        if self.next_token_is_macro():
            self.macro()

        # Handle comments before opening brace
        if self.current_token.type == TokenTypes.HASH:
            self.comment()

        # Special case for records with no body
        if self.current_token.type != TokenTypes.L_BRACE:
            return Record(record_type, record_name, [], [], [])
        with self.brace_delimited_block():
            while self.current_token.type != TokenTypes.R_BRACE:
                if self.next_token_is_macro():
                    previous_token_macro = True
                    self.macro()
                    continue
                if self.current_token.type == TokenTypes.FIELD:
                    fields.append(self.field(previous_token_macro))
                elif self.current_token.type == TokenTypes.INFO:
                    infos.append(self.info())
                elif self.current_token.type == TokenTypes.ALIAS:
                    aliases.append(self.alias_field())
                elif self.current_token.type == TokenTypes.HASH:
                    self.comment()
                else:
                    self.raise_error("Expected info, field or alias")
                previous_token_macro = False

        return Record(record_type, record_name, infos, fields, aliases)

    def alias(self):
        """
        Handler for an EPICS alias (DB level).
        Example:
            alias("$(P)RECORD1", "$(P)RECORD2")
        Returns:
             tuple of (record1, record2)
        """
        self.consume(TokenTypes.ALIAS)
        return self.key_value_pair()

    def comment(self):
        lineno = self.current_token.line
        self.consume(TokenTypes.HASH)

        # Consume all remaining tokens on this line, and do nothing with them.
        while self.current_token.line == lineno:
            self.consume(self.current_token.type)

    def db(self):
        """
        Top-level handler for an EPICS DB. A db is described as being a collection of records.
        Returns:
            List of records, aliases where each record follows the format described in  record()
        """
        records = Db("", [])
        while self.current_token.type != TokenTypes.EOF:
            if self.current_token.type == TokenTypes.RECORD:
                records.records.append(self.record())
            elif self.current_token.type == TokenTypes.HASH:
                self.comment()
            elif self.current_token.type == TokenTypes.ALIAS:
                pv, alias = self.alias()
                # Find the record that this alias belongs to, and add the alias to it.
                # Don't error if we can't find the record that it belongs to,
                # it might be in another DB
                for rec in records.records:
                    if pv == rec.pv or pv in rec.aliases:
                        rec.aliases.append(alias)
                        break
            elif self.next_token_is_macro():
                self.macro()
            else:
                self.raise_error("Expected record or alias")
        return records
