# 中央区域管理器：CenterWidgetManage

**文件位置：** `Widgets/CenterWidget/CenterWidgetManage.py`

**类声明：** `class CenterWidgetManage(QWidget)`

**说明：** `CenterWidgetManage` 是中央区域的布局管理器，负责管理左侧面板（如 FileManage）的注册、显示/隐藏切换，以及中央编辑器的文件打开转发。位于 `MultiFormatViewer` 之上，作为中央区域的顶层容器。

---

## 1. 职责

- 管理左侧可切换面板（如 FileManage）的注册与显隐
- 作为 `CenterWidgetManage.toggle_panel()` 的唯一切换入口
- 通过信号桥接，将面板内的打开文件请求转发到 `MultiFormatViewer`
- 提供灰色调统一配色

> `CenterWidgetManage` **不是** QMainWindow 级别的管理员，不涉及 QDockWidget 的管理。它仅管理 `main_content_widget` 区域内的子面板显隐。

---

## 2. 初始化流程

```python
__init__()
  ├── self._panels = {}                    # panel_id → (QWidget, QHBoxLayout 索引)
  ├── self._setup_ui()                     # 初始化 QHBoxLayout 布局
  ├── self.register_panel("file_manage", file_manage_widget)
  │     └── file_manage_widget 默认隐藏
  └── self.set_widget(content_widget)      # 设置主内容 widget (MultiFormatViewer)
```

### UI 布局结构

```
CenterWidgetManage (QWidget, 背景 #1E1E1E)
└── QHBoxLayout (间距 0, 边距 0)
    ├── PanelContainer (QWidget, 初始宽度 250px, 默认隐藏)
    │   └── 注册的面板 widget
    │
    └── MainContentPlaceholder (QWidget, Expanding)
        └── MultiFormatViewer 实例（由 MainWindow 设置）
```

> ✅ 不需要 .ui 文件 — 纯 QWidget 代码初始化布局。

---

## 3. 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `_panels` | `dict[str, tuple[QWidget, bool]]` | 面板注册表：`panel_id → (widget, visible)` |
| `_main_widget` | `QWidget \| None` | 主内容 widget（MultiFormatViewer） |
| `_panel_container` | `QWidget` | 左侧面板容器 widget |
| `_main_layout` | `QHBoxLayout` | 水平布局 |

---

## 4. 公共接口

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `register_panel(panel_id, widget)` | `str, QWidget` | `bool` | 注册一个面板到左侧区域。返回 `True` 表示注册成功。 |
| `show_panel(panel_id)` | `str` | — | 显示指定面板 |
| `hide_panel(panel_id)` | `str` | — | 隐藏指定面板 |
| `toggle_panel(panel_id)` | `str` | `bool` | 切换面板显隐，返回新的可见状态 |
| `is_panel_visible(panel_id)` | `str` | `bool` | 查询面板是否可见 |
| `open_file_in_editor(file_path)` | `str` | — | 将文件打开请求转发给 MultiFormatViewer |
| `set_widget(widget)` | `QWidget` | — | 设置主内容区域的 widget |

---

## 5. 面板注册机制

```python
def register_panel(self, panel_id: str, widget: QWidget) -> bool:
    """注册面板到左侧区域。panel_id 必须唯一。"""
    if panel_id in self._panels:
        return False  # 已注册，静默忽略

    widget.setParent(self._panel_container)

    # 将 widget 放入 panel_container 的布局
    panel_layout = self._panel_container.layout()
    if panel_layout is None:
        panel_layout = QVBoxLayout(self._panel_container)
        panel_layout.setContentsMargins(0, 0, 0, 0)
    panel_layout.addWidget(widget)

    widget.setVisible(False)  # 默认隐藏
    self._panels[panel_id] = widget
    return True
```

### 面板容器尺寸策略

| 元素 | 策略 |
|------|------|
| PanelContainer（面板容器） | `setFixedWidth(250)` 当有面板可见时；`setFixedWidth(0)` 当无面板可见时 |
| MainContentPlaceholder | 水平方向 `Expanding`，填充剩余空间 |

---

## 6. 面板切换逻辑

```python
def toggle_panel(self, panel_id: str) -> bool:
    """切换面板显隐，返回新状态。"""
    if panel_id not in self._panels:
        return False

    widget = self._panels[panel_id]
    new_visible = not widget.isVisible()
    widget.setVisible(new_visible)

    # 更新容器尺寸
    any_visible = any(w.isVisible() for w in self._panels.values())
    self._panel_container.setFixedWidth(250 if any_visible else 0)

    return new_visible
```

---

## 7. 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `panel_toggled` | `panel_id: str, visible: bool` | 面板显隐状态变更时发射 |

---

## 8. 文件打开转发

```python
def open_file_in_editor(self, file_path: str):
    """转发文件打开请求到 MultiFormatViewer。"""
    if self._main_widget and hasattr(self._main_widget, "open_file"):
        self._main_widget.open_file(file_path)
```

---

## 9. 统一颜色映射

| UI 元素 | 色值 | 说明 |
|---------|------|------|
| 面板背景 | `#252526` | 与 Dock 面板一致的背景色 |
| 面板容器分隔线 | `#454545` | 与 `overview.md` 边框色一致 |
| 主内容区域背景 | `#1E1E1E` | 最深灰，与编辑器画布一致 |

---

## 10. 初始化集成（由 MainWindow 调用）

> ⚠️ **关键设计约束：** `register_panel` 是 FileManage 在架构中的**唯一归属容器**。
> FileManage **不**被放入任何 QDockWidget，其生命周期完全由 CenterWidgetManage
> 的面板注册表管理。这种设计避免了 QDockWidget 与面板容器之间的父对象冲突。

```python
# MainWindow._init_center_widget() 中：
from Widgets.CenterWidget.CenterWidgetManage import CenterWidgetManage
from Widgets.LeftWidget.FileManage import FileManage

self.file_manage_widget = FileManage()
self.center_widget_manager = CenterWidgetManage()
self.center_widget_manager.set_widget(self.multi_format_viewer)
self.center_widget_manager.register_panel("file_manage", self.file_manage_widget)

# 将 manager 注入 LeftSidebar
self.left_sidebar.set_center_widget_manager(self.center_widget_manager)

# 将 manager 设为首个中央 widget
self.central_widget_layout.addWidget(self.center_widget_manager)
```

> CenterWidgetManage 全部负责左侧面板（FileManage）的生命周期——创建、注册、显隐切换。
> QDockWidget 体系不再管理 FileManage。
