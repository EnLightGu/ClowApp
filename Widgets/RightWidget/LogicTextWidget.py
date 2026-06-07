"""
LogicTextWidget — 文本逻辑编辑器

提供逻辑表达式文本编辑、语法高亮、变量映射表、
工具栏（语法检查/格式化/导入导出/数据库交互）以及
与 LogicDiagramWidget 的双向同步机制。
"""

import os
import re

from PyQt5 import uic
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt5.QtGui import (
    QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QPainter, QPen,
    QTextCursor, QTextFormat
)
from PyQt5.QtWidgets import (
    QWidget, QPlainTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QStyle, QLabel, QToolButton, QApplication,
    QTextEdit, QHBoxLayout, QFrame, QComboBox
)

from .LogicConverter import LogicConverter, Lexer, TokenType
from .LogicDatabase import LogicDatabase


# ════════════════════════════════════════════════════════════════
# LogicSyntaxHighlighter
# ════════════════════════════════════════════════════════════════


class LogicSyntaxHighlighter(QSyntaxHighlighter):
    """
    逻辑表达式语法高亮器

    高亮规则：
    - 关键字 AND/OR/NOT/NAND/NOR/XOR → #569CD6 (蓝色)
    - 变量 [A-Z_][A-Z0-9_]*           → #9CDCFE (青色)
    - 括号 ()                          → #FFD700 (金色)
    - 注释 #...                        → #6A9955 (绿色)
    - 赋值 =                           → #DCDCAA (浅黄)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── 关键字格式 ──────────────────────────────────────────────
        self._keyword_format = QTextCharFormat()
        self._keyword_format.setForeground(QColor("#569CD6"))
        self._keyword_format.setFontWeight(QFont.Bold)

        # ── 变量格式 ────────────────────────────────────────────────
        self._variable_format = QTextCharFormat()
        self._variable_format.setForeground(QColor("#9CDCFE"))

        # ── 括号格式 ────────────────────────────────────────────────
        self._paren_format = QTextCharFormat()
        self._paren_format.setForeground(QColor("#FFD700"))
        self._paren_format.setFontWeight(QFont.Bold)

        # ── 注释格式 ────────────────────────────────────────────────
        self._comment_format = QTextCharFormat()
        self._comment_format.setForeground(QColor("#6A9955"))
        self._comment_format.setFontItalic(True)

        # ── 赋值格式 ────────────────────────────────────────────────
        self._assign_format = QTextCharFormat()
        self._assign_format.setForeground(QColor("#DCDCAA"))

        # ── 比较运算符格式 (Task-3) ─────────────────────────────────
        self._comp_format = QTextCharFormat()
        self._comp_format.setForeground(QColor("#DCDCAA"))

        # ── 数字格式 (Task-3) ───────────────────────────────────────
        self._number_format = QTextCharFormat()
        self._number_format.setForeground(QColor("#B5CEA8"))

        # ── 字符串格式 (Task-3) ─────────────────────────────────────
        self._string_format = QTextCharFormat()
        self._string_format.setForeground(QColor("#CE9178"))

        # ── 关键字集合 ──────────────────────────────────────────────
        self._keywords = {
            "AND", "OR", "NOT", "NAND", "NOR", "XOR"
        }

        # ── RULES ───────────────────────────────────────────────────
        # 规则列表: (pattern, format)
        # 顺序很重要：后面的规则会覆盖前面的规则
        self._rules = [
            # 注释 (行注释 #)
            (re.compile(r"#[^\n]*"), self._comment_format),

            # 赋值符号
            (re.compile(r"="), self._assign_format),

            # 逻辑运算符符号（+ = OR, * = AND, ! = NOT, ~ = NOT）
            (re.compile(r"[+*!~]"), self._keyword_format),

            # 比较运算符 Task-3（排在单个 = 之后，以覆盖 == 中的 =）
            (re.compile(r"(?:==|!=|<=|>=|<|>)"), self._comp_format),

            # 括号
            (re.compile(r"[()]"), self._paren_format),

            # 关键词 (大写)
            (re.compile(r"\b(?:AND|OR|NOT|NAND|NOR|XOR)\b"), self._keyword_format),

            # 数字字面量 Task-3（排在变量之前）
            (re.compile(r"\b\d+\.?\d*\b"), self._number_format),

            # 字符串字面量 Task-3
            (re.compile(r'"[^"]*"'), self._string_format),

            # 变量 [A-Z_][A-Z0-9_]* (不匹配关键词)
            (re.compile(r"\b[A-Z_][A-Z0-9_]*\b"), self._variable_format),
        ]

    def highlightBlock(self, text: str):
        """对单个文本块执行语法高亮"""
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)


# ════════════════════════════════════════════════════════════════
# LogicTextWidget
# ════════════════════════════════════════════════════════════════


class LogicTextWidget(QWidget):
    """
    文本逻辑编辑器

    信号:
        text_changed(text: str) — 文本内容变更
        conversion_to_diagram_requested(text: str) — 请求将文本转化为图形
    """

    text_changed = pyqtSignal(str)
    conversion_to_diagram_requested = pyqtSignal(str)

    def __init__(self, parent=None, db: LogicDatabase = None):
        """
        Args:
            parent: 父窗口
            db: LogicDatabase 实例，如不提供则内部创建
        """
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), "LogicTextWidget.ui")
        uic.loadUi(ui_path, self)

        # ── 数据库 ────────────────────────────────────────────────
        self._db = db if db is not None else LogicDatabase()

        # ── 防循环同步标志 ──────────────────────────────────────────
        self._is_syncing = False

        # ── 设置语法高亮 ──────────────────────────────────────────
        self._highlighter = LogicSyntaxHighlighter(self.text_editor.document())

        # ── 配置编辑器 ────────────────────────────────────────────
        self._setup_editor()

        # ── 配置变量映射表 ────────────────────────────────────────
        self._setup_var_table()

        # ── 配置工具栏 ────────────────────────────────────────────
        self._setup_toolbar()

        # ── 连接信号 ──────────────────────────────────────────────
        self.text_editor.textChanged.connect(self._on_text_changed)

        # 初始状态
        self._update_var_table()

    # ── 编辑器设置 ─────────────────────────────────────────────────

    def _setup_editor(self):
        """配置文本编辑器的字体和行号区域"""
        font = QFont("Consolas", 12)
        font.setStyleHint(QFont.Monospace)
        self.text_editor.setFont(font)
        self.text_editor.setTabStopDistance(
            4 * self.text_editor.fontMetrics().horizontalAdvance(' ')
        )

        # 当前行高亮
        self.text_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12pt;
                border: none;
                padding: 4px;
                selection-background-color: #264F78;
            }
        """)

        # 行号区域
        self._line_number_area = _LineNumberArea(self.text_editor)
        self.text_editor.blockCountChanged.connect(self._update_line_number_width)
        self.text_editor.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_width()

        # 当前行高亮
        self.text_editor.cursorPositionChanged.connect(self._highlight_current_line)

    def _highlight_current_line(self):
        """高亮当前行"""
        extra_selections = []
        if not self.text_editor.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2A2D2E")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.text_editor.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.text_editor.setExtraSelections(extra_selections)

    def _line_number_area_width(self) -> int:
        """计算行号区域宽度"""
        digits = 1
        count = max(1, self.text_editor.blockCount())
        while count >= 10:
            count //= 10
            digits += 1
        return 10 + self.text_editor.fontMetrics().horizontalAdvance('9') * digits

    def _update_line_number_width(self):
        """更新行号区域宽度"""
        self.text_editor.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        """更新行号区域滚动位置"""
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )
        if rect.contains(self.text_editor.viewport().rect()):
            self._update_line_number_width()

    # ── 变量映射表 ─────────────────────────────────────────────────

    def _setup_var_table(self):
        """配置变量映射表"""
        self.var_table.setColumnCount(2)
        self.var_table.setHorizontalHeaderLabels(["变量名", "数据类型"])
        header = self.var_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.var_table.setRowCount(0)

    def _update_var_table(self):
        """从当前文本中提取变量并更新映射表"""
        text = self.get_text()
        variables = self._extract_variables(text)

        # 保留已有的数据类型映射
        existing_map = self._get_table_variable_map()

        self.var_table.setRowCount(0)
        for var_name in sorted(variables):
            row = self.var_table.rowCount()
            self.var_table.insertRow(row)

            name_item = QTableWidgetItem(var_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.var_table.setItem(row, 0, name_item)

            # 使用 QComboBox 提供类型选择 (Task-3)
            dtype = existing_map.get(var_name, "bool")
            dtype_combo = QComboBox()
            dtype_combo.addItems(["bool", "int", "float", "string"])
            dtype_combo.setCurrentText(dtype)
            dtype_combo.setStyleSheet("""
                QComboBox {
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                    border: 1px solid #555555;
                    padding: 2px 6px;
                    font-size: 11pt;
                }
                QComboBox:hover {
                    border-color: #569CD6;
                }
                QComboBox::drop-down {
                    border: none;
                }
            """)
            self.var_table.setCellWidget(row, 1, dtype_combo)

    def _extract_variables(self, text: str) -> set:
        """使用 Lexer 从文本中提取变量名（排除关键字）"""
        variables = set()
        try:
            lexer = Lexer(text)
            tokens = lexer.tokenize()
            for token in tokens:
                if token.type == TokenType.VARIABLE:
                    variables.add(token.value)
        except Exception:
            # 解析出错时用正则简单提取
            for match in re.finditer(r'\b[A-Z_][A-Z0-9_]*\b', text):
                word = match.group()
                if word.upper() not in {
                    "AND", "OR", "NOT", "NAND", "NOR", "XOR"
                }:
                    variables.add(word)
        return variables

    def _get_table_variable_map(self) -> dict:
        """从表格中读取现有的变量映射"""
        mapping = {}
        for row in range(self.var_table.rowCount()):
            name_item = self.var_table.item(row, 0)
            if name_item:
                name = name_item.text().strip()
                # 尝试从 QComboBox 获取类型 (Task-3)
                widget = self.var_table.cellWidget(row, 1)
                if isinstance(widget, QComboBox):
                    dtype = widget.currentText()
                else:
                    dtype_item = self.var_table.item(row, 1)
                    dtype = dtype_item.text().strip() if dtype_item else "bool"
                if name:
                    mapping[name] = dtype
        return mapping

    # ── 工具栏（程序化构建）─────────────────────────────────────

    def _setup_toolbar(self):
        """在 toolbar_container 中构建按钮工具栏"""
        layout = self.toolbar_container.layout()
        if layout is None:
            layout = QHBoxLayout()
            self.toolbar_container.setLayout(layout)

        # 清除已有子控件
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        btn_style = """
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 4px;
                border-radius: 3px;
                min-width: 28px;
                min-height: 28px;
            }
            QToolButton:hover {
                background-color: #454545;
            }
            QToolButton:pressed {
                background-color: #555555;
            }
        """

        # 创建按钮
        self.toolbar_check_btn = self._make_tool_button(
            "语法检查", QStyle.SP_MessageBoxQuestion, self._on_validate, btn_style
        )
        self.toolbar_format_btn = self._make_tool_button(
            "格式化", QStyle.SP_FileDialogContentsView, self._on_format, btn_style
        )
        self.toolbar_from_diagram_btn = self._make_tool_button(
            "从图形导入", QStyle.SP_ArrowBack, self._on_import_from_diagram, btn_style
        )
        self.toolbar_to_diagram_btn = self._make_tool_button(
            "导出到图形", QStyle.SP_ArrowForward, self._on_export_to_diagram, btn_style
        )
        self.toolbar_db_save_btn = self._make_tool_button(
            "保存到数据库", QStyle.SP_DialogSaveButton, self._on_save_to_db, btn_style
        )
        self.toolbar_db_load_btn = self._make_tool_button(
            "从数据库加载", QStyle.SP_DialogOpenButton, self._on_load_from_db, btn_style
        )

        # 添加到布局
        layout.addWidget(self.toolbar_check_btn)
        layout.addWidget(self.toolbar_format_btn)
        layout.addWidget(self._make_separator())
        layout.addWidget(self.toolbar_from_diagram_btn)
        layout.addWidget(self.toolbar_to_diagram_btn)
        layout.addWidget(self._make_separator())
        layout.addWidget(self.toolbar_db_save_btn)
        layout.addWidget(self.toolbar_db_load_btn)

        # 拉伸弹簧
        layout.addStretch(1)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(
            "color: #CCCCCC; font-size: 10pt; padding: 2px 8px;"
        )
        layout.addWidget(self.status_label)

    def _make_tool_button(self, tooltip: str, sp_enum, slot, style: str) -> QToolButton:
        """创建标准样式的工具按钮"""
        btn = QToolButton()
        btn.setToolTip(tooltip)
        btn.setIcon(self.style().standardIcon(sp_enum))
        btn.setIconSize(QSize(20, 20))
        btn.setStyleSheet(style)
        btn.clicked.connect(slot)
        return btn

    @staticmethod
    def _make_separator() -> QFrame:
        """创建垂直分隔线"""
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #555555;")
        sep.setFixedWidth(6)
        return sep

    # ── 公共接口 ───────────────────────────────────────────────────

    def get_text(self) -> str:
        """获取当前文本编辑区内容"""
        return self.text_editor.toPlainText()

    def set_text(self, text: str):
        """设置文本编辑区内容（不触发 text_changed 信号）"""
        self.text_editor.blockSignals(True)
        self.text_editor.setPlainText(text)
        self.text_editor.blockSignals(False)
        self._update_var_table()

    def get_variable_map(self) -> dict:
        """
        获取变量映射

        Returns:
            dict: {"变量名": "数据类型", ...}
        """
        return self._get_table_variable_map()

    def set_variable_map(self, mapping: dict):
        """
        设置变量映射

        Args:
            mapping: {"变量名": "数据类型", ...}
        """
        self.var_table.setRowCount(0)
        for name, dtype in mapping.items():
            row = self.var_table.rowCount()
            self.var_table.insertRow(row)
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.var_table.setItem(row, 0, name_item)
            # 使用 QComboBox (Task-3)
            dtype_combo = QComboBox()
            dtype_combo.addItems(["bool", "int", "float", "string"])
            dtype_combo.setCurrentText(dtype)
            dtype_combo.setStyleSheet("""
                QComboBox {
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                    border: 1px solid #555555;
                    padding: 2px 6px;
                    font-size: 11pt;
                }
                QComboBox:hover {
                    border-color: #569CD6;
                }
                QComboBox::drop-down {
                    border: none;
                }
            """)
            self.var_table.setCellWidget(row, 1, dtype_combo)

    def validate_text(self) -> tuple:
        """
        检查语法

        Returns:
            tuple[bool, str]: (通过, 错误信息)
        """
        return LogicConverter.validate(self.get_text())

    def format_text(self) -> str:
        """
        格式化当前文本

        Returns:
            str: 格式化后的文本
        """
        try:
            formatted = LogicConverter.format(self.get_text())
            return formatted
        except Exception as e:
            return self.get_text()

    def import_from_diagram(self, text: str):
        """
        从图形导入文本（设置 + 更新状态）

        Args:
            text: 从图形生成的逻辑表达式文本
        """
        if self._is_syncing:
            return
        self._is_syncing = True
        try:
            self.set_text(text)
            self._update_var_table()
            self.status_label.setText("✓ 已从图形导入")
            self.status_label.setStyleSheet("color: #4EC9B0;")
        finally:
            self._is_syncing = False

    def clear(self):
        """清空文本区和变量表"""
        self.set_text("")
        self.var_table.setRowCount(0)
        self.status_label.setText("已清空")
        self.status_label.setStyleSheet("color: #888888;")

    # ── 内部槽函数 ─────────────────────────────────────────────────

    def _on_text_changed(self):
        """文本内容变更回调——自动提取变量并发出 text_changed 信号"""
        if self._is_syncing:
            return

        text = self.get_text()
        self._update_var_table()
        self.text_changed.emit(text)

    def _on_validate(self):
        """语法检查按钮"""
        text = self.get_text()
        valid, error = LogicConverter.validate(text)
        if valid:
            self.status_label.setText("✓ 语法正确")
            self.status_label.setStyleSheet("color: #4EC9B0;")
        else:
            self.status_label.setText(f"✗ {error}")
            self.status_label.setStyleSheet("color: #F44747;")

    def _on_format(self):
        """格式化按钮"""
        text = self.get_text()
        try:
            formatted = LogicConverter.format(text)
            if self._is_syncing:
                return
            self._is_syncing = True
            try:
                self.set_text(formatted)
                self._update_var_table()
            finally:
                self._is_syncing = False
            self.status_label.setText("✓ 格式化完成")
            self.status_label.setStyleSheet("color: #4EC9B0;")
        except Exception as e:
            self.status_label.setText(f"✗ 格式化失败: {e}")
            self.status_label.setStyleSheet("color: #F44747;")

    def _on_import_from_diagram(self):
        """从图形导入按钮"""
        # 仅提示用户操作方式
        self.status_label.setText("请在图形编辑器中点击「导出到文本」")
        self.status_label.setStyleSheet("color: #569CD6;")

    def _on_export_to_diagram(self):
        """导出到图形按钮"""
        text = self.get_text()
        if not text.strip():
            self.status_label.setText("⚠ 文本为空，无法导出")
            self.status_label.setStyleSheet("color: #FFD700;")
            return

        valid, error = LogicConverter.validate(text)
        if not valid:
            self.status_label.setText(f"✗ 语法错误，请先修正: {error}")
            self.status_label.setStyleSheet("color: #F44747;")
            return

        # 发射信号，由外部连接 LogicDiagramWidget
        self.conversion_to_diagram_requested.emit(text)

    def _on_save_to_db(self):
        """保存到数据库按钮"""
        text = self.get_text()
        if not text.strip():
            self.status_label.setText("⚠ 文本为空，无法保存")
            self.status_label.setStyleSheet("color: #FFD700;")
            return

        # 先验证语法
        valid, error = LogicConverter.validate(text)
        if not valid:
            self.status_label.setText(f"✗ 语法错误: {error}")
            self.status_label.setStyleSheet("color: #F44747;")
            return

        # 弹出保存对话框
        from .LogicSaveDialog import LogicSaveDialog
        dialog = LogicSaveDialog(self)
        if dialog.exec_() == LogicSaveDialog.Accepted:
            data = dialog.get_data()
            try:
                var_map = self.get_variable_map()
                self._db.save(
                    name=data["name"],
                    expression=text,
                    variable_map=var_map,
                    description=data["description"],
                    tags=data["tags"],
                )
                self.status_label.setText(f"✓ 已保存: {data['name']}")
                self.status_label.setStyleSheet("color: #4EC9B0;")
            except Exception as e:
                self.status_label.setText(f"✗ 保存失败: {e}")
                self.status_label.setStyleSheet("color: #F44747;")

    def _on_load_from_db(self):
        """从数据库加载按钮"""
        from .LogicLoadDialog import LogicLoadDialog
        dialog = LogicLoadDialog(self._db, self)
        if dialog.exec_() == LogicLoadDialog.Accepted:
            record = dialog.get_selected()
            if record is None:
                return

            # 防止循环同步
            if self._is_syncing:
                return
            self._is_syncing = True
            try:
                self.set_text(record.get("expression", ""))
                var_map = record.get("variable_map", {})
                if var_map:
                    self.set_variable_map(var_map)
                else:
                    self._update_var_table()
                self.status_label.setText(f"✓ 已加载: {record.get('name', '')}")
                self.status_label.setStyleSheet("color: #4EC9B0;")
            finally:
                self._is_syncing = False

            # 询问是否同步到图形编辑器
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "同步确认",
                "是否同步到图形编辑器？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                self.conversion_to_diagram_requested.emit(record.get("expression", ""))


# ════════════════════════════════════════════════════════════════
# _LineNumberArea (行号区域)
# ════════════════════════════════════════════════════════════════


class _LineNumberArea(QWidget):
    """行号区域（从 SingleTextPreview.LineNumberArea 复用）"""

    def __init__(self, editor: QPlainTextEdit):
        super().__init__(editor)
        self._editor = editor

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor("#1E1E1E"))

        block = self._editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(
            self._editor.blockBoundingGeometry(block)
            .translated(self._editor.contentOffset())
            .top()
        )
        bottom = top + round(self._editor.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(
                    0, top,
                    self.width() - 5,
                    self._editor.fontMetrics().height(),
                    Qt.AlignRight,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + round(self._editor.blockBoundingRect(block).height())
            block_number += 1

        painter.end()

    def sizeHint(self):
        return QSize(self._calculate_width(), 0)

    def _calculate_width(self) -> int:
        """计算合适的宽度"""
        digits = 1
        count = max(1, self._editor.blockCount())
        while count >= 10:
            count //= 10
            digits += 1
        return 10 + self._editor.fontMetrics().horizontalAdvance('9') * digits
