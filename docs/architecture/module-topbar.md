# 自定义标题栏：Topbar

**文件位置：** `Widgets/Sidebars/Topbar.py` + `Topbar.ui`

**类声明：** `class Topbar(QWidget)`

---

## 1. 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `minimize_clicked` | — | 点击最小化按钮 |
| `maximize_clicked` | — | 点击最大化/还原按钮，或双击标题栏 |
| `close_clicked` | — | 点击关闭按钮 |

---

## 2. 公共接口

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `set_title(title)` | `str` | — | 设置标题文本 |
| `get_title()` | — | `str` | 获取当前标题文本 |
| `update_maximize_button(is_maximized)` | `bool` | — | 切换最大化图标（□）与还原图标（❐） |

---

## 3. UI 布局（`Topbar.ui`）

```
Topbar (QWidget, 高 40~80px, 背景 #F6F2EE)  ← 参考统一色彩方案
└── QHBoxLayout (间距 10, 边距 10)
    ├── title_label (QLabel, 黑字 14px bold, 文本"一个应用")
    ├── horizontalSpacer (弹性格子)
    ├── minimize_button (QPushButton, 40×40, 文本"−")
    ├── maximize_button (QPushButton, 40×40, 文本"□")
    └── close_button (QPushButton, 40×40, 文本"×")
```

按钮样式规则：hover 时灰色背景，关闭按钮 hover 红色（`#e81123`）。

---

## 4. 交互实现

### 窗口拖拽

```python
def mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
        self.window().windowHandle().startSystemMove()
        event.accept()
```

### 双击最大化

```python
def mouseDoubleClickEvent(self, event):
    if event.button() == Qt.LeftButton:
        self.maximize_clicked.emit()
        event.accept()
```
