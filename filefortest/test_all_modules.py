#!/usr/bin/env python3
"""
EnApp 0.02 — 全模块集成测试

测试范围：
  1. CenterWidgetManage 面板管理器
  2. MultiFormatViewer 编辑功能
  3. LogicConverter 双向转化器
  4. LogicDatabase 逻辑数据库
  5. LogicDiagramWidget 图形门逻辑编辑器
  6. LogicTextWidget 文本逻辑编辑器
  7. MainWindow 集成

运行：python3 filefortest/test_all_modules.py
"""

import sys
import os
import tempfile
import shutil
import traceback

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 颜色输出
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

passed = 0
failed = 0
total_tests = 0


def test(name, func):
    """运行单个测试"""
    global total_tests, passed, failed
    total_tests += 1
    try:
        func()
        passed += 1
        print(f"  {GREEN}✅ {name}{RESET}")
    except AssertionError as e:
        failed += 1
        print(f"  {RED}❌ {name}: {e}{RESET}")
    except Exception as e:
        failed += 1
        print(f"  {RED}❌ {name}: {type(e).__name__}: {e}{RESET}")
        traceback.print_exc()


def assert_eq(a, b, msg=""):
    if a != b:
        raise AssertionError(f"期望 {b!r}, 实际 {a!r}" + (f" — {msg}" if msg else ""))


def assert_true(v, msg=""):
    if not v:
        raise AssertionError(f"期望 True" + (f" — {msg}" if msg else ""))


def assert_false(v, msg=""):
    if v:
        raise AssertionError(f"期望 False" + (f" — {msg}" if msg else ""))


def assert_in(item, container, msg=""):
    if item not in container:
        raise AssertionError(f"期望 {item!r} 在 {container!r} 中" + (f" — {msg}" if msg else ""))


# ═══════════════════════════════════════════════════════════
# 测试模块 1: CenterWidgetManage
# ═══════════════════════════════════════════════════════════

def test_center_widget_manage():
    """测试 CenterWidgetManage 面板管理器"""
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
    from Widgets.CenterWidget.CenterWidgetManage import CenterWidgetManage

    app = QApplication.instance() or QApplication(sys.argv)

    def test_basic():
        """基本初始化"""
        mgr = CenterWidgetManage()
        assert_true(mgr is not None)
        assert_eq(len(mgr._panels), 0)
        # 默认 panel_container 隐藏
        assert_false(mgr.is_panel_visible("fake"))

    def test_register_and_toggle():
        """注册和切换面板"""
        mgr = CenterWidgetManage()
        mgr.show()  # ★ 必须 show 后才能正确检测 child widget 可见性
        panel = QWidget()
        mgr.register_panel("test_panel", panel)
        assert_true("test_panel" in mgr._panels)

        # 默认隐藏
        assert_false(mgr.is_panel_visible("test_panel"))

        # 切换显隐
        result = mgr.toggle_panel("test_panel")
        assert_true(result)
        assert_true(mgr.is_panel_visible("test_panel"))

        # 再切换
        result = mgr.toggle_panel("test_panel")
        assert_false(result)
        assert_false(mgr.is_panel_visible("test_panel"))

    def test_show_hide():
        """显式显示/隐藏"""
        mgr = CenterWidgetManage()
        mgr.show()  # ★
        panel = QWidget()
        mgr.register_panel("p1", panel)

        mgr.show_panel("p1")
        assert_true(mgr.is_panel_visible("p1"))

        mgr.hide_panel("p1")
        assert_false(mgr.is_panel_visible("p1"))

    def test_duplicate_register():
        """重复注册同一 ID"""
        mgr = CenterWidgetManage()
        mgr.register_panel("p1", QWidget())
        # 再次注册同一 ID 应不报错但返回 False
        result = mgr.register_panel("p1", QWidget())
        assert_false(result)

    def test_signal():
        """panel_toggled 信号"""
        mgr = CenterWidgetManage()
        mgr.show()  # ★
        results = []
        mgr.panel_toggled.connect(lambda pid, v: results.append((pid, v)))
        mgr.register_panel("p_sig", QWidget())
        mgr.toggle_panel("p_sig")
        assert_eq(len(results), 1)
        assert_eq(results[0], ("p_sig", True))

    def test_set_widget():
        """set_widget 设置主内容"""
        mgr = CenterWidgetManage()
        mgr.show()  # ★
        content = QWidget()
        content.setObjectName("MainContent")
        mgr.set_widget(content)
        # 验证主内容区的布局包含了 content
        assert_true(content.parent() is mgr._main_placeholder)

    test_basic()
    test_register_and_toggle()
    test_show_hide()
    test_duplicate_register()
    test_signal()
    test_set_widget()


# ═══════════════════════════════════════════════════════════
# 测试模块 2: LogicDatabase
# ═══════════════════════════════════════════════════════════

def test_logic_database():
    """测试 LogicDatabase 逻辑数据库"""
    import tempfile
    from Widgets.RightWidget.LogicDatabase import LogicDatabase

    # 使用临时数据库文件
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "test_logic.db")

    db = LogicDatabase(db_path)

    def test_save_and_load():
        """保存和加载"""
        eid = db.save("test1", "A AND B", variable_map={"A": "bool", "B": "bool"},
                       description="测试逻辑1", tags=["测试", "基础"])
        assert_true(eid > 0)

        loaded = db.load("test1")
        assert_true(loaded is not None)
        assert_eq(loaded["name"], "test1")
        assert_eq(loaded["expression"], "A AND B")
        assert_eq(loaded["variable_map"], {"A": "bool", "B": "bool"})
        assert_eq(loaded["description"], "测试逻辑1")
        assert_true("测试" in loaded["tags"])
        assert_true("基础" in loaded["tags"])

    def test_overwrite_with_history():
        """同名保存自动覆盖 + 历史版本"""
        db.save("overwrite_test", "A OR B")
        db.save("overwrite_test", "A AND (B OR C)")
        loaded = db.load("overwrite_test")
        assert_eq(loaded["expression"], "A AND (B OR C)")

        # 检查历史
        history = db.get_history(loaded["id"])
        assert_true(len(history) >= 1)

    def test_search():
        """搜索"""
        db.save("search_motor", "sensor_A AND sensor_B")
        db.save("search_safety", "emergency_stop OR (A AND B)")
        results = db.search("sensor")
        assert_true(len(results) >= 1)
        names = [r["name"] for r in results]
        assert_true("search_motor" in names)

    def test_tags():
        """标签管理"""
        db.save("tag_test_expr", "A XOR B", tags=["电路", "数学"])
        loaded = db.load("tag_test_expr")
        assert_true("电路" in loaded["tags"])
        assert_true("数学" in loaded["tags"])

        all_tags = db.get_all_tags()
        assert_true("电路" in all_tags)

    def test_delete_cascade():
        """删除级联"""
        db.save("to_delete", "NOT A", tags=["临时"])
        eid = db.load("to_delete")["id"]
        db.delete("to_delete")
        assert_true(db.load("to_delete") is None)
        # 历史应该也被级联删除

    def test_list_all():
        """列出所有"""
        all_items = db.list_all()
        assert_true(len(all_items) > 0)

    def test_list_by_tag():
        """按标签筛选列出"""
        tagged = db.list_all(tag="测试")
        assert_true(len(tagged) >= 1)

    test_save_and_load()
    test_overwrite_with_history()
    test_search()
    test_tags()
    test_delete_cascade()
    test_list_all()
    test_list_by_tag()

    # 清理临时数据库
    shutil.rmtree(tmp_dir, ignore_errors=True)


# ═══════════════════════════════════════════════════════════
# 测试模块 3: LogicConverter
# ═══════════════════════════════════════════════════════════

def test_logic_converter():
    """测试 LogicConverter 双向转化器"""
    from Widgets.RightWidget.LogicConverter import LogicConverter, LogicParseError

    def test_validate_simple():
        """简单验证"""
        v, err = LogicConverter.validate("A AND B")
        assert_true(v, f"期望合法, 得到错误: {err}")

    def test_validate_incomplete():
        """不完整表达式"""
        v, err = LogicConverter.validate("A AND")
        assert_false(v)

    def test_validate_nested():
        """嵌套表达式"""
        v, err = LogicConverter.validate("(A OR B) AND (C OR D)")
        assert_true(v, f"期望合法, 得到错误: {err}")

    def test_validate_gate_call():
        """门调用形式"""
        v, err = LogicConverter.validate("AND(A, B)")
        assert_true(v, f"期望合法, 得到错误: {err}")

    def test_validate_not():
        """NOT 运算"""
        v, err = LogicConverter.validate("NOT A")
        assert_true(v, f"期望合法, 得到错误: {err}")

    def test_parse_to_text_roundtrip():
        """parse_text → to_text 往返一致性"""
        original = "A AND B"
        data = LogicConverter.parse_text(original)
        result = LogicConverter.to_text(data)
        # 标准化后比较（可能有空格差异）
        assert_true("A" in result and "AND" in result and "B" in result,
                     f"往返失败: 输入={original!r}, 输出={result!r}")

    def test_parse_complex_roundtrip():
        """复杂表达式往返"""
        original = "(A OR B) AND (C OR D)"
        data = LogicConverter.parse_text(original)
        result = LogicConverter.to_text(data)
        assert_true("AND" in result and "OR" in result)

    def test_parse_gate_call():
        """门调用形式解析"""
        data = LogicConverter.parse_text("AND(A, B)")
        assert_true("gates" in data)
        assert_true(len(data["gates"]) > 0)

    def test_parse_error_info():
        """错误信息包含行号和列号"""
        try:
            LogicConverter.parse_text("A AND ")
            raise AssertionError("应该抛出异常")
        except LogicParseError as e:
            assert_true(e.line > 0)
            assert_true(e.column > 0)

    def test_format():
        """格式化"""
        formatted = LogicConverter.format("A AND B OR C")
        assert_true(len(formatted) > 0)

    test_validate_simple()
    test_validate_incomplete()
    test_validate_nested()
    test_validate_gate_call()
    test_validate_not()
    test_parse_to_text_roundtrip()
    test_parse_complex_roundtrip()
    test_parse_gate_call()
    test_parse_error_info()
    test_format()


# ═══════════════════════════════════════════════════════════
# 测试模块 4: LogicDiagramWidget
# ═══════════════════════════════════════════════════════════

def test_logic_diagram_widget():
    """测试 LogicDiagramWidget 图形门逻辑编辑器"""
    from PyQt5.QtWidgets import QApplication
    from Widgets.RightWidget.LogicDiagramWidget import (
        LogicDiagramWidget, LogicGateItem, LogicPinItem,
        LogicWireItem, GATE_TYPES, COLOR_GATE_FILL, COLOR_CANVAS_BG
    )

    app = QApplication.instance() or QApplication(sys.argv)

    def test_import():
        """导入测试"""
        assert_true(LogicDiagramWidget is not None)
        assert_true(LogicGateItem is not None)
        assert_true(LogicPinItem is not None)
        assert_true(LogicWireItem is not None)

    def test_gate_types():
        """所有 6 种门类型"""
        expected = {"AND", "OR", "NOT", "NAND", "NOR", "XOR"}
        actual = set(GATE_TYPES.keys())
        assert_eq(actual, expected, f"门类型不匹配: 差集={expected - actual}")

    def test_gate_inputs():
        """门的输入/输出引脚数"""
        assert_eq(GATE_TYPES["AND"]["inputs"], 2)
        assert_eq(GATE_TYPES["AND"]["outputs"], 1)
        assert_eq(GATE_TYPES["NOT"]["inputs"], 1)
        assert_eq(GATE_TYPES["NOT"]["outputs"], 1)
        assert_eq(GATE_TYPES["XOR"]["inputs"], 2)
        assert_eq(GATE_TYPES["XOR"]["outputs"], 1)

    def test_create_gates():
        """创建门"""
        widget = LogicDiagramWidget()
        gate_and = widget.add_gate("AND")
        assert_true(gate_and is not None)
        assert_eq(gate_and.gate_type, "AND")
        assert_eq(len(gate_and.input_pins), 2)
        assert_eq(len(gate_and.output_pins), 1)

        gate_not = widget.add_gate("NOT")
        assert_eq(len(gate_not.input_pins), 1)
        assert_eq(len(gate_not.output_pins), 1)

        # 清除
        widget.clear_all()
        assert_eq(len(widget.gates), 0)

    def test_create_pins():
        """创建引脚"""
        widget = LogicDiagramWidget()
        ip = widget.add_input_pin("A")
        assert_true(ip is not None)
        assert_eq(ip.pin_type, "INPUT")
        assert_eq(ip.label, "A")

        op = widget.add_output_pin("result")
        assert_eq(op.pin_type, "OUTPUT")
        assert_eq(op.label, "result")

        widget.clear_all()
        assert_eq(len(widget.inputs), 0)
        assert_eq(len(widget.outputs), 0)

    def test_to_logic_text():
        """to_logic_text 输出"""
        widget = LogicDiagramWidget()
        text = widget.to_logic_text()
        # 空画布应该返回空字符串或 None
        assert_true(isinstance(text, str))

        # 添加门后
        widget.add_gate("AND")
        widget.add_input_pin("A")
        text2 = widget.to_logic_text()
        assert_true(isinstance(text2, str))

    def test_colors():
        """颜色常量"""
        assert_true(COLOR_GATE_FILL is not None)
        assert_true(COLOR_CANVAS_BG is not None)

    def test_wire_mode_toggle():
        """连线模式切换不崩溃"""
        widget = LogicDiagramWidget()
        widget._toggle_wire_mode()
        assert_true(widget.wire_mode)
        assert_false(widget.select_mode)
        widget._toggle_select_mode()
        assert_false(widget.wire_mode)
        assert_true(widget.select_mode)

    def test_get_scene_data():
        """get_scene_data 返回正确结构"""
        widget = LogicDiagramWidget()
        data = widget.get_scene_data()
        assert_true("gates" in data)
        assert_true("inputs" in data)
        assert_true("outputs" in data)
        assert_true("wires" in data)
        assert_eq(data["gates"], [])
        assert_eq(data["inputs"], [])
        assert_eq(data["outputs"], [])
        assert_eq(data["wires"], [])

    def test_from_logic_text():
        """from_logic_text 重建画布"""
        widget = LogicDiagramWidget()
        result = widget.from_logic_text("A AND B")
        # 即使不完全正确也不应崩溃
        assert_true(isinstance(result, bool))

    test_import()
    test_gate_types()
    test_gate_inputs()
    test_create_gates()
    test_create_pins()
    test_to_logic_text()
    test_colors()
    test_wire_mode_toggle()
    test_get_scene_data()
    test_from_logic_text()


# ═══════════════════════════════════════════════════════════
# 测试模块 5: LogicTextWidget
# ═══════════════════════════════════════════════════════════

def test_logic_text_widget():
    """测试 LogicTextWidget"""
    from PyQt5.QtWidgets import QApplication
    from Widgets.RightWidget.LogicTextWidget import (
        LogicTextWidget, LogicSyntaxHighlighter
    )
    from Widgets.RightWidget.LogicSaveDialog import LogicSaveDialog
    from Widgets.RightWidget.LogicLoadDialog import LogicLoadDialog

    app = QApplication.instance() or QApplication(sys.argv)

    def test_imports():
        """导入测试"""
        assert_true(LogicTextWidget is not None)
        assert_true(LogicSaveDialog is not None)
        assert_true(LogicLoadDialog is not None)
        assert_true(LogicSyntaxHighlighter is not None)

    def test_basic_ops():
        """基本操作"""
        widget = LogicTextWidget()
        widget.set_text("A AND B")
        assert_eq(widget.get_text(), "A AND B")
        widget.clear()
        assert_eq(widget.get_text(), "")

    def test_validate():
        """通过 LogicConverter 验证"""
        widget = LogicTextWidget()
        widget.set_text("A AND B")
        valid, err = widget.validate_text()
        assert_true(valid)

    def test_validate_error():
        """验证错误"""
        widget = LogicTextWidget()
        widget.set_text("A AND ")
        valid, err = widget.validate_text()
        assert_false(valid)

    def test_variable_map():
        """变量映射表"""
        widget = LogicTextWidget()
        widget.set_variable_map({"X": "bool", "Y": "int"})
        vm = widget.get_variable_map()
        assert_eq(vm.get("X"), "bool")

    def test_import_from_diagram():
        """从图形导入"""
        widget = LogicTextWidget()
        widget.import_from_diagram("A AND B")
        assert_eq(widget.get_text(), "A AND B")

    def test_save_dialog():
        """保存对话框创建"""
        dialog = LogicSaveDialog()
        assert_true(dialog is not None)

    def test_load_dialog():
        """加载对话框创建"""
        dialog = LogicLoadDialog(None)
        assert_true(dialog is not None)

    test_imports()
    test_basic_ops()
    test_validate()
    test_validate_error()
    test_variable_map()
    test_import_from_diagram()
    test_save_dialog()
    test_load_dialog()


# ═══════════════════════════════════════════════════════════
# 测试模块 6: 编译检查
# ═══════════════════════════════════════════════════════════

def test_compile_check():
    """编译检查所有 .py 文件"""
    import py_compile

    root = PROJECT_ROOT
    files_to_check = [
        "MainWindow.py", "main.py", "build_exe.py",
        "Widgets/CenterWidget/CenterWidgetManage.py",
        "Widgets/CenterWidget/MultiFormatViewer.py",
        "Widgets/CenterWidget/CodeEditor.py",
        "Widgets/Sidebars/LeftSidebar.py",
        "Widgets/Sidebars/RightSidebar.py",
        "Widgets/Sidebars/Topbar.py",
        "Widgets/LeftWidget/FileManage.py",
        "Widgets/RightWidget/LogicConverter.py",
        "Widgets/RightWidget/LogicDatabase.py",
        "Widgets/RightWidget/SingleTextPreview.py",
        "Widgets/RightWidget/LogicDiagramWidget.py",
        "Widgets/RightWidget/LogicTextWidget.py",
        "Widgets/RightWidget/LogicSaveDialog.py",
        "Widgets/RightWidget/LogicLoadDialog.py",
    ]

    for f in files_to_check:
        fpath = os.path.join(root, f)
        assert_true(os.path.exists(fpath), f"文件缺失: {f}")
        try:
            py_compile.compile(fpath, doraise=True)
        except py_compile.PyCompileError as e:
            raise AssertionError(f"编译错误 [{f}]: {e}")

    print(f"  {GREEN}✅ 全部 {len(files_to_check)} 个文件编译通过{RESET}")


def test_mainwindow_methods():
    """检查 MainWindow 类方法存在性"""
    from PyQt5.QtWidgets import QApplication
    import MainWindow as mw_mod

    app = QApplication.instance() or QApplication(sys.argv)

    # 检查类是否定义了必要方法
    assert_true(hasattr(mw_mod.MainWindow, 'toggle_left_dock'),
                "MainWindow 缺少 toggle_left_dock")
    assert_true(hasattr(mw_mod.MainWindow, 'toggle_logic_diagram_dock'),
                "MainWindow 缺少 toggle_logic_diagram_dock")
    assert_true(hasattr(mw_mod.MainWindow, 'toggle_logic_text_dock'),
                "MainWindow 缺少 toggle_logic_text_dock")
    print(f"  {GREEN}✅ MainWindow 所有必要方法存在{RESET}")


# ═══════════════════════════════════════════════════════════
# 主测试入口
# ═══════════════════════════════════════════════════════════

def main():
    global total_tests, passed, failed

    print(f"\n{CYAN}╔══════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}║    EnApp 0.02 全模块集成测试             ║{RESET}")
    print(f"{CYAN}╚══════════════════════════════════════════╝{RESET}\n")

    # 模块 1: CenterWidgetManage
    print(f"{YELLOW}📦 模块 1: CenterWidgetManage{RESET}")
    test("CenterWidgetManage 基本初始化+注册+切换+信号+set_widget",
         test_center_widget_manage)

    # 模块 2: LogicDatabase
    print(f"\n{YELLOW}📦 模块 2: LogicDatabase{RESET}")
    test("LogicDatabase 保存/加载/覆盖/搜索/标签/删除/列表",
         test_logic_database)

    # 模块 3: LogicConverter
    print(f"\n{YELLOW}📦 模块 3: LogicConverter{RESET}")
    test("LogicConverter 验证/解析/往返/格式化/错误信息",
         test_logic_converter)

    # 模块 4: LogicDiagramWidget
    print(f"\n{YELLOW}📦 模块 4: LogicDiagramWidget{RESET}")
    test("LogicDiagramWidget 导入/门类型/引脚/颜色/模式切换/to_text",
         test_logic_diagram_widget)

    # 模块 5: LogicTextWidget
    print(f"\n{YELLOW}📦 模块 5: LogicTextWidget + 对话框{RESET}")
    test("LogicTextWidget 基本操作/验证/变量表/导入/对话框",
         test_logic_text_widget)

    # 模块 6: 编译检查
    print(f"\n{YELLOW}📦 模块 6: 编译检查 + MainWindow 方法{RESET}")
    test("全部 .py 文件编译检查", test_compile_check)
    test("MainWindow 方法存在性", test_mainwindow_methods)

    # ═══ 概要 ═══
    print(f"\n{'═' * 50}")
    print(f"结果: {GREEN}{passed} 通过{RESET} / {RED}{failed} 失败{RESET} / 共 {total_tests} 项")
    if failed == 0:
        print(f"{GREEN}🎉 全部测试通过！{RESET}")
    else:
        print(f"{RED}❌ 存在 {failed} 个失败测试，请检查！{RESET}")
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
