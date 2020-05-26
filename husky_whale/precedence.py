from enum import Enum

from husky_whale import token


class ColumnExpressionPrecedence(Enum):
    LOWEST = 0
    ASC_DESC = 1
    AS = 2
    OR = 3
    AND = 4
    NOT = 5
    IS = 6
    EQUALS_LESS_GREATER = 7
    BETWEEN_IN_LIKE = 8
    CONCAT = 9
    SUM = 10
    PRODUCT = 11
    PREFIX = 12
    CAST = 13
    CALL = 14


token_column_precedences = {
    token.ASC: ColumnExpressionPrecedence.ASC_DESC,
    token.DESC: ColumnExpressionPrecedence.ASC_DESC,
    token.AS: ColumnExpressionPrecedence.AS,
    token.IDENTIFIER: ColumnExpressionPrecedence.AS,
    token.OR: ColumnExpressionPrecedence.OR,
    token.AND: ColumnExpressionPrecedence.AND,
    token.NOT: ColumnExpressionPrecedence.NOT,
    token.IS: ColumnExpressionPrecedence.IS,
    token.EQUAL: ColumnExpressionPrecedence.EQUALS_LESS_GREATER,
    token.BANGEQUAL: ColumnExpressionPrecedence.EQUALS_LESS_GREATER,
    token.LTGT: ColumnExpressionPrecedence.EQUALS_LESS_GREATER,
    token.GT: ColumnExpressionPrecedence.EQUALS_LESS_GREATER,
    token.LT: ColumnExpressionPrecedence.EQUALS_LESS_GREATER,
    token.GTEQUAL: ColumnExpressionPrecedence.EQUALS_LESS_GREATER,
    token.LTEQUAL: ColumnExpressionPrecedence.EQUALS_LESS_GREATER,
    token.BETWEEN: ColumnExpressionPrecedence.BETWEEN_IN_LIKE,
    token.IN: ColumnExpressionPrecedence.BETWEEN_IN_LIKE,
    token.ILIKE: ColumnExpressionPrecedence.BETWEEN_IN_LIKE,
    token.LIKE: ColumnExpressionPrecedence.BETWEEN_IN_LIKE,
    token.PIPEPIPE: ColumnExpressionPrecedence.CONCAT,
    token.PLUS: ColumnExpressionPrecedence.SUM,
    token.MINUS: ColumnExpressionPrecedence.SUM,
    token.ASTERISK: ColumnExpressionPrecedence.PRODUCT,
    token.SLASH: ColumnExpressionPrecedence.PRODUCT,
    token.COLONCOLON: ColumnExpressionPrecedence.CAST,
    token.LPAREN: ColumnExpressionPrecedence.CALL,
}


class TableExpressionPrecedence(Enum):
    LOWEST = 0
    JOIN = 1
    AS = 2


token_table_precedences = {
    token.JOIN: TableExpressionPrecedence.JOIN,
    token.AS: TableExpressionPrecedence.AS,
    token.IDENTIFIER: TableExpressionPrecedence.AS,
}
