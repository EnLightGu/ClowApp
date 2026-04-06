import platform
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import uic
# from Widgets.WindowManager import WindowManager

import os



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 加载UI文件
        ui_path = os.path.join(os.path.dirname(__file__), "MainWindow.ui")
        uic.loadUi(ui_path, self)


        if platform.system() == "Linux":
            # 移除默认窗口标题栏 适配linux
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setGeometry(100, 100, 1200, 800)
        else:
            # 移除默认窗口标题栏 适配windows
            from ctypes import windll, wintypes
            self.setWindowFlags(Qt.Window)
            self.setGeometry(100, 100, 1200, 800)
            self.hide_title_bar()
            self.resize(1100, 700)  #刷新窗口使hide_title_bar()生效，需在加载ui之后

        # 设置窗口属性
        self.setWindowTitle("Main Window")

        # 初始化标题栏
        self._init_topbar()
        # 初始化侧边栏
        self._init_sidebars()
        # 初始化中心组件
        self._init_center_widget()


    def hide_title_bar(self):
        from ctypes import windll, wintypes
        hwnd = int(self.winId())
        user32 = windll.user32

        # Windows 常量
        GWL_STYLE = -16
        GWL_EXSTYLE = -20
        WS_CAPTION = 0x00C00000
        WS_THICKFRAME = 0x00040000
        WS_MINIMIZEBOX = 0x00020000
        WS_MAXIMIZEBOX = 0x00010000
        WS_SYSMENU = 0x00080000

        # 获取当前窗口样式
        style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)

        # 移除标题栏，但保留：缩放、最大化、最小化、系统菜单
        style &= ~WS_CAPTION  # 移除标题栏（关键）
        style |= WS_THICKFRAME  # 保留缩放边框
        style |= WS_MINIMIZEBOX  # 保留最小化
        style |= WS_MAXIMIZEBOX  # 保留最大化
        style |= WS_SYSMENU  # 保留系统菜单（右键任务栏）

        user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)

        # 刷新窗口非客户区（让隐藏立即生效）
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)

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

            #设置左侧边栏对中心窗口管理器的引用 #用于left_sidebar的button向center_widget_manager添加dock
            if hasattr(self, 'center_widget_manager'):
                self.left_sidebar.set_center_widget_manager(self.center_widget_manager)

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
#
    def _on_close_clicked(self):
        """关闭窗口"""
        self.close()
#
    def setWindowTitle(self, title):
        """重写设置窗口标题方法，同时更新标题栏"""
        super().setWindowTitle(title)
        if hasattr(self, 'topbar'):
            self.topbar.set_title(title)
#
    def changeEvent(self, event):
        """窗口状态改变事件"""
        super().changeEvent(event)
        if event.type() == event.WindowStateChange:
            if hasattr(self, 'topbar'):
                self.topbar.update_maximize_button(self.isMaximized())

    def _init_center_widget(self):
        """初始化中心组件"""
        try:
            # 导入中心组件
            from Widgets.CenterWidget.CenterWidgetManage import CenterWidgetManage

            # 创建中心窗口管理器实例
            self.center_widget_manager = CenterWidgetManage(self)

            # 设置中心窗口管理器为无边框，避免重复标题栏 #貌似没什么用
            self.center_widget_manager.setWindowFlags(Qt.Widget)

            # 将中心窗口管理器添加到主内容区域的布局中
            self.main_content_widget.layout().addWidget(self.center_widget_manager)

            # 设置中心窗口管理器的大小策略，使其可以扩展
            self.center_widget_manager.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            print("Center widget manager initialized successfully")

            # 如果左侧边栏已经初始化，设置其对中心窗口管理器的引用
            if hasattr(self, 'left_sidebar'):
                self.left_sidebar.set_center_widget_manager(self.center_widget_manager)


        except ImportError as e:
            print(f"Error importing CenterWidget component: {e}")
            print("Please make sure Widgets/CenterWidget/CenterWidgetManage.py exists")
        except Exception as e:
            print(f"Error initializing center widget: {e}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 可以在这里添加清理代码
        event.accept()



if __name__ == "__main__":
    # from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())