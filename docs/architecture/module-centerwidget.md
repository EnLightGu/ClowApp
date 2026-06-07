# 中央区域：MultiFormatViewer

**文件位置：** `Widgets/CenterWidget/MultiFormatViewer.py` + `MultiFormatViewer.ui`

**类声明：** `class MultiFormatViewer(QWidget)`

---

## 1. UI 布局（`MultiFormatViewer.ui`）

```
MultiFormatViewer (QWidget, 背景 #1E1E1E)
└── QVBoxLayout (边距 0)
    └── QTabWidget (Expanding)
        ├── [欢迎标签页]        ← 占位，无文件时显示
        │   └── QLabel ("双击左栏文件以打开")
        │
        ├── [readme.md]        ← 每个文件一个标签页
        │   └── QsciScintilla / QPlainTextEdit (可编辑)
        │
        └── [app.py]
            └── QsciScintilla / QPlainTextEdit (可编辑)
```

### 统一颜色映射

| UI 元素 | 色值 | 说明 |
|---------|------|------|
| 中央区域背景 | `#1E1E1E` | 最深灰 |
| 标签页背景（未选中） | `#2D2D2D` | 中深灰 |
| 标签页背景（选中） | `#1E1E1E` | 同背景 |
| 标签页文字（未选中） | `#888888` | 中灰 |
| 标签页文字（选中） | `#FFFFFF` | 白色 |
| 编辑器背景 | `#1E1E1E` | 最深灰 |
| 编辑器前景 | `#FFFFFF` | 白色文字 |
| 行号背景 | `#252526` | 深灰 |
| 行号文字 | `#888888` | 中灰 |
| 当前行高亮 | `#2A2D2E` | 浅灰高亮 |
| 选中文本背景 | `#264F78` | 蓝色选区 |

---

## 2. 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `tab_widget` | `QTabWidget` | 标签页容器 |
| `open_files` | `dict[str, QWidget]` | 文件路径 → 编辑器 widget 的映射 |
| `current_file_path` | `str \| None` | 当前激活标签页的文件路径 |

---

## 3. 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `current_file_changed` | `file_path: str \| None` | 当前标签页切换 |
| `file_modified_changed` | `file_path: str, is_modified: bool` | 🆕 文件修改状态变更 |
| `file_saved` | `file_path: str` | 🆕 文件已保存 |
| `editor_mode_changed` | `is_editable: bool` | 🆕 编辑/只读模式切换 |

---

## 4. 公共接口

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `open_file(file_path)` | `str` | `tuple[bool, str]` | 打开文件（可编辑模式） |
| `close_file(tab_index)` | `int` | `bool` | 关闭标签页，检查未保存修改 |
| `close_all_files()` | — | — | 关闭所有文件 |
| `get_current_file_path()` | — | `str \| None` | 获取当前文件路径 |
| | | | |
| **编辑操作** 🆕 | | | |
| `save_current_file()` | — | `bool` | 保存当前文件 |
| `save_current_file_as()` | — | `bool` | 另存为 |
| `is_current_modified()` | — | `bool` | 当前文件是否已修改 |
| `undo()` / `redo()` | — | — | 撤销/重做 |
| `cut()` / `copy()` / `paste()` | — | — | 剪切/复制/粘贴 |
| `find(text)` | `str` | `bool` | 查找 |
| `replace(old, new)` | `str, str` | `int` | 替换，返回替换次数 |

---

## 5. 核心逻辑 — `open_file()`

```
open_file(file_path)
  │
  ├── 文件存在性检查
  │
  ├── 文件大小检查 (>10MB 弹窗确认)
  │
  ├── 重复检查 (file_path in open_files)
  │   ├── True → 切换到已有标签页
  │   └── False → 继续
  │
  ├── 编码检测与读取 (chardet → fallback: UTF-8 → GBK → Latin-1)
  │
  ├── 创建编辑器
  │   ├── QsciScintilla (推荐) 或 QPlainTextEdit
  │   ├── setReadOnly(False)              ← ★ 可编辑模式
  │   ├── 语法高亮 (QsciLexer 子类)
  │   ├── 行号 + 折叠 + 自动缩进
  │   ├── 右键菜单: 复制/粘贴/保存等
  │   └── 等宽字体 (Consolas 12pt)
  │
  ├── tab_widget.addTab(editor, basename)
  └── open_files[file_path] = editor
```

---

## 6. 编辑模式变更

从 v0.01 的**只读预览**升级为 v0.02 的**可编辑**模式：

| 变更 | 原值 | 新值 |
|------|------|------|
| 编辑器组件 | `QPlainTextEdit` | `QsciScintilla`（推荐） |
| 读写模式 | `setReadOnly(True)` | `setReadOnly(False)` |
| 语法高亮 | 无 | `QsciLexer` 子类 |
| 右键菜单 | 无 | 复制/粘贴/剪切/保存/全选 |

---

## 7. 文件未保存提示

```python
def close_file(self, tab_index):
    editor = self.tab_widget.widget(tab_index)
    if editor is None:
        return False

    # 检查是否已修改
    if hasattr(editor, 'isModified') and editor.isModified():
        reply = QMessageBox.warning(
            self, "文件未保存",
            "该文件已修改，是否保存更改？",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )
        if reply == QMessageBox.Save:
            self._save_editor_file(editor, tab_index)
        elif reply == QMessageBox.Cancel:
            return False
        # Discard → 继续关闭

    # 清理
    to_remove = [path for path, w in self.open_files.items() if w is editor]
    for path in to_remove:
        del self.open_files[path]
    self.tab_widget.removeTab(tab_index)
    return True
```

---

## 8. 键盘快捷键

| 快捷键 | 操作 |
|--------|------|
| `Ctrl+Z` | 撤销 |
| `Ctrl+Y` | 重做 |
| `Ctrl+X` | 剪切 |
| `Ctrl+C` | 复制 |
| `Ctrl+V` | 粘贴 |
| `Ctrl+A` | 全选 |
| `Ctrl+F` | 查找 |
| `Ctrl+H` | 替换 |
| `Ctrl+S` | 保存 |
| `Ctrl+Shift+S` | 另存为 |

---

## 9. 支持的文本文件格式

> 与 v0.01 一致，详见 [overview.md](overview.md)。

扩展名：`.txt`, `.md`, `.py`, `.js`, `.ts`, `.json`, `.xml`, `.yaml`, `.html`, `.css`, `.c`, `.cpp`, `.java`, `.sql`, `.csv`, `.log`, `.sh`, `.bat`, `.ini`, `.cfg`, `.toml` 等。

---

## 10. QFileSystemWatcher（文件变更监测）

```
MultiFormatViewer
  │
  └── QFileSystemWatcher
        └── 为每个打开的文件注册监听
              ├── 外部修改 → 标签页标题前加 "● " 标记 + 询问是否重新加载
              └── 文件删除 → 标签页标题前加 "✕ 已删除" 标记
```
