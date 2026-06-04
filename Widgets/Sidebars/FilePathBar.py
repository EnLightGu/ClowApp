from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt


class FilePathBar(QWidget):
    """底部路径栏 — 显示当前文件的完整路径"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)

        self.path_label = QLabel("当前文件: (无)")
        self.path_label.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        layout.addWidget(self.path_label)
        layout.addStretch()

        self.setStyleSheet("background-color: #252526;")
        # 高度 = 字体高度 + 上下边距（紧凑）
        font_metrics = self.path_label.fontMetrics()
        line_height = font_metrics.height()
        self.setFixedHeight(line_height + 8)  # 8px 垂直内边距

    def set_file_path(self, file_path):
        """设置显示的文件路径"""
        if file_path:
            self.path_label.setText(f"当前文件: {file_path}")
            # tooltip 显示完整路径
            self.path_label.setToolTip(file_path)
        else:
            self.path_label.setText("当前文件: (无)")
            self.path_label.setToolTip("")
