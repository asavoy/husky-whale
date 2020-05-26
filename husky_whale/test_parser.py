import pprint
import unittest

from husky_whale import token
from husky_whale.ast import Node
from husky_whale.lexer import Lexer
from husky_whale.parser import Parser
from husky_whale.utils import node_to_dict, node_to_tree


def dict_formatter(node_dict: dict) -> str:
    return pprint.pformat(node_dict, indent=2, width=120, sort_dicts=False)


class ParserTestCase(unittest.TestCase):
    def assertParsedAll(self, parser: Parser, result: Node):
        failures = []
        query_input = parser.lexer.input
        current_token = parser.current_token
        result_string = result.string()

        if query_input != result_string:
            failures.append(
                f"Result string does not match input:\nActual:   {result_string}\nExpected: {query_input}"
            )

        if current_token.type != token.EOF:
            failures.append(
                f"Did not parse until EOF:\nCurrent token: {repr(current_token)}"
            )

        if failures:
            debug_output = [
                f"Input:  {query_input}\nResult: {result_string}",
                node_to_tree(result),
            ]
            self.fail(
                "\n\n".join([f"{len(failures)} problems:"] + failures + debug_output)
            )

    def assertParsedStructure(self, parser: Parser, result: Node, expected: dict):
        failures = []
        query_input = parser.lexer.input
        result_string = result.string()

        actual_dict = node_to_dict(result)
        if actual_dict != expected:
            failures.append(
                f"Result structure does not match input:\nActual:   {dict_formatter(actual_dict)}\nExpected: {dict_formatter(expected)}"
            )

        if failures:
            debug_output = [
                f"Input:  {query_input}\nResult: {result_string}",
                node_to_tree(result),
            ]
            self.fail(
                "\n\n".join([f"{len(failures)} problems:"] + failures + debug_output)
            )

    def test_column_expression(self):
        query = "- 1 + 2 * 3 * 4"
        parser = Parser(Lexer(query))
        result = parser.parse_column_expression()
        self.assertParsedAll(parser, result)

    def test_column_expression_precedence(self):
        query = "- 1 + 2 * 3 + 4"
        parser = Parser(Lexer(query))
        result = parser.parse_column_expression()
        self.assertParsedAll(parser, result)
        self.assertParsedStructure(
            parser,
            result,
            {
                "left": {
                    "left": {"operator": "-", "right": "1"},
                    "operator": "+",
                    "right": {"left": "2", "operator": "*", "right": "3"},
                },
                "operator": "+",
                "right": "4",
            },
        )

        query = "- 1 + 2 * (3 + 4)"
        parser = Parser(Lexer(query))
        result = parser.parse_column_expression()
        self.assertParsedAll(parser, result)
        self.assertParsedStructure(
            parser,
            result,
            {
                "left": {"operator": "-", "right": "1"},
                "operator": "+",
                "right": {
                    "left": "2",
                    "operator": "*",
                    "right": {
                        "expression": {"left": "3", "operator": "+", "right": "4"}
                    },
                },
            },
        )

    def test_column_expression_and(self):
        query = "x = 1 AND y = 2"
        parser = Parser(Lexer(query))
        result = parser.parse_column_expression()
        self.assertParsedAll(parser, result)
        self.assertParsedStructure(
            parser,
            result,
            {
                "left": {"left": {"column": "x"}, "operator": "=", "right": "1"},
                "operator": "AND",
                "right": {"left": {"column": "y"}, "operator": "=", "right": "2"},
            },
        )

    def test_column_expression_is_not_null(self):
        query = "x IS NOT NULL"
        parser = Parser(Lexer(query))
        result = parser.parse_column_expression()
        self.assertParsedAll(parser, result)
        self.assertParsedStructure(
            parser,
            result,
            {
                "left": {"column": "x"},
                "operator": "IS",
                "right": {"operator": "NOT", "right": "NULL"},
            },
        )

    def test_column_expression_between(self):
        query = "x BETWEEN a AND b"
        parser = Parser(Lexer(query))
        result = parser.parse_column_expression()
        self.assertParsedAll(parser, result)

    def test_column_expression_call(self):
        with self.subTest("no args"):
            query = "now()"
            parser = Parser(Lexer(query))
            result = parser.parse_column_expression()
            self.assertParsedAll(parser, result)
            self.assertParsedStructure(parser, result, {"function": "now"})

        with self.subTest("composition"):
            query = "upper('hello') || concat(' ', lower('world'))"
            parser = Parser(Lexer(query))
            result = parser.parse_column_expression()
            self.assertParsedAll(parser, result)
            self.assertParsedStructure(
                parser,
                result,
                {
                    "left": {"function": "upper", "0": "'hello'"},
                    "operator": "||",
                    "right": {
                        "function": "concat",
                        "0": "' '",
                        "1": {"function": "lower", "0": "'world'"},
                    },
                },
            )

    def test_column_alias(self):
        with self.subTest("full form"):
            query = "x AS y"
            parser = Parser(Lexer(query))
            result = parser.parse_column_expression()
            self.assertParsedAll(parser, result)
            self.assertParsedStructure(
                parser, result, {"value": {"column": "x"}, "as_": "AS", "alias": "y"}
            )

        with self.subTest("shorthand form"):
            query = "x y"
            parser = Parser(Lexer(query))
            result = parser.parse_column_expression()
            self.assertParsedAll(parser, result)
            self.assertParsedStructure(
                parser, result, {"value": {"column": "x"}, "alias": "y"}
            )

    def test_table_alias(self):
        with self.subTest("full form"):
            query = "users AS u"
            parser = Parser(Lexer(query))
            result = parser.parse_table_expression()
            self.assertParsedAll(parser, result)
            self.assertParsedStructure(
                parser, result, {"value": {"table": "users"}, "as_": "AS", "alias": "u"}
            )

        with self.subTest("shorthand form"):
            query = "users u"
            parser = Parser(Lexer(query))
            result = parser.parse_table_expression()
            self.assertParsedAll(parser, result)
            self.assertParsedStructure(
                parser, result, {"value": {"table": "users"}, "alias": "u"}
            )

    def test_select_join(self):
        query = "SELECT u.id FROM users u JOIN schools ON u.school_id = schools.id"
        parser = Parser(Lexer(query))
        result = parser.parse_select()
        self.assertParsedAll(parser, result)
        self.assertParsedStructure(
            parser,
            result,
            {
                "select": "SELECT",
                "results": {"0": {"table": "u", "column": "id"}},
                "from_": {
                    "from_": "FROM",
                    "expression": {
                        "left": {"value": {"table": "users"}, "alias": "u"},
                        "join": "JOIN",
                        "right": {"table": "schools"},
                        "on": "ON",
                        "condition": {
                            "left": {"table": "u", "column": "school_id"},
                            "operator": "=",
                            "right": {"table": "schools", "column": "id"},
                        },
                    },
                },
            },
        )

    def test_select_full(self):
        query = "SELECT COUNT(*) FROM users WHERE is_active IS TRUE GROUP BY country HAVING COUNT(*) > 0 ORDER BY COUNT(*) DESC LIMIT 10"
        parser = Parser(Lexer(query))
        result = parser.parse_select()
        self.assertParsedAll(parser, result)
        self.assertParsedStructure(
            parser,
            result,
            {
                "select": "SELECT",
                "results": {"0": {"function": "COUNT", "0": "*"}},
                "from_": {"from_": "FROM", "expression": {"table": "users"}},
                "where": {
                    "where": "WHERE",
                    "expression": {
                        "left": {"column": "is_active"},
                        "operator": "IS",
                        "right": "TRUE",
                    },
                },
                "group_by": {"0": {"column": "country"}},
                "having": {
                    "having": "HAVING",
                    "expression": {
                        "left": {"0": "*", "function": "COUNT"},
                        "operator": ">",
                        "right": "0",
                    },
                },
                "order_by": {
                    "0": {"order": "DESC", "value": {"function": "COUNT", "0": "*"}},
                },
                "limit": {"expression": "10", "limit": "LIMIT"},
            },
        )


if __name__ == "__main__":
    unittest.main()
