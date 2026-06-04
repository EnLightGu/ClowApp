# 中央 Dock 管理器：CenterWidgetManage

**文件位置：** `Widgets/CenterWidget/CenterWidgetManage.py` + `CenterWidgetManage.ui`

**类声明：** `class CenterWidgetManage(QMainWindow)`

---

## 1. 设计说明

`CenterWidgetManage` 继承自 `QMainWindow`，利用其原生的 `QDockWidget` 支持，将自身作为可嵌入的 Dock 容器提供给 `MainWindow`。它被嵌入到 `main_content_widget` 中，所有子窗口都以 Dock Widget 的形式动态接入。

---

## 2. 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `self.custom_docks` | `dict[str, QDockWidget]` | 以 `dock_id` 为键的 Dock 窗口字典 |

---

## 3. 公共接口

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `add_custom_widget(widget, title, area, dock_id)` | `QWidget`, `str`, `Qt.DockWidgetArea`, `str` | `QDockWidget` | 将 Widget 包装为 Dock 并注册到指定区域 |
| `get_custom_dock(dock_id)` | `str` | `QDockWidget \| None` | 按 ID 查找已注册的 Dock |
| `toggle_custom_dock(dock_id)` | `str` | `bool \| None` | 切换 Dock 可见性，返回切换后状态 |
| `get_dock_widget()` | — | `dict` | 返回 `self.custom_docks` 字典 |

---

## 4. 核心方法实现

### `add_custom_widget()`

```python
def add_custom_widget(self, widget, title="Custom Widget",
                      area=Qt.RightDockWidgetArea, dock_id=None):
    dock = QDockWidget(title, self)
    dock.setWidget(widget)
    dock.setAllowedAreas(Qt.AllDockWidgetAreas)
    self.addDockWidget(area, dock)
    if dock_id:
        self.custom_docks[dock_id] = dock
    return dock
```

### `toggle_custom_dock()`

```python
def toggle_custom_dock(self, dock_id):
    dock = self.get_custom_dock(dock_id)
    if dock:
        new_visibility = not dock.isVisible()
        dock.setVisible(new_visibility)
        return new_visibility
    return None
```

---

## 5. 注册表状态管理

```
custom_docks = {}                     # 初始空字典

add_custom_widget(..., dock_id="file_manage")
  → custom_docks["file_manage"] = <QDockWidget>

get_custom_dock("file_manage")
  → <QDockWidget> 或 None

toggle_custom_dock("file_manage")
  → True (显示) / False (隐藏) / None (不存在)
```
