# 主窗口层：MainWindow

**文件位置：** `MainWindow.py` + `MainWindow.ui`

**类声明：** `class MainWindow(QMainWindow)`

---

## 1. 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `self.topbar` | `Topbar` | 自定义标题栏实例 |
| `self.left_sidebar` | `LeftSidebar` | 左侧边栏实例 |
| `self.right_sidebar` | `RightSidebar` | 右侧边栏实例 |
| `self.multi_format_viewer` | `MultiFormatViewer` | 中央多格式预览/编辑器 |
| | | |
| **QDockWidget 属性** | | |
| `self.left_sidebar_dock` | `QDockWidget` | 左侧固定边栏（80px，不可移动） |
| `self.right_dock` | `QDockWidget` | 右侧预览（SingleTextPreview，默认隐藏） |
| `self.right_sidebar_dock` | `QDockWidget` | 右侧固定边栏（80px，不可移动） |
| `self.bottom_dock` | `QDockWidget` | 底部路径栏（FilePathBar） |
| `self.logic_diagram_dock` 🆕 | `QDockWidget` | 逻辑门图形编辑器，默认隐藏 |
| `self.logic_text_dock` 🆕 | `QDockWidget` | 文本逻辑编辑器，默认隐藏 |
| | | |
| **逻辑分析模块属性** 🆕 | | |
| `self.logic_diagram_widget` | `LogicDiagramWidget` | 逻辑门图形编辑器实例 |
| `self.logic_text_widget` | `LogicTextWidget` | 文本逻辑编辑器实例 |
| `self.logic_db` | `LogicDatabase` | 逻辑数据库管理器 |

---

## 2. UI 布局（`MainWindow.ui`）

```
centralwidget (QWidget, 全填充 VBoxLayout, 边距 0)
├── topbar_widget (高 40px, 背景 #333333)
│   └── [Topbar 实例]
│
└── content_widget (QHBoxLayout, 间距 0)
    ├── left_sidebar_widget (宽 80px, 背景 #2D2D2D)
    │   └── [LeftSidebar 实例]
    │
    ├── main_content_widget (Expanding, 背景 #1E1E1E)
    │   └── [MultiFormatViewer 实例]
    │
    └── right_sidebar_widget (宽 80px, 背景 #2D2D2D)
        └── [RightSidebar 实例]
```

---

## 3. 初始化流程

```
__init__()
  ├── uic.loadUi("MainWindow.ui")        # 加载四分区布局
  ├── 平台判断 + 移除原生标题栏
  ├── setWindowTitle("Main Window")
  ├── _init_topbar()
  ├── _init_center_widget()               # CenterWidgetManage + FileManage 创建与注册
  ├── _init_sidebars()                    # 创建 LeftSidebar + RightSidebar
  └── _init_docks()                       # 所有 QDockWidget
```

---

## 4. _init_docks() — 完整实现

```python
def _init_docks(self):
    from Widgets.RightWidget.SingleTextPreview import SingleTextPreview
    from Widgets.Sidebars.FilePathBar import FilePathBar
    from Widgets.RightWidget.LogicDiagramWidget import LogicDiagramWidget
    from Widgets.RightWidget.LogicTextWidget import LogicTextWidget
    from Widgets.RightWidget.LogicDatabase import LogicDatabase

    # ── A. 左侧固定边栏 ──
    self.left_sidebar_dock = QDockWidget("", self)
    self.left_sidebar_dock.setWidget(self.left_sidebar)
    self.left_sidebar_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
    self.left_sidebar_dock.setTitleBarWidget(QWidget())
    self.left_sidebar_dock.setFixedWidth(80)
    self.addDockWidget(Qt.LeftDockWidgetArea, self.left_sidebar_dock)

    # ── B. 底部路径栏 ──
    self.file_path_bar = FilePathBar()
    self.bottom_dock = QDockWidget("", self)
    self.bottom_dock.setWidget(self.file_path_bar)
    self.bottom_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
    self.bottom_dock.setTitleBarWidget(QWidget())
    self.bottom_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
    self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)

    # ── D. 右侧预览 Dock ──
    self.single_text_preview = SingleTextPreview()
    self.right_dock = QDockWidget("预览", self)
    self.right_dock.setWidget(self.single_text_preview)
    self.right_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
    self.right_dock.setFeatures(
        QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable
    )
    self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)

    # ── E. 逻辑门图形编辑器 Dock ── 🆕
    self.logic_diagram_widget = LogicDiagramWidget()
    self.logic_diagram_dock = QDockWidget("逻辑门编辑器", self)
    self.logic_diagram_dock.setWidget(self.logic_diagram_widget)
    self.logic_diagram_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
    self.logic_diagram_dock.setFeatures(
        QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable
    )
    self.addDockWidget(Qt.RightDockWidgetArea, self.logic_diagram_dock)
    self.logic_diagram_dock.setVisible(False)

    # ── F. 文本逻辑编辑器 Dock ── 🆕
    self.logic_text_widget = LogicTextWidget()
    self.logic_text_dock = QDockWidget("文本逻辑编辑器", self)
    self.logic_text_dock.setWidget(self.logic_text_widget)
    self.logic_text_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
    self.logic_text_dock.setFeatures(
        QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable
    )
    self.addDockWidget(Qt.RightDockWidgetArea, self.logic_text_dock)
    self.logic_text_dock.setVisible(False)

    # ── G. 右侧固定边栏 ──
    self.right_sidebar_dock = QDockWidget("", self)
    self.right_sidebar_dock.setWidget(self.right_sidebar)
    self.right_sidebar_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
    self.right_sidebar_dock.setTitleBarWidget(QWidget())
    self.right_sidebar_dock.setFixedWidth(80)
    self.addDockWidget(Qt.RightDockWidgetArea, self.right_sidebar_dock)

    # ── 右侧区域分割 ──
    # 右侧整体排列: [预览 | 逻辑门 | 文本逻辑 | 边栏]
    self.splitDockWidget(self.right_dock, self.logic_diagram_dock, Qt.Vertical)
    self.splitDockWidget(self.logic_diagram_dock, self.logic_text_dock, Qt.Vertical)
    self.splitDockWidget(self.logic_text_dock, self.right_sidebar_dock, Qt.Vertical)

    # ── 信号连接 ──
    self.file_manage_widget.file_double_clicked.connect(
        self._on_file_manage_double_clicked
    )
    self.multi_format_viewer.current_file_changed.connect(
        self.file_path_bar.set_file_path
    )

    # 逻辑分析模块信号 🆕
    self.logic_diagram_widget.conversion_to_text_requested.connect(
        self._on_diagram_to_text
    )
    self.logic_text_widget.conversion_to_diagram_requested.connect(
        self._on_text_to_diagram
    )

    # ── 右侧 dock 区域尺寸约束策略 ──
    # 当多个面板同时打开时，使用 minimumSize 防止面板被挤压到不可用
    self.right_dock.setMinimumSize(150, 100)
    self.logic_diagram_dock.setMinimumSize(200, 100)
    self.logic_text_dock.setMinimumSize(200, 100)
    self.right_sidebar_dock.setFixedWidth(80)  # 固定边栏宽度不变

    # ── Tab 折叠方案（可选）──
    # 当同时打开多个逻辑面板时，可使用 tabifyDockWidget 让它们折叠成标签页：
    # self.tabifyDockWidget(self.logic_diagram_dock, self.logic_text_dock)
    # self.tabifyDockWidget(self.logic_diagram_dock, self.right_dock)
    # 用户可通过点击标签切换面板，避免垂直分割导致面板过于狭窄

    # ── 数据库初始化 ── 🆕
    self.logic_db = LogicDatabase()
```

---

## 5. 新增切换方法

```python
def toggle_left_dock(self):
    """切换 FileManage 面板显隐（由 CenterWidgetManage 控制）"""
    return self.center_widget_manager.toggle_panel("file_manage")

def toggle_right_dock(self):
    """切换右侧预览 dock 显隐"""
    visible = self.right_dock.isVisible()
    self.right_dock.setVisible(not visible)
    return not visible

def toggle_logic_diagram_dock(self):
    """切换逻辑门图形编辑器显隐"""     # 🆕
    visible = self.logic_diagram_dock.isVisible()
    self.logic_diagram_dock.setVisible(not visible)
    return not visible

def toggle_logic_text_dock(self):
    """切换文本逻辑编辑器显隐"""       # 🆕
    visible = self.logic_text_dock.isVisible()
    self.logic_text_dock.setVisible(not visible)
    return not visible
```

---

## 6. 双向转化信号槽

```python
def _on_diagram_to_text(self):
    """图形 → 文本"""     # 🆕
    text = self.logic_diagram_widget.to_logic_text()
    self.logic_text_widget.import_from_diagram(text)
    self.logic_text_dock.setVisible(True)

def _on_text_to_diagram(self, text):
    """文本 → 图形"""     # 🆕
    success = self.logic_diagram_widget.from_logic_text(text)
    if success:
        self.logic_diagram_dock.setVisible(True)
```

---

## 7. 文件管理 ↔ 中央编辑器 通信

```
用户双击 FileManage.treeView 中的文本文件
  │
  ├── emit file_double_clicked(file_path)
  │
  ▼
MainWindow._on_file_manage_double_clicked()
  │
  ├── multi_format_viewer.open_file(file_path)      # 中央编辑器打开
  └── single_text_preview.open_file(file_path)       # 右侧预览同步
```

---

## 8. QDockWidget 布局总览

```
┌──────────┬──────────────────────────────┬──────────────┐
│LeftSide  │                              │ RightSide    │
│bar Dock  │  中央区域 (MultiFormatViewer │  | Preview   │
│(固定80px) │  + FileManage 内部面板)      │  | LogicDia  │
│          │  由 CenterWidgetManage 管理   │  | LogicTxt  │
│          │                              │              │
├──────────┤                              ├──────────────┤
│(无 Dock) │                              │RightSidebar  │
│FileManage│                              │(固定80px)     │
│由Center- │                              │              │
│WidgetMgr │                              │              │
│管理      │                              │              │
└──────────┴──────────────────────────────┴──────────────┘
┌──────────────────────────────────────────────────────────┐
│                   Bottom Dock (FilePathBar)               │
└──────────────────────────────────────────────────────────┘

> **注：** FileManage **不再**由 QDockWidget 管理。它作为内部面板注册到
> `CenterWidgetManage`，通过 LeftSidebar 按钮切换。
> 详见 [`module-center-manage.md`](module-center-manage.md)。
```
┌──────────────────────────────────────────────────────────┐
│                   Bottom Dock (FilePathBar)               │
└──────────────────────────────────────────────────────────┘
```

---

## 9. 窗口控制信号槽

| Topbar 信号 | 槽函数 | 行为 |
|-------------|--------|------|
| `minimize_clicked` | `_on_minimize_clicked()` | `showMinimized()` |
| `maximize_clicked` | `_on_maximize_clicked()` | `showNormal()` / `showMaximized()` |
| `close_clicked` | `_on_close_clicked()` | `close()` |

---

## 10. 事件处理

| 方法 | 触发时机 | 行为 |
|------|----------|------|
| `changeEvent(event)` | 窗口状态改变 | 更新 Topbar 最大化按钮图标 |
| `closeEvent(event)` | 窗口关闭 | 资源清理 |
| `setWindowTitle(title)` | 重写父类 | 同步更新 Topbar 标题文本 |
