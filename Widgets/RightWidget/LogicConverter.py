"""
LogicConverter — 逻辑表达式 ↔ 图形门电路的双向转化器

纯静态工具类，无 UI 依赖。

语法 (BNF):
    <expr>       := <comparison> ( "OR" <comparison> )*
    <comparison> := <term> ( <comp_op> <term> )?
    <comp_op>    := "==" | "!=" | "<" | ">" | "<=" | ">="
    <term>       := <factor> ( "AND" <factor> )*
    <factor>     := "NOT" <factor>
                  | "(" <expr> ")"
                  | <variable>
                  | <number>
                  | <string>
                  | <gate_call>

    <gate_call>  := <gate_name> "(" <expr> ( "," <expr> )* ")"
    <gate_name>  := "AND" | "OR" | "NOT" | "NAND" | "NOR" | "XOR"
    <variable>   := [A-Z_][A-Z0-9_]*
    <number>     := \d+(\.\d+)?
    <string>     := "[^"]*"
"""
from __future__ import annotations

import re
from collections import OrderedDict, defaultdict, deque
from typing import Any, Optional

# ════════════════════════════════════════════════════════════════
# LogicParseError
# ════════════════════════════════════════════════════════════════


class LogicParseError(Exception):
    """逻辑表达式解析错误，包含行列位置信息"""

    def __init__(self, message: str, line: int = 1, column: int = 1):
        self.line = line
        self.column = column
        self.message = message
        super().__init__(f"第 {line} 行第 {column} 列: {message}")


# ════════════════════════════════════════════════════════════════
# Token definitions
# ════════════════════════════════════════════════════════════════


class TokenType:
    """Token 类型常量"""
    VARIABLE = "VARIABLE"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    NAND = "NAND"
    NOR = "NOR"
    XOR = "XOR"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    ASSIGN = "ASSIGN"
    # 数值变量和字符变量支持 (Task-3)
    NUMBER = "NUMBER"
    STRING = "STRING"
    COMP_EQ = "COMP_EQ"
    COMP_NE = "COMP_NE"
    COMP_LT = "COMP_LT"
    COMP_GT = "COMP_GT"
    COMP_LE = "COMP_LE"
    COMP_GE = "COMP_GE"
    EOF = "EOF"


class Token:
    """词法单元"""

    __slots__ = ("type", "value", "line", "column")

    def __init__(self, type_: str, value: str, line: int, column: int):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, L{self.line}:C{self.column})"


# ════════════════════════════════════════════════════════════════
# Lexer (词法分析器)
# ════════════════════════════════════════════════════════════════


class Lexer:
    """词法分析器：将文本字符串转化为 Token 流"""

    KEYWORDS = {
        "AND": TokenType.AND,
        "OR": TokenType.OR,
        "NOT": TokenType.NOT,
        "NAND": TokenType.NAND,
        "NOR": TokenType.NOR,
        "XOR": TokenType.XOR,
    }

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1

    def _current(self) -> str:
        """返回当前字符，越界返回空串"""
        if self.pos < len(self.text):
            return self.text[self.pos]
        return ""

    def _advance(self):
        """前进一个字符，更新行列号"""
        if self._current() == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1

    def _skip_whitespace(self):
        """跳过空白和注释"""
        while self.pos < len(self.text):
            ch = self._current()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "#":
                # 行注释：跳过直到行尾
                while self.pos < len(self.text) and self._current() != "\n":
                    self._advance()
            else:
                break

    def _make_token(self, type_: str, value: str) -> Token:
        return Token(type_, value, self.line, self.column - len(value) + 1)

    def tokenize(self) -> list[Token]:
        """执行词法分析，返回 Token 列表"""
        tokens: list[Token] = []

        while self.pos < len(self.text):
            self._skip_whitespace()
            if self.pos >= len(self.text):
                break

            ch = self._current()
            start_col = self.column
            start_line = self.line

            # 单字符 / 双字符 token
            if ch == "(":
                self._advance()
                tokens.append(Token(TokenType.LPAREN, "(", start_line, start_col))
            elif ch == ")":
                self._advance()
                tokens.append(Token(TokenType.RPAREN, ")", start_line, start_col))
            elif ch == ",":
                self._advance()
                tokens.append(Token(TokenType.COMMA, ",", start_line, start_col))
            elif ch == "=":
                # = 或 == (Task-3: 双字符比较运算符优先)
                self._advance()
                if self._current() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.COMP_EQ, "==", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.ASSIGN, "=", start_line, start_col))
            elif ch == "<":
                # < 或 <= (Task-3)
                self._advance()
                if self._current() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.COMP_LE, "<=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.COMP_LT, "<", start_line, start_col))
            elif ch == ">":
                # > 或 >= (Task-3)
                self._advance()
                if self._current() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.COMP_GE, ">=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.COMP_GT, ">", start_line, start_col))
            elif ch == "+":
                # 速记符号: + 代表 OR
                self._advance()
                tokens.append(Token(TokenType.OR, "+", start_line, start_col))
            elif ch == "*":
                # 速记符号: * 代表 AND
                self._advance()
                tokens.append(Token(TokenType.AND, "*", start_line, start_col))
            elif ch == "!":
                # 速记符号: ! 或 != (Task-3: 双字符比较运算符优先)
                self._advance()
                if self._current() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.COMP_NE, "!=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.NOT, "!", start_line, start_col))
            elif ch == "~":
                # 速记符号: ~ 代表 NOT
                self._advance()
                tokens.append(Token(TokenType.NOT, "~", start_line, start_col))
            elif ch == '"':
                # 字符串字面量 (Task-3)
                self._advance()  # skip opening quote
                content_chars = []
                while self.pos < len(self.text) and self._current() != '"':
                    if self._current() == '\n':
                        raise LogicParseError(
                            "字符串字面量中不允许换行", self.line, self.column
                        )
                    if self._current() == '\\':
                        self._advance()
                        if self.pos >= len(self.text):
                            raise LogicParseError(
                                "未闭合的字符串字面量", start_line, start_col
                            )
                        escaped = self._current()
                        if escaped == '"':
                            content_chars.append('"')
                        elif escaped == '\\':
                            content_chars.append('\\')
                        elif escaped == 'n':
                            content_chars.append('\n')
                        else:
                            content_chars.append(escaped)
                    else:
                        content_chars.append(self._current())
                    self._advance()
                if self.pos >= len(self.text):
                    raise LogicParseError(
                        "未闭合的字符串字面量", start_line, start_col
                    )
                self._advance()  # skip closing quote
                tokens.append(Token(TokenType.STRING, "".join(content_chars),
                                    start_line, start_col))
            elif ch.isdigit():
                # 数字字面量 (Task-3)
                num_chars = []
                while self.pos < len(self.text) and (
                    self._current().isdigit() or self._current() == "."
                ):
                    num_chars.append(self._current())
                    self._advance()
                num_text = "".join(num_chars)
                if num_text.count(".") > 1:
                    raise LogicParseError(
                        f"非法数字格式 '{num_text}'", start_line, start_col
                    )
                try:
                    value = float(num_text) if "." in num_text else int(num_text)
                except ValueError:
                    raise LogicParseError(
                        f"非法数字格式 '{num_text}'", start_line, start_col
                    )
                tokens.append(Token(TokenType.NUMBER, value,
                                    start_line, start_col))
            elif ch.isalpha() or ch == "_":
                # 标识符或关键字
                ident = []
                while self.pos < len(self.text) and (self._current().isalnum() or self._current() == "_"):
                    ident.append(self._current())
                    self._advance()
                word = "".join(ident).upper()
                if word in self.KEYWORDS:
                    token_type = self.KEYWORDS[word]
                else:
                    # 变量名保持原始大小写，但规范要求 [A-Z_][A-Z0-9_]*
                    token_type = TokenType.VARIABLE
                tokens.append(Token(token_type, word if token_type != TokenType.VARIABLE else "".join(ident),
                                    start_line, start_col))
            else:
                # 非法字符
                raise LogicParseError(
                    f"非法字符 '{ch}' (U+{ord(ch):04X})",
                    self.line, self.column
                )

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens


# ════════════════════════════════════════════════════════════════
# AST 节点定义
# ════════════════════════════════════════════════════════════════


class ASTNode:
    """抽象语法树节点基类"""
    __slots__ = ()


class VariableNode(ASTNode):
    """变量节点"""
    __slots__ = ("name",)

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"Variable({self.name})"


class UnaryOpNode(ASTNode):
    """一元运算节点 (NOT)"""
    __slots__ = ("op", "operand")

    def __init__(self, op: str, operand: ASTNode):
        self.op = op  # "NOT"
        self.operand = operand

    def __repr__(self):
        return f"UnaryOp({self.op}, {self.operand})"


class BinaryOpNode(ASTNode):
    """二元运算节点 (AND, OR)"""
    __slots__ = ("op", "left", "right")

    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.op = op  # "AND" or "OR"
        self.left = left
        self.right = right

    def __repr__(self):
        return f"BinaryOp({self.op}, {self.left}, {self.right})"


class GateCallNode(ASTNode):
    """门调用节点 e.g. AND(A, B), NAND(A, B)"""
    __slots__ = ("gate_name", "args")

    def __init__(self, gate_name: str, args: list[ASTNode]):
        self.gate_name = gate_name  # AND, OR, NOT, NAND, NOR, XOR
        self.args = args

    def __repr__(self):
        return f"GateCall({self.gate_name}, {self.args})"


class ComparisonNode(ASTNode):
    """比较运算节点 (Task-3)"""
    __slots__ = ("op", "left", "right")

    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.op = op      # "==", "!=", "<", ">", "<=", ">="
        self.left = left
        self.right = right

    def __repr__(self):
        return f"Comparison({self.op}, {self.left}, {self.right})"


class NumberNode(ASTNode):
    """数字字面量节点 (Task-3)"""
    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value  # int or float

    def __repr__(self):
        return f"Number({self.value})"


class StringNode(ASTNode):
    """字符串字面量节点 (Task-3)"""
    __slots__ = ("value",)

    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f"String({self.value!r})"


# ════════════════════════════════════════════════════════════════
# Parser (递归下降语法分析器)
# ════════════════════════════════════════════════════════════════


class Parser:
    """
    递归下降语法分析器

    Grammar:
        <statement>  := <expr>
                      | <variable> "=" <expr>

        <expr>       := <comparison> ( "OR" <comparison> )*
        <comparison> := <term> ( <comp_op> <term> )?
        <comp_op>    := "==" | "!=" | "<" | ">" | "<=" | ">="
        <term>       := <factor> ( "AND" <factor> )*
        <factor>     := "NOT" <factor>
                      | "(" <expr> ")"
                      | <variable>
                      | <number>
                      | <string>
                      | <gate_call>

        <gate_call>  := <gate_name> "(" <expr> ( "," <expr> )* ")"
    """

    # Gate tokens that can start a gate_call
    GATE_TOKENS = {TokenType.AND, TokenType.OR, TokenType.NOT,
                   TokenType.NAND, TokenType.NOR, TokenType.XOR}

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _consume(self, expected_type: Optional[str] = None) -> Token:
        """消费当前 token，可选类型检查"""
        token = self._peek()
        if expected_type is not None and token.type != expected_type:
            raise LogicParseError(
                f"期望 {self._type_name(expected_type)}，"
                f"但遇到 {self._type_name(token.type)} '{token.value}'",
                token.line, token.column
            )
        self.pos += 1
        return token

    @staticmethod
    def _type_name(type_: str) -> str:
        """返回 Token 类型的中文或可读名称"""
        names = {
            TokenType.VARIABLE: "变量",
            TokenType.AND: "'AND'",
            TokenType.OR: "'OR'",
            TokenType.NOT: "'NOT'",
            TokenType.NAND: "'NAND'",
            TokenType.NOR: "'NOR'",
            TokenType.XOR: "'XOR'",
            TokenType.LPAREN: "'('",
            TokenType.RPAREN: "')'",
            TokenType.COMMA: "','",
            TokenType.ASSIGN: "'='",
            TokenType.NUMBER: "数字",
            TokenType.STRING: "字符串",
            TokenType.COMP_EQ: "'=='",
            TokenType.COMP_NE: "'!='",
            TokenType.COMP_LT: "'<'",
            TokenType.COMP_GT: "'>'",
            TokenType.COMP_LE: "'<='",
            TokenType.COMP_GE: "'>='",
            TokenType.EOF: "文件结束",
        }
        return names.get(type_, type_)

    def parse(self) -> tuple[Optional[str], ASTNode]:
        """
        <statement> := <expr> | <variable> "=" <expr>

        Returns:
            (output_var_name_or_None, ast_root)
        """
        # 尝试检测 assignment 形式
        if (self._peek().type == TokenType.VARIABLE
                and self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].type == TokenType.ASSIGN):
            var_token = self._consume(TokenType.VARIABLE)
            self._consume(TokenType.ASSIGN)
            expr = self._parse_expr()
            return var_token.value, expr
        expr = self._parse_expr()
        return None, expr

    def _parse_expr(self) -> ASTNode:
        """
        <expr> := <comparison> ( "OR" <comparison> )*
        """
        left = self._parse_comparison()
        while self._peek().type == TokenType.OR:
            self._consume(TokenType.OR)
            right = self._parse_comparison()
            left = BinaryOpNode("OR", left, right)
        return left

    def _parse_comparison(self) -> ASTNode:
        """
        <comparison> := <term> ( <comp_op> <term> )?
        """
        left = self._parse_term()
        comp_tokens = {
            TokenType.COMP_EQ, TokenType.COMP_NE,
            TokenType.COMP_LT, TokenType.COMP_GT,
            TokenType.COMP_LE, TokenType.COMP_GE,
        }
        if self._peek().type in comp_tokens:
            op_token = self._consume()
            right = self._parse_term()
            return ComparisonNode(op_token.value, left, right)
        return left

    def _parse_term(self) -> ASTNode:
        """
        <term> := <factor> ( "AND" <factor> )*
        """
        left = self._parse_factor()
        while self._peek().type == TokenType.AND:
            self._consume(TokenType.AND)
            right = self._parse_factor()
            left = BinaryOpNode("AND", left, right)
        return left

    def _parse_factor(self) -> ASTNode:
        """
        <factor> := "NOT" <factor>
                  | "(" <expr> ")"
                  | <variable>
                  | <number>
                  | <string>
                  | <gate_call>
        """
        token = self._peek()

        # NOT <factor>
        if token.type == TokenType.NOT:
            self._consume(TokenType.NOT)
            operand = self._parse_factor()
            return UnaryOpNode("NOT", operand)

        # "(" <expr> ")"
        if token.type == TokenType.LPAREN:
            self._consume(TokenType.LPAREN)
            expr = self._parse_expr()
            self._consume(TokenType.RPAREN)
            return expr

        # <gate_call> := <gate_name> "(" ...
        if token.type in self.GATE_TOKENS:
            gate_token = self._consume()
            # 关键：必须后跟 '(' 才是 gate_call；否则当作普通变量或语法错误
            if self._peek().type == TokenType.LPAREN:
                return self._parse_gate_call(gate_token)
            # 如果是 NOT 没有跟 '('，已经在上面的 NOT 分支处理了
            # 如果 AND/OR/NAND/NOR/XOR 没有跟 '('，则报错
            raise LogicParseError(
                f"关键字 '{gate_token.value}' 后需要跟 '(' 作为门调用",
                gate_token.line, gate_token.column
            )

        # <number> (Task-3)
        if token.type == TokenType.NUMBER:
            self._consume(TokenType.NUMBER)
            return NumberNode(token.value)

        # <string> (Task-3)
        if token.type == TokenType.STRING:
            self._consume(TokenType.STRING)
            return StringNode(token.value)

        # <variable>
        if token.type == TokenType.VARIABLE:
            self._consume(TokenType.VARIABLE)
            return VariableNode(token.value)

        # 无法识别的 token
        raise LogicParseError(
            f"意外的 token '{token.value}' ({self._type_name(token.type)})",
            token.line, token.column
        )

    def _parse_gate_call(self, gate_token: Token) -> GateCallNode:
        """
        <gate_call> := <gate_name> "(" <expr> ( "," <expr> )* ")"
        gate_token 是已经消费的 gate_name token
        """
        self._consume(TokenType.LPAREN)
        args: list[ASTNode] = []

        # 允许空参数列表？语法定义要求至少一个 expr，但保守处理
        # 实际上 NAND() 无意义
        while self._peek().type != TokenType.RPAREN:
            if args:
                self._consume(TokenType.COMMA)
            expr = self._parse_expr()
            args.append(expr)

        self._consume(TokenType.RPAREN)

        # NOT 门调用可以接受一个参数
        if gate_token.value == "NOT" and len(args) != 1:
            raise LogicParseError(
                f"NOT 门需要一个参数，但提供了 {len(args)} 个",
                gate_token.line, gate_token.column
            )

        # AND, OR, NAND, NOR, XOR 至少需要 2 个参数
        if gate_token.value in ("AND", "OR", "NAND", "NOR", "XOR") and len(args) < 2:
            raise LogicParseError(
                f"{gate_token.value} 门至少需要 2 个参数，但提供了 {len(args)} 个",
                gate_token.line, gate_token.column
            )

        return GateCallNode(gate_token.value, args)


# ════════════════════════════════════════════════════════════════
# AST → 文本（用于 format 和内部辅助）
# ════════════════════════════════════════════════════════════════


def _ast_to_text(node: ASTNode, parent_op: Optional[str] = None,
                 left_side: bool = True) -> str:
    """
    将 AST 节点转化为字符串表达式，加入必要括号

    Args:
        node: AST 节点
        parent_op: 父级运算符（用于决定是否需要括号）
        left_side: 是否在父运算符的左侧
    """
    if isinstance(node, VariableNode):
        return node.name

    if isinstance(node, NumberNode):
        return str(node.value)

    if isinstance(node, StringNode):
        return f'"{node.value}"'

    if isinstance(node, UnaryOpNode):
        inner = _ast_to_text(node.operand, "NOT", left_side=True)
        return f"NOT {inner}"

    if isinstance(node, BinaryOpNode):
        need_paren = False
        if parent_op and node.op != parent_op:
            # OR 内嵌 AND 或反之：需要括号
            need_paren = True
        elif parent_op and node.op == parent_op and not left_side:
            # 同样优先级右侧通常不需要括号，但为了清晰可加
            pass

        left = _ast_to_text(node.left, node.op, left_side=True)
        right = _ast_to_text(node.right, node.op, left_side=False)
        inner = f"{left} {node.op} {right}"
        if need_paren:
            return f"({inner})"
        return inner

    if isinstance(node, ComparisonNode):
        left = _ast_to_text(node.left, node.op, left_side=True)
        right = _ast_to_text(node.right, node.op, left_side=False)
        inner = f"{left} {node.op} {right}"
        # 当作为父表达式子节点时包裹括号
        if parent_op:
            return f"({inner})"
        return inner

    if isinstance(node, GateCallNode):
        args_text = ", ".join(_ast_to_text(arg, None) for arg in node.args)
        return f"{node.gate_name}({args_text})"

    return str(node)


def _has_binary_op(node: ASTNode) -> bool:
    """检查节点或其子节点中是否包含二元运算符（含比较运算）"""
    if isinstance(node, (BinaryOpNode, ComparisonNode)):
        return True
    if isinstance(node, UnaryOpNode):
        return _has_binary_op(node.operand)
    if isinstance(node, GateCallNode):
        return any(_has_binary_op(arg) for arg in node.args)
    return False


# ════════════════════════════════════════════════════════════════
# AST → 格式化文本（含缩进换行）
# ════════════════════════════════════════════════════════════════


def _ast_to_formatted(node: ASTNode, indent: int = 0, indent_size: int = 4) -> str:
    """
    将 AST 格式化为漂亮的多行文本

    规则：
    - 简单表达式（变量、一元 NOT、单个二元运算）保持一行
    - 多级嵌套的二元运算，每级缩进
    - 门调用每个参数一行
    """
    prefix = " " * indent

    if isinstance(node, VariableNode):
        return f"{prefix}{node.name}"

    if isinstance(node, NumberNode):
        return f"{prefix}{node.value}"

    if isinstance(node, StringNode):
        return f'{prefix}"{node.value}"'

    if isinstance(node, UnaryOpNode):
        inner = _ast_to_text(node.operand, "NOT", left_side=True)
        return f"{prefix}NOT {inner}"

    if isinstance(node, BinaryOpNode):
        # 判断是否"简单"（左右都是变量或 NOT + 变量）
        left_simple = _is_simple(node.left)
        right_simple = _is_simple(node.right)

        if left_simple and right_simple:
            left_txt = _ast_to_text(node.left, node.op, left_side=True)
            right_txt = _ast_to_text(node.right, node.op, left_side=False)
            return f"{prefix}{left_txt} {node.op} {right_txt}"

        left_txt = _ast_to_formatted(node.left, indent + indent_size, indent_size).lstrip()
        right_txt = _ast_to_formatted(node.right, indent + indent_size, indent_size).lstrip()
        return f"{prefix}{node.op}\n{prefix}  {left_txt}\n{prefix}  {right_txt}"

    if isinstance(node, ComparisonNode):
        left_txt = _ast_to_text(node.left, node.op, left_side=True)
        right_txt = _ast_to_text(node.right, node.op, left_side=False)
        return f"{prefix}{left_txt} {node.op} {right_txt}"

    if isinstance(node, GateCallNode):
        lines = [f"{prefix}{node.gate_name}("]
        for i, arg in enumerate(node.args):
            arg_text = _ast_to_formatted(arg, indent + indent_size, indent_size).lstrip()
            comma = "," if i < len(node.args) - 1 else ""
            lines.append(f"{' ' * (indent + indent_size)}{arg_text}{comma}")
        lines.append(f"{prefix})")
        return "\n".join(lines)

    return str(node)


def _is_simple(node: ASTNode) -> bool:
    """判断节点是否为简单表达式（变量、常量、一元 NOT 运算）"""
    if isinstance(node, VariableNode):
        return True
    if isinstance(node, (NumberNode, StringNode)):
        return True
    if isinstance(node, UnaryOpNode):
        return _is_simple(node.operand)
    if isinstance(node, GateCallNode):
        # 单参数 NOT 门调用也算简单
        if node.gate_name == "NOT" and len(node.args) == 1:
            return _is_simple(node.args[0])
        return False
    if isinstance(node, BinaryOpNode):
        return _is_simple(node.left) and _is_simple(node.right)
    if isinstance(node, ComparisonNode):
        return False
    return False


# ════════════════════════════════════════════════════════════════
# AST → 图形布局 (Sugiyama 简化版)
# ════════════════════════════════════════════════════════════════


class LayoutManager:
    """
    AST → 图形布局生成器（Sugiyama 简化版）

    将 AST 节点转化为层级结构，分配坐标，生成 scene_items dict。
    """

    # 布局参数
    GATE_WIDTH = 100
    GATE_HEIGHT = 60
    INPUT_RADIUS = 20
    OUTPUT_WIDTH = 60
    OUTPUT_HEIGHT = 30
    H_SPACING = 120   # 层级间水平间距
    V_SPACING = 80    # 同层垂直间距
    MARGIN_LEFT = 50
    MARGIN_TOP = 50
    PIN_RADIUS = 6

    def __init__(self):
        self._node_id_counter = 0
        self._pin_id_counter = 0
        self._wire_id_counter = 0

        self._gates: list[dict] = []
        self._inputs: list[dict] = []
        self._outputs: list[dict] = []
        self._wires: list[dict] = []

        # Internal mapping: AST node -> assigned level
        self._node_levels: dict[int, int] = {}
        # AST node -> dict item
        self._node_items: dict[int, dict] = {}
        # pin_id -> owner info
        self._pin_map: dict[str, dict] = {}

    def _next_node_id(self) -> str:
        self._node_id_counter += 1
        return f"n{self._node_id_counter}"

    def _next_pin_id(self) -> str:
        self._pin_id_counter += 1
        return f"p{self._pin_id_counter}"

    def _next_wire_id(self) -> str:
        self._wire_id_counter += 1
        return f"w{self._wire_id_counter}"

    def _collect_variables(self, node: ASTNode) -> set[str]:
        """收集 AST 中所有变量名（去重）"""
        vars_: set[str] = set()
        stack = [node]
        while stack:
            n = stack.pop()
            if isinstance(n, VariableNode):
                vars_.add(n.name)
            elif isinstance(n, (NumberNode, StringNode)):
                pass  # 常量，不收集为变量
            elif isinstance(n, UnaryOpNode):
                stack.append(n.operand)
            elif isinstance(n, (BinaryOpNode, ComparisonNode)):
                stack.append(n.left)
                stack.append(n.right)
            elif isinstance(n, GateCallNode):
                stack.extend(n.args)
        return vars_

    def _collect_constants(self, node: ASTNode) -> dict[int, str]:
        """收集 AST 中所有常量节点，返回 {id(node): label}"""
        constants: dict[int, str] = {}
        stack = [node]
        while stack:
            n = stack.pop()
            if isinstance(n, NumberNode):
                constants[id(n)] = str(n.value)
            elif isinstance(n, StringNode):
                constants[id(n)] = f'"{n.value}"'
            elif isinstance(n, VariableNode):
                pass
            elif isinstance(n, UnaryOpNode):
                stack.append(n.operand)
            elif isinstance(n, (BinaryOpNode, ComparisonNode)):
                stack.append(n.left)
                stack.append(n.right)
            elif isinstance(n, GateCallNode):
                stack.extend(n.args)
        return constants

    def _depth_of(self, node: ASTNode) -> int:
        """
        计算节点的深度（最长路径上的节点数）
        叶子节点（变量、数字、字符串）深度为 1
        """
        if isinstance(node, (VariableNode, NumberNode, StringNode)):
            return 1
        if isinstance(node, UnaryOpNode):
            return 1 + self._depth_of(node.operand)
        if isinstance(node, (BinaryOpNode, ComparisonNode)):
            return 1 + max(self._depth_of(node.left), self._depth_of(node.right))
        if isinstance(node, GateCallNode):
            if not node.args:
                return 1
            return 1 + max(self._depth_of(arg) for arg in node.args)
        return 1

    def _assign_levels(self, node: ASTNode, base_level: int = 0):
        """
        为 AST 节点分配层级（level 0 = 最左侧/输入层）
        使用简单的自底向上层级分配
        """
        if id(node) in self._node_levels:
            return

        if isinstance(node, (VariableNode, NumberNode, StringNode)):
            self._node_levels[id(node)] = 0
            return

        if isinstance(node, UnaryOpNode):
            self._assign_levels(node.operand, base_level)
            op_level = self._node_levels.get(id(node.operand), 0) + 1
            self._node_levels[id(node)] = op_level
            return

        if isinstance(node, (BinaryOpNode, ComparisonNode)):
            self._assign_levels(node.left, base_level)
            self._assign_levels(node.right, base_level)
            left_level = self._node_levels.get(id(node.left), 0)
            right_level = self._node_levels.get(id(node.right), 0)
            op_level = max(left_level, right_level) + 1
            self._node_levels[id(node)] = op_level
            return

        if isinstance(node, GateCallNode):
            max_child = 0
            for arg in node.args:
                self._assign_levels(arg, base_level)
                child_level = self._node_levels.get(id(arg), 0)
                max_child = max(max_child, child_level)
            self._node_levels[id(node)] = max_child + 1
            return

    def _layout(self, root: ASTNode, output_var: Optional[str] = None) -> dict:
        """
        执行完整布局，返回 scene_items dict
        """
        variables = self._collect_variables(root)
        constants = self._collect_constants(root)
        self._assign_levels(root)

        # 确定所有层级
        all_levels: dict[int, list[tuple[int, ASTNode]]] = defaultdict(list)
        for node_id, level in self._node_levels.items():
            all_levels[level].append((node_id, self._find_node(root, node_id)))

        if not all_levels:
            max_level = 0
        else:
            max_level = max(all_levels.keys())

        # 为每个层级分配垂直位置
        level_y_positions: dict[int, float] = {}
        level_counts: dict[int, int] = {}

        for level in range(max_level + 1):
            nodes_in_level = all_levels.get(level, [])
            level_counts[level] = len(nodes_in_level)
            total_height = (len(nodes_in_level) - 1) * self.V_SPACING
            level_y_positions[level] = self.MARGIN_TOP + total_height / 2.0

        # 为输入变量创建 input 项
        input_pin_map: dict[str, str] = {}  # variable_name -> pin_id
        input_y = level_y_positions.get(0, self.MARGIN_TOP)
        var_list = sorted(variables)
        for i, var_name in enumerate(var_list):
            pin_id = self._next_pin_id()
            y = self.MARGIN_TOP + i * self.V_SPACING
            self._inputs.append({
                "id": f"input_{var_name}",
                "label": var_name,
                "x": self.MARGIN_LEFT,
                "y": y,
                "pin_id": pin_id,
            })
            input_pin_map[var_name] = pin_id

        # 为常量（数字/字符串）创建 input 项 (Task-3)
        self._constant_pin_map: dict[int, str] = {}  # node_id -> pin_id
        for j, (node_id, label) in enumerate(constants.items()):
            pin_id = self._next_pin_id()
            y = self.MARGIN_TOP + (len(var_list) + j) * self.V_SPACING
            self._inputs.append({
                "id": f"const_{node_id}",
                "label": label,
                "x": self.MARGIN_LEFT,
                "y": y,
                "pin_id": pin_id,
            })
            self._constant_pin_map[node_id] = pin_id

        # 遍历 AST 创建 gate/operator 节点
        self._convert_node(root, input_pin_map, output_var, max_level + 1)

        # 添加输出项，并连线到根节点的输出 pin
        if output_var:
            pin_id = self._next_pin_id()
            output_x = self.MARGIN_LEFT + (max_level + 2) * self.H_SPACING
            output_y = self.MARGIN_TOP
            self._outputs.append({
                "id": f"output_{output_var}",
                "label": output_var,
                "x": output_x,
                "y": output_y,
                "pin_id": pin_id,
            })
            # 连线：根节点（AST 根）的输出 pin → 输出项的 pin
            root_item = self._node_items.get(id(root))
            if root_item:
                root_out_pin = root_item.get("output_pin_id")
                if root_out_pin:
                    self._wires.append({
                        "id": self._next_wire_id(),
                        "source_pin_id": root_out_pin,
                        "target_pin_id": pin_id,
                    })

        return {
            "gates": self._gates,
            "inputs": self._inputs,
            "outputs": self._outputs,
            "wires": self._wires,
        }

    def _find_node(self, root: ASTNode, target_id: int) -> Optional[ASTNode]:
        """在 AST 中按 id 查找节点"""
        if id(root) == target_id:
            return root
        if isinstance(root, UnaryOpNode):
            return self._find_node(root.operand, target_id)
        if isinstance(root, (BinaryOpNode, ComparisonNode)):
            result = self._find_node(root.left, target_id)
            if result:
                return result
            return self._find_node(root.right, target_id)
        if isinstance(root, GateCallNode):
            for arg in root.args:
                result = self._find_node(arg, target_id)
                if result:
                    return result
        return None

    def _convert_node(self, node: ASTNode, input_pin_map: dict[str, str],
                      output_var: Optional[str], output_level: int):
        """
        递归地将 AST 节点转换为 gate 项和连线
        """
        if isinstance(node, (VariableNode, NumberNode, StringNode)):
            return  # 变量/常量已作为 input 处理

        if isinstance(node, UnaryOpNode):
            self._convert_node(node.operand, input_pin_map, output_var, output_level)
            self._create_gate_for_node(node, input_pin_map)
            return

        if isinstance(node, (BinaryOpNode, ComparisonNode)):
            self._convert_node(node.left, input_pin_map, output_var, output_level)
            self._convert_node(node.right, input_pin_map, output_var, output_level)
            self._create_gate_for_node(node, input_pin_map)
            return

        if isinstance(node, GateCallNode):
            for arg in node.args:
                self._convert_node(arg, input_pin_map, output_var, output_level)
            self._create_gate_for_node(node, input_pin_map)
            return

    def _create_gate_for_node(self, node: ASTNode, input_pin_map: dict[str, str]):
        """
        为 AST 节点创建 gate 项，连接其输入输出
        """
        level = self._node_levels.get(id(node), 0)
        gate_id = self._next_node_id()

        if isinstance(node, UnaryOpNode):
            gate_type = "NOT"
        elif isinstance(node, BinaryOpNode):
            gate_type = node.op
        elif isinstance(node, ComparisonNode):
            gate_type = "CMP"
        elif isinstance(node, GateCallNode):
            gate_type = node.gate_name
        else:
            gate_type = "AND"

        input_pins: list[dict] = []
        output_pins: list[dict] = []

        # 收集输入子节点
        children: list[ASTNode] = []
        if isinstance(node, UnaryOpNode):
            children = [node.operand]
        elif isinstance(node, (BinaryOpNode, ComparisonNode)):
            children = [node.left, node.right]
        elif isinstance(node, GateCallNode):
            children = list(node.args)

        # 为子节点获取输出 pin id
        for child in children:
            child_pin = self._get_child_output_pin(child)
            if child_pin:
                in_pin_id = self._next_pin_id()
                input_pins.append({
                    "id": in_pin_id,
                    "label": "",
                    "pin_id": in_pin_id,
                })
                # 创建连线
                self._wires.append({
                    "id": self._next_wire_id(),
                    "source_pin_id": child_pin,
                    "target_pin_id": in_pin_id,
                })

        # 输出 pin
        out_pin_id = self._next_pin_id()
        output_pins.append({
            "id": out_pin_id,
            "label": f"{gate_type}_out",
            "pin_id": out_pin_id,
        })

        # 存储映射
        self._node_items[id(node)] = {
            "gate_id": gate_id,
            "output_pin_id": out_pin_id,
        }

        # 计算位置
        x = self.MARGIN_LEFT + (level + 1) * self.H_SPACING
        y = self.MARGIN_TOP + level * self.V_SPACING

        self._gates.append({
            "id": gate_id,
            "gate_type": gate_type,
            "op": getattr(node, 'op', None),  # 比较运算符 (Task-3)
            "x": x,
            "y": y,
            "input_pins": input_pins,
            "output_pins": output_pins,
        })

    def _get_child_output_pin(self, child: ASTNode) -> Optional[str]:
        """获取子节点的输出 pin id"""
        if isinstance(child, VariableNode):
            # 从 input 中查找
            for inp in self._inputs:
                if inp["label"] == child.name:
                    return inp.get("pin_id")
            return None
        if isinstance(child, (NumberNode, StringNode)):
            # 从常量 pin 映射中查找 (Task-3)
            return getattr(self, '_constant_pin_map', {}).get(id(child))
        # 从已创建的 gate 中查找
        item = self._node_items.get(id(child))
        if item:
            return item.get("output_pin_id")
        return None


# ════════════════════════════════════════════════════════════════
# to_text: 画布数据 → 文本表达式
# ════════════════════════════════════════════════════════════════


def _to_text_from_scene(scene_items: dict) -> str:
    """
    从 scene_items 生成文本表达式。

    scene_items 格式:
        {
            "gates": [{"id": "...", "gate_type": "AND", "x": ..., "y": ...,
                       "input_pins": [{"id": "...", "label": "...", "pin_id": "..."}],
                       "output_pins": [{"id": "...", "label": "...", "pin_id": "..."}]}],
            "inputs": [{"id": "...", "label": "A", "x": ..., "y": ...,
                        "pin_id": "..."}],
            "outputs": [{"id": "...", "label": "result", "x": ..., "y": ...,
                          "pin_id": "..."}],
            "wires": [{"id": "...", "source_pin_id": "...", "target_pin_id": "..."}]
        }
    """
    gates = scene_items.get("gates", [])
    inputs = scene_items.get("inputs", [])
    outputs = scene_items.get("outputs", [])
    wires = scene_items.get("wires", [])

    if not gates and not inputs and not outputs:
        return ""

    # 构建 pin → 表达式映射
    # 对于 input pin，其表达式就是标签名
    # 对于 gate output pin，其表达式是 gate_call(...)
    # 对于 output pin，其表达式用于生成最终结果

    # pin_id → 信息
    pin_to_info: dict[str, dict] = {}

    # 记录所有 wire 连接
    # source_pin_id → [target_pin_id]
    out_edges: dict[str, list[str]] = defaultdict(list)
    # target_pin_id → source_pin_id
    in_edges: dict[str, str] = {}

    for wire in wires:
        src = wire.get("source_pin_id", "")
        tgt = wire.get("target_pin_id", "")
        if src and tgt:
            out_edges[src].append(tgt)
            in_edges[tgt] = src

    # 为输入 pin 建立表达式
    for inp in inputs:
        pin_id = inp.get("pin_id", "")
        label = inp.get("label", inp.get("id", "?")).strip()
        if not label:
            label = inp.get("id", "?")
        pin_to_info[pin_id] = {"expr": label, "type": "input", "id": inp.get("id", "")}

    # 为输出 pin 建立映射
    output_pins: dict[str, str] = {}  # pin_id → label
    for out in outputs:
        pin_id = out.get("pin_id", "")
        label = out.get("label", "result")
        output_pins[pin_id] = label
        pin_to_info[pin_id] = {"expr": None, "type": "output", "label": label, "id": out.get("id", "")}

    # 为 gate pin 建立映射
    for gate in gates:
        gate_type = gate.get("gate_type", "AND")
        gate_id = gate.get("id", "")
        for pin in gate.get("output_pins", []):
            pin_id = pin.get("pin_id", pin.get("id", ""))
            if pin_id:
                pin_to_info[pin_id] = {
                    "expr": None,
                    "type": "gate_output",
                    "gate_id": gate_id,
                    "gate_type": gate_type,
                }
        for pin in gate.get("input_pins", []):
            pin_id = pin.get("pin_id", pin.get("id", ""))
            if pin_id:
                label = pin.get("label", "")
                pin_to_info[pin_id] = {
                    "expr": None,
                    "type": "gate_input",
                    "gate_id": gate_id,
                    "label": label,
                }

    # 拓扑排序计算表达式
    # 从 inputs 出发，沿 wires 向前传播
    # 需要计算每个 gate output pin 的表达式

    def _resolve_expr(pin_id: str, visited: set[str]) -> tuple[str, Optional[str]]:
        """递归计算某个 pin 的表达式

        Returns:
            (expr_text, top_operator):
                expr_text: 表达式文本
                top_operator: None（叶子节点）, "AND", "OR", "GATE"（门调用/一元运算）
        """
        if pin_id in visited:
            raise LogicParseError(f"检测到电路中存在环路（pin: {pin_id}）")
        visited.add(pin_id)

        info = pin_to_info.get(pin_id)
        if info is None:
            visited.discard(pin_id)
            return ("?", None)

        if info.get("type") == "input":
            visited.discard(pin_id)
            return (info["expr"], None)

        if info.get("type") == "output":
            # 输出引脚本身不产生表达式
            visited.discard(pin_id)
            return ("?", None)

        if info.get("type") == "gate_output":
            gate_id = info["gate_id"]
            gate_type = info["gate_type"]
            # 找这个 gate 的所有 input pin
            gate = None
            for g in gates:
                if g.get("id") == gate_id:
                    gate = g
                    break
            if gate is None:
                visited.discard(pin_id)
                return ("?", None)

            input_pins = gate.get("input_pins", [])
            input_results: list[tuple[str, Optional[str]]] = []
            for ip in input_pins:
                ip_id = ip.get("pin_id", ip.get("id", ""))
                if ip_id in in_edges:
                    src_pin = in_edges[ip_id]
                    input_results.append(_resolve_expr(src_pin, visited))
                else:
                    input_results.append(("?", None))

            if not input_results:
                visited.discard(pin_id)
                return ("?", None)

            if gate_type == "NOT":
                # 一元 NOT：子表达式包含二元运算符时需要括号
                sub_text, sub_op = input_results[0]
                if sub_op in ("AND", "OR"):
                    expr = f"NOT ({sub_text})"
                else:
                    expr = f"NOT {sub_text}"
                info["expr"] = expr
                visited.discard(pin_id)
                return (expr, "GATE")

            elif gate_type == "CMP":
                # 比较运算 (Task-3)
                op_str = gate.get("op", "==")
                parts = [r[0] for r in input_results]
                if len(parts) >= 2:
                    expr = f"{parts[0]} {op_str} {parts[1]}"
                else:
                    expr = " ? "
                info["expr"] = expr
                visited.discard(pin_id)
                return (expr, "CMP")

            elif gate_type in ("AND", "OR"):
                # 二元操作符：需要根据优先级添加括号
                parts = []
                for sub_text, sub_op in input_results:
                    # 如果子表达式包含另一类操作符，需要加括号
                    if sub_op is not None and sub_op != gate_type and sub_op != "GATE":
                        parts.append(f"({sub_text})")
                    else:
                        parts.append(sub_text)
                expr = f" {gate_type} ".join(parts)
                info["expr"] = expr
                visited.discard(pin_id)
                return (expr, gate_type)

            else:
                # NAND, NOR, XOR — 使用 gate_call 形式
                # 子表达式不需要括号（函数调用参数天然隔离）
                args_text = ", ".join(r[0] for r in input_results)
                expr = f"{gate_type}({args_text})"
                info["expr"] = expr
                visited.discard(pin_id)
                return (expr, "GATE")

        visited.discard(pin_id)
        return ("?", None)

    # 计算所有输出 pin 的表达式
    results: list[str] = []
    for out_pin_id, out_label in output_pins.items():
        visited: set[str] = set()
        if out_pin_id in in_edges:
            src = in_edges[out_pin_id]
            expr, _ = _resolve_expr(src, visited)
            results.append(f"{out_label} = {expr}")

    # 如果没有明确的 output，尝试从输出端开始反向计算
    if not results:
        # 从没有出边的 gate output 开始
        gate_outputs_with_no_out = []
        for gate in gates:
            for pin in gate.get("output_pins", []):
                pin_id = pin.get("pin_id", pin.get("id", ""))
                if pin_id and pin_id not in out_edges:
                    gate_outputs_with_no_out.append(pin_id)

        for pin_id in gate_outputs_with_no_out:
            visited: set[str] = set()
            expr, _ = _resolve_expr(pin_id, visited)
            results.append(expr)

    if not results:
        return ""

    return "\n".join(results)


# ════════════════════════════════════════════════════════════════
# LogicConverter（主入口）
# ════════════════════════════════════════════════════════════════


class LogicConverter:
    """
    逻辑表达式 ↔ 图形门电路的转化器（纯静态工具类）
    """

    @staticmethod
    def to_text(scene_items: dict) -> str:
        """
        从画布项集合生成文本表达式

        Args:
            scene_items: {
                "gates": [dict, ...],
                "inputs": [dict, ...],
                "outputs": [dict, ...],
                "wires": [dict, ...]
            }

        Returns:
            字符串形式的逻辑表达式
        """
        try:
            return _to_text_from_scene(scene_items)
        except LogicParseError:
            raise
        except Exception as e:
            return f"# 转化错误: {e}"

    @staticmethod
    def parse_text(text: str) -> dict:
        """
        解析文本表达式为图形数据（scene_items dict）

        Args:
            text: 逻辑表达式文本

        Returns:
            scene_items dict

        Raises:
            LogicParseError: 语法错误时抛出（含行号/列号）
        """
        text = text.strip()
        if not text:
            return {"gates": [], "inputs": [], "outputs": [], "wires": []}

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        output_var, ast_root = parser.parse()

        # 检查是否还有未消费的 token
        if parser._peek().type != TokenType.EOF:
            token = parser._peek()
            raise LogicParseError(
                f"表达式结束后有多余内容 '{token.value}'",
                token.line, token.column
            )

        # 生成布局
        layout = LayoutManager()
        scene_items = layout._layout(ast_root, output_var)

        return scene_items

    @staticmethod
    def validate(text: str) -> tuple[bool, str]:
        """
        语法验证

        Args:
            text: 逻辑表达式文本

        Returns:
            (True, "") 或 (False, "第 X 行第 Y 列: 错误信息")
        """
        try:
            text_stripped = text.strip()
            if not text_stripped:
                return True, ""

            lexer = Lexer(text)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            parser.parse()

            # 检查是否有多余内容
            if parser._peek().type != TokenType.EOF:
                token = parser._peek()
                return False, f"第 {token.line} 行第 {token.column} 列: " \
                              f"表达式结束后有多余内容 '{token.value}'"

            return True, ""
        except LogicParseError as e:
            return False, f"第 {e.line} 行第 {e.column} 列: {e.message}"
        except Exception as e:
            return False, f"解析错误: {e}"

    @staticmethod
    def format(text: str) -> str:
        """
        格式化表达式（适当缩进换行）

        Args:
            text: 逻辑表达式文本

        Returns:
            格式化后的字符串

        Raises:
            LogicParseError: 语法错误时抛出
        """
        text_stripped = text.strip()
        if not text_stripped:
            return ""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        output_var, ast_root = parser.parse()

        # 检查 EOF
        if parser._peek().type != TokenType.EOF:
            token = parser._peek()
            raise LogicParseError(
                f"表达式结束后有多余内容 '{token.value}'",
                token.line, token.column
            )

        body = _ast_to_formatted(ast_root)
        if output_var:
            return f"{output_var} =\n{body}"
        return body
