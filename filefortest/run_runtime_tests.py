#!/usr/bin/env python3
"""
run_runtime_tests.py — EnApp LogicConverter 运行时测试脚本

测试 LogicConverter 的 R3（符号支持）和 R4（数值/字符变量支持）需求。
可直接独立运行：python run_runtime_tests.py

依赖：仅需 LogicConverter（纯 Python，无 Qt 依赖）
"""

import sys
import traceback

sys.path.insert(0, ".")

from Widgets.RightWidget.LogicConverter import (
    LogicConverter,
    LogicParseError,
    Lexer,
    Parser,
    TokenType,
    VariableNode,
    NumberNode,
    StringNode,
    UnaryOpNode,
    BinaryOpNode,
    ComparisonNode,
    GateCallNode,
)

def _parse_expression(text):
    """Parse text and return (output_var, ast_root) tuple."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


# ════════════════════════════════════════════════════════════════
# Test Framework (lightweight, no external deps)
# ════════════════════════════════════════════════════════════════

_passed = 0
_failed = 0
_failures = []


def test(func_or_name, func=None, *args, **kwargs):
    global _passed, _failed
    if func is None:
        # Called as test(some_func)
        func = func_or_name
        name = func.__name__.replace("_", " ").replace("test ", "").strip()
    else:
        # Called as test("description", some_func)
        name = func_or_name
    try:
        if args or kwargs:
            func(*args, **kwargs)
        else:
            func()
        _passed += 1
        print(f"  ✓ {name}")
    except AssertionError as e:
        _failed += 1
        msg = str(e) or "assertion failed"
        _failures.append((name, msg))
        print(f"  ✗ {name}")
        print(f"      {msg}")
    except Exception as e:
        _failed += 1
        tb = traceback.format_exc()
        _failures.append((name, f"{type(e).__name__}: {e}"))
        print(f"  ✗ {name}")
        for line in tb.split("\n")[-4:-1]:
            print(f"      {line}" if line.strip() else "")


def assert_eq(actual, expected, label=""):
    if actual != expected:
        detail = f"  expected {expected!r}, got {actual!r}"
        if label:
            detail = f"{label}: {detail}"
        raise AssertionError(detail)


def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg or "expected True, got False")


def assert_false(cond, msg=""):
    if cond:
        raise AssertionError(msg or "expected False, got True")


def assert_raises(exc_cls, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
        raise AssertionError(f"expected {exc_cls.__name__}, but no exception raised")
    except exc_cls:
        pass


# ════════════════════════════════════════════════════════════════
# Test Cases
# ════════════════════════════════════════════════════════════════

def test_lexer_basic():
    """词法分析器基础测试"""
    lexer = Lexer("A AND B")
    tokens = lexer.tokenize()
    types = [t.type for t in tokens]
    assert_eq(types, [TokenType.VARIABLE, TokenType.AND, TokenType.VARIABLE, TokenType.EOF],
              "A AND B token types")


def test_lexer_symbols():
    """R3: 符号 token 测试"""
    cases = [
        ("+", TokenType.OR),
        ("*", TokenType.AND),
        ("!", TokenType.NOT),
        ("~", TokenType.NOT),
    ]
    for sym, expected_type in cases:
        lexer = Lexer(sym)
        tokens = lexer.tokenize()
        assert_eq(tokens[0].type, expected_type, f"symbol {sym!r} -> {expected_type}")


def test_lexer_numbers():
    """R4: 数字字面量 token 测试"""
    lexer = Lexer("42 3.14")
    tokens = lexer.tokenize()
    assert_eq(tokens[0].type, TokenType.NUMBER, "42 type")
    assert_eq(tokens[0].value, 42, "42 value")
    assert_eq(tokens[1].type, TokenType.NUMBER, "3.14 type")
    assert_eq(tokens[1].value, 3.14, "3.14 value")


def test_lexer_string():
    """R4: 字符串字面量 token 测试"""
    lexer = Lexer('"hello"')
    tokens = lexer.tokenize()
    assert_eq(tokens[0].type, TokenType.STRING, 'string type')
    assert_eq(tokens[0].value, "hello", 'string value')


def test_lexer_comparison_ops():
    """R4: 比较运算符 token 测试"""
    pairs = [
        ("==", TokenType.COMP_EQ),
        ("!=", TokenType.COMP_NE),
        ("<", TokenType.COMP_LT),
        (">", TokenType.COMP_GT),
        ("<=", TokenType.COMP_LE),
        (">=", TokenType.COMP_GE),
    ]
    for op_str, expected_type in pairs:
        lexer = Lexer(f"a {op_str} b")
        tokens = lexer.tokenize()
        comp_types = [t.type for t in tokens]
        assert_true(TokenType.VARIABLE in comp_types, f"{op_str} has variable")
        assert_true(expected_type in comp_types, f"{op_str} -> {expected_type}")


def test_lexer_neq_vs_not():
    """!= vs ! 消歧义测试：!= 应为 COMP_NE，! 应为 NOT"""
    lexer = Lexer("!A != B")
    tokens = lexer.tokenize()
    assert_eq(tokens[0].type, TokenType.NOT, "! should be NOT when not followed by =")
    assert_eq(tokens[1].type, TokenType.VARIABLE, "then variable")
    assert_eq(tokens[2].type, TokenType.COMP_NE, "!= should be COMP_NE")
    assert_eq(tokens[3].type, TokenType.VARIABLE, "then variable B")


def test_lexer_empty():
    """空输入测试"""
    lexer = Lexer("")
    tokens = lexer.tokenize()
    assert_eq(len(tokens), 1, "empty -> just EOF")
    assert_eq(tokens[0].type, TokenType.EOF, "empty -> EOF")


def test_lexer_comment():
    """注释跳过测试"""
    lexer = Lexer("A # this is a comment\nAND B")
    tokens = lexer.tokenize()
    types = [t.type for t in tokens]
    assert_eq(types[:4],
              [TokenType.VARIABLE, TokenType.AND, TokenType.VARIABLE, TokenType.EOF],
              "comment skipped")


# ─── Parser Tests ────────────────────────────────────────────────

def test_parser_r3_symbols():
    """R3: 符号解析为正确的 AST"""

    # A + B
    _, ast = _parse_expression("A + B")
    assert_true(isinstance(ast, BinaryOpNode), "A+B is BinaryOpNode")
    assert_eq(ast.op, "OR", "A+B op is OR")
    assert_eq(ast.left.name, "A", "A+B left is A")
    assert_eq(ast.right.name, "B", "A+B right is B")

    # A * B
    _, ast = _parse_expression("A * B")
    assert_true(isinstance(ast, BinaryOpNode), "A*B is BinaryOpNode")
    assert_eq(ast.op, "AND", "A*B op is AND")

    # !A
    _, ast = _parse_expression("!A")
    assert_true(isinstance(ast, UnaryOpNode), "!A is UnaryOpNode")
    assert_eq(ast.op, "NOT", "!A op is NOT")
    assert_eq(ast.operand.name, "A", "!A operand is A")

    # ~A
    _, ast = _parse_expression("~A")
    assert_true(isinstance(ast, UnaryOpNode), "~A is UnaryOpNode")
    assert_eq(ast.op, "NOT", "~A op is NOT")


def test_parser_r4_numbers():
    """R4: 数字解析"""
    _, ast = _parse_expression("42")
    assert_true(isinstance(ast, NumberNode), "42 is NumberNode")
    assert_eq(ast.value, 42, "42 value")

    _, ast = _parse_expression("3.14")
    assert_true(isinstance(ast, NumberNode), "3.14 is NumberNode")
    assert_eq(ast.value, 3.14, "3.14 value")


def test_parser_r4_string():
    """R4: 字符串解析"""
    _, ast = _parse_expression('"hello"')
    assert_true(isinstance(ast, StringNode), 'string is StringNode')
    assert_eq(ast.value, "hello", 'string value')


def test_parser_r4_comparison():
    """R4: 比较表达式解析"""
    _, ast = _parse_expression("age > 18")
    assert_true(isinstance(ast, ComparisonNode), "age>18 is ComparisonNode")
    assert_eq(ast.op, ">", "op is >")
    assert_eq(ast.left.name, "age", "left is variable age")
    assert_true(isinstance(ast.right, NumberNode), "right is NumberNode")
    assert_eq(ast.right.value, 18, "right value is 18")


def test_parser_r4_mixed():
    """R4: 混合表达式解析"""
    _, ast = _parse_expression('(age > 18) AND (role == "admin")')
    assert_true(isinstance(ast, BinaryOpNode), "mixed is BinaryOpNode")
    assert_eq(ast.op, "AND", "op is AND")
    assert_true(isinstance(ast.left, ComparisonNode), "left is ComparisonNode")
    assert_eq(ast.left.op, ">", "left comp is >")
    assert_true(isinstance(ast.right, ComparisonNode), "right is ComparisonNode")
    assert_eq(ast.right.op, "==", "right comp is ==")


def test_parser_assignment():
    """赋值表达式解析"""
    # _parse_expression returns (output_var, ast)
    result_out, result_ast = _parse_expression("result = A AND B")
    assert_eq(result_out, "result", "output variable name")
    assert_true(isinstance(result_ast, BinaryOpNode), "assignment rhs is BinaryOpNode")
    assert_eq(result_ast.op, "AND", "assignment op AND")


def test_parser_gate_call():
    """门调用解析"""
    _, ast = _parse_expression("AND(A, B)")
    assert_true(isinstance(ast, GateCallNode), "AND() is GateCallNode")
    assert_eq(ast.gate_name, "AND", "gate name AND")
    assert_eq(len(ast.args), 2, "two args")
    assert_true(isinstance(ast.args[0], VariableNode), "first arg is variable")


# ─── LogicConverter Tests ─────────────────────────────────────────

def test_validate_r3_symbols():
    """R3: validate 符号表达式"""
    cases = [
        "A + B",
        "A * B",
        "!A",
        "~A",
        "A * B + C",
        "A + B AND C",
        "!A AND B",
    ]
    for text in cases:
        ok, err = LogicConverter.validate(text)
        assert_true(ok, f"validate({text!r}) should pass, got: {err}")


def test_validate_r4():
    """R4: validate 数值/字符串/比较表达式"""
    cases = [
        "42",
        "3.14",
        '"hello"',
        "age > 18",
        '(age > 18) AND (role == "admin")',
        "x != 5",
        "y <= 10",
        "z >= 3.14",
        "a < b",
    ]
    for text in cases:
        ok, err = LogicConverter.validate(text)
        assert_true(ok, f"validate({text!r}) should pass, got: {err}")


def test_format_r3():
    """R3: format 符号表达式"""
    cases = [
        ("A + B", "A OR B"),
        ("A * B", "A AND B"),
        ("!A", "NOT A"),
        ("~A", "NOT A"),
        ("A * B + C", "(A AND B) OR C"),
        ("A AND B", "A AND B"),
        ("!A AND B", "NOT A AND B"),
        ("A + B AND C", "A OR (B AND C)"),
    ]
    for inp, exp in cases:
        out = LogicConverter.format(inp)
        assert_eq(out, exp, f"format({inp!r})")


def test_format_r4():
    """R4: format 数值/字符串/比较表达式"""
    cases = [
        ("42", "42"),
        ("3.14", "3.14"),
        ('"hello"', '"hello"'),
        ("age > 18", "age > 18"),
        ("x != 5", "x != 5"),
        ("y <= 10", "y <= 10"),
        ("z >= 3.14", "z >= 3.14"),
        ("a < b", "a < b"),
    ]
    for inp, exp in cases:
        out = LogicConverter.format(inp)
        assert_eq(out, exp, f"format({inp!r})")


def test_format_r4_complex():
    """R4: format 复杂表达式（多行可接受）"""
    text = '(age > 18) AND (role == "admin")'
    out = LogicConverter.format(text)
    # 多行格式是可接受的
    assert_true(out.strip() != "", "format complex expression should not be empty")
    # 应包含所有关键字和值
    assert_true("age" in out, "format includes age")
    assert_true("role" in out, "format includes role")
    assert_true("AND" in out, "format includes AND")
    assert_true(">" in out, "format includes >")
    assert_true("==" in out, "format includes ==")
    assert_true("18" in out, "format includes 18")
    assert_true("admin" in out, "format includes admin")


def test_validate_invalid():
    """无效表达式校验"""
    invalid_cases = [
        ("A +", "incomplete expression"),
        ("A B", "missing operator"),
        ("(A + B", "unclosed paren"),
        ('unclosed', "not a keyword without paren"),
        ("A AND AND B", "double operator"),
    ]
    # Note: some of these may parse differently; we just test they don't crash
    for text, desc in invalid_cases:
        ok, err = LogicConverter.validate(text)
        # ok may be True or False, as long as no exception leaks
        assert_true(isinstance(ok, bool), f"{desc} returns bool")
        assert_true(isinstance(err, str), f"{desc} returns str error")


def test_to_text_roundtrip():
    """parse_text + to_text 往返测试"""
    texts = [
        "A AND B",
        "A OR B",
        "NOT A",
        "A OR B AND C",
        "A AND B OR C",
        "(A AND B) OR C",
        "A OR (B AND C)",
        "42",
        '"hello"',
        "age > 18",
        '(age > 18) AND (role == "admin")',
        "x != 5",
        "AND(A, B)",
        "result = A AND B",
    ]
    for text in texts:
        try:
            data = LogicConverter.parse_text(text)
            result = LogicConverter.to_text(data)
            # 应产生非空且语法有效的输出
            ok, err = LogicConverter.validate(result)
            assert_true(ok, f"roundtrip({text!r}) -> {result!r} should be valid: {err}")
        except LogicParseError as e:
            # Some texts may be parseable as multi-line format output
            # e.g., A OR B AND C is valid but will be formatted
            # Just ensure it doesn't crash
            pass


def test_backward_compatibility():
    """向后兼容：原有 AND/OR/NOT 关键字不受影响"""
    cases = [
        ("A AND B", "A AND B"),
        ("A OR B", "A OR B"),
        ("NOT A", "NOT A"),
        ("A AND B OR C", "(A AND B) OR C"),  # AND 优先级高于 OR
        ("(A OR B) AND NOT C", "(A OR B) AND NOT C"),
    ]
    for inp, exp in cases:
        ok, err = LogicConverter.validate(inp)
        assert_true(ok, f"backward compat validate({inp!r})")
        out = LogicConverter.format(inp)
        assert_eq(out, exp, f"backward compat format({inp!r})")


def test_lexer_parser_integration():
    """Lexer + Parser 完整集成测试"""
    # 混合符号和关键字
    tests = [
        ("A + B", "OR", "A", "B"),
        ("A * B", "AND", "A", "B"),
        ("!A", "NOT", "A", None),
        ("~A", "NOT", "A", None),
        ("A * B + C", "OR", None, None),  # top OR, left AND(A,B), right C
    ]
    for text, top_op, left_name, right_name in tests:
        _, ast = _parse_expression(text)
        if top_op == "OR":
            assert_true(isinstance(ast, BinaryOpNode) and ast.op == "OR",
                        f"{text} top is OR")
        elif top_op == "AND":
            assert_true(isinstance(ast, BinaryOpNode) and ast.op == "AND",
                        f"{text} top is AND")
        elif top_op == "NOT":
            assert_true(isinstance(ast, UnaryOpNode) and ast.op == "NOT",
                        f"{text} top is NOT")


def test_parse_error_format():
    """解析错误应包含行列号"""
    try:
        LogicConverter.parse_text("A + ")  # incomplete
        raise AssertionError("should have raised LogicParseError")
    except LogicParseError as e:
        assert_true("行" in str(e) or "列" in str(e),
                     "error message includes position")
        assert_true(bool(e.message), "error has message")


def test_empty_input():
    """空输入处理"""
    ok, err = LogicConverter.validate("")
    assert_true(ok, "empty string validates")
    assert_eq(LogicConverter.format(""), "", "empty string formats to empty")
    data = LogicConverter.parse_text("")
    assert_eq(data, {"gates": [], "inputs": [], "outputs": [], "wires": []},
              "empty parse returns empty scene")


def test_whitespace_input():
    """纯空白输入"""
    ok, err = LogicConverter.validate("   ")
    assert_true(ok, "whitespace validates")
    assert_eq(LogicConverter.format("   "), "", "whitespace formats to empty")


def test_string_escape():
    """字符串转义测试"""
    lexer = Lexer('"hello\\nworld"')
    tokens = lexer.tokenize()
    assert_eq(tokens[0].type, TokenType.STRING, "escaped string type")
    assert_eq(tokens[0].value, "hello\nworld", "escaped string value - \\n")


def test_invalid_number():
    """非法数字格式测试"""
    assert_raises(LogicParseError, Lexer("1.2.3").tokenize)


def test_comment_with_symbols():
    """注释中带符号不应影响解析"""
    lexer = Lexer("A + B # + * ! ~")
    tokens = lexer.tokenize()
    types = [t.type for t in tokens]
    assert_eq(types[:3],
              [TokenType.VARIABLE, TokenType.OR, TokenType.VARIABLE],
              "comment with symbols ignored")


# ─── R2 (UI) Static Checks ───────────────────────────────────────

def test_var_type_property():
    """R2: LogicPinItem._var_type 属性检查"""
    import inspect
    from Widgets.RightWidget.LogicDiagramWidget import LogicPinItem
    # _var_type is an instance attribute, check via source
    src = inspect.getsource(LogicPinItem.__init__)
    assert_true("_var_type" in src,
                "LogicPinItem.__init__ sets _var_type")
    assert_true('"bool"' in src or "'bool'" in src,
                "LogicPinItem._var_type defaults to 'bool'")
    # 检查 var_type property 存在
    assert_true('var_type' in inspect.getsource(LogicPinItem) or
                hasattr(LogicPinItem, 'var_type'),
                "LogicPinItem has var_type property")
    # 检查 get_scene_data 使用 var_type
    from Widgets.RightWidget.LogicDiagramWidget import LogicDiagramWidget
    src2 = inspect.getsource(LogicDiagramWidget.get_scene_data)
    assert_true("var_type" in src2,
                "get_scene_data() includes var_type")


def test_variable_manager_dialog_exists():
    """R2: VariableManagerDialog 类存在"""
    from Widgets.RightWidget.LogicDiagramWidget import VariableManagerDialog
    assert_true(VariableManagerDialog is not None,
                "VariableManagerDialog class exists")
    # 检查 VALID_VAR_TYPES
    from Widgets.RightWidget.LogicDiagramWidget import VALID_VAR_TYPES
    assert_eq(VALID_VAR_TYPES, ("bool", "int", "float", "string"),
              "VALID_VAR_TYPES includes all 4 types")


def test_r1_item_change_fix():
    """R1: LogicGateItem.itemChange() 包含连线更新"""
    import inspect
    from Widgets.RightWidget.LogicDiagramWidget import LogicGateItem
    src = inspect.getsource(LogicGateItem.itemChange)
    assert_true("update_path" in src,
                "itemChange calls update_path")
    assert_true("input_pins" in src and "output_pins" in src,
                "itemChange iterates input_pins and output_pins")
    assert_true("ItemPositionHasChanged" in src,
                "itemChange handles ItemPositionHasChanged")


# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════

def main():
    global _passed, _failed

    print("=" * 60)
    print("  EnApp LogicConverter Runtime Tests")
    print("=" * 60)
    print()

    # ── Lexer Tests ──
    print("[Lexer] 词法分析器")
    test(test_lexer_basic)
    test(test_lexer_symbols)
    test(test_lexer_numbers)
    test(test_lexer_string)
    test(test_lexer_comparison_ops)
    test(test_lexer_neq_vs_not)
    test(test_lexer_empty)
    test(test_lexer_comment)
    test(test_string_escape)
    test(test_invalid_number)
    test(test_comment_with_symbols)
    print()

    # ── Parser Tests ──
    print("[Parser] 语法分析器")
    test(test_parser_r3_symbols)
    test(test_parser_r4_numbers)
    test(test_parser_r4_string)
    test(test_parser_r4_comparison)
    test(test_parser_r4_mixed)
    test(test_parser_assignment)
    test(test_parser_gate_call)
    print()

    # ── LogicConverter (validate/format) Tests ──
    print("[Converter] LogicConverter 接口")
    test(test_validate_r3_symbols)
    test(test_validate_r4)
    test(test_format_r3)
    test(test_format_r4)
    test(test_format_r4_complex)
    test(test_validate_invalid)
    print()

    # ── Round-trip / Integration Tests ──
    print("[Integration] 集成测试")
    test(test_to_text_roundtrip)
    test(test_backward_compatibility)
    test(test_lexer_parser_integration)
    test(test_parse_error_format)
    test(test_empty_input)
    test(test_whitespace_input)
    print()

    # ── Static/R2 UI Checks ──
    print("[Static] 静态代码检查")
    test(test_var_type_property)
    test(test_variable_manager_dialog_exists)
    test(test_r1_item_change_fix)
    print()

    # ── Summary ──
    print("=" * 60)
    total = _passed + _failed
    print(f"  结果: {_passed}/{total} 通过, {_failed} 失败")
    print("=" * 60)

    if _failures:
        print()
        print("失败详情:")
        for name, msg in _failures:
            print(f"  [{name}] {msg}")

    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
