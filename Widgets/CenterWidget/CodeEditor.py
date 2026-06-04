"""
CodeEditor — 带行号显示的只读文本编辑器组件

从 MultiFileEditor.py 中提取，供 MultiFormatViewer 复用。
"""
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QFont, QColor, QPainter, QTextFormat
from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QTextEdit


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
    """带行号显示和暗色主题的只读文本编辑器"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 行号区域
        self.line_number_area = LineNumberArea(self)

        # 信号连接
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        # 设置暗色主题
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #CCCCCC;
                border: none;
            }
        """)

        # 等宽字体 12pt
        font = QFont("Courier New", 12)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        # 只读
        self.setReadOnly(True)

        # Tab 宽度 4 空格
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)

        # 初始化行号区域宽度
        self.update_line_number_area_width()

        # 高亮当前行
        self.highlight_current_line()

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
                # 当前行高亮白色，其他行灰色
                if block == current_block:
                    painter.setPen(QColor("#FFFFFF"))
                else:
                    painter.setPen(QColor("#858585"))
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
