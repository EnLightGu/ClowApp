# 中央区域：CenterWidgetManage + MultiFileEditor

**文件位置：** `Widgets/CenterWidget/CenterWidgetManage.py`（无 `.ui` 文件）

**类声明：** `class CenterWidgetManage(QWidget)`

---

## 1. 设计说明

`CenterWidgetManage` 继承自 `QWidget`（不再嵌套 QMainWindow），采用 **左面板 + 中央编辑器** 的简洁布局。中央区域是 `MultiFileEditor`（多文件文本预览器），左侧是可选面板（如 FileManage），由侧边栏按钮控制显隐。

```
CenterWidgetManage (QWidget)
└── QHBoxLayout (间距 0, 边距 0)
    ├── left_panel (QWidget, 宽 400px, 背景 #282828)
    │   └── [Dock Widget]       ← 由左侧栏按钮控制显示/隐藏
    │
    └── MultiFileEditor (Expanding, 背景 #1E1E1E)
         └── QTabWidget
              ├── [欢迎标签页]
              ├── [file1.py]
              └── [file2.md]
```

> **为何不用 QMainWindow + QDockWidget：**
> `QMainWindow` 设计为顶级窗口，嵌套在另一个 `QMainWindow` 中会导致 Dock 停靠行为异常、焦点和状态保存不可预期。改用 `QWidget` + 手动布局管理，既避免了嵌套问题，也简化了架构。

---

## 2. 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `self.multi_file_editor` | `MultiFileEditor` | 多文件文本编辑器实例（中央区域） |
| `self.left_panel` | `QWidget` | 左侧面板容器（作为 Dock widget 的占位） |
| `self.left_panel_widget` | `QWidget \| None` | 当前注册到左侧面板的 widget |
| `self.right_panel_widget` | `QWidget \| None` | 当前注册到右侧面板的 widget |
| `self.right_panel` | `QWidget` | 右侧面板容器（预留，默认隐藏） |
| `self.custom_panels` | `dict[str, tuple[QWidget, str]]` | 以 `panel_id` 为键，(widget, position) 注册信息字典 |

---

## 3. 公共接口

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `register_panel(widget, panel_id, position)` | `QWidget`, `str`, `str` | `bool` | 注册一个 widget 到指定位置（`"left"` / `"right"`），return 是否成功 |
| `show_panel(panel_id)` | `str` | `bool` | 显示指定面板 |
| `hide_panel(panel_id)` | `str` | `bool` | 隐藏指定面板 |
| `toggle_panel(panel_id)` | `str` | `bool \| None` | 切换面板可见性，return 切换后状态 |
| `is_panel_visible(panel_id)` | `str` | `bool` | 查询面板是否可见 |
| `open_file_in_editor(file_path)` | `str` | `tuple[bool, str]` | 在中央编辑器中打开文件，return `(成功, 错误信息)` |
| `get_editor()` | — | `MultiFileEditor` | 获取编辑器实例引用 |

---

## 4. 面板管理实现

### `register_panel()`

```python
def register_panel(self, widget, panel_id, position="left"):
    if position == "left":
        self.left_panel_widget = widget
        # 将 widget 放入 left_panel 已有的布局中
        self.left_panel.layout().addWidget(widget)
        self.left_panel.setVisible(True)
    elif position == "right":
        self.right_panel_widget = widget
        self.right_panel.layout().addWidget(widget)
        self.right_panel.setVisible(True)
    else:
        return False
    self.custom_panels[panel_id] = (widget, position)
    return True
```

### `toggle_panel()`

```python
def toggle_panel(self, panel_id):
    if panel_id not in self.custom_panels:
        return None
    _, position = self.custom_panels[panel_id]
    if position == "left":
        container = self.left_panel
    elif position == "right":
        container = self.right_panel
    else:
        return None
    new_visibility = not container.isVisible()
    container.setVisible(new_visibility)
    return new_visibility
```

---

## 5. MultiFileEditor（多文件文本编辑器）

**文件位置：** `Widgets/CenterWidget/MultiFileEditor.py` + `MultiFileEditor.ui`

**类声明：** `class MultiFileEditor(QWidget)`

### 5.1 UI 布局

```
MultiFileEditor (QWidget)
└── QVBoxLayout (边距 0)
    └── QTabWidget (Expanding)
        ├── [欢迎标签页]        ← 占位，无文件时显示
        │   └── QLabel ("双击左栏文件以预览")
        │
        ├── [readme.md]        ← 每个文件一个标签页
        │   └── QPlainTextEdit (只读 + 行号)
        │
        └── [app.py]
            └── QPlainTextEdit (只读 + 行号)
```

- 标签页可关闭（`QTabWidget.setTabsClosable(True)` + `tabCloseRequested` 信号）
- 标签页标题 = 文件名（`app.py`），tooltip = 完整路径
- 关闭标签页时自动清理所有内部映射

### 5.2 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `self.tab_widget` | `QTabWidget` | 标签页容器 |
| `self.open_files` | `dict[str, QPlainTextEdit]` | **文件路径 → 编辑器 widget** 的映射（不缓存索引） |

> **为什么用 `QPlainTextEdit` 而不是 `int`？**
> 标签页索引会在关闭中间标签页时发生变化（如关闭第 1 页后，第 2 页索引从 1→0）。直接存储 widget 引用，通过 `QTabWidget.indexOf(widget)` 动态获取索引，避免索引偏移问题。

### 5.3 公共接口

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `open_file(file_path)` | `str` | `tuple[bool, str]` | 打开文件，return `(成功, 错误信息或空串)` |
| `close_file(tab_index)` | `int` | `bool` | 关闭指定标签页，自动清理 `open_files` |
| `close_all_files()` | — | — | 关闭所有文件标签页 |
| `get_current_file_path()` | — | `str \| None` | 获取当前激活标签页的文件路径 |

### 5.4 核心逻辑 — `open_file()`

```
open_file(file_path)
  │
  ├── 文件存在性检查
  │   └── 不存在 → return (False, "文件不存在: {path}")
  │
  ├── 文件大小检查
  │   ├── > 10MB → QMessageBox.warning("文件过大", "是否继续打开？")
  │   │             ├── 用户确认 → 继续
  │   │             └── 用户取消 → return (False, "用户取消")
  │   └── ≤ 10MB → 继续
  │
  ├── 重复检查（file_path in open_files）
  │   ├── True → 切换到已有标签页
  │   │         └── tab_widget.setCurrentWidget(open_files[file_path])
  │   │         └── return (True, "")
  │   └── False → 继续
  │
  ├── 编码检测与读取
  │   ├── 尝试自动检测编码 (chardet)
  │   │   ├── 检测成功 → 用检测到的编码读取
  │   │   └── 检测失败或无 chardet → fallback 链:
  │   │         ├── UTF-8
  │   │         ├── UTF-16 (含 BOM)
  │   │         ├── GBK (中文环境常用)
  │   │         ├── Latin-1 (任意字节可解码)
  │   │         └── 全部失败 → return (False, "无法解码文件编码")
  │   │
  │   └── 读取成功
  │         ├── 创建 QPlainTextEdit
  │         │   ├── setPlainText(content)
  │         │   ├── setReadOnly(True)          ← 当前为只读预览模式
  │         │   ├── 行号显示 (LineNumberArea 扩展)
  │         │   └── setFont(等宽字体, 12pt)
  │         │
  │         ├── tab_widget.addTab(editor, os.path.basename(file_path))
  │         ├── tab_widget.setTabToolTip(index, file_path)
  │         ├── tab_widget.setCurrentWidget(editor)
  │         └── open_files[file_path] = editor  ← 存储 widget 引用
  │         └── return (True, "")
```

### 5.5 核心逻辑 — `close_file()`

```python
def close_file(self, tab_index):
    editor = self.tab_widget.widget(tab_index)
    if editor is None:
        return False

    # 从 open_files 中移除（遍历查找匹配的 widget）
    to_remove = [path for path, w in self.open_files.items() if w is editor]
    for path in to_remove:
        del self.open_files[path]

    # 移除标签页
    self.tab_widget.removeTab(tab_index)
    return True
```

### 5.6 行号显示（LineNumberArea）

`QPlainTextEdit` 行号通过标准 Qt 行号组件实现：在 `QPlainTextEdit` 左侧绘制一个 `QWidget`，通过 `paintEvent` 绘制行号，并同步滚动。

```
LineNumberArea (QWidget, 宽 50px)
  └── 背景 #252526, 字体灰色
  └── 当前行号高亮为白色
  └── 与 QPlainTextEdit 同步垂直滚动
```

### 5.7 错误反馈

| 场景 | 用户可见反馈 |
|------|------------|
| 文件不存在 | 无操作（已从 treeView 逻辑过滤），return 错误信息 |
| 文件 > 10MB | `QMessageBox.warning` 弹窗询问是否继续 |
| 编码解码失败 | 错误标签页，显示"无法解码文件" + 编码信息 |
| 权限不足 | 错误标签页，显示"无权限读取: {path}" |
| 读取成功 | 正常显示文本 |

### 5.8 支持的文本文件格式

| 文件扩展名 | 说明 |
|-----------|------|
| `.txt` | 纯文本 |
| `.md`, `.markdown` | Markdown |
| `.py`, `.js`, `.ts`, `.jsx`, `.tsx` | 源代码 |
| `.json`, `.xml`, `.yaml`, `.yml` | 配置文件/数据 |
| `.ini`, `.cfg`, `.conf` | 配置文件 |
| `.log` | 日志文件 |
| `.csv` | CSV 数据 |
| `.html`, `.css`, `.scss`, `.less` | Web 前端 |
| `.sh`, `.bat`, `.ps1` | 脚本文件 |
| `.c`, `.cpp`, `.h`, `.hpp`, `.java` | 编译语言源码 |
| `.sql` | SQL 脚本 |
| `.toml` | TOML 配置文件 |
| `.gitignore`, `.env`, `Dockerfile`, `Makefile` | 无扩展名文本文件（按文件名匹配） |

### 5.9 预留扩展

| 方向 | 说明 |
|------|------|
| 语法高亮 | 引入 `QSyntaxHighlighter` 子类（如 PythonHighlighter） |
| 搜索/替换 | 在标签页上方添加搜索栏 |
| 编码选择 | 右键菜单 → 用其他编码重新打开 |
| 编辑模式 | `setReadOnly(False)` 切换为可编辑模式 |
| 侧边大纲 | 显示文件结构（Markdown 标题、Python 函数等） |

---

## 6. 初始化流程

```
__init__()
  ├── super().__init__(parent)
  │
  ├── 创建 MultiFileEditor 实例
  │     └── MultiFileEditor()
  │
  ├── 创建 left_panel（QWidget, 默认隐藏）
  │     └── QVBoxLayout（边距 0）
  │
  ├── 创建 right_panel（QWidget, 默认隐藏）← 预留
  │     └── QVBoxLayout（边距 0）
  │
  ├── 主布局 QHBoxLayout（边距 0, 间距 0）
  │     ├── addWidget(self.left_panel)                   ← 左面板
  │     ├── addWidget(self.multi_file_editor, stretch=1)  ← 中央编辑器（占满剩余空间）
  │     ├── addWidget(self.right_panel)                   ← 右面板（预留）
  │     └── setContentsMargins(0, 0, 0, 0)
  │
  └── self.custom_panels = {}          ← 初始化面板字典
```

---

## 7. FileManage ↔ CenterWidget 通信

```
用户双击 FileManage.treeView 中的文本文件
  │
  ├── emit file_double_clicked(file_path)
  │
  ▼
MainWindow（中转，见 MainWindow §6）
  │
  ├── center_widget_manager.open_file_in_editor(file_path)
  │
  ▼
CenterWidgetManage.open_file_in_editor(file_path)
  │
  └── return multi_file_editor.open_file(file_path)
        └── (True, "") 或 (False, "错误信息")
```

---

## 8. 文件变更自动监测（QFileSystemWatcher）

```
MultiFileEditor
  │
  └── QFileSystemWatcher
        └── 为每个打开的标签页文件注册监听
              ├── 文件内容被外部修改 → 标签页标题前加 "● " 标记
              └── 文件被删除 → 标签页标题前加 "✕ 已删除" 标记
```

> 注：当前版本为只读预览，`QFileSystemWatcher` 仅用于提醒用户文件已变更，不涉及自动重新加载。
