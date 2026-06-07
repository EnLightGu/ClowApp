# 左侧边栏：LeftSidebar

**文件位置：** `Widgets/Sidebars/LeftSidebar.py` + `LeftSidebar.ui`

**类声明：** `class LeftSidebar(QWidget)`

---

## 1. 职责

`LeftSidebar` 是一个纯按钮面板，职责仅限于：
- 显示功能按钮（图标 + tooltip）
- 按钮点击时调用 `CenterWidgetManage.toggle_panel()`（详见 [`module-center-manage.md`](module-center-manage.md)）切换面板显隐

它**不参与**任何 widget 的创建和信号连接——这些由 `MainWindow._init_center_widget()` 统一管理。

---

## 2. 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `center_widget_manager` | `CenterWidgetManage \| None` | 对中央区域管理器的引用，由 MainWindow 注入 |
| `FILE_MANAGE_PANEL_ID` | `str` | 常量 `"file_manage"`，FileManage 面板的唯一标识符 |

---

## 3. 公共接口

| 方法 | 参数 | 说明 |
|------|------|------|
| `set_center_widget_manager(manager)` | `CenterWidgetManage` | 设置中央区域管理器引用 |
| `set_button1_icon(icon)` / `set_button2_icon(icon)` | `QIcon` | 动态更换按钮图标 |
| `set_button1_tooltip(text)` / `set_button2_tooltip(text)` | `str` | 设置按钮提示文本 |

---

## 4. UI 布局（`LeftSidebar.ui`）

```
LeftSidebar (QWidget, 宽 40~80px, 背景 #2D2D2D)
└── QVBoxLayout (间距 10, 边距 5)
    ├── button1 (QPushButton, 图标 icon1.ico, tooltip="文件管理")
    ├── button2 (QPushButton, 图标 icon2.ico, tooltip="编辑工具")
    └── verticalSpacer (Expanding)
```

---

## 5. 面板开关逻辑

**`_on_button1_clicked()`** 完整流程：

```
用户点击 button1
  │
  └── center_widget_manager.toggle_panel(FILE_MANAGE_PANEL_ID)
        │
        ├── 面板已注册 →
        │     └── center_widget_manager.toggle_panel("file_manage")
        │           └── 切换 left_panel 可见性，返回新状态
        │
        └── 面板未注册 → 无操作（初始化时已注册）
```

> button2（编辑工具）为预留状态，点击仅输出调试日志。
