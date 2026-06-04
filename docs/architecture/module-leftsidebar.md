# 左侧边栏：LeftSidebar

**文件位置：** `Widgets/Sidebars/LeftSidebar.py` + `LeftSidebar.ui`

**类声明：** `class LeftSidebar(QWidget)`

---

## 1. 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `center_widget_manager` | `CenterWidgetManage \| None` | 对 Dock 管理器的引用，由 MainWindow 注入 |
| `FILE_MANAGE_DOCK_ID` | `str` | 常量 `"file_manage"`，FileManage Dock 的唯一标识符 |

---

## 2. 公共接口

| 方法 | 参数 | 说明 |
|------|------|------|
| `set_center_widget_manager(manager)` | `CenterWidgetManage` | 设置 Dock 管理器引用 |
| `set_button1_icon(icon)` / `set_button2_icon(icon)` | `QIcon` | 动态更换按钮图标 |
| `set_button1_tooltip(text)` / `set_button2_tooltip(text)` | `str` | 设置按钮提示文本 |

---

## 3. UI 布局（`LeftSidebar.ui`）

```
LeftSidebar (QWidget, 宽 40~80px, 背景 #696969)
└── QVBoxLayout (间距 10, 边距 5)
    ├── button1 (QPushButton, 图标 icon1.ico, tooltip="文件管理")
    ├── button2 (QPushButton, 图标 icon2.ico, tooltip="编辑工具")
    └── verticalSpacer (Expanding)
```

---

## 4. Dock 开关逻辑

**`_on_button1_clicked()`** 完整流程：

```
用户点击 button1
  │
  └── center_widget_manager.get_custom_dock("file_manage")
        │
        ├── None (Dock 不存在)
        │     ├── 创建 FileManage widget
        │     ├── center_widget_manager.add_custom_widget(
        │     │       file_manage_widget,
        │     │       title="文件管理",
        │     │       area=Qt.LeftDockWidgetArea,
        │     │       dock_id=FILE_MANAGE_DOCK_ID
        │     │   )
        │     └── dock.setFeatures(Movable | Floatable)
        │
        └── QDockWidget (Dock 已存在)
              └── center_widget_manager.toggle_custom_dock("file_manage")
                    └── dock.setVisible(not dock.isVisible())
```
