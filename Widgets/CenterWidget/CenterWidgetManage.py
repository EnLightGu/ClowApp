import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QSize
from PyQt5 import uic
import os


class CenterWidgetManage(QMainWindow):
    """
    具有dock功能的中心窗口管理类
    继承自QMainWindow，支持dock窗口功能
    布局参照CenterWidgetManage.ui设计
    """

    def __init__(self, parent=None):
        """
        初始化中心窗口管理器

        Args:
            parent: 父窗口，默认为None
        """
        super().__init__(parent)

        # 设置窗口属性
        self.setWindowTitle("Center Widget Manager")
        self.setMinimumSize(400, 300)

        # 加载UI文件
        self._load_ui()

        # 初始化dock区域 #可用于单独run时测试
        # self._init_dock_area()

        # 存储自定义dock窗口的引用
        self.custom_docks = {}  # 字典，用于存储不同类型的dock窗口


    def _load_ui(self):
        """加载UI文件"""
        try:
            # 获取UI文件路径
            ui_path = os.path.join(os.path.dirname(__file__), "CenterWidgetManage.ui")
            # 创建中心部件并加载UI
            uic.loadUi(ui_path, self)

        except Exception as e:
            print(f"Error loading UI: {e}")


    def _init_dock_area(self):
        """初始化dock区域"""
        # 创建左侧dock窗口
        self.left_dock = QDockWidget("Left Dock", self)
        self.left_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # 创建左侧dock内容
        left_widget = QWidget()
        left_widget.setStyleSheet("background-color: #55AAFF;")
        left_layout = QVBoxLayout()
        left_label = QLabel("Left Dock Area")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_layout.addWidget(left_label)
        left_widget.setLayout(left_layout)

        self.left_dock.setWidget(left_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)


    def get_dock_widget(self):
        """
        获取dock窗口部件

        Returns:
            QDockWidget: 左侧dock窗口？？？？
        """
        #应该return self.custom_docks，其中为{dock_id:dock}对
        return self.custom_docks

    def add_custom_widget(self, widget, title="Custom Widget", area=Qt.RightDockWidgetArea, dock_id=None):
        """
        添加自定义widget到dock区域

        Args:
            widget: 要添加的QWidget
            title: dock窗口标题
            area: dock区域
            dock_id: dock窗口的唯一标识符，用于后续管理

        Returns:
            QDockWidget: 创建的dock窗口
        """
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(area, dock)

        # 如果提供了dock_id，则存储引用
        if dock_id:
            self.custom_docks[dock_id] = dock

        return dock

    def get_custom_dock(self, dock_id):
        """
        获取指定ID的自定义dock窗口
        Args:
            dock_id: dock窗口的唯一标识符

        Returns:
            QDockWidget: 对应的dock窗口，如果不存在则返回None
        """
        return self.custom_docks.get(dock_id)

    def toggle_custom_dock(self, dock_id):
        """
        切换指定ID的自定义dock窗口的可见性
        Args:
            dock_id: dock窗口的唯一标识符

        Returns:
            bool: 切换后的可见性状态，如果dock不存在则返回None
        """
        dock = self.get_custom_dock(dock_id)
        if dock:
            new_visibility = not dock.isVisible()   #bool值取反
            dock.setVisible(new_visibility)
            return new_visibility
        return None


if __name__ == "__main__":
    # 测试代码
    app = QApplication(sys.argv)
    window = CenterWidgetManage()
    window.show()
    sys.exit(app.exec_())