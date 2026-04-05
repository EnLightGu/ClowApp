import sys
from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5 import uic
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 移除默认窗口标题栏
        self.setWindowFlags(Qt.FramelessWindowHint)

        # 加载UI文件
        ui_path = os.path.join(os.path.dirname(__file__), "MainWindow.ui")
        uic.loadUi(ui_path, self)
        
        # 设置窗口属性
        self.setWindowTitle("Main Window")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化标题栏
        self._init_topbar()

        # 初始化侧边栏
        self._init_sidebars()

    def _init_topbar(self):
        """初始化自定义标题栏"""
        try:
            from Widgets.Sidebars.Topbar import Topbar
            # 创建标题栏
            self.topbar = Topbar()
            self.topbar_widget.layout().addWidget(self.topbar)

            # 设置标题
            self.topbar.set_title(self.windowTitle())

            # 连接标题栏信号
            self.topbar.minimize_clicked.connect(self._on_minimize_clicked)
            self.topbar.maximize_clicked.connect(self._on_maximize_clicked)
            self.topbar.close_clicked.connect(self._on_close_clicked)

            # 初始最大化按钮状态
            self.topbar.update_maximize_button(self.isMaximized())
        except ImportError as e:
            print(f"Error importing topbar component: {e}")
            print("Please make sure Widgets/Sidebars/Topbar.py exists")

    def _init_sidebars(self):
        """初始化侧边栏"""
        try:
            # 导入侧边栏组件
            from Widgets.Sidebars.LeftSidebar import LeftSidebar
            from Widgets.Sidebars.RightSidebar import RightSidebar

            # 创建左侧边栏
            self.left_sidebar = LeftSidebar()
            self.left_sidebar_widget.layout().addWidget(self.left_sidebar)

            # 创建右侧边栏
            self.right_sidebar = RightSidebar()
            self.right_sidebar_widget.layout().addWidget(self.right_sidebar)

        except ImportError as e:
            print(f"Error importing sidebar components: {e}")
            print("Please make sure Widgets/Sidebars folder contains LeftSidebar.py and RightSidebar.py")

    def _on_minimize_clicked(self):
        """最小化窗口"""
        self.showMinimized()

    def _on_maximize_clicked(self):
        """最大化/还原窗口"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        # 更新标题栏按钮状态
        self.topbar.update_maximize_button(self.isMaximized())

    def _on_close_clicked(self):
        """关闭窗口"""
        self.close()

    def setWindowTitle(self, title):
        """重写设置窗口标题方法，同时更新标题栏"""
        super().setWindowTitle(title)
        if hasattr(self, 'topbar'):
            self.topbar.set_title(title)

    def changeEvent(self, event):
        """窗口状态改变事件"""
        super().changeEvent(event)
        if event.type() == event.WindowStateChange:
            if hasattr(self, 'topbar'):
                self.topbar.update_maximize_button(self.isMaximized())

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 可以在这里添加清理代码
        event.accept()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())