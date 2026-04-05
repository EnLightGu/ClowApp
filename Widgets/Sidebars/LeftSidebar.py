from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QStyle, QDockWidget
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon
from PyQt5 import uic
import os

class LeftSidebar(QWidget):
    def __init__(self):
        super().__init__()
        self._load_ui()
        self._init_connections()

        # 变量
        self.center_widget_manager = None  # 对CenterWidgetManage的引用
        self.FILE_MANAGE_DOCK_ID = "file_manage"  # FileManage dock窗口的唯一标识符

    def _load_ui(self):
        """加载UI文件"""
        ui_path = os.path.join(os.path.dirname(__file__), "LeftSidebar.ui")
        uic.loadUi(ui_path, self)

        # 设置图标（UI文件中无法设置图标，需要在代码中设置）
        # 设置图标（使用本地图标文件）
        icon_dir = os.path.dirname(__file__)

        # 使用本地图标文件
        icon1_path = os.path.join(icon_dir, "icon1.ico")
        icon2_path = os.path.join(icon_dir, "icon2.ico")

        if os.path.exists(icon1_path):
            self.button1.setIcon(QIcon(icon1_path))
            self.button1.setIconSize(QSize(32, 32))  # 设置图标大小像素
        else:
            # 备用方案：使用Qt内置图标
            self.button1.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_DirIcon', 0)))

        if os.path.exists(icon2_path):
            self.button2.setIcon(QIcon(icon2_path))
            self.button2.setIconSize(QSize(32, 32))  # 设置图标大小像素
        else:
            # 备用方案：使用Qt内置图标
            self.button2.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_FileIcon', 0)))

    def _init_connections(self):
        """初始化信号连接"""
        self.button1.clicked.connect(self._on_button1_clicked)
        self.button2.clicked.connect(self._on_button2_clicked)
        
    def _on_button1_clicked(self):
        """按钮1点击事件 - 控制FileManage窗口作为dock出现在CenterWidgetManage中"""
        print("左侧边栏按钮1被点击 - 控制FileManage窗口")

        # 检查是否有center_widget_manager的引用
        if self.center_widget_manager is None:
            print("错误: center_widget_manager未设置")
            return

        try:
            # 导入FileManage类
            from Widgets.LeftWidget.FileManage import FileManage

            # 尝试获取已存在的FileManage dock窗口
            existing_dock = self.center_widget_manager.get_custom_dock(self.FILE_MANAGE_DOCK_ID)

            # 如果FileManage dock窗口不存在，则创建并显示
            if existing_dock is None:
                # 创建FileManage实例
                file_manage_widget = FileManage()

                # 将FileManage添加到CenterWidgetManage的dock区域
                # 使用左侧dock区域，因为FileManage通常放在左侧
                file_manage_dock = self.center_widget_manager.add_custom_widget(
                    file_manage_widget,
                    title="文件管理",
                    area=Qt.LeftDockWidgetArea,
                    dock_id=self.FILE_MANAGE_DOCK_ID
                )

                # 设置dock窗口属性
                file_manage_dock.setFeatures(
                    QDockWidget.DockWidgetMovable |
                    QDockWidget.DockWidgetFloatable
                )

                print("FileManage dock窗口已创建并显示在左侧")
            else:
                # 如果dock窗口已存在，则切换其可见性
                new_visibility = self.center_widget_manager.toggle_custom_dock(self.FILE_MANAGE_DOCK_ID)

                if new_visibility is not None:
                    if new_visibility:
                        print("FileManage dock窗口已显示")
                    else:
                        print("FileManage dock窗口已隐藏")
                else:
                    print("错误: 无法切换FileManage dock窗口的可见性")

        except ImportError as e:
            print(f"错误: 无法导入FileManage类 - {e}")
            print("请确保Widgets/LeftWidget/FileManage.py存在")
        except Exception as e:
            print(f"错误: 创建或管理FileManage dock窗口时发生错误 - {e}")
    def _on_button2_clicked(self):
        """按钮2点击事件"""
        print("左侧边栏按钮2被点击")
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

    def set_center_widget_manager(self, manager):
        """设置对CenterWidgetManage的引用"""
        self.center_widget_manager = manager