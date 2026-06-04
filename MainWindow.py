import platform
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QCursor
from PyQt5 import uic

import os


# 窗口边缘拖拽调整大小的阈值（像素）
RESIZE_MARGIN = 8



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

        # ① 初始化标题栏（无依赖）
        self._init_topbar()
        # ② 初始化中央预览器
        self._init_center_widget()
        # ③ 初始化侧边栏（创建 LeftSidebar/RightSidebar widget）
        self._init_sidebars()
        # ④ 初始化 QDockWidget（边栏QDock + 文件管理 + 底部路径 + 右侧预览）
        self._init_docks()


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

    # ── 窗口边缘调整大小 ──
    _resizing = False
    _resize_dir = 0  # 0=None 1=L 2=R 3=T 4=B 5=TL 6=TR 7=BL 8=BR

    def _get_resize_cursor(self, pos):
        """根据鼠标位置返回调整大小的光标和方向"""
        rect = self.rect()
        x, y = pos.x(), pos.y()
        w, h = rect.width(), rect.height()

        on_left = x < RESIZE_MARGIN
        on_right = x > w - RESIZE_MARGIN
        on_top = y < RESIZE_MARGIN
        on_bottom = y > h - RESIZE_MARGIN

        if on_top and on_left:
            return QCursor(Qt.SizeFDiagCursor), 5
        if on_top and on_right:
            return QCursor(Qt.SizeBDiagCursor), 6
        if on_bottom and on_left:
            return QCursor(Qt.SizeBDiagCursor), 7
        if on_bottom and on_right:
            return QCursor(Qt.SizeFDiagCursor), 8
        if on_left:
            return QCursor(Qt.SizeHorCursor), 1
        if on_right:
            return QCursor(Qt.SizeHorCursor), 2
        if on_top:
            return QCursor(Qt.SizeVerCursor), 3
        if on_bottom:
            return QCursor(Qt.SizeVerCursor), 4
        return QCursor(Qt.ArrowCursor), 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            cursor, direction = self._get_resize_cursor(event.pos())
            if direction:
                self._resizing = True
                self._resize_dir = direction
                self._resize_start_pos = event.globalPos()
                self._resize_start_geom = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing and self._resize_dir:
            delta = event.globalPos() - self._resize_start_pos
            dx, dy = delta.x(), delta.y()
            geom = QRect(self._resize_start_geom)

            if self._resize_dir == 1:  # Left
                geom.setLeft(geom.left() + dx)
            elif self._resize_dir == 2:  # Right
                geom.setRight(geom.right() + dx)
            elif self._resize_dir == 3:  # Top
                geom.setTop(geom.top() + dy)
            elif self._resize_dir == 4:  # Bottom
                geom.setBottom(geom.bottom() + dy)
            elif self._resize_dir == 5:  # Top-Left
                geom.setTopLeft(geom.topLeft() + delta)
            elif self._resize_dir == 6:  # Top-Right
                geom.setTopRight(geom.topRight() + delta)
            elif self._resize_dir == 7:  # Bottom-Left
                geom.setBottomLeft(geom.bottomLeft() + delta)
            elif self._resize_dir == 8:  # Bottom-Right
                geom.setBottomRight(geom.bottomRight() + delta)

            if geom.width() >= self.minimumWidth() and geom.height() >= self.minimumHeight():
                self.setGeometry(geom)
            event.accept()
            return

        # 鼠标悬停时改变光标
        if not self._resizing:
            cursor, _ = self._get_resize_cursor(event.pos())
            self.setCursor(cursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resizing:
            self._resizing = False
            self._resize_dir = 0
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _init_topbar(self):
        """初始化自定义标题栏"""
        try:
            from Widgets.Sidebars.Topbar import Topbar
            # 创建标题栏
            self.topbar = Topbar()
            self.topbar_widget.layout().addWidget(self.topbar)

            # 设置标题
            self.topbar.set_title('主窗口')

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
        """初始化侧边栏 QDockWidget，注入主窗口引用"""
        try:
            from Widgets.Sidebars.LeftSidebar import LeftSidebar
            from Widgets.Sidebars.RightSidebar import RightSidebar

            self.left_sidebar = LeftSidebar()
            self.left_sidebar.set_main_window(self)

            self.right_sidebar = RightSidebar()
            self.right_sidebar.set_main_window(self)

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
        """初始化中央多格式预览器（替代 CenterWidgetManage）"""
        from Widgets.CenterWidget.MultiFormatViewer import MultiFormatViewer
        from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy

        try:
            # 为 main_content_widget 创建布局
            layout = QVBoxLayout(self.main_content_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # 创建 MultiFormatViewer
            self.multi_format_viewer = MultiFormatViewer(self)
            self.multi_format_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout.addWidget(self.multi_format_viewer)

            print("MultiFormatViewer initialized successfully")

        except ImportError as e:
            print(f"Error importing MultiFormatViewer: {e}")
            print("Please make sure Widgets/CenterWidget/MultiFormatViewer.py exists")
        except Exception as e:
            print(f"Error initializing center widget: {e}")

    def _on_file_manage_double_clicked(self, file_path):
        """文件双击 → 中央预览器打开 + 右侧单文本预览"""
        # 中央多格式预览器打开
        success, error_msg = self.multi_format_viewer.open_file(file_path)
        if not success:
            print(f"打开文件失败: {error_msg}")

        # 右侧单文本预览（只支持文本文件）
        self.single_text_preview.open_file(file_path)

    def _init_docks(self):
        """初始化所有 QDockWidget（左右边栏固定 + 文件管理Dock + 底部路径 + 右侧预览）"""
        from Widgets.LeftWidget.FileManage import FileManage
        from Widgets.RightWidget.SingleTextPreview import SingleTextPreview
        from Widgets.Sidebars.FilePathBar import FilePathBar

        # ── A. 左侧固定边栏 QDockWidget ──
        self.left_sidebar_dock = QDockWidget("", self)
        self.left_sidebar_dock.setWidget(self.left_sidebar)
        self.left_sidebar_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.left_sidebar_dock.setTitleBarWidget(QWidget())
        self.left_sidebar_dock.setFixedWidth(80)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_sidebar_dock)

        # ── B. 左侧 Dock — FileManage（与边栏水平分割）──
        self.file_manage_widget = FileManage()
        self.left_dock = QDockWidget("文件管理", self)
        self.left_dock.setWidget(self.file_manage_widget)
        self.left_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.left_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)
        # 用 splitDockWidget 将左侧区域水平拆分为 [边栏 | 文件管理]，边栏永远在左边缘
        self.splitDockWidget(self.left_sidebar_dock, self.left_dock, Qt.Horizontal)
        self.left_dock.setVisible(False)  # 默认隐藏

        # ── C. 底部 Dock — FilePathBar（无标题栏）──
        self.file_path_bar = FilePathBar()
        self.bottom_dock = QDockWidget("", self)
        self.bottom_dock.setWidget(self.file_path_bar)
        self.bottom_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.bottom_dock.setTitleBarWidget(QWidget())
        self.bottom_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)
        self.bottom_dock.setVisible(True)

        # ── D. 右侧预览 Dock — SingleTextPreview ──
        self.single_text_preview = SingleTextPreview()
        self.right_dock = QDockWidget("预览", self)
        self.right_dock.setWidget(self.single_text_preview)
        self.right_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.right_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)

        # ── E. 右侧固定边栏 QDockWidget（与预览水平分割，永远在最右边缘）──
        self.right_sidebar_dock = QDockWidget("", self)
        self.right_sidebar_dock.setWidget(self.right_sidebar)
        self.right_sidebar_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.right_sidebar_dock.setTitleBarWidget(QWidget())
        self.right_sidebar_dock.setFixedWidth(80)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_sidebar_dock)
        # splitDockWidget: 拆分为 [预览 | 边栏]，边栏永远在右边缘
        self.splitDockWidget(self.right_dock, self.right_sidebar_dock, Qt.Horizontal)
        self.right_dock.setVisible(False)  # 预览 dock 默认隐藏

        # ===== 信号连接 =====
        self.file_manage_widget.file_double_clicked.connect(self._on_file_manage_double_clicked)
        self.multi_format_viewer.current_file_changed.connect(self.file_path_bar.set_file_path)

    def toggle_left_dock(self):
        """切换左侧 FileManage dock 显隐"""
        visible = self.left_dock.isVisible()
        self.left_dock.setVisible(not visible)
        return not visible

    def toggle_right_dock(self):
        """切换右侧预览 dock 显隐"""
        visible = self.right_dock.isVisible()
        self.right_dock.setVisible(not visible)
        return not visible

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