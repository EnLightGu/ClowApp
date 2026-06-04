from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QStyle
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon
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

        # 设置图标（使用本地图标文件）
        icon_dir = os.path.dirname(__file__)

        # 使用本地图标文件
        icon3_path = os.path.join(icon_dir, "icon3.ico")
        icon4_path = os.path.join(icon_dir, "icon4.ico")

        if os.path.exists(icon3_path):
            self.button1.setIcon(QIcon(icon3_path))
            self.button1.setIconSize(QSize(32, 32))  # 设置图标大小像素
        else:
            # 备用方案：使用Qt内置图标
            self.button1.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_DirIcon', 0)))

        if os.path.exists(icon4_path):
            self.button2.setIcon(QIcon(icon4_path))
            self.button2.setIconSize(QSize(32, 32))  # 设置图标大小像素
        else:
            # 备用方案：使用Qt内置图标
            self.button2.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_FileIcon', 0)))

    def _init_connections(self):
        """初始化信号连接"""
        self.button1.clicked.connect(self._on_button1_clicked)
        self.button2.clicked.connect(self._on_button2_clicked)
        
    def _on_button1_clicked(self):
        """按钮1点击事件 - 切换右侧预览 dock 显隐"""
        print("右侧边栏按钮1被点击 - 切换预览面板")
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.toggle_right_dock()
        
    def _on_button2_clicked(self):
        """按钮2点击事件"""
        print("右侧边栏按钮2被点击")
        # 这里可以添加具体的功能逻辑
        
    def set_button1_icon(self, icon):
        """设置按钮1图标"""
        self.button1.setIcon(icon)
        
    def set_button2_icon(self, icon):
        """设置按钮2图标"""
        self.button2.setIcon(icon)
        
    def set_button1_tooltip(self, text):
        """设置按钮1提示文本"""
        self.button1.setToolTip(text)
        
    def set_button2_tooltip(self, text):
        """设置按钮2提示文本"""
        self.button2.setToolTip(text)

    def set_main_window(self, main_window):
        """设置对 MainWindow 的引用"""
        self.main_window = main_window