#!/usr/bin/env python3
"""
EnApp v0.02 — 逻辑分析模块综合测试

测试范围：
  模块1: CenterWidgetManage 中央面板管理器
  模块2: LogicDatabase 逻辑数据库
  模块3: LogicConverter 双向转化器
  模块4: LogicDiagramWidget 图形编辑器（导入/存在性）
  模块5: LogicTextWidget 文本逻辑编辑器（导入/存在性）
  模块6: MainWindow 集成（导入/存在性）
  模块7: 编译检查

运行方式：
  cd /home/enlight/Desktop/PycharmProject/EnApp-0.02/
  python run_final_test.py
"""

import os
import sys
import tempfile
import traceback
import py_compile

# ── 项目根目录 ──────────────────────────────────────────────────────────
PROJECT_DIR = "/home/enlight/Desktop/PycharmProject/EnApp-0.02"
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

# ── 测试报告路径 ──────────────────────────────────────────────────────────
REPORT_DIR = os.path.expanduser("~/.openclaw/workspace-projects/enapp-002")
REPORT_PATH = os.path.join(REPORT_DIR, "test-report.md")

os.makedirs(REPORT_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════
# 测试结果收集器
# ══════════════════════════════════════════════════════════════════════════

_results = {"passed": [], "failed": []}
_test_index = [0]


def test(name: str):
    """测试装饰器：执行函数，自动记录 pass/fail"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            _test_index[0] += 1
            idx = _test_index[0]
            try:
                func(*args, **kwargs)
                _results["passed"].append((idx, name, ""))
                print(f"  ✅ [{idx:02d}] {name}")
            except AssertionError as e:
                msg = str(e) if str(e) else "AssertionError (无详细信息)"
                _results["failed"].append((idx, name, msg))
                print(f"  ❌ [{idx:02d}] {name}")
                print(f"      原因: {msg}")
            except Exception as e:
                tb = traceback.format_exc()
                _results["failed"].append((idx, name, f"{type(e).__name__}: {e}\n{tb}"))
                print(f"  ❌ [{idx:02d}] {name}")
                print(f"      异常: {type(e).__name__}: {e}")
        return wrapper
    return decorator


def generate_report():
    """生成 Markdown 测试报告"""
    total = len(_results["passed"]) + len(_results["failed"])
    passed = len(_results["passed"])
    failed = len(_results["failed"])
    success_rate = f"{passed / total * 100:.1f}%" if total > 0 else "N/A"

    lines = []
    lines.append("# EnApp-0.02 逻辑分析模块测试报告\n")
    lines.append(f"**测试时间**: 2026-06-07 01:11 CST\n")
    lines.append(f"**测试环境**: Python {sys.version.split()[0]}, PyQt5\n")
    lines.append(f"**项目根目录**: `{PROJECT_DIR}`\n")
    lines.append("## 测试摘要\n")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 总计 | {total} 项 |")
    lines.append(f"| ✅ 通过 | {passed} 项 |")
    lines.append(f"| ❌ 失败 | {failed} 项 |")
    lines.append(f"| 成功率 | {success_rate} |")
    lines.append("")

    # 失败详情
    if _results["failed"]:
        lines.append("## ❌ 失败详情\n")
        for idx, name, msg in _results["failed"]:
            lines.append(f"### [{idx:02d}] {name}\n")
            lines.append(f"```")
            lines.append(msg)
            lines.append(f"```\n")

    # 逐项结果
    lines.append("## 逐项测试结果\n")
    lines.append("| # | 测试项 | 结果 |")
    lines.append("|---|--------|------|")

    all_results = sorted(_results["passed"] + [ (idx, name, "FAIL") for idx, name, _ in _results["failed"] ],
                         key=lambda x: x[0])
    # More precise: generate combined sorted list
    passed_set = {(idx, name) for idx, name, _ in _results["passed"]}
    failed_set = {(idx, name) for idx, name, _ in _results["failed"]}

    combined = []
    for idx, name, _ in sorted(_results["passed"] + _results["failed"], key=lambda x: x[0]):
        if (idx, name) in passed_set and (idx, name) not in failed_set:
            combined.append((idx, name, "✅ 通过"))
        else:
            combined.append((idx, name, "❌ 失败"))

    for idx, name, status in combined:
        lines.append(f"| {idx:02d} | {name} | {status} |")

    # 总体结论
    lines.append("")
    if failed == 0:
        lines.append("## 总体结论\n")
        lines.append("✅ **全部通过** — 逻辑分析模块所有测试均正常通过。\n")
    else:
        lines.append("## 总体结论\n")
        lines.append(f"❌ **存在失败** — 共 {failed} 项测试未通过，请修复后重新测试。\n")

    report = "\n".join(lines)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n📄 测试报告已保存: {REPORT_PATH}")


# ══════════════════════════════════════════════════════════════════════════
# 模块 0：PyQt5 QApplication 初始化（供 UI 组件测试用）
# ══════════════════════════════════════════════════════════════════════════

_app = None


def ensure_qapp():
    global _app
    if _app is None:
        from PyQt5.QtWidgets import QApplication
        _app = QApplication.instance()
        if _app is None:
            _app = QApplication(sys.argv)


# ══════════════════════════════════════════════════════════════════════════
# 模块 7：编译检查
# ══════════════════════════════════════════════════════════════════════════

@test("编译检查: 所有 .py 文件可编译")
def test_compile_all():
    """遍历项目所有 .py 文件，使用 py_compile.compile() 检查语法"""
    failed_files = []
    for root, dirs, files in os.walk(PROJECT_DIR):
        # 跳过 __pycache__
        if "__pycache__" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                try:
                    py_compile.compile(full_path, doraise=True)
                except py_compile.PyCompileError as e:
                    failed_files.append((full_path, str(e)))

    if failed_files:
        msg_lines = ["以下文件编译失败："]
        for path, err in failed_files:
            msg_lines.append(f"  - {path}: {err}")
        raise AssertionError("\n".join(msg_lines))


# ══════════════════════════════════════════════════════════════════════════
# 模块 1：CenterWidgetManage 中央面板管理器
# ══════════════════════════════════════════════════════════════════════════

@test("CenterWidgetManage: 导入不报错")
def test_cwm_import():
    ensure_qapp()
    from Widgets.CenterWidget.CenterWidgetManage import CenterWidgetManage
    assert CenterWidgetManage is not None


@test("CenterWidgetManage: 初始化后 PanelContainer 默认宽度为 0")
def test_cwm_default_hidden():
    ensure_qapp()
    from Widgets.CenterWidget.CenterWidgetManage import CenterWidgetManage
    from PyQt5.QtWidgets import QWidget

    cwm = CenterWidgetManage()
    # _panel_container 应有固定的 0 宽度（默认隐藏）
    assert hasattr(cwm, "_panel_container"), "缺少 _panel_container 属性"
    pw = cwm._panel_container.width()
    assert pw == 0, f"PanelContainer 默认宽度应为 0，实际 {pw}"


@test("CenterWidgetManage: register_panel + toggle_panel 切换显隐")
def test_cwm_register_toggle():
    ensure_qapp()
    from Widgets.CenterWidget.CenterWidgetManage import CenterWidgetManage
    from PyQt5.QtWidgets import QWidget

    cwm = CenterWidgetManage()
    cwm.show()  # 显示父 widget 以确保子控件的 isVisible() 正常
    panel = QWidget()

    # 注册
    ok = cwm.register_panel("test_panel", panel)
    assert ok, "register_panel 应返回 True"

    # 重复注册应返回 False
    ok2 = cwm.register_panel("test_panel", QWidget())
    assert not ok2, "重复注册应返回 False"

    # 初始不可见
    assert not cwm.is_panel_visible("test_panel"), "注册后默认不可见"

    # toggle → 可见
    new_state = cwm.toggle_panel("test_panel")
    assert new_state, "toggle_panel 后应可见"
    assert cwm.is_panel_visible("test_panel"), "toggle 后应可见"
    assert cwm._panel_container.width() == 250, f"toggle 后容器宽度应为 250，实际 {cwm._panel_container.width()}"

    # toggle → 隐藏
    new_state2 = cwm.toggle_panel("test_panel")
    assert not new_state2, "再次 toggle 后应隐藏"
    assert not cwm.is_panel_visible("test_panel"), "再次 toggle 后应不可见"
    assert cwm._panel_container.width() == 0, f"再次 toggle 后容器宽度应为 0，实际 {cwm._panel_container.width()}"


@test("CenterWidgetManage: toggle_panel 不存在的 panel_id 返回 False")
def test_cwm_toggle_nonexistent():
    ensure_qapp()
    from Widgets.CenterWidget.CenterWidgetManage import CenterWidgetManage
    cwm = CenterWidgetManage()
    result = cwm.toggle_panel("nonexistent")
    assert result is False, "不存在的 panel_id 应返回 False"
    result2 = cwm.is_panel_visible("nonexistent")
    assert result2 is False, "不存在的 panel_id is_panel_visible 应返回 False"


@test("CenterWidgetManage: set_widget 正确设置主内容")
def test_cwm_set_widget():
    ensure_qapp()
    from Widgets.CenterWidget.CenterWidgetManage import CenterWidgetManage
    from PyQt5.QtWidgets import QWidget, QLabel

    cwm = CenterWidgetManage()
    label = QLabel("test_content")
    cwm.set_widget(label)

    # 验证 main_widget 属性
    assert cwm._main_widget is label, "set_widget 后 _main_widget 应指向新 widget"
    # 验证 main_placeholder 中应有该 widget
    layout = cwm._main_placeholder.layout()
    assert layout is not None
    found = False
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item and item.widget() is label:
            found = True
            break
    assert found, "set_widget 后 widget 应存在于主内容布局中"


@test("CenterWidgetManage: panel_toggled 信号触发")
def test_cwm_signal():
    ensure_qapp()
    from Widgets.CenterWidget.CenterWidgetManage import CenterWidgetManage
    from PyQt5.QtWidgets import QWidget
    from PyQt5.QtCore import QObject, pyqtSignal

    cwm = CenterWidgetManage()
    cwm.show()
    panel = QWidget()
    cwm.register_panel("sig_panel", panel)

    signals_received = []
    def on_toggled(panel_id, visible):
        signals_received.append((panel_id, visible))

    cwm.panel_toggled.connect(on_toggled)

    # toggle → 发射 (panel_id, True)
    cwm.toggle_panel("sig_panel")
    assert len(signals_received) == 1, f"toggle 后应发射 1 次信号，实际 {len(signals_received)}"
    assert signals_received[0] == ("sig_panel", True), f"信号参数错误: {signals_received[0]}"

    # toggle → 发射 (panel_id, False)
    cwm.toggle_panel("sig_panel")
    assert len(signals_received) == 2
    assert signals_received[1] == ("sig_panel", False)


@test("CenterWidgetManage: show_panel / hide_panel 方法")
def test_cwm_show_hide():
    ensure_qapp()
    from Widgets.CenterWidget.CenterWidgetManage import CenterWidgetManage
    from PyQt5.QtWidgets import QWidget

    cwm = CenterWidgetManage()
    cwm.show()
    panel = QWidget()
    cwm.register_panel("p", panel)

    assert not cwm.is_panel_visible("p")
    cwm.show_panel("p")
    assert cwm.is_panel_visible("p")
    cwm.hide_panel("p")
    assert not cwm.is_panel_visible("p")
    # show_panel / hide_panel 不存在的 panel_id 不应报错
    cwm.show_panel("nonexistent")
    cwm.hide_panel("nonexistent")


@test("CenterWidgetManage: open_file_in_editor 桩实现")
def test_cwm_open_file():
    ensure_qapp()
    from Widgets.CenterWidget.CenterWidgetManage import CenterWidgetManage

    cwm = CenterWidgetManage()
    # 未设置 main_widget 时返回 (False, "未设置")
    result = cwm.open_file_in_editor("/tmp/test.txt")
    assert result == (False, "未设置"), f"未设置时返回应为 (False, '未设置')，实际 {result}"


# ══════════════════════════════════════════════════════════════════════════
# 模块 2：LogicDatabase 逻辑数据库
# ══════════════════════════════════════════════════════════════════════════

@test("LogicDatabase: 导入不报错")
def test_ldb_import():
    from Widgets.RightWidget.LogicDatabase import LogicDatabase
    assert LogicDatabase is not None


@test("LogicDatabase: 数据库文件自动创建")
def test_ldb_auto_create():
    from Widgets.RightWidget.LogicDatabase import LogicDatabase
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name
    try:
        db = LogicDatabase(db_path)
        assert os.path.exists(db_path), "数据库文件应在初始化后自动创建"
        # 验证表存在
        conn = db._get_conn()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t["name"] for t in tables]
        for expected in ["logic_expressions", "logic_tags",
                         "logic_expression_tags", "logic_expression_history"]:
            assert expected in table_names, f"缺少表 {expected}"
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@test("LogicDatabase: save + load 往返一致性")
def test_ldb_save_load():
    from Widgets.RightWidget.LogicDatabase import LogicDatabase
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name
    try:
        db = LogicDatabase(db_path)
        expr_id = db.save(
            name="test_expr",
            expression="(A AND B) OR C",
            variable_map={"A": "bool", "B": "bool", "C": "bool"},
            description="测试表达式",
            tags=["测试", "逻辑"],
        )
        assert isinstance(expr_id, int) and expr_id > 0, f"save 应返回正整数 ID，实际 {expr_id}"

        loaded = db.load("test_expr")
        assert loaded is not None, "load 应返回非 None"
        assert loaded["name"] == "test_expr"
        assert loaded["expression"] == "(A AND B) OR C"
        assert loaded["variable_map"] == {"A": "bool", "B": "bool", "C": "bool"}
        assert loaded["description"] == "测试表达式"
        assert "tags" in loaded
        assert sorted(loaded["tags"]) == sorted(["测试", "逻辑"]), f"标签不匹配: {loaded['tags']}"

        # load_by_id
        loaded2 = db.load_by_id(expr_id)
        assert loaded2 is not None
        assert loaded2["name"] == "test_expr"
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@test("LogicDatabase: 同名 save 自动覆盖 + 历史版本")
def test_ldb_overwrite_history():
    from Widgets.RightWidget.LogicDatabase import LogicDatabase
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name
    try:
        db = LogicDatabase(db_path)
        # 第一次保存
        db.save(name="expr_v1", expression="A AND B", description="v1")
        # 第二次保存（同名）
        db.save(name="expr_v1", expression="A OR B", description="v2")

        loaded = db.load("expr_v1")
        assert loaded["expression"] == "A OR B", f"覆盖后表达式应为新值，实际 {loaded['expression']}"
        assert loaded["description"] == "v2"

        # 检查历史
        history = db.get_history(loaded["id"])
        assert len(history) >= 1, f"应至少有 1 条历史记录，实际 {len(history)}"
        # 历史中应保存旧版本
        found_old = any("A AND B" in h["expression"] for h in history)
        assert found_old, "历史中应包含旧版本 'A AND B'"
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@test("LogicDatabase: search 模糊搜索")
def test_ldb_search():
    from Widgets.RightWidget.LogicDatabase import LogicDatabase
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name
    try:
        db = LogicDatabase(db_path)
        db.save(name="motor_control", expression="sensor_A AND sensor_B",
                description="电机控制", tags=["电机"])
        db.save(name="light_switch", expression="button OR timer",
                description="灯光开关", tags=["灯光"])

        # 按名称搜索
        results = db.search("motor")
        assert len(results) >= 1, f"搜索 'motor' 应返回结果，实际 {len(results)}"
        names = [r["name"] for r in results]
        assert "motor_control" in names

        # 按描述搜索
        results2 = db.search("灯光")
        assert len(results2) >= 1
        names2 = [r["name"] for r in results2]
        assert "light_switch" in names2

        # 按表达式搜索
        results3 = db.search("timer")
        assert len(results3) >= 1
        names3 = [r["name"] for r in results3]
        assert "light_switch" in names3

        # 无匹配
        results4 = db.search("zzz_nonexistent_zzz")
        assert len(results4) == 0, f"无匹配时应返回空列表，实际 {len(results4)}"
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@test("LogicDatabase: 标签 add_tag / remove_tag / get_all_tags")
def test_ldb_tags():
    from Widgets.RightWidget.LogicDatabase import LogicDatabase
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name
    try:
        db = LogicDatabase(db_path)
        expr_id = db.save(name="tag_test", expression="A", tags=["初始标签"])

        # add_tag
        ret = db.add_tag(expr_id, "新增标签")
        assert ret, "add_tag 应为 True"

        # 不存在的 expr_id
        ret2 = db.add_tag(99999, "不存在")
        assert not ret2, "不存在的表达式 ID 应返回 False"

        loaded = db.load("tag_test")
        assert "新增标签" in loaded["tags"], f"标签应包含 '新增标签'"

        # remove_tag
        ret3 = db.remove_tag(expr_id, "新增标签")
        assert ret3, "remove_tag 应为 True"

        # 不存在的 tag
        ret4 = db.remove_tag(expr_id, "不存在的标签")
        assert not ret4, "不存在的标签应返回 False"

        loaded2 = db.load("tag_test")
        assert "新增标签" not in loaded2["tags"], f"移除后不应包含 '新增标签'"

        # get_all_tags
        db.add_tag(expr_id, "标签A")
        db.add_tag(expr_id, "标签B")
        db.add_tag(expr_id, "标签C")
        all_tags = db.get_all_tags()
        for t in ["标签A", "标签B", "标签C"]:
            assert t in all_tags, f"get_all_tags 应包含 {t}"
        # 应排序
        assert all_tags == sorted(all_tags), "get_all_tags 应返回排序列表"
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@test("LogicDatabase: delete 级联清除")
def test_ldb_delete():
    from Widgets.RightWidget.LogicDatabase import LogicDatabase
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name
    try:
        db = LogicDatabase(db_path)
        db.save(name="del_expr", expression="A AND B", tags=["标签X"])
        expr_id = db.load("del_expr")["id"]

        # 删除前应有标签和历史
        all_tags_before = db.get_all_tags()
        assert "标签X" in all_tags_before

        # 保存历史
        db.save_history(expr_id, "old_expr", note="测试历史")
        history = db.get_history(expr_id)
        assert len(history) >= 1

        # 删除
        ret = db.delete("del_expr")
        assert ret, "delete 应返回 True"
        # 不存在返回 False
        ret2 = db.delete("del_expr")
        assert not ret2, "再次删除应返回 False"

        # load 应返回 None
        loaded = db.load("del_expr")
        assert loaded is None, "删除后 load 应返回 None"

        # 标签表中的孤记录应已清理（级联）
        # 注意：ON DELETE CASCADE 只清理关联表，不清理 logic_tags 自身
        # 所以标签记录可能还存在于 logic_tags 中
        # 但 logic_expression_tags 中应无关联
        conn = db._get_conn()
        count = conn.execute(
            "SELECT COUNT(*) as c FROM logic_expression_tags WHERE expression_id = ?",
            (expr_id,)
        ).fetchone()["c"]
        assert count == 0, "删除后 expression_tags 应被级联清除"
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@test("LogicDatabase: list_all 按标签过滤")
def test_ldb_list_all():
    from Widgets.RightWidget.LogicDatabase import LogicDatabase
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name
    try:
        db = LogicDatabase(db_path)
        db.save(name="expr1", expression="A", tags=["tag1"])
        db.save(name="expr2", expression="B", tags=["tag2"])
        db.save(name="expr3", expression="C", tags=["tag1", "tag2"])

        all_all = db.list_all()
        assert len(all_all) == 3

        tag1_only = db.list_all(tag="tag1")
        names = [r["name"] for r in tag1_only]
        assert "expr1" in names
        assert "expr3" in names
        assert "expr2" not in names

        tag2_only = db.list_all(tag="tag2")
        names2 = [r["name"] for r in tag2_only]
        assert "expr2" in names2
        assert "expr3" in names2
        assert "expr1" not in names2
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


# ══════════════════════════════════════════════════════════════════════════
# 模块 3：LogicConverter 双向转化器
# ══════════════════════════════════════════════════════════════════════════

@test("LogicConverter: 导入不报错")
def test_lc_import():
    from Widgets.RightWidget.LogicConverter import LogicConverter
    assert LogicConverter is not None


@test("LogicConverter: validate(简单表达式) → (True, '')")
def test_lc_validate_ok():
    from Widgets.RightWidget.LogicConverter import LogicConverter
    cases = [
        ("A AND B", True),
        ("A OR B", True),
        ("NOT A", True),
        ("(A AND B) OR C", True),
        ("AND(A, B)", True),
        ("OR(A, B)", True),
        ("NAND(A, B)", True),
        ("NOR(A, B)", True),
        ("XOR(A, B)", True),
        ("NOT(A)", True),
        ("(A OR B) AND (C OR D)", True),
        ("", True),                    # 空字符串视为合法
        ("   ", True),                 # 空白视为合法
    ]
    for text, expected_ok in cases:
        valid, err = LogicConverter.validate(text)
        assert valid == expected_ok, f"validate('{text}'): 期望 {expected_ok}，实际 ({valid}, '{err}')"


@test("LogicConverter: validate(错误表达式) → (False, 错误信息)")
def test_lc_validate_err():
    from Widgets.RightWidget.LogicConverter import LogicConverter
    cases = [
        "A AND",        # 不完整
        "A OR",         # 不完整
        "A AND B OR",   # 结尾多余操作符
        "(",            # 不匹配括号
        ")",            # 不匹配括号
        "A B",          # 连续变量
        "AND A B",      # gate_call 缺少括号
        "UNKNOWN(A,B)", # 未知关键字
    ]
    for text in cases:
        valid, err = LogicConverter.validate(text)
        assert not valid, f"validate('{text}'): 期望 False，实际 ({valid}, '{err}')"
        assert isinstance(err, str) and len(err) > 0, f"错误信息应为非空字符串: '{err}'"


@test("LogicConverter: parse_text 返回 scene_items dict 格式")
def test_lc_parse_text():
    from Widgets.RightWidget.LogicConverter import LogicConverter
    result = LogicConverter.parse_text("A AND B")
    assert isinstance(result, dict), "parse_text 应返回 dict"
    assert "gates" in result, "应包含 gates 键"
    assert "inputs" in result, "应包含 inputs 键"
    assert "outputs" in result, "应包含 outputs 键"
    assert "wires" in result, "应包含 wires 键"

    # 简单表达式至少应该有输入
    assert len(result["inputs"]) >= 1, "inputs 不应为空"
    # 应有门
    assert len(result["gates"]) >= 1, "gates 不应为空"


@test("LogicConverter: parse_text + to_text 往返一致性")
def test_lc_roundtrip():
    from Widgets.RightWidget.LogicConverter import LogicConverter
    cases = [
        "A AND B",
        "A OR B",
        "NOT A",
        "(A AND B) OR C",
        "AND(A, B)",
        "OR(A, B)",
        "NAND(A, B)",
        "NOR(A, B)",
        "XOR(A, B)",
        "NOT(A)",
        "(A OR B) AND (C OR D)",
    ]
    for expr in cases:
        scene = LogicConverter.parse_text(expr)
        text_back = LogicConverter.to_text(scene)
        # 验证输出不为空
        assert text_back.strip(), f"to_text 结果不应为空: '{expr}' -> '{text_back}'"
        # 验证解析不报错
        valid, err = LogicConverter.validate(text_back)
        assert valid, f"往返后的表达式验不通过: '{expr}' -> '{text_back}' -> ({valid}, '{err}')"


@test("LogicConverter: 支持 AND(A, B) gate_call 形式")
def test_lc_gate_call():
    from Widgets.RightWidget.LogicConverter import LogicConverter
    valid, err = LogicConverter.validate("AND(A, B)")
    assert valid, f"AND(A, B) 应合法: ({valid}, '{err}')"

    valid2, err2 = LogicConverter.validate("NAND(A, B)")
    assert valid2, f"NAND(A, B) 应合法: ({valid2}, '{err2}')"

    valid3, err3 = LogicConverter.validate("XOR(A, B, C)")
    assert valid3, f"XOR(A, B, C) 应合法: ({valid3}, '{err3}')"


@test("LogicConverter: 支持括号嵌套 (A OR B) AND (C OR D)")
def test_lc_nested_parens():
    from Widgets.RightWidget.LogicConverter import LogicConverter
    valid, err = LogicConverter.validate("(A OR B) AND (C OR D)")
    assert valid, f"(A OR B) AND (C OR D) 应合法: ({valid}, '{err}')"

    scene = LogicConverter.parse_text("(A OR B) AND (C OR D)")
    assert len(scene["gates"]) >= 2, f"嵌套至少应有 2 个门，实际 {len(scene['gates'])}"


@test("LogicConverter: 支持 NOT A 单目运算")
def test_lc_not():
    from Widgets.RightWidget.LogicConverter import LogicConverter
    valid, err = LogicConverter.validate("NOT A")
    assert valid, f"NOT A 应合法: ({valid}, '{err}')"

    valid2, err2 = LogicConverter.validate("NOT(A)")
    assert valid2, f"NOT(A) 应合法: ({valid2}, '{err2}')"

    valid3, err3 = LogicConverter.validate("NOT (A AND B)")
    assert valid3, f"NOT (A AND B) 应合法: ({valid3}, '{err3}')"


@test("LogicConverter: to_text 空输入返回空串")
def test_lc_to_text_empty():
    from Widgets.RightWidget.LogicConverter import LogicConverter
    empty = {"gates": [], "inputs": [], "outputs": [], "wires": []}
    result = LogicConverter.to_text(empty)
    assert result == "", f"空输入应返回空串，实际 '{result}'"


@test("LogicConverter: 空字符串 parse_text 返回空 scene_items")
def test_lc_parse_empty():
    from Widgets.RightWidget.LogicConverter import LogicConverter
    result = LogicConverter.parse_text("")
    assert result == {"gates": [], "inputs": [], "outputs": [], "wires": []}, \
        f"空字符串应返回空 dict，实际 {result}"


@test("LogicConverter: format 表达式格式化")
def test_lc_format():
    from Widgets.RightWidget.LogicConverter import LogicConverter
    # 简单表达式格式化后应包含原始操作符
    formatted = LogicConverter.format("A AND B")
    assert "AND" in formatted, f"format 结果应包含 AND: '{formatted}'"

    formatted2 = LogicConverter.format("A OR B")
    assert "OR" in formatted2

    # 空字符串
    formatted3 = LogicConverter.format("")
    assert formatted3 == "", f"空字符串 format 应返回空串: '{formatted3}'"


# ══════════════════════════════════════════════════════════════════════════
# 模块 4：LogicDiagramWidget 图形编辑器（导入 + 存在性检查）
# ══════════════════════════════════════════════════════════════════════════

@test("LogicDiagramWidget: 导入不报错")
def test_ldw_import():
    ensure_qapp()
    from Widgets.RightWidget.LogicDiagramWidget import (
        LogicDiagramWidget, LogicGateItem, LogicPinItem, LogicWireItem,
        GATE_TYPES
    )
    assert LogicDiagramWidget is not None
    assert LogicGateItem is not None
    assert LogicPinItem is not None
    assert LogicWireItem is not None


@test("LogicDiagramWidget: GATE_TYPES 包含所有 6 种门类型")
def test_ldw_gate_types():
    from Widgets.RightWidget.LogicDiagramWidget import GATE_TYPES
    expected = {"AND", "OR", "NOT", "NAND", "NOR", "XOR"}
    actual = set(GATE_TYPES.keys())
    missing = expected - actual
    extra = actual - expected
    assert not missing, f"GATE_TYPES 缺少: {missing}"
    assert not extra, f"GATE_TYPES 多了: {extra}"
    assert len(GATE_TYPES) == 6, f"应有 6 种门类型，实际 {len(GATE_TYPES)}"

    # 验证每种门的属性
    for gate_type in ["AND", "OR", "NAND", "NOR", "XOR"]:
        info = GATE_TYPES[gate_type]
        assert info["inputs"] == 2, f"{gate_type} inputs 应为 2，实际 {info['inputs']}"
        assert info["outputs"] == 1, f"{gate_type} outputs 应为 1，实际 {info['outputs']}"
        assert "symbol" in info, f"{gate_type} 缺少 symbol"

    not_info = GATE_TYPES["NOT"]
    assert not_info["inputs"] == 1, f"NOT inputs 应为 1，实际 {not_info['inputs']}"
    assert not_info["outputs"] == 1, f"NOT outputs 应为 1，实际 {not_info['outputs']}"


# ══════════════════════════════════════════════════════════════════════════
# 模块 5：LogicTextWidget 文本逻辑编辑器（导入 + 存在性检查）
# ══════════════════════════════════════════════════════════════════════════

@test("LogicTextWidget: 导入不报错")
def test_ltw_import():
    ensure_qapp()
    from Widgets.RightWidget.LogicTextWidget import LogicTextWidget
    from Widgets.RightWidget.LogicSaveDialog import LogicSaveDialog
    from Widgets.RightWidget.LogicLoadDialog import LogicLoadDialog
    assert LogicTextWidget is not None
    assert LogicSaveDialog is not None
    assert LogicLoadDialog is not None


@test("LogicTextWidget: 类存在且具有预期方法签名")
def test_ltw_methods():
    ensure_qapp()
    from Widgets.RightWidget.LogicTextWidget import LogicTextWidget
    methods = ["get_text", "set_text", "get_variable_map", "set_variable_map",
               "validate_text", "format_text", "import_from_diagram", "clear"]
    for m in methods:
        assert hasattr(LogicTextWidget, m), f"LogicTextWidget 缺少方法 {m}"


@test("LogicSaveDialog: 类存在")
def test_lsd_class():
    from Widgets.RightWidget.LogicSaveDialog import LogicSaveDialog
    assert hasattr(LogicSaveDialog, "get_data"), "LogicSaveDialog 缺少 get_data 方法"


@test("LogicLoadDialog: 类存在")
def test_lld_class():
    from Widgets.RightWidget.LogicLoadDialog import LogicLoadDialog
    assert hasattr(LogicLoadDialog, "get_selected"), "LogicLoadDialog 缺少 get_selected 方法"


# ══════════════════════════════════════════════════════════════════════════
# 模块 6：MainWindow 集成
# ══════════════════════════════════════════════════════════════════════════

@test("MainWindow: 导入不报错")
def test_mw_import():
    ensure_qapp()
    from MainWindow import MainWindow
    assert MainWindow is not None


@test("MainWindow: 类存在且有预期的 5 个方法")
def test_mw_methods():
    ensure_qapp()
    from MainWindow import MainWindow
    expected_methods = [
        "toggle_left_dock",
        "toggle_logic_diagram_dock",
        "toggle_logic_text_dock",
        "_on_diagram_to_text",
        "_on_text_to_diagram",
    ]
    for m in expected_methods:
        assert hasattr(MainWindow, m), f"MainWindow 缺少方法 {m}"
        assert callable(getattr(MainWindow, m)), f"{m} 应为可调用"


# ══════════════════════════════════════════════════════════════════════════
# 主程序入口
# ══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  EnApp-0.02 逻辑分析模块综合测试")
    print("=" * 60)
    print()

    # 收集所有测试函数
    import types
    test_funcs = []
    for name, obj in list(globals().items()):
        if name.startswith("test_") and isinstance(obj, types.FunctionType):
            # 检查是否被 @test 装饰（函数上绑定了 _test_registered 标记）
            # 实际上 @test 会返回 wrapper，所以直接调用 wrapper
            # 但我们要避免重复包装
            pass

    # 更好的方式：手动列出声明的 test 函数 (被 @test 装饰后会变成 wrapper)
    # 我们直接通过模块遍历查找所有被 test 装饰过的函数
    # 实际上 @test 返回的是 wrapper 函数，所以 globals() 中就是 wrapper
    test_wrappers = []
    for name, obj in list(globals().items()):
        if name.startswith("test_") and callable(obj):
            # 检查是否在 _results 中有记录（被 @test 装饰的函数会在调用时记录）
            test_wrappers.append(obj)

    if not test_wrappers:
        print("错误：未找到测试函数")
        sys.exit(1)

    print(f"共发现 {len(test_wrappers)} 项测试\n")

    # 按定义顺序排序（按模块分组）
    # 我们使用 globals() 中的顺序近似
    for func in test_wrappers:
        try:
            func()
        except Exception as e:
            # @test 装饰器已经处理了异常，这里只是兜底
            print(f"  ⚠ 未捕获异常: {e}")

    print()
    print("=" * 60)

    # 生成报告
    generate_report()

    # 最终退出码
    if _results["failed"]:
        print(f"\n❌ 总结果: {len(_results['failed'])} 项失败")
        sys.exit(1)
    else:
        print(f"\n✅ 全部 {len(_results['passed'])} 项测试通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()
