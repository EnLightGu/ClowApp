# 逻辑门图形编辑器：LogicDiagramWidget

**文件位置：** `Widgets/RightWidget/LogicDiagramWidget.py` + `LogicDiagramWidget.ui`

**类声明：** `class LogicDiagramWidget(QWidget)`

**父容器：** `logic_diagram_dock`（QDockWidget）
**控制按钮：** `RightSidebar.button2`（tooltip="逻辑门编辑器"）

---

## 1. UI 布局（`LogicDiagramWidget.ui`）

```
LogicDiagramWidget (QWidget, 背景 #252526)
└── QVBoxLayout (间距 0, 边距 0)
    ├── toolbar (QToolBar, 高 36px, 背景 #333333)
    │   ├── QToolButton — 添加 AND 门 (文字标签 "AND")
    │   ├── QToolButton — 添加 OR 门 (文字标签 "OR")
    │   ├── QToolButton — 添加 NOT 门 (文字标签 "NOT")
    │   ├── QToolButton — 添加 NAND 门 (文字标签 "NAND")
    │   ├── QToolButton — 添加 NOR 门 (文字标签 "NOR")
    │   ├── QToolButton — 添加 XOR 门 (文字标签 "XOR")
    │   ├── separator
    │   ├── QToolButton — 添加输入引脚 (QStyle.SP_ArrowRight)
    │   ├── QToolButton — 添加输出引脚 (QStyle.SP_ArrowLeft)
    │   ├── separator
    │   ├── QToolButton — 连线模式 (QStyle.SP_ArrowForward)
    │   ├── QToolButton — 选中模式 (QStyle.SP_FileDialogDetailedView)
    │   ├── separator
    │   ├── QToolButton — 清除全部 (QStyle.SP_DialogCloseButton)
    │   └── QToolButton — 导出为文本 (QStyle.SP_FileIcon)
    │
    └── gate_canvas (QGraphicsView, 背景 #1E1E1E)
          └── QGraphicsScene (画布)
```

> UI 文件定义静态布局，业务逻辑全部在 `.py` 中实现。
>
> **图标来源策略：** 逻辑门按钮（AND/OR/NOT/NAND/NOR/XOR）使用**文字标签**方案（见第 9 节），
> 非门按钮**优先使用 `QStyle.StandardPixmap` 内置图标**。
> 整体无需为每个按钮准备独立的自定义图标文件。
> 自定义图标文件（如有）存放在 `Widgets/Sidebars/icons/` 目录，
> 见 [`module-build.md`](module-build.md) 数据文件清单。

### 统一颜色映射

| UI 元素 | 色值 | 说明 |
|---------|------|------|
| 工具栏背景 | `#333333` | 中灰色 |
| 工具栏按钮 | `#3C3C3C` / `#454545` (hover) | 浅灰渐变 |
| 工具栏文字 | `#FFFFFF` | 白色 |
| 画布背景 | `#1E1E1E` | 最深灰 |
| 逻辑门填充 | `#2D4A7A` | 深蓝灰 |
| 逻辑门边框 | `#4A8BC2` | 蓝灰 |
| 门内符号 | `#FFFFFF` | 白色 |
| 输入引脚 | `#4EC9B0` | 青色 |
| 输出引脚 | `#CE9178` | 橙色 |
| 连线默认 | `#DCDCAA` | 米白 |
| 连线选中 | `#FFD700` | 金色 |
| 画布网格 | `#2D2D2D` | 极浅灰点 |

---

## 2. 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `scene` | `QGraphicsScene` | 画布场景 |
| `view` | `QGraphicsView` | 画布视图 |
| `gates` | `list[LogicGateItem]` | 当前画布上的所有逻辑门 |
| `inputs` | `list[LogicPinItem]` | 所有输入引脚 |
| `outputs` | `list[LogicPinItem]` | 所有输出引脚 |
| `wires` | `list[LogicWireItem]` | 所有连线 |
| `wire_mode` | `bool` | 是否处于连线模式 |
| `current_wire` | `LogicWireItem \| None` | 正在绘制的连线 |

---

## 3. 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `diagram_changed` | — | 画布内容发生变更（添加/删除门、连线等） |
| `conversion_to_text_requested` | `text: str` | 请求将当前图形转化为文本逻辑 |

---

## 4. 公共接口

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `to_logic_text()` | — | `str` | 将当前图形逻辑转化为文本逻辑表达式 |
| `from_logic_text(text)` | `str` | `bool` | 从文本逻辑表达式重建图形 |
| `clear_all()` | — | — | 清空画布所有内容 |
| `export_image(path)` | `str` | `bool` | 导出画布为 PNG 图片 |
| `add_gate(gate_type)` | `str` | `LogicGateItem` | 添加指定类型的逻辑门到画布 |
| `add_input_pin(label)` | `str` | `LogicPinItem` | 添加输入引脚 |
| `add_output_pin(label)` | `str` | `LogicPinItem` | 添加输出引脚 |
| `get_scene_data()` | — | `dict` | 获取画布完整数据结构，供 LogicConverter 使用 |

---

## 5. 内部类设计

### 5.1 LogicGateItem

```python
class LogicGateItem(QGraphicsItem):
    """逻辑门图形项"""

    GATE_TYPES = {
        "AND":  {"inputs": 2, "outputs": 1, "symbol": "&"},
        "OR":   {"inputs": 2, "outputs": 1, "symbol": "≥1"},
        "NOT":  {"inputs": 1, "outputs": 1, "symbol": "1"},
        "NAND": {"inputs": 2, "outputs": 1, "symbol": "&○"},
        "NOR":  {"inputs": 2, "outputs": 1, "symbol": "≥1○"},
        "XOR":  {"inputs": 2, "outputs": 1, "symbol": "=1"},
    }

    def __init__(self, gate_type: str, parent=None):
        self.gate_type = gate_type
        self.input_pins: list[LogicPinItem] = []
        self.output_pins: list[LogicPinItem] = []
        self._init_pins()
        super().__init__(parent)

    def paint(self, painter, option, widget):
        """绘制 ANSI/IEEE 标准逻辑门形状"""
        # 使用统一颜色方案: 填充 #2D4A7A, 边框 #4A8BC2, 文字 #FFFFFF
        ...
```

### 5.2 LogicPinItem

```python
class LogicPinItem(QGraphicsItem):
    """引脚（输入/输出端子）"""

    PIN_TYPES = {"INPUT": 0, "OUTPUT": 1}

    def __init__(self, pin_type: str, label: str = "", parent=None):
        self.pin_type = pin_type  # "INPUT" / "OUTPUT"
        self.label = label
        self.connections: list[LogicWireItem] = []
        super().__init__(parent)
```

### 5.3 LogicWireItem

```python
class LogicWireItem(QGraphicsItem):
    """连线"""

    def __init__(self, source_pin: LogicPinItem, target_pin: LogicPinItem, parent=None):
        self.source_pin = source_pin
        self.target_pin = target_pin
        self._path = QPainterPath()
        self._update_path()
        super().__init__(parent)
```

---

## 6. 交互规则

| 操作 | 行为 |
|------|------|
| 点击工具栏门按钮 | 在画布中心创建对应类型的 `LogicGateItem` |
| 点击工具栏引脚按钮 | 在画布左上角创建对应类型的 `LogicPinItem` |
| 拖拽选中 | 移动门/引脚位置，连线自动跟随 |
| 连线模式：点击引脚 A → 点击引脚 B | 创建 `LogicWireItem` |
| 选中项 + `Delete` 键 | 删除选中的门/引脚/连线 |
| 双击输入引脚标签 | 弹出 `QInputDialog`，修改变量名 |
| 右键菜单 | 「删除」「重命名」「属性」 |

---

## 7. 画布网格

画布背景以 20px 间距绘制网格线，辅助对齐：

```
painter.setPen(QPen(QColor("#2D2D2D"), 1))
for x in range(0, width, 20):
    painter.drawLine(x, 0, x, height)
for y in range(0, height, 20):
    painter.drawLine(0, y, width, y)
```

---

## 8. 初始化流程

```
__init__()
  ├── uic.loadUi("LogicDiagramWidget.ui")     # 加载 UI 布局
  ├── 初始化 scene: QGraphicsScene()
  ├── 设置 view: QGraphicsView(scene)
  │     ├── setRenderHints(抗锯齿)
  │     ├── setDragMode(RubberBandDrag)
  │     └── setBackgroundBrush(QColor("#1E1E1E"))
  │
  ├── 初始化数据
  │     ├── gates = []
  │     ├── inputs = []
  │     ├── outputs = []
  │     ├── wires = []
  │     └── wire_mode = False
  │
  └── _connect_toolbar_signals()
```

---

## 9. Toolbar 图标映射（QStyle.StandardPixmap）

所有工具栏按钮使用 Qt 内置标准图标，零文件依赖：

| 按钮 | 显示方式 | 说明 |
|------|----------|------|
| AND / OR / NOT / NAND / NOR / XOR 门 | **文字标签** `setText("AND")` 等 + `ToolButtonTextOnly` | 按钮上直接显示门名称，用户无需悬停即可区分 |
| 输入引脚 | `QStyle.SP_ArrowRight` | 右箭头表示输入方向 |
| 输出引脚 | `QStyle.SP_ArrowLeft` | 左箭头表示输出方向 |
| 连线模式 | `QStyle.SP_ArrowForward` | 前箭头表示连线连接 |
| 选中模式 | `QStyle.SP_FileDialogDetailedView` | 列表/选中图标 |
| 清除全部 | `QStyle.SP_DialogCloseButton` | 标准关闭叉号 |
| 导出为文本 | `QStyle.SP_FileIcon` | 文件图标表示导出 |

> **门按钮文字标签实现说明：** 6 个门按钮使用 `QToolButton.setText("AND")` 等方法设置文字，
> 配合 `setToolButtonStyle(Qt.ToolButtonTextOnly)` 使按钮仅显示文字标签。
> 可通过样式表设置背景色（如 `#3C3C3C`）和边框微样式以增强可读性。
> 非门按钮（引脚、连线、选中、清除、导出）继续使用 `QStyle.StandardPixmap` 图标。

> 如需要更精确的图标外观，可备选自定义图标文件存放在 `Widgets/Sidebars/icons/` 目录，
> 并更新 [`module-build.md`](module-build.md) 的数据文件清单。

```python
def _connect_toolbar_signals(self):
    self.toolbar_and_btn.clicked.connect(lambda: self.add_gate("AND"))
    self.toolbar_or_btn.clicked.connect(lambda: self.add_gate("OR"))
    self.toolbar_not_btn.clicked.connect(lambda: self.add_gate("NOT"))
    self.toolbar_nand_btn.clicked.connect(lambda: self.add_gate("NAND"))
    self.toolbar_nor_btn.clicked.connect(lambda: self.add_gate("NOR"))
    self.toolbar_xor_btn.clicked.connect(lambda: self.add_gate("XOR"))
    self.toolbar_input_btn.clicked.connect(lambda: self.add_input_pin(""))
    self.toolbar_output_btn.clicked.connect(lambda: self.add_output_pin(""))
    self.toolbar_wire_btn.clicked.connect(self._toggle_wire_mode)
    self.toolbar_select_btn.clicked.connect(self._toggle_select_mode)
    self.toolbar_clear_btn.clicked.connect(self.clear_all)
    self.toolbar_to_text_btn.clicked.connect(self._on_export_to_text)
```
