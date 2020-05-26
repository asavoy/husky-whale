from typing import List

from husky_whale import token
from husky_whale.token import Token


class Lexer:
    def __init__(self, input: str):
        self.input: str = input
        self.char: str = ""
        self.char_pos: int = 0
        self.read_pos: int = 0
        self.read_char()

    def next_whitespace_and_token(self) -> (List[Token], Token):
        whitespace = []
        while True:
            t = self.next_token()
            if t.type in (token.WHITESPACE, token.COMMENT_SINGLE):
                whitespace.append(t)
                continue
            else:
                return whitespace, t

    def next_token(self) -> Token:
        c = self.char
        t = Token(token.ILLEGAL, c)

        if is_whitespace(c):
            return Token(token.WHITESPACE, self.read_whitespace())
        elif c == '"':
            return Token(token.IDENTIFIER, self.read_identifier())
        elif c == "'":
            return Token(token.STRING, self.read_string())
        elif c == "+":
            t = Token(token.PLUS, c)
        elif c == "-":
            t = Token(token.SUBTRACT, c)
        elif c == "*":
            t = Token(token.ASTERISK, c)
        elif c == "/":
            t = Token(token.SLASH, c)
        elif c == "|":
            if self.peek_char() == "|":
                self.read_char()
                t = Token(token.PIPEPIPE, c + self.char)
            else:
                t = Token(token.PIPE, c)
        elif c == "=":
            t = Token(token.EQUAL, c)
        elif c == "!":
            if self.peek_char() == "=":
                self.read_char()
                t = Token(token.BANGEQUAL, c + self.char)
            else:
                t = Token(token.BANG, c)
        elif c == "<":
            pc = self.peek_char()
            if pc == "=":
                self.read_char()
                t = Token(token.LTEQUAL, c + self.char)
            elif pc == ">":
                self.read_char()
                t = Token(token.LTGT, c + self.char)
            else:
                t = Token(token.LT, c)
        elif c == ">":
            if self.peek_char() == "=":
                self.read_char()
                t = Token(token.GTEQUAL, c + self.char)
            else:
                t = Token(token.GT, c)
        elif c == ",":
            t = Token(token.COMMA, c)
        elif c == ".":
            t = Token(token.FULLSTOP, c)
        elif c == ":":
            if self.peek_char() == ":":
                self.read_char()
                t = Token(token.COLONCOLON, c + self.char)
            else:
                t = Token(token.COLON, c)
        elif c == "(":
            t = Token(token.LPAREN, c)
        elif c == ")":
            t = Token(token.RPAREN, c)
        elif c == "":
            t = Token(token.EOF, c)
        else:
            if is_letter(c) or c == "_":
                identifier = self.read_identifier()
                identifier_upper = identifier.upper()
                if identifier_upper in keyword_tokens and self.char != "(":
                    return Token(keyword_tokens[identifier_upper], identifier)
                else:
                    return Token(token.IDENTIFIER, identifier)
            elif is_number(c):
                integer = self.read_integer()
                return Token(token.INTEGER, integer)
            else:
                pass
        self.read_char()
        return t

    def peek_char(self) -> str:
        if self.read_pos >= len(self.input):
            return ""
        else:
            return self.input[self.read_pos]

    def read_char(self) -> None:
        if self.read_pos >= len(self.input):
            self.char = ""
        else:
            self.char = self.input[self.read_pos]
        self.char_pos = self.read_pos
        self.read_pos += 1

    def read_whitespace(self) -> str:
        start = self.char_pos
        while is_whitespace(self.char):
            self.read_char()
        return self.input[start : self.char_pos]

    def read_identifier(self) -> str:
        start = self.char_pos
        while True:
            quoted = self.char == '"'
            if quoted:
                self.read_char()
                while self.char != '"':
                    self.read_char()
                self.read_char()
            else:
                while is_identifier_char(self.char):
                    self.read_char()
            if self.char != ".":
                break
            else:
                self.read_char()
                continue
        return self.input[start : self.char_pos]

    def read_string(self) -> str:
        start = self.char_pos
        self.read_char()
        while self.char != "'":
            self.read_char()
        self.read_char()
        return self.input[start : self.char_pos]

    def read_integer(self) -> str:
        start = self.char_pos
        while is_number(self.char):
            self.read_char()
        return self.input[start : self.char_pos]


def is_letter(c: str) -> bool:
    return "a" <= c <= "z" or "A" <= c <= "Z"


def is_number(c: str) -> bool:
    return "0" <= c <= "9"


def is_identifier_char(c: str) -> bool:
    return "a" <= c <= "z" or "A" <= c <= "Z" or "0" <= c <= "9" or c == "_"


def is_whitespace(c: str) -> bool:
    return c == " " or c == "\n" or c == "\t"


keyword_tokens = {
    "AES128": token.AES128,
    "AES256": token.AES256,
    "ALL": token.ALL,
    "ALLOWOVERWRITE": token.ALLOWOVERWRITE,
    "ANALYSE": token.ANALYSE,
    "ANALYZE": token.ANALYZE,
    "AND": token.AND,
    "ANY": token.ANY,
    "ARRAY": token.ARRAY,
    "AS": token.AS,
    "ASC": token.ASC,
    "AVG": token.AVG,
    "AUTHORIZATION": token.AUTHORIZATION,
    "AZ64": token.AZ64,
    "BACKUP": token.BACKUP,
    "BETWEEN": token.BETWEEN,
    "BINARY": token.BINARY,
    "BLANKSASNULL": token.BLANKSASNULL,
    "BOTH": token.BOTH,
    "BY": token.BY,
    "BYTEDICT": token.BYTEDICT,
    "BZIP2": token.BZIP2,
    "CASE": token.CASE,
    "CAST": token.CAST,
    "CHECK": token.CHECK,
    "COLLATE": token.COLLATE,
    "COLUMN": token.COLUMN,
    "COUNT": token.COUNT,
    "CONSTRAINT": token.CONSTRAINT,
    "CREATE": token.CREATE,
    "CREDENTIALS": token.CREDENTIALS,
    "CROSS": token.CROSS,
    "CURRENT_DATE": token.CURRENT_DATE,
    "CURRENT_TIME": token.CURRENT_TIME,
    "CURRENT_TIMESTAMP": token.CURRENT_TIMESTAMP,
    "CURRENT_USER": token.CURRENT_USER,
    "CURRENT_USER_ID": token.CURRENT_USER_ID,
    "DEFAULT": token.DEFAULT,
    "DEFERRABLE": token.DEFERRABLE,
    "DEFLATE": token.DEFLATE,
    "DEFRAG": token.DEFRAG,
    "DELTA": token.DELTA,
    "DELTA32K": token.DELTA32K,
    "DESC": token.DESC,
    "DISABLE": token.DISABLE,
    "DISTINCT": token.DISTINCT,
    "DO": token.DO,
    "ELSE": token.ELSE,
    "EMPTYASNULL": token.EMPTYASNULL,
    "ENABLE": token.ENABLE,
    "ENCODE": token.ENCODE,
    "ENCRYPT": token.ENCRYPT,
    "ENCRYPTION": token.ENCRYPTION,
    "END": token.END,
    "EXCEPT": token.EXCEPT,
    "EXPLICIT": token.EXPLICIT,
    "FALSE": token.FALSE,
    "FOR": token.FOR,
    "FOREIGN": token.FOREIGN,
    "FREEZE": token.FREEZE,
    "FROM": token.FROM,
    "FULL": token.FULL,
    "GLOBALDICT256": token.GLOBALDICT256,
    "GLOBALDICT64K": token.GLOBALDICT64K,
    "GRANT": token.GRANT,
    "GROUP": token.GROUP,
    "GZIP": token.GZIP,
    "HAVING": token.HAVING,
    "IDENTITY": token.IDENTITY,
    "IGNORE": token.IGNORE,
    "ILIKE": token.ILIKE,
    "IN": token.IN,
    "INITIALLY": token.INITIALLY,
    "INNER": token.INNER,
    "INTERSECT": token.INTERSECT,
    "INTO": token.INTO,
    "IS": token.IS,
    "ISNULL": token.ISNULL,
    "JOIN": token.JOIN,
    "LANGUAGE": token.LANGUAGE,
    "LEADING": token.LEADING,
    "LEFT": token.LEFT,
    "LIKE": token.LIKE,
    "LIMIT": token.LIMIT,
    "LOCALTIME": token.LOCALTIME,
    "LOCALTIMESTAMP": token.LOCALTIMESTAMP,
    "LUN": token.LUN,
    "LUNS": token.LUNS,
    "LZO": token.LZO,
    "LZOP": token.LZOP,
    "MINUS": token.MINUS,
    "MOSTLY13": token.MOSTLY13,
    "MOSTLY32": token.MOSTLY32,
    "MOSTLY8": token.MOSTLY8,
    "NATURAL": token.NATURAL,
    "NEW": token.NEW,
    "NOT": token.NOT,
    "NOTNULL": token.NOTNULL,
    "NULL": token.NULL,
    "NULLS": token.NULLS,
    "OFF": token.OFF,
    "OFFLINE": token.OFFLINE,
    "OFFSET": token.OFFSET,
    "OID": token.OID,
    "OLD": token.OLD,
    "ON": token.ON,
    "ONLY": token.ONLY,
    "OPEN": token.OPEN,
    "OR": token.OR,
    "ORDER": token.ORDER,
    "OUTER": token.OUTER,
    "OVERLAPS": token.OVERLAPS,
    "PARALLEL": token.PARALLEL,
    "PARTITION": token.PARTITION,
    "PERCENT": token.PERCENT,
    "PERMISSIONS": token.PERMISSIONS,
    "PLACING": token.PLACING,
    "PRIMARY": token.PRIMARY,
    "RAW": token.RAW,
    "READRATIO": token.READRATIO,
    "RECOVER": token.RECOVER,
    "REFERENCES": token.REFERENCES,
    "RESPECT": token.RESPECT,
    "REJECTLOG": token.REJECTLOG,
    "RESORT": token.RESORT,
    "RESTORE": token.RESTORE,
    "RIGHT": token.RIGHT,
    "SELECT": token.SELECT,
    "SESSION_USER": token.SESSION_USER,
    "SIMILAR": token.SIMILAR,
    "SNAPSHOT": token.SNAPSHOT,
    "SOME": token.SOME,
    "SUM": token.SUM,
    "SYSDATE": token.SYSDATE,
    "SYSTEM": token.SYSTEM,
    "TABLE": token.TABLE,
    "TAG": token.TAG,
    "TDES": token.TDES,
    "TEXT255": token.TEXT255,
    "TEXT32K": token.TEXT32K,
    "THEN": token.THEN,
    "TIMESTAMP": token.TIMESTAMP,
    "TO": token.TO,
    "TOP": token.TOP,
    "TRAILING": token.TRAILING,
    "TRUE": token.TRUE,
    "TRUNCATECOLUMNS": token.TRUNCATECOLUMNS,
    "UNION": token.UNION,
    "UNIQUE": token.UNIQUE,
    "USER": token.USER,
    "USING": token.USING,
    "VERBOSE": token.VERBOSE,
    "WALLET": token.WALLET,
    "WHEN": token.WHEN,
    "WHERE": token.WHERE,
    "WITH": token.WITH,
    "WITHOUT": token.WITHOUT,
}
