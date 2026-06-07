"""
CenterWidgetManage — 中央区域管理器

顶层 QWidget 容器，负责管理左侧面板（如 FileManage）的注册与显隐切换，
以及中央编辑器的文件打开转发。

位置：Widgets/CenterWidget/CenterWidgetManage.py
"""

from typing import Dict, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSizePolicy, QSplitter,
)

# ════════════════════════════════════════════════════════════════
# CenterWidgetManage
# ════════════════════════════════════════════════════════════════
class CenterWidgetManage(QWidget):
    """
    中央区域管理器 — 管理左侧/右侧面板注册/显隐以及中央编辑器内容设置。

    Layout:
        CenterWidgetManage (QWidget, background #1E1E1E)
        └── QHBoxLayout (spacing 0, margin 0)
            ├── LeftPanelContainer (QWidget, 250px, hidden by default, bg #252526)
            ├── MainContentPlaceholder (QWidget, Expanding, bg #1E1E1E)
            └── RightPanelContainer (QWidget, 0px, hidden by default, bg #252526)

    Signals:
        panel_toggled(str, bool): 面板显隐状态变更时发射，参数 (panel_id, visible)
        right_panel_toggled(str, bool): 右侧面板显隐状态变更时发射
    """

    panel_toggled = pyqtSignal(str, bool)
    right_panel_toggled = pyqtSignal(str, bool)

    # ── 右侧面板默认宽度 ──
    RIGHT_PANEL_MIN_WIDTH = 200
    RIGHT_PANEL_DEFAULT_WIDTH = 250

    # ──────────────────────────────────────────────────────────
    # 初始化
    # ──────────────────────────────────────────────────────────
    def __init__(self, parent=None):
        super().__init__(parent)

        # ── 属性 ─────────────────────────────────────────────
        self._panels: Dict[str, QWidget] = {}  # panel_id → widget (左侧)
        self._right_panels: Dict[str, QWidget] = {}  # panel_id → widget (右侧)
        self._right_panel_visible: Dict[str, bool] = {}  # panel_id → visible (右侧显隐状态)
        self._main_widget: Optional[QWidget] = None  # 主内容 widget（MultiFormatViewer）

        # ── 布局 ─────────────────────────────────────────────
        self.setStyleSheet("background-color: #1E1E1E;")
        self._setup_ui()

    # ══════════════════════════════════════════════════════════
    # UI 初始化
    # ══════════════════════════════════════════════════════════

    def _setup_ui(self):
        """初始化 QHBoxLayout 布局结构"""
        # ── 主布局 ───────────────────────────────────────────
        self._main_layout = QHBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # ── LeftPanelContainer（左侧面板容器） ────────────────
        self._panel_container = QWidget(self)
        self._panel_container.setStyleSheet("background-color: #252526;")
        self._panel_container.setFixedWidth(0)
        self._panel_container.setVisible(True)

        panel_layout = QVBoxLayout(self._panel_container)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        self._main_layout.addWidget(self._panel_container)

        # ── QSplitter（中央 + 右侧面板，可拖拽调整大小） ────
        self._splitter = QSplitter(Qt.Horizontal, self)
        self._splitter.setHandleWidth(4)
        self._splitter.setStyleSheet(""
            "QSplitter::handle { background-color: #454545; }"
            "QSplitter::handle:hover { background-color: #007ACC; }"
        "")
        self._splitter.setChildrenCollapsible(False)  # 防止子面板被完全折叠

        # ── MainContentPlaceholder（中央主内容区域） ─────────
        self._main_placeholder = QWidget(self._splitter)
        self._main_placeholder.setStyleSheet("background-color: #1E1E1E;")
        self._main_placeholder.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )

        content_layout = QVBoxLayout(self._main_placeholder)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # ── RightPanelContainer（右侧面板容器） ───────────────
        self._right_panel_container = QWidget(self._splitter)
        self._right_panel_container.setStyleSheet("background-color: #252526;")
        self._right_panel_container.setMinimumWidth(self.RIGHT_PANEL_MIN_WIDTH)

        right_panel_layout = QVBoxLayout(self._right_panel_container)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(1)

        # 初始隐藏右侧面板（宽度设为0）
        self._right_panel_container.hide()

        self._main_layout.addWidget(self._splitter)

    # ══════════════════════════════════════════════════════════
    # 公共属性
    # ══════════════════════════════════════════════════════════

    @property
    def multi_format_viewer(self) -> Optional[QWidget]:
        return self._main_widget

    @multi_format_viewer.setter
    def multi_format_viewer(self, widget: Optional[QWidget]):
        self._main_widget = widget

    # ══════════════════════════════════════════════════════════
    # 左侧面板注册系统
    # ══════════════════════════════════════════════════════════

    def register_panel(self, panel_id: str, widget: QWidget) -> bool:
        """注册一个面板到左侧区域"""
        if panel_id in self._panels:
            return False

        widget.setParent(self._panel_container)
        panel_layout = self._panel_container.layout()
        if panel_layout is None:
            panel_layout = QVBoxLayout(self._panel_container)
            panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(widget)

        widget.setVisible(False)
        self._panels[panel_id] = widget
        return True

    # ══════════════════════════════════════════════════════════
    # 左侧面板切换方法
    # ══════════════════════════════════════════════════════════

    def show_panel(self, panel_id: str):
        if panel_id not in self._panels:
            return
        widget = self._panels[panel_id]
        if not widget.isVisible():
            widget.setVisible(True)
            self._update_container_width()
            self.panel_toggled.emit(panel_id, True)

    def hide_panel(self, panel_id: str):
        if panel_id not in self._panels:
            return
        widget = self._panels[panel_id]
        if widget.isVisible():
            widget.setVisible(False)
            self._update_container_width()
            self.panel_toggled.emit(panel_id, False)

    def toggle_panel(self, panel_id: str) -> bool:
        if panel_id not in self._panels:
            return False
        widget = self._panels[panel_id]
        new_visible = not widget.isVisible()
        widget.setVisible(new_visible)
        self._update_container_width()
        self.panel_toggled.emit(panel_id, new_visible)
        return new_visible

    def is_panel_visible(self, panel_id: str) -> bool:
        if panel_id not in self._panels:
            return False
        return self._panels[panel_id].isVisible()

    def _update_container_width(self):
        any_visible = any(w.isVisible() for w in self._panels.values())
        self._panel_container.setFixedWidth(250 if any_visible else 0)

    # ══════════════════════════════════════════════════════════
    # 右侧面板注册系统
    # ══════════════════════════════════════════════════════════

    def register_right_panel(self, panel_id: str, widget: QWidget) -> bool:
        """注册一个面板到右侧区域（预览/逻辑门/文本逻辑等）"""
        if panel_id in self._right_panels:
            return False

        widget.setParent(self._right_panel_container)
        right_layout = self._right_panel_container.layout()
        if right_layout is None:
            right_layout = QVBoxLayout(self._right_panel_container)
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(1)

        # 使用 QSplitter 或 VBoxLayout 让面板垂直排列
        widget.setVisible(False)
        right_layout.addWidget(widget)
        self._right_panels[panel_id] = widget
        return True

    def show_right_panel(self, panel_id: str):
        if panel_id not in self._right_panels:
            return
        widget = self._right_panels[panel_id]
        self._right_panel_visible[panel_id] = True
        widget.setVisible(True)
        self._update_right_container_width()
        self.right_panel_toggled.emit(panel_id, True)

    def hide_right_panel(self, panel_id: str):
        if panel_id not in self._right_panels:
            return
        widget = self._right_panels[panel_id]
        self._right_panel_visible[panel_id] = False
        widget.setVisible(False)
        self._update_right_container_width()
        self.right_panel_toggled.emit(panel_id, False)

    def toggle_right_panel(self, panel_id: str) -> bool:
        if panel_id not in self._right_panels:
            return False
        widget = self._right_panels[panel_id]
        new_visible = not self._right_panel_visible.get(panel_id, False)
        self._right_panel_visible[panel_id] = new_visible
        widget.setVisible(new_visible)
        self._update_right_container_width()
        self.right_panel_toggled.emit(panel_id, new_visible)
        return new_visible

    def is_right_panel_visible(self, panel_id: str) -> bool:
        return self._right_panel_visible.get(panel_id, False)

    def _update_right_container_width(self):
        """通过 QSplitter 控制右侧面板显隐和大小"""
        any_visible = any(v for v in self._right_panel_visible.values())
        if any_visible:
            # 显示右侧面板
            self._right_panel_container.show()
            # 设置 splitter 大小：主内容占大部分，右面板 250px
            total = self._splitter.width()
            if total > self.RIGHT_PANEL_DEFAULT_WIDTH:
                self._splitter.setSizes([total - self.RIGHT_PANEL_DEFAULT_WIDTH, self.RIGHT_PANEL_DEFAULT_WIDTH])
            else:
                self._splitter.setSizes([total // 2, total // 2])
        else:
            # 隐藏右侧面板
            self._right_panel_container.hide()

    # ══════════════════════════════════════════════════════════
    # 主内容设置
    # ══════════════════════════════════════════════════════════

    def set_widget(self, widget: QWidget):
        """设置主内容区域的 widget（例如 MultiFormatViewer）"""
        layout = self._main_placeholder.layout()
        if layout is None:
            layout = QVBoxLayout(self._main_placeholder)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        layout.addWidget(widget)
        self._main_widget = widget

    # ══════════════════════════════════════════════════════════
    # 文件打开转发
    # ══════════════════════════════════════════════════════════

    def open_file_in_editor(self, file_path: str) -> tuple:
        if self._main_widget and hasattr(self._main_widget, "open_file"):
            return self._main_widget.open_file(file_path)
        return (False, "未设置")

    # ══════════════════════════════════════════════════════════
    # 文件打开转发
    # ══════════════════════════════════════════════════════════

    def open_file_in_editor(self, file_path: str):
        """
        将文件打开请求转发到 MultiFormatViewer。

        如果已设置 _main_widget 且其具备 open_file 方法，则调用之；
        否则返回 (False, "未设置") 桩实现。

        Args:
            file_path: 文件路径

        Returns:
            tuple[bool, str]: (成功标志, 错误信息或空串)
        """
        if self._main_widget and hasattr(self._main_widget, "open_file"):
            return self._main_widget.open_file(file_path)
        return (False, "未设置")
