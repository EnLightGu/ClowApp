import platform
import sys

from PyQt5.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, QApplication,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QCursor
from PyQt5 import uic

import os


# 窗口边缘拖拽调整大小的阈值（像素），扩大至30便于鼠标操作
RESIZE_MARGIN = 30

# ── 边栏尺寸常量 ──
SIDEBAR_WIDTH = 80
SIDEBAR_MIN_HEIGHT = 100



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
            try:
                from ctypes import windll, wintypes
                self.setWindowFlags(Qt.Window)
                self.setGeometry(100, 100, 1200, 800)
                self.hide_title_bar()
                self.resize(1100, 700)
            except Exception as e:
                print(f"隐藏标题栏失败 (非 Windows 环境?): {e}")

        # 设置窗口属性
        self.setWindowTitle("Main Window")

        # ① 初始化标题栏（无依赖）
        self._init_topbar()
        # ② 初始化中央区域（CenterWidgetManage + 文件管理 + 右面板内容）
        self._init_center_widget()
        # ③ 初始化侧边栏（左/右边栏 → 主布局中固定）
        self._init_sidebars()
        # ④ 初始化底部路径栏 QDockWidget
        self._init_bottom_dock()


    def hide_title_bar(self):
        try:
            from ctypes import windll, wintypes
            hwnd = int(self.winId())
            user32 = windll.user32

            GWL_STYLE = -16
            GWL_EXSTYLE = -20
            WS_CAPTION = 0x00C00000
            WS_THICKFRAME = 0x00040000
            WS_MINIMIZEBOX = 0x00020000
            WS_MAXIMIZEBOX = 0x00010000
            WS_SYSMENU = 0x00080000

            style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
            style &= ~WS_CAPTION
            style |= WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU
            user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)
            user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
        except Exception as e:
            print(f"隐藏标题栏失败 (非 Windows 环境?): {e}")

    # ── 窗口边缘调整大小 ──
    _resizing = False
    _resize_dir = 0

    def _get_resize_cursor(self, pos):
        rect = self.rect()
        x, y = pos.x(), pos.y()
        w, h = rect.width(), rect.height()

        on_left = x < RESIZE_MARGIN
        on_right = x > w - RESIZE_MARGIN
        on_top = y < RESIZE_MARGIN
        on_bottom = y > h - RESIZE_MARGIN

        if on_top and on_left:    return QCursor(Qt.SizeFDiagCursor), 5
        if on_top and on_right:   return QCursor(Qt.SizeBDiagCursor), 6
        if on_bottom and on_left: return QCursor(Qt.SizeBDiagCursor), 7
        if on_bottom and on_right:return QCursor(Qt.SizeFDiagCursor), 8
        if on_left:  return QCursor(Qt.SizeHorCursor), 1
        if on_right: return QCursor(Qt.SizeHorCursor), 2
        if on_top:   return QCursor(Qt.SizeVerCursor), 3
        if on_bottom:return QCursor(Qt.SizeVerCursor), 4
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

            dirs = {
                1: lambda g: g.setLeft(g.left() + dx),
                2: lambda g: g.setRight(g.right() + dx),
                3: lambda g: g.setTop(g.top() + dy),
                4: lambda g: g.setBottom(g.bottom() + dy),
                5: lambda g: g.setTopLeft(g.topLeft() + delta),
                6: lambda g: g.setTopRight(g.topRight() + delta),
                7: lambda g: g.setBottomLeft(g.bottomLeft() + delta),
                8: lambda g: g.setBottomRight(g.bottomRight() + delta),
            }
            dirs.get(self._resize_dir, lambda g: None)(geom)

            if geom.width() >= self.minimumWidth() and geom.height() >= self.minimumHeight():
                self.setGeometry(geom)
            event.accept()
            return

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
            self.topbar = Topbar()
            self.topbar_widget.layout().addWidget(self.topbar)
            self.topbar.set_title('主窗口')
            self.topbar.minimize_clicked.connect(self._on_minimize_clicked)
            self.topbar.maximize_clicked.connect(self._on_maximize_clicked)
            self.topbar.close_clicked.connect(self._on_close_clicked)
            self.topbar.update_maximize_button(self.isMaximized())
        except ImportError as e:
            print(f"Error importing topbar component: {e}")

    def _init_sidebars(self):
        """初始化左右侧边栏，放入主布局"""
        try:
            from Widgets.Sidebars.LeftSidebar import LeftSidebar
            from Widgets.Sidebars.RightSidebar import RightSidebar

            self.left_sidebar = LeftSidebar()
            self.left_sidebar.set_main_window(self)

            self.right_sidebar = RightSidebar()
            self.right_sidebar.set_main_window(self)

            # 左边栏 → content_widget 索引 0
            self.left_sidebar_widget = QWidget()
            self.left_sidebar_widget.setFixedWidth(SIDEBAR_WIDTH)
            self.left_sidebar_widget.setStyleSheet("background-color: #2D2D2D;")
            layout_l = QVBoxLayout(self.left_sidebar_widget)
            layout_l.setContentsMargins(0, 0, 0, 0)
            layout_l.addWidget(self.left_sidebar)
            self.content_widget.layout().insertWidget(0, self.left_sidebar_widget)

            # 右边栏 → content_widget 索引 2（main_content 在索引1）
            self.right_sidebar_widget = QWidget()
            self.right_sidebar_widget.setFixedWidth(SIDEBAR_WIDTH)
            self.right_sidebar_widget.setStyleSheet("background-color: #2D2D2D;")
            layout_r = QVBoxLayout(self.right_sidebar_widget)
            layout_r.setContentsMargins(0, 0, 0, 0)
            layout_r.addWidget(self.right_sidebar)
            self.content_widget.layout().insertWidget(2, self.right_sidebar_widget)

            # 注入 CenterWidgetManage 引用到 LeftSidebar
            self.left_sidebar.set_center_widget_manager(self.center_widget_manager)

        except ImportError as e:
            print(f"Error importing sidebar components: {e}")

    def _init_center_widget(self):
        """初始化中央区域 — CenterWidgetManage + MultiFormatViewer + 右内容面板"""
        from Widgets.CenterWidget.MultiFormatViewer import MultiFormatViewer
        from Widgets.CenterWidget.CenterWidgetManage import CenterWidgetManage
        from Widgets.LeftWidget.FileManage import FileManage
        from Widgets.RightWidget.SingleTextPreview import SingleTextPreview
        from Widgets.RightWidget.LogicDiagramWidget import LogicDiagramWidget
        from Widgets.RightWidget.LogicTextWidget import LogicTextWidget

        # 创建 CenterWidgetManage
        layout = QVBoxLayout(self.main_content_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.center_widget_manager = CenterWidgetManage(self)
        layout.addWidget(self.center_widget_manager)

        # 创建 MultiFormatViewer 并设为主内容
        self.multi_format_viewer = MultiFormatViewer(self)
        self.center_widget_manager.set_widget(self.multi_format_viewer)

        # ── 左面板：FileManage ──
        self.file_manage_widget = FileManage()
        self.center_widget_manager.register_panel("file_manage", self.file_manage_widget)
        self.center_widget_manager.hide_panel("file_manage")
        self.file_manage_widget.file_double_clicked.connect(self._on_file_manage_double_clicked)

        # ── 右面板 1：SingleTextPreview ──
        self.single_text_preview = SingleTextPreview()
        self.single_text_preview.setStyleSheet("background-color: #1E1E1E; color: #FFFFFF;")
        self.center_widget_manager.register_right_panel("preview", self.single_text_preview)

        # ── 右面板 2：LogicDiagramWidget ──
        self.logic_diagram_widget = LogicDiagramWidget()
        self.logic_diagram_widget.setStyleSheet("background-color: #1E1E1E; color: #FFFFFF;")
        self.center_widget_manager.register_right_panel("logic_diagram", self.logic_diagram_widget)

        # ── 右面板 3：LogicTextWidget ──
        self.logic_text_widget = LogicTextWidget()
        self.logic_text_widget.setStyleSheet("background-color: #1E1E1E; color: #FFFFFF;")
        self.center_widget_manager.register_right_panel("logic_text", self.logic_text_widget)

        # ── 信号：双向转化 ──
        self.logic_diagram_widget.conversion_to_text_requested.connect(self._on_diagram_to_text)
        self.logic_text_widget.conversion_to_diagram_requested.connect(self._on_text_to_diagram)

        # ── 数据库 ──
        from Widgets.RightWidget.LogicDatabase import LogicDatabase
        self.logic_db = LogicDatabase()

    def _on_file_manage_double_clicked(self, file_path):
        success, error_msg = self.multi_format_viewer.open_file(file_path)
        if not success:
            print(f"打开文件失败: {error_msg}")
        self.single_text_preview.open_file(file_path)

    def _init_bottom_dock(self):
        """初始化底部路径栏 QDockWidget（唯一使用的 QDockWidget）"""
        from Widgets.Sidebars.FilePathBar import FilePathBar

        self.file_path_bar = FilePathBar()
        self.bottom_dock = QDockWidget("", self)
        self.bottom_dock.setWidget(self.file_path_bar)
        self.bottom_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.bottom_dock.setTitleBarWidget(QWidget())
        self.bottom_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)
        self.bottom_dock.setVisible(True)

        # 信号：文件路径更新
        self.multi_format_viewer.current_file_changed.connect(self.file_path_bar.set_file_path)

    def _on_minimize_clicked(self):
        self.showMinimized()

    def _on_maximize_clicked(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self.topbar.update_maximize_button(self.isMaximized())

    def _on_close_clicked(self):
        self.close()

    def setWindowTitle(self, title):
        super().setWindowTitle(title)
        if hasattr(self, 'topbar'):
            self.topbar.set_title(title)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == event.WindowStateChange and hasattr(self, 'topbar'):
            self.topbar.update_maximize_button(self.isMaximized())

    # ── 侧边栏按钮 → 切换右侧面板 ──

    def toggle_left_dock(self):
        """切换左侧 FileManage 面板"""
        return self.center_widget_manager.toggle_panel("file_manage")

    def toggle_right_dock(self):
        """切换右侧预览面板"""
        return self.center_widget_manager.toggle_right_panel("preview")

    def toggle_logic_diagram_dock(self):
        """切换逻辑门图形编辑器面板"""
        return self.center_widget_manager.toggle_right_panel("logic_diagram")

    def toggle_logic_text_dock(self):
        """切换文本逻辑编辑器面板"""
        return self.center_widget_manager.toggle_right_panel("logic_text")

    def _on_diagram_to_text(self, text):
        """图形 → 文本"""
        self.logic_text_widget.import_from_diagram(text)
        self.center_widget_manager.show_right_panel("logic_text")

    def _on_text_to_diagram(self, text):
        """文本 → 图形"""
        success = self.logic_diagram_widget.from_logic_text(text)
        if success:
            self.center_widget_manager.show_right_panel("logic_diagram")

    def closeEvent(self, event):
        if hasattr(self, 'multi_format_viewer') and self.multi_format_viewer:
            if self.multi_format_viewer.is_current_modified():
                reply = QMessageBox.question(
                    self, "确认退出",
                    "有文件未保存，确定要退出吗？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    event.ignore()
                    return
        event.accept()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())