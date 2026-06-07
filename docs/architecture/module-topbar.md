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
Topbar (QWidget, 高 40px, 背景 #333333)
└── QHBoxLayout (间距 10, 边距 10)
    ├── title_label (QLabel, 字体 #FFFFFF 14px bold, 文本"主窗口")
    ├── horizontalSpacer (弹性格子)
    ├── minimize_button (QPushButton, 40×40, 文字 #FFFFFF, 文本"−")
    ├── maximize_button (QPushButton, 40×40, 文字 #FFFFFF, 文本"□")
    └── close_button (QPushButton, 40×40, 文字 #FFFFFF, 文本"×")
```

### 统一颜色映射

| UI 元素 | 色值 | 说明 |
|---------|------|------|
| 顶栏背景 | `#333333` | 中灰（区别于深灰侧栏） |
| 标题文字 | `#FFFFFF` | 白色 |
| 按钮文字 | `#FFFFFF` | 白色 |
| 按钮 hover | `#3C3C3C` | 浅灰高亮 |
| 按钮 pressed | `#454545` | 更亮灰 |
| 关闭按钮 hover | `#C42B1C` | 红色（唯一例外，保持用户习惯） |
| 关闭按钮 pressed | `#A51D0F` | 深红 |

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

---

## 5. 按钮样式（`setStyleSheet`）

```python
_button_style = """
QPushButton {
    background: transparent;
    color: #FFFFFF;
    font-size: 18px;
    border: none;
    border-radius: 4px;
}
QPushButton:hover {
    background: #3C3C3C;
}
QPushButton:pressed {
    background: #454545;
}
"""

_close_button_style = """
QPushButton {
    background: transparent;
    color: #FFFFFF;
    font-size: 18px;
    border: none;
    border-radius: 4px;
}
QPushButton:hover {
    background: #C42B1C;
}
QPushButton:pressed {
    background: #A51D0F;
}
"""
```
