from typing import Callable, List, Optional

from husky_whale import ast
from husky_whale import token
from husky_whale.lexer import Lexer
from husky_whale.precedence import (
    ColumnExpressionPrecedence,
    TableExpressionPrecedence,
    token_column_precedences,
    token_table_precedences,
)
from husky_whale.token import Token


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_whitespace: List[Token] = []
        self.current_token: Token = Token(token.ILLEGAL, "")
        self.peek_whitespace: List[Token] = []
        self.peek_token: Token = Token(token.ILLEGAL, "")
        # Fill current and peek values
        self.next_token()
        self.next_token()

    def next_token(self) -> None:
        self.current_whitespace, self.current_token = (
            self.peek_whitespace,
            self.peek_token,
        )
        self.peek_whitespace, self.peek_token = self.lexer.next_whitespace_and_token()

    def current_token_is(self, *types):
        return any(self.current_token.type == type_ for type_ in types)

    def peek_token_is(self, *types):
        return any(self.peek_token.type == type_ for type_ in types)

    def current_column_precedence(self) -> ColumnExpressionPrecedence:
        return token_column_precedences.get(
            self.current_token.type, ColumnExpressionPrecedence.LOWEST
        )

    def peek_column_precedence(self) -> ColumnExpressionPrecedence:
        return token_column_precedences.get(
            self.peek_token.type, ColumnExpressionPrecedence.LOWEST
        )

    def parse_whitespace(self) -> List[str]:
        w = [w.literal for w in self.current_whitespace]
        self.current_whitespace = []
        return w

    def parse_statement(self) -> ast.Statement:
        return self.parse_select()

    def parse_select(self) -> ast.Select:
        preceding = self.parse_whitespace()

        assert self.current_token.type == token.SELECT
        select = self.parse_keyword()

        results = self.parse_results_clause()
        from_ = (
            self.parse_from_clause() if self.current_token.type == token.FROM else None
        )
        where = (
            self.parse_where_clause()
            if self.current_token.type == token.WHERE
            else None
        )
        group_by = (
            self.parse_group_by_clause()
            if self.current_token.type == token.GROUP
            else None
        )
        having = (
            self.parse_having_clause()
            if self.current_token.type == token.HAVING
            else None
        )
        order_by = (
            self.parse_order_by_clause()
            if self.current_token.type == token.ORDER
            else None
        )
        limit = (
            self.parse_limit_clause()
            if self.current_token.type == token.LIMIT
            else None
        )

        trailing = self.parse_whitespace()

        return ast.Select(
            preceding=preceding,
            select=select,
            results=results,
            from_=from_,
            where=where,
            group_by=group_by,
            having=having,
            order_by=order_by,
            limit=limit,
            trailing=trailing,
        )

    def parse_keyword(self) -> ast.Keyword:
        preceding = self.parse_whitespace()
        keyword = ast.Keyword(
            preceding=preceding,
            keyword=self.current_token.type,
            literal=self.current_token.literal,
            trailing=[],
        )
        self.next_token()
        return keyword

    def parse_results_clause(self) -> ast.ResultsClause:
        preceding = self.parse_whitespace()
        expressions = []
        while True:
            expression = self.parse_column_expression()
            trailing = self.parse_whitespace()
            expression = expression.replace(dict(trailing=trailing))
            expressions.append(expression)
            if self.current_token_is(token.COMMA):
                self.next_token()
                continue
            else:
                break

        return ast.ResultsClause(
            preceding=preceding, expressions=expressions, trailing=[]
        )

    def parse_from_clause(self) -> ast.FromClause:
        preceding = self.parse_whitespace()

        assert self.current_token.type == token.FROM
        from_ = self.parse_keyword()

        expression = self.parse_table_expression()

        trailing = self.parse_whitespace()
        # self.next_token()
        return ast.FromClause(
            preceding=preceding, from_=from_, expression=expression, trailing=trailing,
        )

    def parse_where_clause(self) -> ast.WhereClause:
        preceding = self.parse_whitespace()

        assert self.current_token.type == token.WHERE
        where = self.parse_keyword()

        expression = self.parse_column_expression()
        trailing = self.parse_whitespace()
        return ast.WhereClause(
            preceding=preceding, where=where, expression=expression, trailing=trailing,
        )

    def parse_group_by_clause(self) -> ast.GroupByClause:
        preceding = self.parse_whitespace()
        assert self.current_token.type == token.GROUP
        group = self.parse_keyword()
        assert self.current_token.type == token.BY
        by = self.parse_keyword()
        expressions = []
        while True:
            expression = self.parse_column_expression()
            trailing = self.parse_whitespace()
            expression = expression.replace(dict(trailing=trailing))
            expressions.append(expression)
            if self.current_token_is(token.COMMA):
                self.next_token()
                continue
            else:
                break

        return ast.GroupByClause(
            preceding=preceding,
            group=group,
            by=by,
            expressions=expressions,
            trailing=[],
        )

    def parse_having_clause(self) -> ast.HavingClause:
        preceding = self.parse_whitespace()

        assert self.current_token.type == token.HAVING
        having = self.parse_keyword()

        expression = self.parse_column_expression()
        trailing = self.parse_whitespace()
        return ast.HavingClause(
            preceding=preceding,
            having=having,
            expression=expression,
            trailing=trailing,
        )

    def parse_order_by_clause(self) -> ast.OrderByClause:
        preceding = self.parse_whitespace()
        assert self.current_token.type == token.ORDER
        order = self.parse_keyword()
        assert self.current_token.type == token.BY
        by = self.parse_keyword()
        expressions = []
        while True:
            expression = self.parse_column_expression()
            trailing = self.parse_whitespace()
            expression = expression.replace(dict(trailing=trailing))
            expressions.append(expression)
            if self.current_token_is(token.COMMA):
                self.next_token()
                continue
            else:
                break

        return ast.OrderByClause(
            preceding=preceding,
            order=order,
            by=by,
            expressions=expressions,
            trailing=[],
        )

    def parse_limit_clause(self) -> ast.LimitClause:
        preceding = self.parse_whitespace()

        assert self.current_token.type == token.LIMIT
        limit = self.parse_keyword()

        expression = self.parse_column_expression()
        trailing = self.parse_whitespace()
        self.next_token()
        return ast.LimitClause(
            preceding=preceding, limit=limit, expression=expression, trailing=trailing,
        )

    # Pratt parser algorithm
    def parse_column_expression(
        self, precedence: ColumnExpressionPrecedence = ColumnExpressionPrecedence.LOWEST
    ) -> ast.ColumnExpression:
        prefix_fn = self.column_prefix_parse_fn(self.current_token.type)
        if not prefix_fn:
            raise ParseError(
                f"no prefix parse function for token {self.current_token.type}"
            )

        left_exp = prefix_fn()

        while (
            self.current_token.type != token.EOF
            and precedence.value < self.current_column_precedence().value
        ):
            infix_fn = self.column_infix_parse_fn(self.current_token.type)
            if not infix_fn:
                return left_exp
            left_exp = infix_fn(left_exp)
        return left_exp

    def parse_column_prefix_expression(self) -> ast.ColumnPrefixExpression:
        preceding = self.parse_whitespace()
        operator = self.parse_keyword()
        return ast.ColumnPrefixExpression(
            preceding=preceding,
            operator=operator,
            right=self.parse_column_expression(ColumnExpressionPrecedence.PREFIX),
            trailing=[],
        )

    def parse_column_infix_expression(
        self, left_exp: ast.ColumnExpression
    ) -> ast.ColumnInfixExpression:
        precedence = self.current_column_precedence()
        operator = self.parse_keyword()
        expression = ast.ColumnInfixExpression(
            preceding=[],
            left=left_exp,
            operator=operator,
            right=self.parse_column_expression(precedence),
            trailing=[],
        )
        return expression

    def parse_column_group_expression(self) -> ast.ColumnGroupExpression:
        preceding = self.parse_whitespace()
        assert self.current_token.type == token.LPAREN
        self.next_token()
        expression = self.parse_column_expression()
        assert self.current_token.type == token.RPAREN
        trailing = self.parse_whitespace()
        self.next_token()
        return ast.ColumnGroupExpression(
            preceding=preceding, expression=expression, trailing=trailing,
        )

    def parse_column_call_expression(
        self, function: ast.ColumnIdentifier
    ) -> ast.ColumnCallExpression:
        arguments = []

        preceding = self.parse_whitespace()
        assert self.current_token.type == token.LPAREN
        self.next_token()

        if self.current_token.type == token.RPAREN:
            self.next_token()
            return ast.ColumnCallExpression(
                preceding=preceding, function=function, arguments=arguments, trailing=[]
            )

        while True:
            argument = self.parse_column_expression()
            trailing = self.parse_whitespace()
            argument = argument.replace(dict(trailing=trailing))
            arguments.append(argument)
            if self.current_token_is(token.COMMA):
                self.next_token()
                continue
            elif self.current_token_is(token.RPAREN):
                self.next_token()
                break
            else:
                raise ParseError("unexpected token " + self.current_token.type)

        return ast.ColumnCallExpression(
            preceding=preceding, function=function, arguments=arguments, trailing=[]
        )

    def parse_column_between_expression(
        self, left_exp: ast.ColumnExpression
    ) -> ast.ColumnBetweenExpression:
        assert self.current_token.type == token.BETWEEN
        precedence = self.current_column_precedence()
        between = self.parse_keyword()
        start = self.parse_column_expression(precedence)
        assert self.current_token.type == token.AND
        and_ = self.parse_keyword()
        expression = ast.ColumnBetweenExpression(
            preceding=[],
            left=left_exp,
            between=between,
            start=start,
            and_=and_,
            end=self.parse_column_expression(precedence),
            trailing=[],
        )
        return expression

    def column_prefix_parse_fn(
        self, token_type: str
    ) -> Callable[[], ast.ColumnPrefixExpression]:
        prefix_parse_fns = {
            token.INTEGER: self.parse_column_integer,
            token.STRING: self.parse_column_string,
            token.NULL: self.parse_keyword,
            token.TRUE: self.parse_keyword,
            token.FALSE: self.parse_keyword,
            token.IDENTIFIER: self.parse_column_identifier,
            token.ASTERISK: self.parse_keyword,
            token.NOT: self.parse_column_prefix_expression,
            token.SUBTRACT: self.parse_column_prefix_expression,
            token.LPAREN: self.parse_column_group_expression,
            # TODO: token.WHEN: self.parse_column_when_expression,
        }
        return prefix_parse_fns.get(token_type, None)

    def column_infix_parse_fn(
        self, token_type: str
    ) -> Callable[[ast.ColumnExpression], ast.ColumnInfixExpression]:
        infix_parse_fns = {
            token.AS: self.parse_column_alias_expression,
            token.IDENTIFIER: self.parse_column_alias_expression,
            token.DESC: self.parse_column_order_expression,
            token.ASC: self.parse_column_order_expression,
            token.AND: self.parse_column_infix_expression,
            token.OR: self.parse_column_infix_expression,
            token.IS: self.parse_column_infix_expression,
            token.BETWEEN: self.parse_column_between_expression,
            token.EQUAL: self.parse_column_infix_expression,
            token.BANGEQUAL: self.parse_column_infix_expression,
            token.LTGT: self.parse_column_infix_expression,
            token.GT: self.parse_column_infix_expression,
            token.LT: self.parse_column_infix_expression,
            token.GTEQUAL: self.parse_column_infix_expression,
            token.LTEQUAL: self.parse_column_infix_expression,
            token.PLUS: self.parse_column_infix_expression,
            token.MINUS: self.parse_column_infix_expression,
            token.ASTERISK: self.parse_column_infix_expression,
            token.SLASH: self.parse_column_infix_expression,
            token.COLONCOLON: self.parse_column_infix_expression,
            token.PIPEPIPE: self.parse_column_infix_expression,
            token.LPAREN: self.parse_column_call_expression,
        }
        return infix_parse_fns.get(token_type, None)

    def parse_column_integer(self) -> ast.ColumnLiteral:
        preceding = self.parse_whitespace()
        literal = self.current_token.literal
        self.next_token()
        return ast.ColumnLiteral(preceding=preceding, literal=literal, trailing=[],)

    def parse_column_string(self) -> ast.ColumnLiteral:
        preceding = self.parse_whitespace()
        literal = self.current_token.literal
        self.next_token()
        return ast.ColumnLiteral(preceding=preceding, literal=literal, trailing=[],)

    def parse_column_identifier(self) -> ast.ColumnIdentifier:
        preceding = self.parse_whitespace()
        # TODO: parse properly
        parts = self.current_token.literal.split(".")
        assert len(parts) <= 3
        self.next_token()
        return ast.ColumnIdentifier(
            preceding=preceding,
            schema=parts[-3] if len(parts) == 3 else None,
            table=parts[-2] if len(parts) >= 2 else None,
            column=parts[-1],
            trailing=[],
        )

    def parse_column_alias_expression(
        self, left_exp: ast.ColumnExpression
    ) -> ast.ColumnAlias:
        preceding = self.parse_whitespace()

        as_ = self.parse_keyword() if self.current_token.type == token.AS else None

        assert self.current_token.type == token.IDENTIFIER
        alias = self.current_token.literal
        self.next_token()

        return ast.ColumnAlias(
            preceding=preceding, value=left_exp, as_=as_, alias=alias, trailing=[],
        )

    def parse_column_order_expression(
        self, left_exp: ast.ColumnExpression
    ) -> ast.ColumnOrderExpression:
        preceding = self.parse_whitespace()

        assert self.current_token.type in (token.ASC, token.DESC)
        order = self.parse_keyword()

        return ast.ColumnOrderExpression(
            preceding=preceding, value=left_exp, order=order, trailing=[],
        )

    def current_table_precedence(self) -> TableExpressionPrecedence:
        return token_table_precedences.get(
            self.current_token.type, TableExpressionPrecedence.LOWEST
        )

    def peek_table_precedence(self) -> TableExpressionPrecedence:
        return token_table_precedences.get(
            self.peek_token.type, TableExpressionPrecedence.LOWEST
        )

    # Pratt parser algorithm
    def parse_table_expression(
        self, precedence: TableExpressionPrecedence = TableExpressionPrecedence.LOWEST
    ) -> ast.TableExpression:
        prefix_fn = self.table_prefix_parse_fn(self.current_token.type)
        if not prefix_fn:
            raise ParseError(
                f"no prefix parse function for token {self.current_token.type}"
            )

        left_exp = prefix_fn()

        while (
            self.current_token.type != token.EOF
            and precedence.value < self.current_table_precedence().value
        ):
            infix_fn = self.table_infix_parse_fn(self.current_token.type)
            if not infix_fn:
                return left_exp
            left_exp = infix_fn(left_exp)
        return left_exp

    def parse_table_prefix_expression(self) -> ast.TablePrefixExpression:
        preceding = self.parse_whitespace()
        operator = self.parse_keyword()
        return ast.TablePrefixExpression(
            preceding=preceding,
            operator=operator,
            right=self.parse_table_expression(TableExpressionPrecedence.PREFIX),
            trailing=[],
        )

    def parse_table_infix_expression(
        self, left_exp: ast.TableExpression
    ) -> ast.TableInfixExpression:
        preceding = self.parse_whitespace()
        precedence = self.current_table_precedence()
        operator = self.parse_keyword()
        expression = ast.TableInfixExpression(
            preceding=preceding,
            left=left_exp,
            operator=operator,
            right=self.parse_table_expression(precedence),
            trailing=[],
        )
        return expression

    def parse_table_join(
        self, left_exp: ast.TableExpression
    ) -> ast.TableJoinExpression:
        preceding = self.parse_whitespace()

        assert self.current_token.type == token.JOIN
        join = self.parse_keyword()
        right_exp = self.parse_table_expression()

        assert self.current_token.type == token.ON
        on = self.parse_keyword()
        condition = self.parse_column_expression()
        trailing = self.parse_whitespace()

        return ast.TableJoinExpression(
            preceding=preceding,
            left=left_exp,
            join=join,
            right=right_exp,
            on=on,
            condition=condition,
            trailing=trailing,
        )

    def table_prefix_parse_fn(
        self, token_type: str
    ) -> Optional[Callable[[], ast.TablePrefixExpression]]:
        prefix_parse_fns = {
            token.IDENTIFIER: self.parse_table_identifier,
            # TODO: subquery
            # token.LPAREN: self.parse_prefix_expression,
        }
        return prefix_parse_fns.get(token_type, None)

    def table_infix_parse_fn(
        self, token_type: str
    ) -> Optional[Callable[[ast.TableExpression], ast.TableInfixExpression]]:
        infix_parse_fns = {
            token.JOIN: self.parse_table_join,
            token.AS: self.parse_table_alias_expression,
            token.IDENTIFIER: self.parse_table_alias_expression,
        }
        return infix_parse_fns.get(token_type, None)

    def parse_table_identifier(self) -> ast.TableIdentifier:
        preceding = self.parse_whitespace()
        # TODO: parse properly
        parts = self.current_token.literal.split(".")
        assert len(parts) <= 3
        self.next_token()
        return ast.TableIdentifier(
            preceding=preceding,
            schema=parts[-2] if len(parts) == 2 else None,
            table=parts[-1],
            trailing=[],
        )

    def parse_table_alias_expression(
        self, left_exp: ast.TableExpression
    ) -> ast.TableAlias:
        preceding = self.parse_whitespace()

        as_ = self.parse_keyword() if self.current_token.type == token.AS else None

        assert self.current_token.type == token.IDENTIFIER
        alias = self.current_token.literal
        self.next_token()

        return ast.TableAlias(
            preceding=preceding, value=left_exp, as_=as_, alias=alias, trailing=[],
        )
