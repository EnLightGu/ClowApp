from PyQt5.QtWidgets import QWidget, QFileSystemModel, QPushButton
from PyQt5.QtCore import Qt, QDir, QSortFilterProxyModel, pyqtSignal, QFileSystemWatcher
import os
from PyQt5 import uic


class DirectoryFirstProxyModel(QSortFilterProxyModel):
    """排序代理模型：目录始终排在文件前面"""
    def lessThan(self, left, right):
        left_info = left.data(QFileSystemModel.FileInfoRole)
        right_info = right.data(QFileSystemModel.FileInfoRole)
        left_is_dir = left_info.isDir()
        right_is_dir = right_info.isDir()
        if left_is_dir != right_is_dir:
            return left_is_dir
        return super().lessThan(left, right)


class FileManage(QWidget):
    """
    文件管理子窗口
    """

    # 双击文本文件时发射文件路径
    file_double_clicked = pyqtSignal(str)
    # 选中目录时发射目录路径
    directory_selected = pyqtSignal(str)

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

        # 设置默认路径
        self._set_default_path()

    def _set_default_path(self):
        """
        设置 pathLineEdit 的默认文本为当前 Python 文件所在目录
        （即 UI 文件所在目录）
        """
        target_path = self._current_dir
        self.pathLineEdit.setText(target_path.replace("\\", "/"))
        # 同时更新 treeView 的 root index，修复路径输入框与树视图不一致问题
        root_index = self.sort_proxy.mapFromSource(
            self.file_model.index(target_path)
        )
        self.treeView.setRootIndex(root_index)

    def get_current_path(self):
        """
        获取当前路径文本框中的路径（可被外部调用）
        Returns:
            str: 当前显示的路径字符串
        """
        return self.pathLineEdit.text()

    def _load_ui(self):
        """加载UI文件并添加快捷按钮"""
        ui_path = os.path.join(os.path.dirname(__file__), "FileManage.ui")
        uic.loadUi(ui_path, self)

        # 在路径栏添加上一级按钮
        path_layout = self.pathLineEdit.parent().layout()
        idx = path_layout.indexOf(self.refreshButton)  # refresh 按钮后面
        self.go_up_button = QPushButton("↑")
        self.go_up_button.setToolTip("上一级目录")
        self.go_up_button.setFixedWidth(30)
        path_layout.insertWidget(idx, self.go_up_button)

        # 添加常用路径快捷按钮
        self.home_btn = QPushButton("🏠")
        self.home_btn.setToolTip("Home")
        self.home_btn.setFixedWidth(30)
        path_layout.insertWidget(idx, self.home_btn)

    def _init_file_system(self):
        """初始化文件系统模型"""
        # 创建文件系统模型
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")  # 设置根路径为空，显示所有驱动器

        # 设置过滤器，只显示目录和文件（不显示 . 和 ..）
        self.file_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs)

        # 创建排序代理模型：目录优先
        self.sort_proxy = DirectoryFirstProxyModel()
        self.sort_proxy.setSourceModel(self.file_model)

        # 树视图使用排序代理模型
        self.treeView.setModel(self.sort_proxy)

        # 隐藏不需要的列（只显示名称列）
        self.treeView.setHeaderHidden(True)
        for i in range(1, self.file_model.columnCount()):
            self.treeView.hideColumn(i)

        # 初始化文件变更监听器
        self.file_watcher = QFileSystemWatcher(self)
        self.file_watcher.directoryChanged.connect(self._on_directory_changed)

        # 注册当前路径到监听器
        initial_path = QDir.homePath()
        self.file_watcher.addPath(initial_path)

    def _connect_signals(self):
        """连接信号和槽"""
        # 刷新按钮点击
        self.refreshButton.clicked.connect(self._on_refresh_clicked)

        # 路径编辑框回车
        self.pathLineEdit.returnPressed.connect(self._on_path_changed)

        # 树视图选择变化
        self.treeView.selectionModel().selectionChanged.connect(
            self._on_tree_selection_changed
        )

        # 树视图双击（需手动连接，Qt Designer 不自动生成）
        self.treeView.doubleClicked.connect(self._on_tree_item_double_clicked)

        # 快捷路径按钮
        self.go_up_button.clicked.connect(self._go_up)
        self.home_btn.clicked.connect(lambda: self._quick_path("🏠 主页"))

    def _update_watcher_path(self, new_path):
        """更新文件监听器注册的路径"""
        # 移除所有已有路径
        watched_paths = self.file_watcher.directories()
        if watched_paths:
            self.file_watcher.removePaths(watched_paths)
        # 添加新路径
        self.file_watcher.addPath(new_path)

    def _go_up(self):
        """进入父目录"""
        current_path = self.pathLineEdit.text()
        parent = os.path.dirname(current_path)
        if parent and parent != current_path and os.path.exists(parent):
            self.pathLineEdit.setText(parent)
            self._update_tree_view(parent)

    def _quick_path(self, path_name):
        """快速跳转到常用路径"""
        paths = {
            "🏠 主页": os.path.expanduser("~"),
            "🖥️ 桌面": os.path.expanduser("~/Desktop"),
            "📁 文档": os.path.expanduser("~/Documents"),
        }
        target = paths.get(path_name)
        if target and os.path.exists(target):
            self.pathLineEdit.setText(target)
            self._update_tree_view(target)

    def _update_tree_view(self, path):
        """更新 treeView 显示指定路径"""
        if os.path.exists(path):
            root_index = self.sort_proxy.mapFromSource(
                self.file_model.index(path)
            )
            self.treeView.setRootIndex(root_index)
            self._update_watcher_path(path)

    def _on_refresh_clicked(self):
        """刷新按钮点击事件"""
        current_path = self.pathLineEdit.text()
        if os.path.exists(current_path):
            self._update_tree_view(current_path)
        else:
            fallback = os.path.expanduser("~")
            self.pathLineEdit.setText(fallback)
            self._update_tree_view(fallback)

    def _on_path_changed(self):
        """路径编辑框内容变化事件"""
        new_path = self.pathLineEdit.text()
        if os.path.exists(new_path):
            # 更新 treeView 的根索引
            root_index = self.sort_proxy.mapFromSource(
                self.file_model.index(new_path)
            )
            self.treeView.setRootIndex(root_index)
            self._update_watcher_path(new_path)
        else:
            self.pathLineEdit.setText("路径不存在")

    def _on_tree_selection_changed(self):
        """树视图选择变化事件"""
        selected_indexes = self.treeView.selectedIndexes()
        if selected_indexes:
            # 通过排序代理映射到源模型索引
            source_index = self.sort_proxy.mapToSource(selected_indexes[0])
            file_path = self.file_model.filePath(source_index)
            if os.path.isdir(file_path):
                self.pathLineEdit.setText(file_path)
                # 目录被选中时发射 directory_selected 信号
                self.directory_selected.emit(file_path)

    def _on_tree_item_double_clicked(self, index):
        """树视图项双击事件

        通过 sort_proxy.mapToSource(index) 获取真实路径。
        目录 → 展开/折叠（默认行为）。
        文本文件 → emit file_double_clicked(file_path)。
        其他文件 → 打印日志。
        """
        # 映射到源模型获取真实路径
        source_index = self.sort_proxy.mapToSource(index)
        file_path = self.file_model.filePath(source_index)

        if os.path.isdir(file_path):
            # 目录：默认行为（展开/折叠），无需额外操作
            # 同时发射 directory_selected 信号
            self.directory_selected.emit(file_path)
        elif self._is_text_file(file_path):
            # 文本文件：发射信号由外部打开
            self.file_double_clicked.emit(file_path)
        else:
            print(f"不支持预览: {file_path}")

    def _is_text_file(self, file_path):
        """判断文件是否可以被 MultiFormatViewer 预览"""
        preview_extensions = {
            '.txt', '.md', '.py', '.js', '.json', '.xml', '.yaml', '.yml',
            '.ini', '.cfg', '.conf', '.log', '.csv', '.html', '.css',
            '.sh', '.bat', '.c', '.cpp', '.h', '.java', '.sql', '.toml',
            '.gitignore', '.env',
            '.xlsx', '.xls',  # 表格文件
        }
        _, ext = os.path.splitext(file_path)
        basename = os.path.basename(file_path)
        if ext.lower() in preview_extensions:
            return True
        if basename in ('Dockerfile', 'Makefile'):
            return True
        return False

    def _on_directory_changed(self, path):
        """QFileSystemWatcher 检测到目录变更 → 自动刷新 treeView

        当文件系统发生变更（创建/删除文件或目录）时，
        重新设置当前 treeView 的根索引以刷新视图。
        """
        current_path = self.pathLineEdit.text()
        if current_path and os.path.exists(current_path):
            root_index = self.sort_proxy.mapFromSource(
                self.file_model.index(current_path)
            )
            self.treeView.setRootIndex(root_index)
            print(f"目录已变更，自动刷新: {current_path}")

    def show_window(self):
        """显示窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
