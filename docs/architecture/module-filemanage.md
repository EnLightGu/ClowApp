# 文件管理组件：FileManage

**文件位置：** `Widgets/LeftWidget/FileManage.py` + `FileManage.ui`

**类声明：** `class FileManage(QWidget)`

---

## 1. UI 布局（`FileManage.ui`）

```
FileManage (QWidget, 400×300, 背景 #252526)
└── QVBoxLayout
    ├── QHBoxLayout (路径栏)
    │   ├── pathLabel (QLabel, "路径:")
    │   ├── pathLineEdit (QLineEdit)
    │   └── refreshButton (QPushButton, "刷新")
    │
    └── treeView (QTreeView, 目录树, 隐藏表头)
```

- **移除原 `listView`**，仅保留 `treeView`
- `treeView` 同时显示目录和文件
- `treeView` 的模型过滤器改为 `AllEntries | NoDotAndDotDot`
- 通过 `QSortFilterProxyModel` 实现**目录始终显示在文件前面**

---

## 2. 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `self.file_model` | `QFileSystemModel` | 文件系统模型（过滤器：`AllEntries \| NoDotAndDotDot`） |
| `self.sort_proxy` | `QSortFilterProxyModel` | **新增**：排序代理模型，让目录排在文件前面 |
| `self.file_watcher` | `QFileSystemWatcher` | **新增**：文件变更监听器，支持自动刷新 |

> 移除了原 `self.list_model` 属性。

---

## 3. 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `file_double_clicked` | `file_path: str` | 双击文本文件时发射，通知 CenterWidget 打开文件 |
| `directory_selected` | `dir_path: str` | 选中目录时发射 |

---

## 4. 信号与槽

| 控件 | 信号 | 槽函数 | 说明 |
|------|------|--------|------|
| `refreshButton` | `clicked` | `_on_refresh_clicked()` | 刷新当前路径（重新设置 rootPath） |
| `pathLineEdit` | `returnPressed` | `_on_path_changed()` | 回车跳转到路径 |
| `treeView` | `selectionChanged` | `_on_tree_selection_changed()` | 选择目录或文件时更新路径显示 |
| `treeView` | `doubleClicked` | `_on_tree_item_double_clicked()` | 双击目录→展开/进入；双击文件→发射 `file_double_clicked` |

---

## 5. 交互逻辑

### 路径变更

```
路径输入 + 回车
  │
  └── os.path.exists(new_path) ?
      ├── True  → file_model.setRootPath(path)
      │            treeView.setRootIndex(sort_proxy.mapFromSource(file_model.index(path)))
      │            file_watcher.addPath(path)     ← 监听新路径
      │
      └── False → pathLineEdit.setText("路径不存在")
```

### 树视图双击

```
双击树视图项
  │
  ├── 通过 sort_proxy.mapToSource(index) 获取实际路径
  │
  └── os.path.isdir(file_path) ?
      ├── True  → 展开/折叠目录（treeView 默认行为）
      └── False → 判断文件扩展名
                    ├── 文本文件 (.txt, .md, .py, .json 等)
                    │   └── emit file_double_clicked(file_path) → CenterWidget 打开文件
                    └── 其他文件 → print(f"不支持预览: {file_path}")
```

### 目录优先排序

使用 `QSortFilterProxyModel` 确保目录始终在文件前面显示：

```python
class DirectoryFirstProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        # 获取源模型的 file info
        left_info = left.data(QFileSystemModel.FileInfoRole)
        right_info = right.data(QFileSystemModel.FileInfoRole)

        left_is_dir = left_info.isDir()
        right_is_dir = right_info.isDir()

        # 目录永远排在文件前面
        if left_is_dir != right_is_dir:
            return left_is_dir  # True → 左为目录，排在前面

        # 同为目录或同为文件：按名称字母序
        return super().lessThan(left, right)
```

### 自动刷新（QFileSystemWatcher）

```
_init_file_system() 时
  │
  ├── file_watcher.addPath(home_dir)    ← 监听当前路径
  │
  └── file_watcher.directoryChanged.connect(_on_directory_changed)
        └── _on_directory_changed(path):
              ├── 当前显示的正好是这个目录？
              │   └── True → _on_refresh_clicked() 自动刷新
              └── 忽略
```

---

## 6. 初始化细节

### 初始化顺序

```python
_init_file_system()          # ① 加载文件模型 + 排序代理 + 文件监听器
_connect_signals()           # ② 连接信号（含 treeView 双击 + 文件变更信号）
_set_default_path()          # ③ 将 pathLineEdit 改为当前文件目录
```

- **默认路径：** 家目录（`_init_file_system` 中设置），随后 `_set_default_path` 将输入框文本改为当前 Python 文件所在目录
  > ⚠️ 已知问题：初始化后路径输入框显示当前目录，但文件树仍显示家目录内容，两者不一致
- **树视图：** 设置隐藏表头，仅显示名称列（隐藏大小、类型、修改日期等列）
- **模型过滤器：** `QDir.AllEntries | QDir.NoDotAndDotDot`
- **排序代理：** `DirectoryFirstProxyModel`，目录始终在文件前面

### 公共接口

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `get_current_path()` | `str` | 获取当前路径输入框中的文本 |
