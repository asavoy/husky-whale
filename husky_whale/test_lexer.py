import unittest
from typing import List

from husky_whale import token
from husky_whale.lexer import Lexer
from husky_whale.token import Token


def read_all_tokens(lexer: Lexer) -> List[Token]:
    tokens = []
    while True:
        t = lexer.next_token()
        tokens.append(t)
        if t.type == token.EOF:
            return tokens


class LexerTestCase(unittest.TestCase):
    def test_simple(self):
        query = "+()"
        lexer = Lexer(query)
        tokens = read_all_tokens(lexer)
        self.assertEqual(
            tokens,
            [
                Token(token.PLUS, "+"),
                Token(token.LPAREN, "("),
                Token(token.RPAREN, ")"),
                Token(token.EOF, ""),
            ],
        )

    def test_words(self):
        query = '''select 'hello' AS world, "select"'''
        lexer = Lexer(query)
        tokens = read_all_tokens(lexer)
        self.assertEqual(
            tokens,
            [
                Token(token.SELECT, "select"),
                Token(token.WHITESPACE, " "),
                Token(token.STRING, "'hello'"),
                Token(token.WHITESPACE, " "),
                Token(token.AS, "AS"),
                Token(token.WHITESPACE, " "),
                Token(token.IDENTIFIER, "world"),
                Token(token.COMMA, ","),
                Token(token.WHITESPACE, " "),
                Token(token.IDENTIFIER, '"select"'),
                Token(token.EOF, ""),
            ],
        )

    def test_is_not_null(self):
        query = "x IS NOT NULL"
        lexer = Lexer(query)
        tokens = read_all_tokens(lexer)
        self.assertEqual(
            tokens,
            [
                Token(token.IDENTIFIER, "x"),
                Token(token.WHITESPACE, " "),
                Token(token.IS, "IS"),
                Token(token.WHITESPACE, " "),
                Token(token.NOT, "NOT"),
                Token(token.WHITESPACE, " "),
                Token(token.NULL, "NULL"),
                Token(token.EOF, ""),
            ],
        )

    def test_identifier(self):
        query = """some_schema."some_table".some_field"""
        lexer = Lexer(query)
        tokens = read_all_tokens(lexer)
        self.assertEqual(
            tokens,
            [
                Token(token.IDENTIFIER, 'some_schema."some_table".some_field'),
                Token(token.EOF, ""),
            ],
        )

    def test_keyword_vs_function_identifier(self):
        # LEFT is a keyword as well as a function
        query = "LEFT JOIN"
        lexer = Lexer(query)
        tokens = read_all_tokens(lexer)
        self.assertEqual(
            tokens,
            [
                Token(token.LEFT, "LEFT"),
                Token(token.WHITESPACE, " "),
                Token(token.JOIN, "JOIN"),
                Token(token.EOF, ""),
            ],
        )

        query = "LEFT()"
        lexer = Lexer(query)
        tokens = read_all_tokens(lexer)
        self.assertEqual(
            tokens,
            [
                Token(token.IDENTIFIER, "LEFT"),
                Token(token.LPAREN, "("),
                Token(token.RPAREN, ")"),
                Token(token.EOF, ""),
            ],
        )

    def test_query(self):
        query = """
SELECT u.id, u.first_name || ' ' || u.last_name AS user_name
FROM users u
"""
        lexer = Lexer(query)
        tokens = read_all_tokens(lexer)
        self.assertEqual(
            tokens,
            [
                Token(token.WHITESPACE, "\n"),
                Token(token.SELECT, "SELECT"),
                Token(token.WHITESPACE, " "),
                Token(token.IDENTIFIER, "u.id"),
                Token(token.COMMA, ","),
                Token(token.WHITESPACE, " "),
                Token(token.IDENTIFIER, "u.first_name"),
                Token(token.WHITESPACE, " "),
                Token(token.PIPEPIPE, "||"),
                Token(token.WHITESPACE, " "),
                Token(token.STRING, "' '"),
                Token(token.WHITESPACE, " "),
                Token(token.PIPEPIPE, "||"),
                Token(token.WHITESPACE, " "),
                Token(token.IDENTIFIER, "u.last_name"),
                Token(token.WHITESPACE, " "),
                Token(token.AS, "AS"),
                Token(token.WHITESPACE, " "),
                Token(token.IDENTIFIER, "user_name"),
                Token(token.WHITESPACE, "\n"),
                Token(token.FROM, "FROM"),
                Token(token.WHITESPACE, " "),
                Token(token.IDENTIFIER, "users"),
                Token(token.WHITESPACE, " "),
                Token(token.IDENTIFIER, "u"),
                Token(token.WHITESPACE, "\n"),
                Token(token.EOF, ""),
            ],
        )


if __name__ == "__main__":
    unittest.main()
