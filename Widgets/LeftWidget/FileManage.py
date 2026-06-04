from PyQt5.QtWidgets import QWidget, QFileSystemModel
from PyQt5.QtCore import Qt, QDir
import os
from PyQt5 import uic

class FileManage(QWidget):
    """
    文件管理子窗口
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # 记录当前 Python 文件的路径，用于构造 UI 文件的绝对路径
        self._current_dir = os.path.dirname(os.path.abspath(__file__))

        # 构建 UI 文件的完整路径
        ui_path = os.path.join(self._current_dir, "FileManage.ui")
        
        # 初始化UI
        self._load_ui()
        
        # 初始化文件系统模型
        self._init_file_system()

        # 连接信号和槽
        self._connect_signals()

        # 确保标签居中
        # self.ui.label.setAlignment(Qt.AlignCenter)
        #设置默认路径
        self._set_default_path()

    def _set_default_path(self):
        """
        设置 pathLineEdit 的默认文本为当前 Python 文件所在目录
        （即 UI 文件所在目录）
        """
        # self.pathLineEdit 是从 UI 文件中自动生成的对象名，对应 QLineEdit
        # 将目录路径中的反斜杠转换为正斜杠（Windows兼容），或者直接保留
        # 这里使用标准路径格式，如 "C:/Users/...”
        self.pathLineEdit.setText(self._current_dir.replace("\\", "/"))

    def get_current_path(self):
        """
        获取当前路径文本框中的路径（可被外部调用）
        Returns:
            str: 当前显示的路径字符串
        """
        return self.pathLineEdit.text()

    def _load_ui(self):
        """加载UI文件"""
        ui_path = os.path.join(os.path.dirname(__file__), "FileManage.ui")
        uic.loadUi(ui_path, self)
        
    def _init_file_system(self):
        """初始化文件系统模型"""
        # 创建文件系统模型
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")  # 设置根路径为空，显示所有驱动器

        # 设置过滤器，只显示目录和文件
        self.file_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs)

        # 设置树视图的模型
        self.treeView.setModel(self.file_model)

        # 隐藏不需要的列（只显示名称列）
        self.treeView.setHeaderHidden(True)
        for i in range(1, self.file_model.columnCount()):
            self.treeView.hideColumn(i)

        # 设置列表视图的模型
        self.list_model = QFileSystemModel()
        self.list_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
        self.listView.setModel(self.list_model)

        # 设置初始路径
        initial_path = QDir.homePath()  # 用户主目录
        self.pathLineEdit.setText(initial_path)
        self._update_list_view(initial_path)

    def _connect_signals(self):
        """连接信号和槽"""
        # 刷新按钮点击
        self.refreshButton.clicked.connect(self._on_refresh_clicked)

        # 路径编辑框回车
        self.pathLineEdit.returnPressed.connect(self._on_path_changed)

        # 树视图选择变化
        self.treeView.selectionModel().selectionChanged.connect(self._on_tree_selection_changed)

        # 列表视图双击
        self.listView.doubleClicked.connect(self._on_list_item_double_clicked)

    def _on_refresh_clicked(self):
        """刷新按钮点击事件"""
        current_path = self.pathLineEdit.text()
        if os.path.exists(current_path):
            self._update_list_view(current_path)
        else:
            # 如果路径不存在，回到根目录
            self.pathLineEdit.setText("C:\\")
            self._update_list_view("C:\\")

    def _on_path_changed(self):
        """路径编辑框内容变化事件"""
        new_path = self.pathLineEdit.text()
        if os.path.exists(new_path):
            self._update_list_view(new_path)
        else:
            # 路径不存在，显示错误信息
            self.pathLineEdit.setText("路径不存在")

    def _on_tree_selection_changed(self):
        """树视图选择变化事件"""
        selected_indexes = self.treeView.selectedIndexes()
        if selected_indexes:
            index = selected_indexes[0]
            file_path = self.file_model.filePath(index)
            if os.path.isdir(file_path):
                self.pathLineEdit.setText(file_path)
                self._update_list_view(file_path)

    def _on_list_item_double_clicked(self, index):
        """列表视图项双击事件"""
        file_path = self.list_model.filePath(index)
        if os.path.isdir(file_path):
            # 如果是目录，更新路径并刷新列表
            self.pathLineEdit.setText(file_path)
            self._update_list_view(file_path)
        else:
            # 如果是文件，可以在这里添加打开文件的逻辑
            print(f"打开文件: {file_path}")

    def _update_list_view(self, path):
        """更新列表视图显示指定路径的内容"""
        # 设置列表视图的根路径
        self.list_model.setRootPath(path)
        root_index = self.list_model.index(path)
        self.listView.setRootIndex(root_index)

        # 更新树视图的展开状态
        tree_index = self.file_model.index(path)
        if tree_index.isValid():
            self.treeView.expand(tree_index)
            self.treeView.setCurrentIndex(tree_index)
            self.treeView.scrollTo(tree_index)

    def show_window(self):
        """显示窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
