from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
import os
from PyQt5 import uic

class FileManage(QWidget):
    """
    文件管理子窗口
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化UI
        self._load_ui()
        
        # 确保标签居中
        # self.ui.label.setAlignment(Qt.AlignCenter)

    def _load_ui(self):
        """加载UI文件"""
        ui_path = os.path.join(os.path.dirname(__file__), "FileManage.ui")
        uic.loadUi(ui_path, self)
        
    def show_window(self):
        """显示窗口"""
        self.show()
        self.raise_()
        self.activateWindow()