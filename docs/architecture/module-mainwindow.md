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
| `self.center_widget_manager` | `CenterWidgetManage` | 中央 Dock 管理器实例 |

---

## 2. UI 布局（`MainWindow.ui`）

```
centralwidget (QWidget, 全填充 VBoxLayout, 边距 0)
├── topbar_widget (高 40px, 背景 #F6F2EE)
│   └── [Topbar 实例]
│
└── content_widget (QHBoxLayout, 间距 0)
    ├── left_sidebar_widget (宽 80px, 背景 #282828)
    │   └── [LeftSidebar 实例]
    │
    ├── main_content_widget (Expanding, 背景 #282828)
    │   └── [CenterWidgetManage 实例 — 内嵌 QMainWindow]
    │
    └── right_sidebar_widget (宽 80px, 背景 #282828)
        └── [RightSidebar 实例]
```

---

## 3. 初始化流程

```
__init__()
  ├── uic.loadUi("MainWindow.ui")     # 加载四分区布局
  ├── hide_title_bar()                 # 跨平台移除原生标题栏
  ├── _init_topbar()                   # 创建 Topbar 并连接信号
  ├── _init_sidebars()                 # 创建左右侧栏
  └── _init_center_widget()            # 创建 Dock 管理器
```

---

## 4. 跨平台窗口适配

### `hide_title_bar()` 方法

| 平台 | 实现 | 代码 |
|------|------|------|
| Linux | `Qt.FramelessWindowHint` | `self.setWindowFlags(Qt.FramelessWindowHint)` |
| Windows | Win32 API | `SetWindowLongPtrW` + `SetWindowPos` |

### Windows 实现细节

```python
hwnd = int(self.winId())
user32 = windll.user32

# 移除标题栏（WS_CAPTION = 0x00C00000）
style &= ~WS_CAPTION

# 保留缩放边框、最小化、最大化、系统菜单
style |= WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU

user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)
# 刷新非客户区
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

## 6. 事件处理

| 方法 | 触发时机 | 行为 |
|------|----------|------|
| `changeEvent(event)` | 窗口状态改变（最大化/还原） | 更新 Topbar 最大化按钮图标 |
| `closeEvent(event)` | 窗口关闭 | 预留清理代码入口 |
| `setWindowTitle(title)` | 重写父类 | 同时更新 Topbar 标题文本 |
