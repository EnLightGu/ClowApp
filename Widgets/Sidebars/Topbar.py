from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5 import uic
import os

class Topbar(QWidget):
    """自定义标题栏组件"""

    # 定义信号
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 加载UI文件
        ui_path = os.path.join(os.path.dirname(__file__), "Topbar.ui")
        uic.loadUi(ui_path, self)

        # 设置窗口标志，使其成为标题栏
        self.setWindowFlags(Qt.FramelessWindowHint)

        # 连接按钮信号
        self.minimize_button.clicked.connect(self._on_minimize_clicked)
        self.maximize_button.clicked.connect(self._on_maximize_clicked)
        self.close_button.clicked.connect(self._on_close_clicked)

        # 初始化最大化按钮状态
        self._is_maximized = False

        # 启用鼠标跟踪
        self.setMouseTracking(True)

    def set_title(self, title):
        """设置标题文本"""
        self.title_label.setText(title)

    def get_title(self):
        """获取标题文本"""
        return self.title_label.text()

    def _on_minimize_clicked(self):
        """最小化按钮点击事件"""
        self.minimize_clicked.emit()

    def _on_maximize_clicked(self):
        """最大化/还原按钮点击事件"""
        self.maximize_clicked.emit()

    def _on_close_clicked(self):
        """关闭按钮点击事件"""
        self.close_clicked.emit()

    def update_maximize_button(self, is_maximized):
        """更新最大化按钮状态"""
        self._is_maximized = is_maximized
        if is_maximized:
            self.maximize_button.setText("❐")  # 还原图标
        else:
            self.maximize_button.setText("□")  # 最大化图标

    def mousePressEvent(self, event):
        """鼠标按下事件 - 只处理标题栏区域的拖动"""
        if event.button() == Qt.LeftButton:
            # 启动窗口拖动
            self.window().windowHandle().startSystemMove()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件，用于最大化/还原"""
        if event.button() == Qt.LeftButton:
            self.maximize_clicked.emit()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
