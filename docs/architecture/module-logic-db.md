# 逻辑数据库：LogicDatabase

**文件位置：** `Widgets/RightWidget/LogicDatabase.py`

**类声明：** `class LogicDatabase`

**说明：** 纯数据层模块，无 UI 文件。负责逻辑表达式的持久化存储与检索。

---

## 1. 技术选型

| 项目 | 选择 | 说明 |
|------|------|------|
| 引擎 | SQLite3（Python 内置 `sqlite3`） | 零依赖，单文件 |
| 文件位置 | `~/.enapp/logic_db.sqlite` | 用户数据目录 |
| 归档模式 | WAL（Write-Ahead Logging） | 并发读性能 |
| 外键 | 启用 `PRAGMA foreign_keys=ON` | 数据完整性 |

---

## 2. 数据库路径

```python
import os
import sqlite3

DB_DIR = os.path.expanduser("~/.enapp")
DB_PATH = os.path.join(DB_DIR, "logic_db.sqlite")

def get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5)  # 5秒超时，防止多实例并发写锁
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
```

---

## 3. 表结构

```sql
-- 逻辑表达式主表
CREATE TABLE IF NOT EXISTS logic_expressions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    description   TEXT DEFAULT '',
    expression    TEXT NOT NULL,
    variable_map  TEXT DEFAULT '{}',       -- JSON: {"A": "bool", "B": "int"}
    created_at    TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at    TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 标签表
CREATE TABLE IF NOT EXISTS logic_tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- 表达式 ↔ 标签 多对多关联
CREATE TABLE IF NOT EXISTS logic_expression_tags (
    expression_id INTEGER NOT NULL REFERENCES logic_expressions(id) ON DELETE CASCADE,
    tag_id        INTEGER NOT NULL REFERENCES logic_tags(id) ON DELETE CASCADE,
    PRIMARY KEY (expression_id, tag_id)
);

-- 版本历史
CREATE TABLE IF NOT EXISTS logic_expression_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    expression_id INTEGER NOT NULL REFERENCES logic_expressions(id) ON DELETE CASCADE,
    expression    TEXT NOT NULL,
    variable_map  TEXT DEFAULT '{}',
    changed_at    TEXT DEFAULT (datetime('now', 'localtime')),
    change_note   TEXT DEFAULT ''
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_expr_name      ON logic_expressions(name);
CREATE INDEX IF NOT EXISTS idx_expr_updated   ON logic_expressions(updated_at);
CREATE INDEX IF NOT EXISTS idx_history_expr   ON logic_expression_history(expression_id);
```

---

## 4. 类接口

### 4.1 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `db_path` | `str` | 数据库文件路径 |

### 4.2 CRUD 操作

```python
class LogicDatabase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_tables()

    def save(self, name: str, expression: str,
             variable_map: dict = None,
             description: str = "",
             tags: list[str] = None) -> int:
        """
        保存/更新逻辑表达式。
        已存在同名 → UPDATE（自动 save_history 记录旧版）
        不存在 → INSERT
        Returns: 表达式 id
        """
        ...

    def load(self, name: str) -> dict | None:
        """按名称加载"""
        ...

    def load_by_id(self, expr_id: int) -> dict | None:
        """按 ID 加载"""
        ...

    def delete(self, name: str) -> bool:
        """删除表达式及关联的标签和历史"""
        ...

    def list_all(self, tag: str = None) -> list[dict]:
        """列出所有表达式，可选按标签过滤"""
        ...
```

### 4.3 搜索

```python
    def search(self, keyword: str) -> list[dict]:
        """按名称/描述/表达式模糊搜索 (LIKE %keyword%)"""
        ...
```

### 4.4 标签管理

```python
    def add_tag(self, expr_id: int, tag: str) -> bool:
        """为表达式添加标签（标签不存在则自动创建）"""
        ...

    def remove_tag(self, expr_id: int, tag: str) -> bool:
        """移除表达式标签"""
        ...

    def get_all_tags(self) -> list[str]:
        """获取所有标签列表"""
        ...
```

### 4.5 版本历史

```python
    def save_history(self, expr_id: int, old_expression: str,
                     old_variable_map: dict = None,
                     note: str = "") -> int:
        """保存修改前的快照"""
        ...

    def get_history(self, expr_id: int) -> list[dict]:
        """获取修改历史"""
        ...
```

---

## 5. 数据格式

### 返回字典结构

```python
{
    "id": 1,
    "name": "motor_control",
    "expression": "(sensor_A AND sensor_B) OR emergency_stop",
    "variable_map": {"sensor_A": "bool", "sensor_B": "bool", "emergency_stop": "bool"},
    "description": "电机控制逻辑",
    "tags": ["安全", "电机", "传感器"],
    "created_at": "2026-06-07 00:21:00",
    "updated_at": "2026-06-07 00:21:00"
}
```

> **`variable_map` 类型说明：** `variable_map` 中的类型字段（如 `"bool"`、`"int"`）
> **仅作为元数据标签使用**，用于给用户提供参考信息。实际逻辑运算
> （AND / OR / NOT / NAND / NOR / XOR）全部视为**布尔值**处理，
> 不区分整数与布尔类型。用户可自定义任意标签名，或统一使用 `"bool"`。

---

## 6. 数据库初始化

```python
def __init__(self, db_path: str = DB_PATH):
    self.db_path = db_path
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    self._ensure_tables()

def _ensure_tables(self):
    with sqlite3.connect(self.db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(DDL_SQL)  # 上述 CREATE TABLE 语句
```

---

## 7. 数据库对话框

用于从数据库加载/保存时的交互界面，与 `LogicTextWidget` 的工具栏按钮配合使用。

| 对话框 | 类名 | 文件位置 | 说明 |
|--------|------|----------|------|
| 保存对话框 | `LogicSaveDialog` | `Widgets/RightWidget/LogicSaveDialog.ui` + `.py` | 输入名称/描述/标签 |
| 加载对话框 | `LogicLoadDialog` | `Widgets/RightWidget/LogicLoadDialog.ui` + `.py` | 搜索/列表/标签筛选 |

### 7.1 LogicSaveDialog

```
LogicSaveDialog (QDialog, 背景 #2D2D2D)
└── QVBoxLayout
    ├── QLabel "逻辑名称" (#FFFFFF)
    ├── QLineEdit name_edit (背景 #1E1E1E, 前景 #FFFFFF)
    ├── QLabel "描述" (#CCCCCC)
    ├── QLineEdit desc_edit (背景 #1E1E1E, 前景 #FFFFFF)
    ├── QLabel "标签（逗号分隔）" (#CCCCCC)
    ├── QLineEdit tags_edit (背景 #1E1E1E, 前景 #FFFFFF)
    ├── QSpacerItem
    └── QDialogButtonBox (确定 / 取消)
```

### 7.2 LogicLoadDialog

```
LogicLoadDialog (QDialog, 背景 #2D2D2D)
└── QVBoxLayout
    ├── QHBoxLayout
    │   ├── QLineEdit search_edit (背景 #1E1E1E, 前景 #FFFFFF, placeholder="搜索...")
    │   └── QPushButton search_btn ("搜索", 背景 #3C3C3C, 前景 #FFFFFF)
    ├── QHBoxLayout
    │   ├── QComboBox tag_filter (背景 #333333, 前景 #FFFFFF) ← "全部标签"
    │   └── QLabel count_label ("共 5 条", #888888)
    ├── QTableWidget result_table (背景 #252526, 前景 #FFFFFF)
    │   ├── 列: 名称 | 描述 | 标签 | 更新时间
    │   └── 行: 双击选中
    └── QDialogButtonBox (确定 / 取消)
```

---

## 8. 完整交互流程

### 保存流程

```
用户点击「保存到数据库」(logic_txt toolbar)
  │
  ├── 弹出 LogicSaveDialog
  │     ├── 用户填写名称 / 描述 / 标签
  │     └── 点击确定
  │
  ├── LogicConverter.validate(text)  # 二次确认语法正确
  │
  └── LogicDatabase.save(name, text, variable_map, description, tags)
        └── 状态栏: "✓ 已保存: motor_control"
```

### 加载流程

```
用户点击「从数据库加载」(logic_txt toolbar)
  │
  ├── 弹出 LogicLoadDialog
  │     ├── 搜索 / 标签筛选
  │     └── 用户选中记录 → 双击/确定
  │
  ├── LogicDatabase.load(name)
  │     → expression / variable_map / description
  │
  ├── LogicTextWidget.set_text(expression)
  ├── LogicTextWidget.set_variable_map(variable_map)
  │
  └── 弹出确认: "是否同步到图形编辑器？"
        ├── 是 → LogicConverter.parse_text() → LogicDiagramWidget
        └── 否 → 仅显示文本
```
