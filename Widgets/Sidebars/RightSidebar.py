from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QStyle, QToolTip
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon, QFont
from PyQt5 import uic
import os


class RightSidebar(QWidget):
    def __init__(self):
        super().__init__()
        self._load_ui()
        self._init_connections()

        # 变量
        self.main_window = None  # 对 MainWindow 的引用

    def _load_ui(self):
        """加载UI文件"""
        ui_path = os.path.join(os.path.dirname(__file__), "RightSidebar.ui")
        uic.loadUi(ui_path, self)

        # 设置图标（UI文件中无法设置图标，需要在代码中设置）
        icon_dir = os.path.dirname(__file__)

        icon3_path = os.path.join(icon_dir, "icon3.ico")
        icon_logic_gate_path = os.path.join(icon_dir, "icon_logic_gate.ico")
        icon_logic_txt_path = os.path.join(icon_dir, "icon_logic_txt.ico")

        # button1 — 预览
        if os.path.exists(icon3_path):
            self.button1.setIcon(QIcon(icon3_path))
            self.button1.setIconSize(QSize(48, 48))
        else:
            self.button1.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))

        # button2 — 逻辑门编辑器
        if os.path.exists(icon_logic_gate_path):
            self.button2.setIcon(QIcon(icon_logic_gate_path))
            self.button2.setIconSize(QSize(48, 48))
        else:
            self.button2.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        # button3 — 文本逻辑
        if os.path.exists(icon_logic_txt_path):
            self.button3.setIcon(QIcon(icon_logic_txt_path))
            self.button3.setIconSize(QSize(48, 48))
        else:
            self.button3.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))

        # ★ 全局设置 ToolTip 字体大小（让提示更醒目）
        QToolTip.setFont(QFont("Microsoft YaHei", 11))
        self._setup_button_styles()

    def _setup_button_styles(self):
        """一次性设置按钮样式表，避免递归叠加"""
        btn_style = """
            QPushButton {
                background-color: transparent; border: none;
                border-radius: 6px; min-width: 48px; min-height: 48px;
            }
            QPushButton:hover { background-color: #3C3C3C; border: 1px solid #454545; }
            QPushButton:pressed { background-color: #454545; }
        """
        for btn in [self.button1, self.button2, self.button3]:
            btn.setStyleSheet(btn_style)

    def _init_connections(self):
        """初始化信号连接"""
        self.button1.clicked.connect(self._on_button1_clicked)
        self.button2.clicked.connect(self._on_button2_clicked)
        self.button3.clicked.connect(self._on_button3_clicked)

    def _on_button1_clicked(self):
        """按钮1点击事件 - 切换右侧预览 dock 显隐"""
        print("右侧边栏按钮1被点击 - 切换预览面板")
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.toggle_right_dock()

    def _on_button2_clicked(self):
        """按钮2点击事件 - 切换逻辑门图形编辑器"""
        print("右侧边栏按钮2被点击 - 切换逻辑门图形编辑器")
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.toggle_logic_diagram_dock()

    def _on_button3_clicked(self):
        """按钮3点击事件 - 切换文本逻辑编辑器"""
        print("右侧边栏按钮3被点击 - 切换文本逻辑编辑器")
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.toggle_logic_text_dock()

    def set_button1_icon(self, icon):
        """设置按钮1图标"""
        self.button1.setIcon(icon)

    def set_button2_icon(self, icon):
        """设置按钮2图标"""
        self.button2.setIcon(icon)

    def set_button1_tooltip(self, text):
        self.button1.setToolTip(text)

    def set_button2_tooltip(self, text):
        self.button2.setToolTip(text)

    def set_button3_icon(self, icon):
        self.button3.setIcon(icon)

    def set_button3_tooltip(self, text):
        self.button3.setToolTip(text)

    def set_main_window(self, main_window):
        """设置对 MainWindow 的引用"""
        self.main_window = main_window