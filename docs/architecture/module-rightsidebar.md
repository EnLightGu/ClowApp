# 右侧边栏：RightSidebar

**文件位置：** `Widgets/Sidebars/RightSidebar.py` + `RightSidebar.ui`

**类声明：** `class RightSidebar(QWidget)`

---

## 1. UI 布局（`RightSidebar.ui`）

```
RightSidebar (QWidget, 宽 80px, 背景 #2D2D2D)
└── QVBoxLayout (间距 10, 边距 5)
    ├── button1 (QPushButton, icon3.ico, iconSize 32×32, tooltip="预览")
    ├── button2 (QPushButton, icon_logic_gate.ico, iconSize 32×32, tooltip="逻辑门编辑器")  ← 🆕
    ├── button3 (QPushButton, icon_logic_txt.ico, iconSize 32×32, tooltip="文本逻辑")       ← 🆕
    └── verticalSpacer (Expanding)
```

> UI 文件定义布局和按钮位置，信号连接与逻辑在 `.py` 中实现。

### 统一颜色映射

| UI 元素 | 色值 | 说明 |
|---------|------|------|
| 侧栏背景 | `#2D2D2D` | 中深灰 |
| 按钮默认 | `transparent` | 透明 |
| 按钮 hover | `#3C3C3C` | 浅灰高亮 |
| 按钮 pressed | `#454545` | 更亮灰 |
| 按钮 tooltip | `#CCCCCC` | 白色文字 |

---

## 2. 公共接口

| 方法 | 说明 |
|------|------|
| `set_button1_icon(icon)` / `set_button2_icon(icon)` / `set_button3_icon(icon)` | 更换按钮图标 |
| `set_button1_tooltip(text)` / `set_button2_tooltip(text)` / `set_button3_tooltip(text)` | 设置按钮提示文本 |
| `set_main_window(main_window)` | 设置对 MainWindow 的引用，用于调用 dock 切换方法 |

---

## 3. 按钮行为

| 按钮 | tooltip | 点击行为 |
|------|---------|----------|
| **button1** | "预览" | `main_window.toggle_right_dock()` — 切换右侧预览面板 |
| **button2** 🆕 | "逻辑门编辑器" | `main_window.toggle_logic_diagram_dock()` — 切换逻辑门图形编辑器 |
| **button3** 🆕 | "文本逻辑" | `main_window.toggle_logic_text_dock()` — 切换文本逻辑编辑器 |

### 实现代码

```python
def _on_button1_clicked(self):
    if self.main_window:
        self.main_window.toggle_right_dock()

def _on_button2_clicked(self):
    if self.main_window:
        self.main_window.toggle_logic_diagram_dock()

def _on_button3_clicked(self):
    if self.main_window:
        self.main_window.toggle_logic_text_dock()
```

---

## 4. 初始化流程

```
__init__()
  ├── uic.loadUi("RightSidebar.ui")    # 加载三按钮布局
  ├── 设置按钮图标 (备用: Qt 内置图标)
  ├── _init_connections()
  │     ├── button1.clicked → _on_button1_clicked
  │     ├── button2.clicked → _on_button2_clicked
  │     └── button3.clicked → _on_button3_clicked
  │
  └── main_window = None  # 由 set_main_window() 注入
```

---

## 5. UI 文件新增内容（`RightSidebar.ui`）

```xml
<!-- button2: 逻辑门编辑器 -->
<widget class="QPushButton" name="button2">
  <property name="minimumSize">
    <size><width>48</width><height>48</height></size>
  </property>
  <property name="maximumSize">
    <size><width>64</width><height>64</height></size>
  </property>
  <property name="toolTip">
    <string>逻辑门编辑器</string>
  </property>
  <property name="text">
    <string/>
  </property>
</widget>

<!-- button3: 文本逻辑 -->
<widget class="QPushButton" name="button3">
  <property name="minimumSize">
    <size><width>48</width><height>48</height></size>
  </property>
  <property name="maximumSize">
    <size><width>64</width><height>64</height></size>
  </property>
  <property name="toolTip">
    <string>文本逻辑</string>
  </property>
  <property name="text">
    <string/>
  </property>
</widget>
```

---

## 6. 图标文件清单

| 文件 | 用途 |
|------|------|
| `icon3.ico` | button1 — 预览（已有） |
| `icon_logic_gate.ico` 🆕 | button2 — 逻辑门编辑器 |
| `icon_logic_txt.ico` 🆕 | button3 — 文本逻辑 |

> 图标建议使用 32×32 像素，白色/灰色系单色图标，保持与深色背景协调。
