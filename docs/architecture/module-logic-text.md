# 文本逻辑编辑器：LogicTextWidget + LogicConverter

**文件位置：**
- `Widgets/RightWidget/LogicTextWidget.py` + `LogicTextWidget.ui` — 界面
- `Widgets/RightWidget/LogicConverter.py` — 双向转化器（无 UI，纯逻辑）

**类声明：**
- `class LogicTextWidget(QWidget)`
- `class LogicConverter`（静态工具类）

**父容器：** `logic_text_dock`（QDockWidget）
**控制按钮：** `RightSidebar.button3`（tooltip="文本逻辑"）

---

## 1. UI 布局（`LogicTextWidget.ui`）

```
LogicTextWidget (QWidget, 背景 #252526)
└── QVBoxLayout (间距 0, 边距 0)
    ├── toolbar (QToolBar, 高 36px, 背景 #333333)
    │   ├── QToolButton — 语法检查 (QStyle.SP_MessageBoxQuestion)
    │   ├── QToolButton — 格式化 (QStyle.SP_FileDialogContentsView)
    │   ├── separator
    │   ├── QToolButton — 从图形导入 (QStyle.SP_ArrowBack)
    │   ├── QToolButton — 导出到图形 (QStyle.SP_ArrowForward)
    │   ├── separator
    │   ├── QToolButton — 保存到数据库 (QStyle.SP_DialogSaveButton)
    │   ├── QToolButton — 从数据库加载 (QStyle.SP_DialogOpenButton)
    │   └── spacer + status_label (QLabel, #CCCCCC, 右对齐)
    │
    └── QSplitter (Vertical, 背景 #252526, 手柄 #454545)
        ├── [上] QsciScintilla / QPlainTextEdit (背景 #1E1E1E, 前景 #FFFFFF)
        │   ├── 等宽字体 (Consolas / 12pt)
        │   ├── 关键字高亮: AND, OR, NOT, NAND, NOR, XOR (#569CD6)
        │   ├── 变量高亮: [A-Z_][A-Z0-9_]* (#9CDCFE)
        │   ├── 括号匹配 (#FFD700)
        │   ├── 行号 (#888888)
        │   └── 当前行高亮 (#2A2D2E)
        │
        └── [下] QTableWidget (只读, 背景 #252526)
            ├── 列1: 变量名 (#FFFFFF)
            ├── 列2: 数据类型 (#CCCCCC)
            ├── 用户可编辑修改
            └── 示例:
                  A → bool
                  B → bool
                  result → bool
```

> UI 文件定义布局和默认样式，具体颜色通过 `setStyleSheet` 在代码中统一设置。
>
> **图标来源策略：** 所有工具栏按钮**优先使用 `QStyle.StandardPixmap` 内置图标**，
> 无需为每个按钮准备独立的自定义图标文件。
> 各按钮与 `QStyle.StandardPixmap` 的映射见第 6 节补充说明。
> 自定义图标文件（如有）存放在 `Widgets/Sidebars/icons/` 目录。

---

## 2. 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `text_editor` | `QsciScintilla \| QPlainTextEdit` | 文本逻辑编辑区 |
| `var_table` | `QTableWidget` | 变量映射表（变量名 ↔ 数据类型） |
| `status_label` | `QLabel` | 状态信息 |
| `converter` | `LogicConverter` | 与 LogicDiagramWidget 的转化桥梁 |

---

## 3. 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `text_changed` | `text: str` | 文本内容变更 |
| `conversion_to_diagram_requested` | `text: str` | 请求将文本转化为图形 |

---

## 4. 公共接口

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_text()` | — | `str` | 获取当前文本编辑区内容 |
| `set_text(text)` | `str` | — | 设置文本编辑区内容 |
| `get_variable_map()` | — | `dict` | 获取变量映射 `{"A": "bool", "B": "int"}` |
| `set_variable_map(mapping)` | `dict` | — | 设置变量映射 |
| `validate_text()` | — | `tuple[bool, str]` | 检查语法，return `(通过, 错误信息)` |
| `format_text()` | — | `str` | 格式化当前文本 |
| `import_from_diagram(text)` | `str` | — | 从图形导入文本（设置 + 更新状态） |
| `clear()` | — | — | 清空文本区和变量表 |

---

## 5. LogicConverter（双向转化器）

**文件位置：** `Widgets/RightWidget/LogicConverter.py`

纯静态工具类，无 UI 依赖。

### 5.1 接口

```python
class LogicConverter:
    """逻辑表达式 ↔ 图形门电路的转化器"""

    @staticmethod
    def to_text(scene_items: dict) -> str:
        """
        从画布项集合生成文本表达式

        Args:
            scene_items: {
                "gates": [LogicGateItem, ...],
                "inputs": [LogicPinItem, ...],
                "outputs": [LogicPinItem, ...],
                "wires": [LogicWireItem, ...]
            }

        Returns:
            字符串形式的逻辑表达式
        """
        ...

    @staticmethod
    def parse_text(text: str) -> dict:
        """
        解析文本表达式为图形数据

        Args:
            text: 逻辑表达式文本

        Returns:
            scene_items dict

        Raises:
            LogicParseError: 语法错误时抛出（含行号/列号）
        """
        ...

    @staticmethod
    def validate(text: str) -> tuple[bool, str]:
        """验证语法，return (True, "") 或 (False, "错误位置")"""
        ...

    @staticmethod
    def format(text: str) -> str:
        """格式化（缩进、换行、对齐）"""
        ...
```

### 5.2 文本逻辑语法

```bnf
<expr>       := <term> ( "OR" <term> )*
<term>       := <factor> ( "AND" <factor> )*
<factor>     := "NOT" <factor>
              | "(" <expr> ")"
              | <variable>
              | <gate_call>

<gate_call>  := <gate_name> "(" <expr> ( "," <expr> )* ")"
<gate_name>  := "AND" | "OR" | "NOT" | "NAND" | "NOR" | "XOR"

<variable>   := [A-Z_][A-Z0-9_]*
```

### 5.3 图形 → 文本 转化流程

```
LogicDiagramWidget.get_scene_data()
  │
  └── LogicConverter.to_text(scene_data)
        │
        ├── 1. 构建有向图 (DAG)
        │     ├── 节点 = 门 + 输入引脚
        │     └── 边 = 连线
        │
        ├── 2. 拓扑排序
        │     └── 从输入引脚 → 输出引脚
        │
        ├── 3. 逐级生成文本
        │     ├── 输入引脚 → 变量名
        │     ├── 门 → gate_call(输入表达式...)
        │     └── 输出引脚 → "result = <表达式>"
        │
        └── 4. 返回完整文本
```

### 5.4 文本 → 图形 转化流程

```
LogicTextWidget.get_text()
  │
  └── LogicConverter.parse_text(text)
        │
        ├── 1. 词法分析 (Lexer)
        │     └── Token: VARIABLE, AND, OR, NOT, LPAREN, RPAREN, ...
        │
        ├── 2. 语法分析 (Parser, 递归下降)
        │     └── AST: VariableNode, NotNode, AndNode, GateCallNode, ...
        │
        ├── 3. AST → 图形布局 (Sugiyama 层级布局)
        │     ├── 输入变量 → 最左侧
        │     ├── AST 节点 → LogicGateItem
        │     ├── 自动计算位置
        │     └── 输出引脚 → 最右侧
        │
        └── 4. 返回 scene_items dict
```

### 5.5 错误处理

```python
class LogicParseError(Exception):
    """逻辑表达式解析错误"""

    def __init__(self, message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(f"第 {line} 行第 {column} 列: {message}")
```

---

## 6. 工具栏信号连接

```python
def _connect_toolbar_signals(self):
    self.toolbar_check_btn.clicked.connect(self._on_validate)
    self.toolbar_format_btn.clicked.connect(self._on_format)
    self.toolbar_from_diagram_btn.clicked.connect(self._on_import_from_diagram)
    self.toolbar_to_diagram_btn.clicked.connect(self._on_export_to_diagram)
    self.toolbar_db_save_btn.clicked.connect(self._on_save_to_db)
    self.toolbar_db_load_btn.clicked.connect(self._on_load_from_db)
```

---

## 6.1 Toolbar 图标映射（QStyle.StandardPixmap）

所有工具栏按钮使用 Qt 内置标准图标，零文件依赖：

| 按钮 | QStyle.StandardPixmap 常量 | 说明 |
|------|---------------------------|------|
| 语法检查 | `QStyle.SP_MessageBoxQuestion` | 问号图标表示检查 |
| 格式化 | `QStyle.SP_FileDialogContentsView` | 列表视图图标表示格式化 |
| 从图形导入 | `QStyle.SP_ArrowBack` | 后退箭头表示导入 |
| 导出到图形 | `QStyle.SP_ArrowForward` | 前进箭头表示导出 |
| 保存到数据库 | `QStyle.SP_DialogSaveButton` | 标准保存图标 |
| 从数据库加载 | `QStyle.SP_DialogOpenButton` | 标准打开图标 |

> 如需要更精确的图标外观，可备选自定义图标文件存放在 `Widgets/Sidebars/icons/` 目录。

---

## 7. 语法检查着色

```python
def _on_validate(self):
    text = self.get_text()
    valid, error = LogicConverter.validate(text)
    if valid:
        self.status_label.setText("✓ 语法正确")
        self.status_label.setStyleSheet("color: #4EC9B0;")
    else:
        self.status_label.setText(f"✗ {error}")
        self.status_label.setStyleSheet("color: #F44747;")
```

---

## 8. 双向同步管理

```
用户修改文本 (logic_txt)
  │
  └── 文本变更信号 (500ms 防抖)
        │
        ├── LogicConverter.validate()
        │     ├── 语法错误 → 停止
        │     └── 正确 → LogicConverter.parse_text()
        │           └── 推送到 LogicDiagramWidget
        │
        └── 标记: "文本→图形" (避免循环同步)
```

> **防循环机制：** 双向同步使用 `_is_syncing` 标志位防止循环触发。
> 图形→文本 的自动转化不触发 文本→图形 的自动转化，反之亦然。
> 用户可通过工具栏按钮显式同步。

### 防循环实现

```python
class LogicTextWidget(QWidget):
    def __init__(self):
        self._is_syncing = False
        # ... 其他初始化 ...

    def _on_text_changed(self):
        """文本内容变更回调——文本→图形"""
        if self._is_syncing:
            return
        self._is_syncing = True
        try:
            text = self.get_text()
            valid, error = LogicConverter.validate(text)
            if valid:
                # 推送到 LogicDiagramWidget
                scene_items = LogicConverter.parse_text(text)
                # ... 更新图形画布 ...
        except Exception:
            pass
        finally:
            self._is_syncing = False

    def import_from_diagram(self, text: str):
        """从图形导入——图形→文本，不触发反向同步"""
        if self._is_syncing:
            return
        self._is_syncing = True
        try:
            self.set_text(text)
            self.status_label.setText("✓ 已从图形导入")
            self.status_label.setStyleSheet("color: #4EC9B0;")
        finally:
            self._is_syncing = False
```

> 同样地，`LogicDiagramWidget` 也需要在 `from_logic_text()` 中设置相同的标志位。
> 建议将 `_is_syncing` 抽象为组件级共享状态，或通过 MainWindow 的信号桥接集中控制。
