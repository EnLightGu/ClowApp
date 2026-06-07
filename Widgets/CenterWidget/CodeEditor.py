"""
CodeEditor — 带行号的可编辑文本编辑器组件

从 MultiFileEditor.py 中提取，供 MultiFormatViewer 复用。
v0.02: 可编辑模式 + 右键菜单 + 语法高亮 + Consolas 12pt + 暗色主题
"""
from PyQt5.QtCore import Qt, QRect, QRegularExpression, pyqtSignal
from PyQt5.QtGui import (
    QFont, QColor, QPainter, QTextFormat, QSyntaxHighlighter,
    QTextCharFormat, QFontInfo, QKeySequence, QTextCursor,
)
from PyQt5.QtWidgets import (
    QWidget, QPlainTextEdit, QTextEdit, QMenu, QAction,
)


# ════════════════════════════════════════════════════════════════
# SimpleSyntaxHighlighter
# ════════════════════════════════════════════════════════════════
class SimpleSyntaxHighlighter(QSyntaxHighlighter):
    """
    通用语法高亮器 — 支持编程语言常用关键字、字符串、注释、数字。

    配色方案（匹配架构文档）:
        - 关键字:   #569CD6 (蓝色)
        - 字符串:   #CE9178 (橙棕)
        - 注释:     #6A9955 (绿色)
        - 数字:     #B5CEA8 (青绿)
        - 函数调用: #DCDCAA (淡黄)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        self._build_rules()

    def _build_rules(self):
        """构建高亮规则列表"""
        rules = []

        # ── 1. 注释 ──────────────────────────────────────────
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6A9955"))
        # 单行注释: # 或 //
        rules.append((QRegularExpression(r"#[^\n]*"), comment_fmt))
        rules.append((QRegularExpression(r"//[^\n]*"), comment_fmt))
        # 多行注释块 (/* ... */)
        self._multi_line_comment_fmt = QTextCharFormat()
        self._multi_line_comment_fmt.setForeground(QColor("#6A9955"))
        self._comment_start_expr = QRegularExpression(r"/\*")
        self._comment_end_expr = QRegularExpression(r"\*/")

        # ── 2. 字符串 ────────────────────────────────────────
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#CE9178"))
        # 双引号字符串
        rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), str_fmt))
        # 单引号字符串
        rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), str_fmt))
        # 三引号字符串 (Python)
        triple_str_fmt = QTextCharFormat()
        triple_str_fmt.setForeground(QColor("#CE9178"))
        rules.append((QRegularExpression(r'"""[\s\S]*?"""'), triple_str_fmt))
        rules.append((QRegularExpression(r"'''[\s\S]*?'''"), triple_str_fmt))

        # ── 3. 数字 ──────────────────────────────────────────
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#B5CEA8"))
        rules.append((QRegularExpression(r"\b[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?\b"), num_fmt))

        # ── 4. 关键字 ────────────────────────────────────────
        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor("#569CD6"))
        keyword_fmt.setFontWeight(QFont.Bold)

        keywords = [
            # Python
            "and", "as", "assert", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "finally", "for", "from",
            "global", "if", "import", "in", "is", "lambda", "nonlocal",
            "not", "or", "pass", "raise", "return", "try", "while",
            "with", "yield", "True", "False", "None",
            # JavaScript / TypeScript
            "const", "let", "var", "function", "return", "if", "else",
            "switch", "case", "break", "continue", "default", "for",
            "while", "do", "new", "this", "typeof", "instanceof", "void",
            "delete", "import", "export", "from", "class", "extends",
            "super", "async", "await", "yield", "null", "undefined",
            "true", "false",
            # C / C++ / Java
            "int", "float", "double", "char", "void", "bool", "long",
            "short", "unsigned", "signed", "struct", "union", "enum",
            "typedef", "sizeof", "auto", "static", "extern", "register",
            "volatile", "const", "inline", "virtual", "override",
            "public", "private", "protected", "friend", "operator",
            "template", "typename", "namespace", "using", "throw",
            "try", "catch", "class", "this", "new", "delete",
            "true", "false", "NULL", "nullptr",
            # SQL
            "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES",
            "UPDATE", "SET", "DELETE", "CREATE", "TABLE", "DROP",
            "ALTER", "INDEX", "JOIN", "LEFT", "RIGHT", "INNER",
            "OUTER", "ON", "AND", "OR", "NOT", "IN", "LIKE",
            "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET",
            "AS", "DISTINCT", "COUNT", "SUM", "AVG", "MIN", "MAX",
            "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "CASCADE",
            # Logic keywords (架构文档)
            "AND", "OR", "NOT", "NAND", "NOR", "XOR",
        ]

        for kw in keywords:
            rules.append((QRegularExpression(r"\b{}\b".format(kw)), keyword_fmt))

        # ── 5. 函数调用 ──────────────────────────────────────
        func_fmt = QTextCharFormat()
        func_fmt.setForeground(QColor("#DCDCAA"))
        rules.append((QRegularExpression(r"\b\w+(?=\s*\()"), func_fmt))

        # ── 6. 装饰器 / 预处理 ────────────────────────────────
        decorator_fmt = QTextCharFormat()
        decorator_fmt.setForeground(QColor("#D7BA7D"))
        rules.append((QRegularExpression(r"@\w+"), decorator_fmt))
        rules.append((QRegularExpression(r"#\s*(include|define|pragma|ifdef|ifndef|endif|else|elif)\b"), decorator_fmt))

        self._rules = rules

    def highlightBlock(self, text):
        """高亮一个文本块"""
        # 应用单行规则
        for pattern, fmt in self._rules:
            match = pattern.match(text)
            while match.hasMatch():
                index = match.capturedStart()
                length = match.capturedLength()
                if length > 0:
                    self.setFormat(index, length, fmt)
                match = pattern.match(text, index + length)

        # 处理多行注释
        self._highlight_multi_line_comment(text)

    def _highlight_multi_line_comment(self, text):
        """处理 /* ... */ 跨行注释"""
        self.setCurrentBlockState(0)

        if self.previousBlockState() != 1:
            start_match = self._comment_start_expr.match(text)
            start_index = start_match.capturedStart() if start_match.hasMatch() else -1
        else:
            # 延续上一块的注释
            start_index = 0

        while start_index >= 0:
            end_match = self._comment_end_expr.match(text, start_index)
            if end_match.hasMatch():
                end_index = end_match.capturedStart()
                length = end_index - start_index + end_match.capturedLength()
                if length > 0:
                    self.setFormat(start_index, length, self._multi_line_comment_fmt)
                next_match = self._comment_start_expr.match(text, start_index + length)
                start_index = next_match.capturedStart() if next_match.hasMatch() else -1
            else:
                # 注释在本块未结束
                self.setCurrentBlockState(1)
                length = len(text) - start_index
                if length > 0:
                    self.setFormat(start_index, length, self._multi_line_comment_fmt)
                break


# ════════════════════════════════════════════════════════════════
# LineNumberArea
# ════════════════════════════════════════════════════════════════
class LineNumberArea(QWidget):
    """在 CodeEditor 左侧绘制行号的面板"""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)
        return super().paintEvent(event)

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)


# ════════════════════════════════════════════════════════════════
# CodeEditor（带行号的 QPlainTextEdit）
# ════════════════════════════════════════════════════════════════
class CodeEditor(QPlainTextEdit):
    """
    带行号显示、暗色主题、可编辑的文本编辑器。

    Signals:
        save_requested():     用户通过右键菜单或快捷键请求保存
        modification_state_changed(bool): 修改状态变化
    """

    save_requested = pyqtSignal()
    modification_state_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 行号区域
        self.line_number_area = LineNumberArea(self)

        # 信号连接
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        # 设置暗色主题 — 前景 #FFFFFF
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: none;
                selection-background-color: #264F78;
            }
        """)

        # 等宽字体 Consolas 12pt
        font = QFont("Consolas", 12)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        # 可编辑模式 (v0.02)
        self.setReadOnly(False)

        # Tab 宽度 4 空格
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)

        # 初始化行号区域宽度
        self.update_line_number_area_width()

        # 高亮当前行
        self.highlight_current_line()

        # 修改状态跟踪
        self._is_modified = False
        self.textChanged.connect(self._on_text_changed)

        # 自定义右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # 语法高亮
        self._highlighter = SimpleSyntaxHighlighter(self.document())

    # ── 修改状态 ──────────────────────────────────────────────

    def _on_text_changed(self):
        """文本内容变化 → 更新修改状态"""
        if not self._is_modified:
            self._is_modified = True
            self.modification_state_changed.emit(True)

    def reset_modified(self):
        """保存后重置修改状态"""
        self._is_modified = False
        self.document().setModified(False)
        self.modification_state_changed.emit(False)

    def has_unsaved_changes(self) -> bool:
        """返回当前文件是否已被修改（区别于 QPlainTextEdit.isModified）"""
        return self._is_modified

    # ── 右键菜单 ──────────────────────────────────────────────

    def _show_context_menu(self, position):
        """显示带编辑操作的自定义右键菜单"""
        menu = QMenu(self)

        # 复制
        copy_action = QAction("复制", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy)
        copy_action.setEnabled(self.textCursor().hasSelection())
        menu.addAction(copy_action)

        # 粘贴
        paste_action = QAction("粘贴", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste)
        menu.addAction(paste_action)

        # 剪切
        cut_action = QAction("剪切", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.cut)
        cut_action.setEnabled(self.textCursor().hasSelection())
        menu.addAction(cut_action)

        menu.addSeparator()

        # 全选
        select_all_action = QAction("全选", self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(self.selectAll)
        menu.addAction(select_all_action)

        menu.addSeparator()

        # 保存
        save_action = QAction("保存", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._on_save_requested)
        menu.addAction(save_action)

        menu.exec(self.mapToGlobal(position))

    def _on_save_requested(self):
        """右键菜单或快捷键触发保存请求"""
        self.save_requested.emit()

    # ── 行号宽度 ──────────────────────────────────────────────
    def line_number_area_width(self):
        """根据总行数计算行号区域宽度"""
        digits = len(str(max(1, self.blockCount())))
        return 5 + 10 * digits

    def update_line_number_area_width(self, _new_block_count=None):
        """行数变化时更新行号区宽度"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """同步滚动时更新行号区"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(),
                self.line_number_area.width(),
                rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    # ── 事件重写 ──────────────────────────────────────────────
    def resizeEvent(self, event):
        """窗口大小变化时同步调整行号区域几何"""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(),
                  self.line_number_area_width(), cr.height())
        )

    def keyPressEvent(self, event):
        """按键事件 — Ctrl+S 拦截并转发为 save_requested 信号"""
        if event.matches(QKeySequence.Save):
            self._on_save_requested()
            return
        super().keyPressEvent(event)

    # ── 行号绘制 ──────────────────────────────────────────────
    def line_number_area_paint_event(self, event):
        """绘制行号"""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#252526"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block)
            .translated(self.contentOffset())
            .top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())

        current_block = self.textCursor().block()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                # 当前行白色，其他行 #888888 (v0.02)
                if block == current_block:
                    painter.setPen(QColor("#FFFFFF"))
                else:
                    painter.setPen(QColor("#888888"))
                painter.drawText(
                    0, top,
                    self.line_number_area.width(),
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

        painter.end()

    # ── 当前行高亮 ────────────────────────────────────────────
    def highlight_current_line(self):
        """用浅色背景高亮当前行"""
        extra_selections = []

        selection = QTextEdit.ExtraSelection()
        line_color = QColor("#2A2D2E")
        selection.format.setBackground(line_color)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()

        extra_selections.append(selection)
        self.setExtraSelections(extra_selections)
