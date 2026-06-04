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
| `self.center_widget_manager` | `CenterWidgetManage` | 中央区域管理器（`QWidget`，非 `QMainWindow`） |

> `CenterWidgetManage` 继承自 `QWidget`，避免 QMainWindow 嵌套问题。

---

## 2. UI 布局（`MainWindow.ui`）

```
centralwidget (QWidget, 全填充 VBoxLayout, 边距 0)
├── topbar_widget (高 40px, 背景 #F6F2EE)
│   └── [Topbar 实例]
│
└── content_widget (QHBoxLayout, 间距 0)
    ├── left_sidebar_widget (宽 80px, 背景 #2D2D2D)
    │   └── [LeftSidebar 实例]
    │
    ├── main_content_widget (Expanding, 背景 #1E1E1E)
    │   └── [CenterWidgetManage 实例 — 继承 QWidget]
    │         ├── left_panel (可选显示) ─── [FileManage 等]
    │         └── MultiFileEditor (常驻中央)
    │
    └── right_sidebar_widget (宽 80px, 背景 #2D2D2D)
        └── [RightSidebar 实例]
```

---

## 3. 初始化流程

```
__init__()
  ├── uic.loadUi("MainWindow.ui")        # 加载四分区布局
  ├── 平台判断 + 移除原生标题栏             # 见第 4 节
  ├── setWindowTitle("Main Window")      # 设置窗口标题
  ├── _init_topbar()                      # 创建 Topbar 并连接信号
  ├── _init_sidebars()                    # 创建左右侧栏 + 注入 center_widget_manager
  └── _init_center_widget()               # 创建 CenterWidgetManage + 组件注册 + 信号连接
```

---

## 4. 跨平台窗口适配

### 平台分支逻辑

```python
if platform.system() == "Linux":
    self.setWindowFlags(Qt.FramelessWindowHint)
    self.setGeometry(100, 100, 1200, 800)
elif platform.system() == "Windows":
    self.setWindowFlags(Qt.Window)
    self.setGeometry(100, 100, 1200, 800)
    self.hide_title_bar()
    self.resize(1100, 700)
elif platform.system() == "Darwin":
    # macOS：使用 setTitleBarAppearsTransparent 或 NSWindow 桥接
    # 当前版本暂不支持 macOS，预留占位
    pass
```

| 平台 | 实现方式 | 保留功能 |
|------|----------|----------|
| **Linux** | `setWindowFlags(Qt.FramelessWindowHint)` | 无（靠 Topbar 实现窗口控制） |
| **Windows** | `hide_title_bar()` → Win32 API | 缩放边框、最小/最大按钮、系统菜单 |
| **macOS** | (暂不支持) | — |

> **macOS 备注：** 当前版本未对 macOS 做适配。`FramelessWindowHint` 在 macOS 上可去标题栏但不支持拖拽，Win32 API 完全不适用。后续支持需引入 PyObjC 或 `Cocoa` 桥接。

### `hide_title_bar()` 实现（仅 Windows）

```python
def hide_title_bar(self):
    hwnd = int(self.winId())
    user32 = windll.user32

    style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
    style &= ~WS_CAPTION
    style |= WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU

    user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)
    user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
```

---

## 5. 窗口控制信号槽

| Topbar 信号 | MainWindow 槽函数 | QMainWindow 方法 |
|-------------|-------------------|------------------|
| `minimize_clicked` | `_on_minimize_clicked()` | `showMinimized()` |
| `maximize_clicked` | `_on_maximize_clicked()` | `showNormal()` / `showMaximized()` |
| `close_clicked` | `_on_close_clicked()` | `close()` |

---

## 6. FileManage ↔ CenterWidget 通信集成

### 信号连接时机（在 MainWindow 中统一管理）

信号连接不再交给 `LeftSidebar` 处理，而是由 `MainWindow._init_center_widget()` 统一完成：

```python
def _init_center_widget(self):
    # 1. 创建中央区域管理器
    # 为 main_content_widget 创建布局（UI 文件中它作为 QWidget 无自有布局）
    self.center_widget_manager = CenterWidgetManage(self)
    content_layout = QVBoxLayout(self.main_content_widget)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.addWidget(self.center_widget_manager)

    # 2. 预注册 FileManage（但不显示）
    self.file_manage_widget = FileManage()
    self.center_widget_manager.register_panel(
        self.file_manage_widget,
        panel_id="file_manage",
        position="left"
    )
    self.center_widget_manager.hide_panel("file_manage")  # 默认隐藏

    # 3. ✨ 连接信号：双击文件 → 中央编辑器打开
    self.file_manage_widget.file_double_clicked.connect(
        self._on_file_manage_double_clicked
    )
```

```python
def _on_file_manage_double_clicked(self, file_path):
    success, error_msg = self.center_widget_manager.open_file_in_editor(file_path)
    if not success:
        print(f"打开文件失败: {error_msg}")
```

### 数据流路径

```
FileManage（左侧面板）
  │  双击 .py / .txt / .md ...
  │
  ├── emit file_double_clicked("/path/to/file")
  │
  ▼
MainWindow._on_file_manage_double_clicked()
  │
  ├── center_widget_manager.open_file_in_editor("/path/to/file")
  │     └── return (True, "") 或 (False, "错误信息")
  │
  ▼
CenterWidgetManage
  │
  └── MultiFileEditor.open_file("/path/to/file")
        └── 新建标签页 / 切换到已有标签页
```

### LeftSidebar 的职责（保持纯粹）

```python
# LeftSidebar 只负责"按钮被点击 → 切换面板显隐"
def _on_button1_clicked(self):
    self.center_widget_manager.toggle_panel("file_manage")
```

> `LeftSidebar` 不再参与 FileManage 的创建和信号连接，这些统一由 `MainWindow` 管理，遵循单一职责原则。

---

## 7. 事件处理

| 方法 | 触发时机 | 行为 |
|------|----------|------|
| `changeEvent(event)` | 窗口状态改变（最大化/还原） | 更新 Topbar 最大化按钮图标 |
| `closeEvent(event)` | 窗口关闭 | 清理 `QFileSystemWatcher`、释放资源 |
| `setWindowTitle(title)` | 重写父类 | 同时更新 Topbar 标题文本 |
