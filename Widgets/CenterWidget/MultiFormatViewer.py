"""
MultiFormatViewer — 中央多格式预览器

替换原有的 CenterWidgetManage + MultiFileEditor。
根据文件扩展名自动选择文本页或表格页显示。
"""
import csv
import io
import os
from typing import Optional, Tuple

from PyQt5.QtCore import Qt, pyqtSignal, QFileSystemWatcher
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox, QTabBar,
    QHeaderView, QAbstractItemView,
)

# ── 复用 CodeEditor（带行号） ─────────────────────────────────
from Widgets.CenterWidget.CodeEditor import CodeEditor

# ════════════════════════════════════════════════════════════════
# 常量
# ════════════════════════════════════════════════════════════════

# 文本类扩展名
TEXT_EXTENSIONS = {
    ".txt", ".py", ".js", ".ts", ".md", ".json", ".xml",
    ".yaml", ".yml", ".ini", ".cfg", ".conf", ".log",
    ".html", ".css", ".scss", ".sh", ".bat", ".ps1",
    ".c", ".cpp", ".h", ".hpp", ".java", ".sql", ".toml",
    ".gitignore", ".env",
}

# 无扩展名的文本文件名
TEXT_FILENAMES = {"Dockerfile", "Makefile"}

# 表格类扩展名
GRID_EXTENSIONS = {".csv", ".tsv", ".xlsx", ".xls"}

# 最大文件大小（默认 10 MB）
MAX_FILE_SIZE = 10 * 1024 * 1024


# ════════════════════════════════════════════════════════════════
# MultiFormatViewer
# ════════════════════════════════════════════════════════════════
class MultiFormatViewer(QWidget):
    """
    中央多格式预览器 — 支持文本文件和表格文件的分标签页预览。

    Signals:
        current_file_changed(str): 当前文件路径，无文件时为 ""
    """

    current_file_changed = pyqtSignal(str)

    # ──────────────────────────────────────────────────────────
    # 初始化
    # ──────────────────────────────────────────────────────────
    def __init__(self, parent=None):
        super().__init__(parent)

        # ── 属性 ─────────────────────────────────────────────
        self.open_files: dict[str, Tuple[int, str]] = {}  # {path: (tab_index, file_type)}
        self.file_watcher = QFileSystemWatcher(self)
        self.current_path: str = ""

        # ── 布局 ─────────────────────────────────────────────
        self.setStyleSheet("background-color: #1E1E1E;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── QTabWidget（顶部标签页，可关闭） ─────────────────
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setElideMode(Qt.ElideRight)
        layout.addWidget(self.tab_widget)

        # 标签页样式
        self.tab_widget.setStyleSheet("""
            QTabWidget {
                background-color: #1E1E1E;
            }
            QTabWidget::pane {
                background-color: #1E1E1E;
                border: none;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #CCCCCC;
                padding: 6px 12px;
                border: none;
                border-right: 1px solid #3C3C3C;
                min-width: 60px;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border-bottom: 2px solid #007ACC;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3C3C3C;
            }
        """)

        # ── 欢迎页 ───────────────────────────────────────────
        self._welcome_label = None
        self._add_welcome_tab()

        # ── 信号连接 ─────────────────────────────────────────
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        # 标签拖拽移动后更新索引
        self.tab_widget.tabBar().tabMoved.connect(self._on_tab_moved)
        self.file_watcher.fileChanged.connect(self._on_file_changed)

    # ══════════════════════════════════════════════════════════
    # 欢迎标签页管理
    # ══════════════════════════════════════════════════════════

    def _add_welcome_tab(self):
        """在 tab 0 添加欢迎标签页（不可关闭）"""
        if self._welcome_label is not None:
            return

        label = QLabel("双击左侧文件以预览")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 18px;
                background-color: #1E1E1E;
            }
        """)
        self.tab_widget.insertTab(0, label, "🏠 欢迎")
        self.tab_widget.setCurrentIndex(0)
        self._welcome_label = label

        # 移除欢迎标签页的关闭按钮
        self._remove_close_button(0)

    def _remove_close_button(self, index: int):
        """移除指定索引标签页的关闭按钮"""
        tab_bar = self.tab_widget.tabBar()
        if index < tab_bar.count():
            tab_bar.setTabButton(index, QTabBar.RightSide, None)

    def _has_welcome_tab(self) -> bool:
        """检查欢迎标签页是否存在于 tab widget 中"""
        if self._welcome_label is None:
            return False
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) is self._welcome_label:
                return True
        self._welcome_label = None
        return False

    def _ensure_welcome_first(self):
        """确保欢迎页始终在 tab 0，真实文件从 tab 1 开始"""
        if not self._has_welcome_tab():
            self._add_welcome_tab()
        elif self.tab_widget.indexOf(self._welcome_label) != 0:
            idx = self.tab_widget.indexOf(self._welcome_label)
            self.tab_widget.removeTab(idx)
            self.tab_widget.insertTab(0, self._welcome_label, "🏠 欢迎")
            self._remove_close_button(0)
            self.tab_widget.setCurrentIndex(0)

    def _is_welcome_tab(self, index: int) -> bool:
        """判断指定索引是否为欢迎标签页"""
        if self._welcome_label is None:
            return False
        return self.tab_widget.widget(index) is self._welcome_label

    # ══════════════════════════════════════════════════════════
    # 文件类型检测
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def _detect_file_type(file_path: str) -> str:
        """
        检测文件类型。

        Returns:
            str: "text" | "grid" | "unknown"
        """
        if not os.path.isfile(file_path):
            return "unknown"

        basename = os.path.basename(file_path)
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # 已知文本类型
        if ext in TEXT_EXTENSIONS or basename in TEXT_FILENAMES:
            return "text"

        # 已知表格类型
        if ext in GRID_EXTENSIONS:
            return "grid"

        # 未知扩展名 → 试探性检测
        try:
            with open(file_path, "rb") as f:
                header = f.read(512)
        except Exception:
            return "unknown"

        # 有 null 字节 → 二进制
        if b"\x00" in header:
            return "unknown"

        # 尝试 UTF-8 解码
        try:
            header.decode("utf-8")
            return "text"
        except UnicodeDecodeError:
            return "unknown"

    # ══════════════════════════════════════════════════════════
    # 文件读取 / 编码检测
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def _read_file_with_encoding(
        file_path: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        尝试逐种编码读取文件。

        Returns:
            (content, None)    成功
            (None, error_msg)  失败
        """
        raw_data = None
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read()
        except PermissionError:
            return (None, "无权限读取: {}".format(file_path))
        except Exception as e:
            return (None, "读取文件失败: {}".format(e))

        # 编码检测链
        encodings = []

        # 首选 chardet（可选依赖）
        try:
            import chardet
            detect_result = chardet.detect(raw_data)
            if detect_result and detect_result.get("encoding"):
                detected_enc = detect_result["encoding"]
                encodings.append(detected_enc)
        except ImportError:
            pass

        # fallback 链
        encodings.extend(["utf-8", "utf-16", "gbk", "latin-1"])

        for enc in encodings:
            try:
                return (raw_data.decode(enc), None)
            except (UnicodeDecodeError, UnicodeError, LookupError):
                continue

        return (None, "无法解码文件编码")

    # ══════════════════════════════════════════════════════════
    # 公共接口：open_file
    # ══════════════════════════════════════════════════════════

    def open_file(self, file_path: str) -> Tuple[bool, str]:
        """
        打开文件并在新标签页中显示。

        Args:
            file_path: 文件路径

        Returns:
            Tuple[bool, str]: (成功, 错误信息或空串)
        """
        # ── 1. 文件存在性检查 ────────────────────────────────
        if not os.path.isfile(file_path):
            return (False, "文件不存在: {}".format(file_path))

        # ── 2. 文件大小检查（>10 MB 弹窗确认） ───────────────
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            reply = QMessageBox.warning(
                self,
                "文件过大",
                "文件大小 ({:.1f} MB) 超过 10 MB。\n是否继续打开？".format(
                    file_size / 1024 / 1024
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return (False, "用户取消")

        # ── 3. 重复检查（已在 open_files 中 → 切换标签页） ──
        if file_path in self.open_files:
            # 使用 widget 定位，避免移动后索引失效
            widget = self._get_widget_for_path(file_path)
            if widget is not None:
                idx = self.tab_widget.indexOf(widget)
                if idx >= 0:
                    self.tab_widget.setCurrentIndex(idx)
                    return (True, "")
            # widget 丢失 → 清理残留
            del self.open_files[file_path]

        # ── 4. 文件类型检测 ──────────────────────────────────
        file_type = self._detect_file_type(file_path)

        if file_type == "unknown":
            return (False, "不支持的文件类型: {}".format(file_path))

        # ── 5. 格式处理 ──────────────────────────────────────
        if file_type == "text":
            ok, error = self._open_text_file(file_path)
        elif file_type == "grid":
            ok, error = self._open_grid_file(file_path)
        else:
            return (False, "不支持的文件类型: {}".format(file_type))

        if not ok:
            return (False, error)

        return (True, "")

    # ──────────────────────────────────────────────────────────
    # 文本文件处理
    # ──────────────────────────────────────────────────────────
    def _open_text_file(self, file_path: str) -> Tuple[bool, str]:
        """在文本标签页中打开文件"""
        content, error = self._read_file_with_encoding(file_path)
        if error:
            return (False, error)

        # 创建 CodeEditor
        editor = CodeEditor(self)
        editor.setPlainText(content)

        # 确保欢迎页在 tab 0
        self._ensure_welcome_first()

        file_name = os.path.basename(file_path)
        tab_index = self.tab_widget.addTab(editor, file_name)
        self.tab_widget.setTabToolTip(tab_index, file_path)
        # 先记录到 open_files（必须在 setCurrentWidget 之前，确保 currentChanged 信号可读取）
        self.open_files[file_path] = (tab_index, "text")

        # 后切换标签页
        self.tab_widget.setCurrentWidget(editor)

        # 注册文件变更监听
        self._add_file_watcher(file_path)

        return (True, "")

    # ──────────────────────────────────────────────────────────
    # 表格文件处理
    # ──────────────────────────────────────────────────────────
    def _open_grid_file(self, file_path: str) -> Tuple[bool, str]:
        """在表格标签页中打开 CSV / XLSX 文件"""
        ext = os.path.splitext(file_path)[1].lower()

        table_widget = QTableWidget(self)

        if ext in (".csv", ".tsv"):
            ok, error = self._load_csv_to_table(file_path, table_widget, ext)
        elif ext in (".xlsx", ".xls"):
            ok, error = self._load_xlsx_to_table(file_path, table_widget)
        else:
            return (False, "不支持的表格格式: {}".format(ext))

        if not ok:
            return (False, error)

        # 表格暗色样式
        table_widget.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                color: #CCCCCC;
                gridline-color: #333333;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
            QHeaderView::section {
                background-color: #252526;
                color: #CCCCCC;
                padding: 4px 8px;
                border: 1px solid #333333;
                font-weight: bold;
            }
        """)
        table_widget.setAlternatingRowColors(True)
        table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        table_widget.horizontalHeader().setStretchLastSection(True)
        table_widget.verticalHeader().setDefaultSectionSize(24)

        # 等宽字体
        font = QFont("Courier New", 10)
        table_widget.setFont(font)

        # 确保欢迎页在 tab 0
        self._ensure_welcome_first()

        file_name = os.path.basename(file_path)
        tab_index = self.tab_widget.addTab(table_widget, file_name)
        self.tab_widget.setTabToolTip(tab_index, file_path)
        # 先记录到 open_files（必须在 setCurrentWidget 之前）
        self.open_files[file_path] = (tab_index, "grid")

        # 后切换标签页
        self.tab_widget.setCurrentWidget(table_widget)

        # 注册文件变更监听
        self._add_file_watcher(file_path)

        return (True, "")

    def _load_csv_to_table(
        self, file_path: str, table: QTableWidget, ext: str
    ) -> Tuple[bool, str]:
        """将 CSV/TSV 文件加载到 QTableWidget"""
        delimiter = "," if ext == ".csv" else "\t"
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
        except Exception as e:
            # fallback: 尝试用编码检测读取
            content, error = self._read_file_with_encoding(file_path)
            if error:
                return (False, "读取 CSV 失败: {}".format(e))
            try:
                reader = csv.reader(io.StringIO(content), delimiter=delimiter)
                rows = list(reader)
            except Exception as e2:
                return (False, "解析 CSV 失败: {}".format(e2))

        if not rows:
            return (False, "CSV 文件为空")

        # 第一行作为表头
        headers = rows[0]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        # 其余作为数据行
        data_rows = rows[1:]
        table.setRowCount(len(data_rows))

        for r_idx, row in enumerate(data_rows):
            for c_idx, value in enumerate(row):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(r_idx, c_idx, item)

        table.resizeColumnsToContents()
        return (True, "")

    def _load_xlsx_to_table(
        self, file_path: str, table: QTableWidget
    ) -> Tuple[bool, str]:
        """将 XLSX 文件加载到 QTableWidget（依赖 openpyxl）"""
        try:
            import openpyxl
        except ImportError:
            return (False, "需要安装 openpyxl: pip install openpyxl")

        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active
            if ws is None:
                return (False, "Excel 文件无活动工作表")

            # 收集所有行
            rows_data = list(ws.iter_rows(values_only=True))
            wb.close()

            if not rows_data:
                return (False, "Excel 工作表为空")

            # 第一行作为表头
            headers = rows_data[0]
            table.setColumnCount(len(headers) if headers else 0)
            if headers:
                table.setHorizontalHeaderLabels(
                    [str(h) if h is not None else "" for h in headers]
                )

            # 其余作为数据行
            data_rows = rows_data[1:]
            table.setRowCount(len(data_rows))

            for r_idx, row in enumerate(data_rows):
                for c_idx, value in enumerate(row):
                    display = str(value) if value is not None else ""
                    item = QTableWidgetItem(display)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(r_idx, c_idx, item)

            table.resizeColumnsToContents()
            return (True, "")

        except Exception as e:
            return (False, "读取 XLSX 失败: {}".format(e))

    # ══════════════════════════════════════════════════════════
    # QFileSystemWatcher 管理
    # ══════════════════════════════════════════════════════════

    def _add_file_watcher(self, file_path: str):
        """注册文件变更监听"""
        try:
            self.file_watcher.addPath(file_path)
        except Exception:
            pass

    def _remove_file_watcher(self, file_path: str):
        """移除文件变更监听"""
        try:
            self.file_watcher.removePath(file_path)
        except Exception:
            pass

    def _on_file_changed(self, file_path: str):
        """文件被外部修改 → 标签名前缀 '● ' 标记"""
        if file_path not in self.open_files:
            return

        # 通过 widget 定位，避免移动后索引失效
        widget = self._get_widget_for_path(file_path)
        if widget is None:
            return

        idx = self.tab_widget.indexOf(widget)
        if idx < 0:
            return

        current_title = self.tab_widget.tabText(idx)
        if not current_title.startswith("\u25cf "):
            self.tab_widget.setTabText(idx, "\u25cf {}".format(current_title))

    # ══════════════════════════════════════════════════════════
    # 标签页索引同步（标签拖拽后更新 open_files 索引）
    # ══════════════════════════════════════════════════════════

    def _on_tab_moved(self, _from_index: int, _to_index: int):
        """标签拖拽移动 → 重新整理所有索引"""
        self._reindex_tabs()

    # ══════════════════════════════════════════════════════════
    # 标签页切换
    # ══════════════════════════════════════════════════════════

    def _on_tab_changed(self, index: int):
        """
        标签页切换 → 用 widget 匹配查找文件路径 → 发射信号。

        使用 widget 引用匹配而非存储的索引，确保标签移动后仍能正确映射。
        """
        if index < 0 or self._is_welcome_tab(index):
            self.current_path = ""
            self.current_file_changed.emit("")
            return

        widget = self.tab_widget.widget(index)
        if widget is None:
            self.current_path = ""
            self.current_file_changed.emit("")
            return

        # 通过 widget 引用查找对应的文件路径
        found_path = self._find_path_for_widget(widget)
        if found_path:
            self.current_path = found_path
            self.current_file_changed.emit(found_path)
        else:
            self.current_path = ""
            self.current_file_changed.emit("")

    def _find_path_for_widget(self, widget) -> Optional[str]:
        """通过 widget 引用查找对应的文件路径"""
        for path, (_, _) in self.open_files.items():
            if self._get_widget_for_path(path) is widget:
                return path
        return None

    # ══════════════════════════════════════════════════════════
    # 标签页关闭
    # ══════════════════════════════════════════════════════════

    def _on_tab_close_requested(self, index: int):
        """标签页关闭按钮被点击"""
        if self._is_welcome_tab(index):
            return  # 欢迎页不可关闭
        self.close_file(index)

    def close_file(self, tab_index: int) -> bool:
        """
        关闭指定索引的标签页。

        Args:
            tab_index: 标签页索引

        Returns:
            bool: 是否成功
        """
        widget = self.tab_widget.widget(tab_index)
        if widget is None:
            return False

        # 查找该 widget 对应的文件路径
        to_remove = [
            path for path in self.open_files
            if self._get_widget_for_path(path) is widget
        ]
        for path in to_remove:
            del self.open_files[path]
            self._remove_file_watcher(path)

        # 移除标签页
        self.tab_widget.removeTab(tab_index)

        # 删除后整理 open_files 中的索引
        self._reindex_tabs()

        # 如果所有真实文件都关闭了 → 确保欢迎页在 tab 0
        if not self.open_files:
            self._ensure_welcome_first()
            self.current_path = ""
            self.current_file_changed.emit("")

        return True

    def close_all_files(self):
        """关闭所有文件标签页（保留欢迎页）"""
        for path in list(self.open_files.keys()):
            self._remove_file_watcher(path)

        self.open_files.clear()

        # 移除所有真实文件标签页（保留索引 0 的欢迎页）
        while self.tab_widget.count() > 1:
            self.tab_widget.removeTab(1)

        self.current_path = ""
        self.current_file_changed.emit("")

        # 确保欢迎页在 tab 0
        self._ensure_welcome_first()

    def _reindex_tabs(self):
        """在标签页增删或移动后，重新整理 open_files 中的 tab_index"""
        updated = {}
        for path, (_, file_type) in self.open_files.items():
            widget = self._get_widget_for_path(path)
            if widget is None:
                continue  # widget 已不存在（异常），跳过
            new_idx = self.tab_widget.indexOf(widget)
            if new_idx >= 0:
                updated[path] = (new_idx, file_type)
        self.open_files.clear()
        self.open_files.update(updated)

    def _get_widget_for_path(self, file_path: str):
        """通过 tooltip（存储的路径）查找对应的 widget"""
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabToolTip(i) == file_path:
                return self.tab_widget.widget(i)
        return None

    # ══════════════════════════════════════════════════════════
    # 公共接口：获取状态
    # ══════════════════════════════════════════════════════════

    def get_current_file_path(self) -> Optional[str]:
        """
        获取当前激活标签页的文件路径。

        Returns:
            str | None: 文件路径，当前是欢迎页或没有标签时返回 None
        """
        current = self.tab_widget.currentWidget()
        if current is None or current is self._welcome_label:
            return None
        return self.current_path if self.current_path else None
