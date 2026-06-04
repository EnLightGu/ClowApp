"""
SingleTextPreview — 右侧单文件只读文本预览器

作为右侧 QDockWidget 的内容，显示从 FileManage treeView 双击的最新文本文件。

区别于 MultiFormatViewer：
  - SingleTextPreview：只显示一个文件，不做多标签，只读文本预览
  - MultiFormatViewer：多标签，支持多种格式
"""
import os

from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QFont, QColor, QPainter
from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QVBoxLayout


# ════════════════════════════════════════════════════════════════
# LineNumberArea
# ════════════════════════════════════════════════════════════════
class LineNumberArea(QWidget):
    """行号区域（从 MultiFileEditor 复用）"""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor("#252526"))

        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.editor.blockBoundingGeometry(block).translated(
            self.editor.contentOffset()
        ).top()
        bottom = top + self.editor.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(0, int(top), self.width() - 5,
                                 int(self.editor.fontMetrics().height()),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.editor.blockBoundingRect(block).height()
            block_number += 1

        painter.end()

    def sizeHint(self):
        return QSize(50, 0)


# ════════════════════════════════════════════════════════════════
# CodeEditor
# ════════════════════════════════════════════════════════════════
class CodeEditor(QPlainTextEdit):
    """代码编辑器（从 MultiFileEditor 复用）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        # 暗色主题
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #CCCCCC;
                font-family: 'Courier New', 'Consolas', 'monospace';
                font-size: 12pt;
            }
        """)

        font = QFont("Courier New", 12)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self.setTabStopWidth(4 * self.fontMetrics().width(' '))

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width()

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        return 10 + self.fontMetrics().width('9') * digits

    def update_line_number_area_width(self):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(),
                                         self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )


# ════════════════════════════════════════════════════════════════
# SingleTextPreview
# ════════════════════════════════════════════════════════════════
class SingleTextPreview(QWidget):
    """单文件只读文本预览器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.editor = CodeEditor()
        self.editor.setReadOnly(True)
        layout.addWidget(self.editor)

        self.current_file = None

    def open_file(self, file_path):
        """打开并显示一个文本文件

        Args:
            file_path: 文件路径

        Returns:
            tuple[bool, str]: (成功, 错误信息或空串)
        """
        if not os.path.exists(file_path):
            return False, "文件不存在"

        # 编码检测
        content = self._read_with_encoding(file_path)
        if content is None:
            return False, "无法解码文件编码"

        self.editor.setPlainText(content)
        self.current_file = file_path
        return True, ""

    def _read_with_encoding(self, file_path):
        """编码检测链：chardet → UTF-8 → UTF-16 → GBK → Latin-1

        Returns:
            str | None: 解码后的文本内容，失败返回 None
        """
        # 先用二进制读取
        try:
            with open(file_path, 'rb') as f:
                raw = f.read()
        except (PermissionError, OSError):
            return None

        # 1. chardet 检测（可选依赖）
        try:
            import chardet
            result = chardet.detect(raw)
            encoding = result.get('encoding', 'utf-8')
            if encoding:
                try:
                    return raw.decode(encoding)
                except (UnicodeDecodeError, UnicodeError, LookupError):
                    pass
        except ImportError:
            pass

        # 2. fallback 编码链
        for enc in ['utf-8', 'utf-16', 'gbk', 'latin-1']:
            try:
                return raw.decode(enc)
            except (UnicodeDecodeError, UnicodeError, LookupError):
                continue

        return None

    def clear(self):
        """清空预览"""
        self.editor.clear()
        self.current_file = None
