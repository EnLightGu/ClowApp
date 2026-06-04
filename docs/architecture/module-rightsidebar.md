# 右侧边栏：RightSidebar

**文件位置：** `Widgets/Sidebars/RightSidebar.py` + `RightSidebar.ui`

**类声明：** `class RightSidebar(QWidget)`

---

## 1. UI 布局（`RightSidebar.ui`）

```
RightSidebar (QWidget, 宽 80px, 背景 #2D2D2D)
└── QVBoxLayout
    ├── button1 (QPushButton, 图标 icon3.ico, tooltip="设置")
    ├── button2 (QPushButton, 图标 icon4.ico, tooltip="帮助")
    └── verticalSpacer (Expanding)
```

> 背景色 `#2D2D2D` 参考[统一色彩方案](overview.md#4-统一色彩方案)中的"侧栏"定义。

---

## 2. 公共接口

| 方法 | 说明 |
|------|------|
| `set_button1_icon(icon)` / `set_button2_icon(icon)` | 更换按钮图标 |
| `set_button1_tooltip(text)` / `set_button2_tooltip(text)` | 设置按钮提示文本 |
| `_on_button1_clicked()` | 预留空实现（仅 print 日志） |
| `_on_button2_clicked()` | 预留空实现（仅 print 日志） |

---

## 3. 当前状态

右侧边栏的两个按钮目前为**预留状态**，点击仅输出调试日志。后续可扩展为：

- **button1（设置）：** 打开应用设置面板
- **button2（帮助）：** 打开帮助文档或关于页面
