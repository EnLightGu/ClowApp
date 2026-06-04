# 文件管理组件：FileManage

**文件位置：** `Widgets/LeftWidget/FileManage.py` + `FileManage.ui`

**类声明：** `class FileManage(QWidget)`

---

## 1. UI 布局（`FileManage.ui`）

```
FileManage (QWidget, 400×300, 背景 #55AAFF)
└── QVBoxLayout
    ├── QHBoxLayout (路径栏)
    │   ├── pathLabel (QLabel, "路径:")
    │   ├── pathLineEdit (QLineEdit)
    │   └── refreshButton (QPushButton, "刷新")
    │
    └── QSplitter (水平分割)
        ├── treeView (QTreeView, 目录树, 隐藏表头)
        └── listView (QListView, IconMode, 48×48 图标)
```

---

## 2. 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `self.file_model` | `QFileSystemModel` | 目录树数据模型（过滤器：`AllEntries \| NoDotAndDotDot \| AllDirs`） |
| `self.list_model` | `QFileSystemModel` | 列表视图数据模型（过滤器：`AllEntries \| NoDotAndDotDot`） |

---

## 3. 信号与槽

| 控件 | 信号 | 槽函数 | 说明 |
|------|------|--------|------|
| `refreshButton` | `clicked` | `_on_refresh_clicked()` | 刷新当前路径 |
| `pathLineEdit` | `returnPressed` | `_on_path_changed()` | 回车跳转到路径 |
| `treeView` | `selectionChanged` | `_on_tree_selection_changed()` | 选择目录时更新路径和列表 |
| `listView` | `doubleClicked` | `_on_list_item_double_clicked()` | 双击目录则进入，双击文件则打印路径 |

---

## 4. 交互逻辑

### 路径变更

```
路径输入 + 回车
  │
  └── os.path.exists(new_path) ?
      ├── True  → _update_list_view(new_path)
      │            ├── list_model.setRootPath(path)
      │            └── treeView.setCurrentIndex() + expand()
      └── False → pathLineEdit.setText("路径不存在")
```

### 列表双击

```
双击列表项
  │
  └── os.path.isdir(file_path) ?
      ├── True  → 更新 pathLineEdit + _update_list_view()
      └── False → print(f"打开文件: {file_path}")  ← 预留文件打开逻辑
```

---

## 5. 初始化细节

- **默认路径：** 当前 Python 文件所在目录
- **树视图：** 设置隐藏表头，仅显示名称列（隐藏大小、类型、修改日期等列）
- **列表视图：** `IconMode` 图标模式，48×48 图标大小
