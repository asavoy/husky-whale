# https://www.postgresql.org/docs/11/sql-syntax-lexical.html
# https://docs.aws.amazon.com/redshift/latest/dg/r_names.html
import dataclasses
from dataclasses import dataclass

from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class Node:
    preceding: List[str]
    trailing: List[str]

    def string(self) -> str:
        return ""

    def original_string(self) -> str:
        return "".join(self.preceding) + "".join(self.trailing)

    def child_nodes(self) -> Dict[str, "Node"]:
        return {
            field.name: getattr(self, field.name)
            for field in dataclasses.fields(self)
            if isinstance(getattr(self, field.name, None), Node)
        }

    def as_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    def replace(self, changes: Dict[str, Any]) -> "Node":
        return dataclasses.replace(self, **changes)


@dataclass(frozen=True)
class Keyword(Node):
    keyword: str
    literal: str

    def string(self) -> str:
        return self.literal.upper()

    def original_string(self) -> str:
        return "".join(self.preceding) + self.literal + "".join(self.trailing)


@dataclass(frozen=True)
class ColumnExpression(Node):
    pass


@dataclass(frozen=True)
class ColumnLiteral(ColumnExpression):
    literal: str

    def string(self) -> str:
        return self.literal

    def original_string(self) -> str:
        return "".join(self.preceding) + self.literal + "".join(self.trailing)


@dataclass(frozen=True)
class ColumnPrefixExpression(ColumnExpression):
    operator: Keyword
    right: ColumnExpression

    def string(self) -> str:
        return self.operator.string() + " " + self.right.string()

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.operator.original_string()
            + self.right.original_string()
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class ColumnInfixExpression(ColumnExpression):
    left: ColumnExpression
    operator: Keyword
    right: ColumnExpression

    def string(self) -> str:
        return (
            self.left.string()
            + " "
            + self.operator.string()
            + " "
            + self.right.string()
        )

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.left.original_string()
            + self.operator.original_string()
            + self.right.original_string()
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class ColumnGroupExpression(ColumnExpression):
    expression: ColumnExpression

    def string(self) -> str:
        return "(" + self.expression.string() + ")"

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + "("
            + self.expression.original_string()
            + ")"
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class ColumnBetweenExpression(ColumnExpression):
    left: ColumnExpression
    between: Keyword
    start: ColumnExpression
    and_: Keyword
    end: ColumnExpression

    def string(self) -> str:
        return (
            self.left.string()
            + " "
            + self.between.string()
            + " "
            + self.start.string()
            + " "
            + self.and_.string()
            + " "
            + self.end.string()
        )

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.left.original_string()
            + self.between.original_string()
            + self.start.original_string()
            + self.and_.original_string()
            + self.end.original_string()
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class ColumnIdentifier(ColumnExpression):
    schema: Optional[str]
    table: Optional[str]
    column: str

    def string(self) -> str:
        return (
            (self.schema + "." if self.schema else "")
            + (self.table + "." if self.table else "")
            + self.column
        )

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + (self.schema + "." if self.schema else "")
            + (self.table + "." if self.table else "")
            + self.column
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class ColumnCallExpression(ColumnExpression):
    function: ColumnIdentifier
    arguments: List[ColumnExpression]

    def string(self) -> str:
        return (
            self.function.string()
            + "("
            + ", ".join([ex.string() for ex in self.arguments])
            + ")"
        )

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.function.original_string()
            + "("
            + ",".join([ex.original_string() for ex in self.arguments])
            + ")"
            + "".join(self.trailing)
        )

    def child_nodes(self) -> Dict[str, "Node"]:
        return {
            str(index): self.arguments[index]
            for index, expression in enumerate(self.arguments)
            if isinstance(self.arguments[index], Node)
        }

    def as_dict(self) -> Dict[str, Any]:
        return dict(
            preceding=self.preceding,
            function=self.function,
            **self.child_nodes(),
            trailing=self.trailing,
        )

    def replace(self, changes: Dict[str, Any]) -> "Node":
        result = self
        for field, value in changes.items():
            if field in ("preceding", "trailing", "function"):
                result = dataclasses.replace(self, **{field: value})
            else:
                index = int(field, 10)
                new_arguments = (
                    result.arguments[:index] + [value] + result.arguments[index + 1 :]
                )
                result = dataclasses.replace(self, arguments=new_arguments)
        return dataclasses.replace(self, **changes)


@dataclass(frozen=True)
class ColumnAlias(ColumnExpression):
    value: ColumnExpression
    as_: Optional[Keyword]
    alias: str

    def string(self) -> str:
        return (
            self.value.string()
            + (" " + self.as_.string() + " " if self.as_ else " ")
            + self.alias
        )

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.value.original_string()
            + (self.as_.original_string() if self.as_ else "")
            + self.alias
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class ColumnOrderExpression(ColumnExpression):
    value: ColumnExpression
    order: Keyword

    def string(self) -> str:
        return self.value.string() + " " + self.order.string()

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.value.original_string()
            + self.order.original_string()
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class Statement(Node):
    pass


@dataclass(frozen=True)
class ResultsClause(Node):
    expressions: List[ColumnExpression]

    def string(self) -> str:
        return ", ".join([ex.string() for ex in self.expressions])

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + ",".join([ex.original_string() for ex in self.expressions])
            + "".join(self.trailing)
        )

    def child_nodes(self) -> Dict[str, "Node"]:
        return {
            str(index): self.expressions[index]
            for index, expression in enumerate(self.expressions)
            if isinstance(self.expressions[index], Node)
        }

    def as_dict(self) -> Dict[str, Any]:
        return dict(
            preceding=self.preceding, **self.child_nodes(), trailing=self.trailing,
        )

    def replace(self, changes: Dict[str, Any]) -> "Node":
        result = self
        for field, value in changes.items():
            if field in ("preceding", "trailing"):
                result = dataclasses.replace(self, **{field: value})
            else:
                index = int(field, 10)
                new_expressions = (
                    result.expressions[:index]
                    + [value]
                    + result.expressions[index + 1 :]
                )
                result = dataclasses.replace(self, expressions=new_expressions)
        return dataclasses.replace(self, **changes)


@dataclass(frozen=True)
class TableExpression(Node):
    pass


@dataclass(frozen=True)
class FromClause(Node):
    from_: Keyword
    expression: TableExpression

    def string(self) -> str:
        return self.from_.string() + " " + self.expression.string()

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.from_.original_string()
            + self.expression.original_string()
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class WhereClause(Node):
    where: Keyword
    expression: ColumnExpression

    def string(self) -> str:
        return self.where.string() + " " + self.expression.string()

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.where.original_string()
            + self.expression.original_string()
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class GroupByClause(Node):
    group: Keyword
    by: Keyword
    expressions: List[ColumnExpression]

    def string(self) -> str:
        return (
            self.group.string()
            + " "
            + self.by.string()
            + " "
            + ", ".join([ex.string() for ex in self.expressions])
        )

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.group.original_string()
            + self.by.original_string()
            + ",".join([ex.original_string() for ex in self.expressions])
            + "".join(self.trailing)
        )

    def child_nodes(self) -> Dict[str, "Node"]:
        return {
            str(index): self.expressions[index]
            for index, expression in enumerate(self.expressions)
            if isinstance(self.expressions[index], Node)
        }

    def as_dict(self) -> Dict[str, Any]:
        return dict(
            preceding=self.preceding,
            group=self.group,
            by=self.by,
            **self.child_nodes(),
            trailing=self.trailing,
        )

    def replace(self, changes: Dict[str, Any]) -> "Node":
        result = self
        for field, value in changes.items():
            if field in ("preceding", "trailing", "group", "by"):
                result = dataclasses.replace(self, **{field: value})
            else:
                index = int(field, 10)
                new_expressions = (
                    result.expressions[:index]
                    + [value]
                    + result.expressions[index + 1 :]
                )
                result = dataclasses.replace(self, expressions=new_expressions)
        return dataclasses.replace(self, **changes)


@dataclass(frozen=True)
class HavingClause(Node):
    having: Keyword
    expression: ColumnExpression

    def string(self) -> str:
        return self.having.string() + " " + self.expression.string()

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.having.original_string()
            + self.expression.original_string()
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class OrderByClause(Node):
    order: Keyword
    by: Keyword
    expressions: List[ColumnExpression]

    def string(self) -> str:
        return (
            self.order.string()
            + " "
            + self.by.string()
            + " "
            + ", ".join([ex.string() for ex in self.expressions])
        )

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.order.original_string()
            + self.by.original_string()
            + ",".join([ex.original_string() for ex in self.expressions])
            + "".join(self.trailing)
        )

    def child_nodes(self) -> Dict[str, "Node"]:
        return {
            str(index): self.expressions[index]
            for index, expression in enumerate(self.expressions)
            if isinstance(self.expressions[index], Node)
        }

    def as_dict(self) -> Dict[str, Any]:
        return dict(
            preceding=self.preceding,
            order=self.order,
            by=self.by,
            **self.child_nodes(),
            trailing=self.trailing,
        )

    def replace(self, changes: Dict[str, Any]) -> "Node":
        result = self
        for field, value in changes.items():
            if field in ("preceding", "trailing", "order", "by"):
                result = dataclasses.replace(self, **{field: value})
            else:
                index = int(field, 10)
                new_expressions = (
                    result.expressions[:index]
                    + [value]
                    + result.expressions[index + 1 :]
                )
                result = dataclasses.replace(self, expressions=new_expressions)
        return dataclasses.replace(self, **changes)


@dataclass(frozen=True)
class LimitClause(Node):
    limit: Keyword
    expression: ColumnExpression

    def string(self) -> str:
        return self.limit.string() + " " + self.expression.string()

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.limit.original_string()
            + self.expression.original_string()
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class Select(Statement):
    select: Keyword
    results: ResultsClause
    from_: Optional[FromClause]
    where: Optional[WhereClause]
    group_by: Optional[GroupByClause]
    having: Optional[HavingClause]
    order_by: Optional[OrderByClause]
    limit: Optional[LimitClause]

    def string(self) -> str:
        return " ".join(
            item
            for item in [
                self.select.string(),
                self.results.string(),
                self.from_.string() if self.from_ else "",
                self.where.string() if self.where else "",
                self.group_by.string() if self.group_by else "",
                self.having.string() if self.having else "",
                self.order_by.string() if self.order_by else "",
                self.limit.string() if self.limit else "",
            ]
            if item
        )

    def original_string(self) -> str:
        return "".join(
            item
            for item in [
                "".join(self.preceding),
                self.select.original_string(),
                self.results.original_string(),
                self.from_.original_string() if self.from_ else "",
                self.where.original_string() if self.where else "",
                self.group_by.original_string() if self.group_by else "",
                self.having.original_string() if self.having else "",
                self.order_by.original_string() if self.order_by else "",
                self.limit.original_string() if self.limit else "",
                "".join(self.trailing),
            ]
            if item
        )


@dataclass(frozen=True)
class TableIdentifier(TableExpression):
    schema: Optional[str]
    table: str

    def string(self) -> str:
        return (self.schema + "." if self.schema else "") + self.table

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + (self.schema + "." if self.schema else "")
            + self.table
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class TableAlias(ColumnExpression):
    value: TableExpression
    as_: Optional[Keyword]
    alias: str

    def string(self) -> str:
        return (
            self.value.string()
            + (" " + self.as_.string() + " " if self.as_ else " ")
            + self.alias
        )

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.value.original_string()
            + (self.as_.original_string() if self.as_ else "")
            + self.alias
            + "".join(self.trailing)
        )


@dataclass(frozen=True)
class TablePrefixExpression(TableExpression):
    operator: Keyword
    right: TableExpression


@dataclass(frozen=True)
class TableInfixExpression(TableExpression):
    left: TableExpression
    operator: Keyword
    right: TableExpression


@dataclass(frozen=True)
class TableJoinExpression(TableExpression):
    left: TableExpression
    join: Keyword
    right: TableExpression
    on: Keyword
    condition: ColumnExpression

    def string(self) -> str:
        return (
            self.left.string()
            + " "
            + self.join.string()
            + " "
            + self.right.string()
            + " "
            + self.on.string()
            + " "
            + self.condition.string()
        )

    def original_string(self) -> str:
        return (
            "".join(self.preceding)
            + self.left.original_string()
            + self.join.original_string()
            + self.right.original_string()
            + self.on.original_string()
            + self.condition.original_string()
            + "".join(self.trailing)
        )
