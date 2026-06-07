"""
逻辑门图形编辑器

包含：
- LogicDiagramWidget — 编辑器主控件
- LogicGateItem — 逻辑门图形项
- LogicPinItem — 引脚（输入/输出端子）
- LogicWireItem — 连线
"""

from __future__ import annotations

import uuid
import os

from typing import Optional, Any

from PyQt5.QtWidgets import (
    QWidget, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QToolButton, QInputDialog, QMenu, QAction, QMessageBox,
    QStyle, qApp, QDialog, QTableWidget, QTableWidgetItem,
    QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QHeaderView,
)
from PyQt5.QtCore import (
    Qt, QRectF, QPointF, QLineF, QObject, pyqtSignal, QEvent,
)
from PyQt5.QtGui import (
    QPainter, QPainterPath, QPen, QBrush, QColor, QFont,
    QFontMetrics, QPolygonF,
)
from PyQt5 import uic

from Widgets.RightWidget.LogicConverter import LogicConverter

# ════════════════════════════════════════════════════════════════
# 常量
# ════════════════════════════════════════════════════════════════

GATE_WIDTH = 100
GATE_HEIGHT = 60
PIN_RADIUS = 6
PIN_HIT_RADIUS = 10  # 点击热区略大

COLOR_GATE_FILL = QColor("#2D4A7A")
COLOR_GATE_BORDER = QColor("#4A8BC2")
COLOR_GATE_TEXT = QColor("#FFFFFF")
COLOR_INPUT_PIN = QColor("#4EC9B0")
COLOR_OUTPUT_PIN = QColor("#CE9178")
COLOR_WIRE = QColor("#DCDCAA")
COLOR_WIRE_SELECTED = QColor("#FFD700")
COLOR_GRID = QColor("#2D2D2D")
COLOR_CANVAS_BG = QColor("#1E1E1E")

GATE_TYPES = {
    "AND":  {"inputs": 2, "outputs": 1, "symbol": "&"},
    "OR":   {"inputs": 2, "outputs": 1, "symbol": "≥1"},
    "NOT":  {"inputs": 1, "outputs": 1, "symbol": "1"},
    "NAND": {"inputs": 2, "outputs": 1, "symbol": "&○"},
    "NOR":  {"inputs": 2, "outputs": 1, "symbol": "≥1○"},
    "XOR":  {"inputs": 2, "outputs": 1, "symbol": "=1"},
}

_ID_COUNTER = 0


def _next_id(prefix: str = "id") -> str:
    global _ID_COUNTER
    _ID_COUNTER += 1
    return f"{prefix}{_ID_COUNTER}"


# ════════════════════════════════════════════════════════════════
# GridScene — 带网格背景的场景
# ════════════════════════════════════════════════════════════════


class GridScene(QGraphicsScene):
    """带网格线的画布场景"""

    GRID_SPACING = 20

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """绘制网格背景"""
        painter.fillRect(rect, COLOR_CANVAS_BG)
        painter.setPen(QPen(COLOR_GRID, 1))

        left = int(rect.left()) - (int(rect.left()) % self.GRID_SPACING)
        top = int(rect.top()) - (int(rect.top()) % self.GRID_SPACING)

        x = left
        while x < rect.right():
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += self.GRID_SPACING

        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += self.GRID_SPACING


# ════════════════════════════════════════════════════════════════
# LogicPinItem
# ════════════════════════════════════════════════════════════════


class LogicPinItem(QGraphicsItem):
    """引脚（输入/输出端子）"""

    PIN_TYPES = {"INPUT": 0, "OUTPUT": 1}

    def __init__(self, pin_type: str, label: str = "", parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)
        self.pin_id = _next_id("pin")
        self.pin_type = pin_type  # "INPUT" / "OUTPUT"
        self.label = label
        self.connections: list[LogicWireItem] = []
        self._label_visible = bool(label)
        self._var_type = "bool"  # 变量类型: bool / int / float / string

        # 设置为可选择、可发送几何变化
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

        self._hovered = False

    def boundingRect(self) -> QRectF:
        r = PIN_HIT_RADIUS + 2
        if self._label_visible:
            fm = QFontMetrics(QFont("Consolas", 9))
            tw = fm.width(self.label) + 8
            th = fm.height() + 4
            if self.pin_type == "INPUT":
                return QRectF(-r, -r, r + tw, max(r * 2, th))
            else:
                return QRectF(-r - tw, -r, r + tw, max(r * 2, th))
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter: QPainter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)

        color = COLOR_INPUT_PIN if self.pin_type == "INPUT" else COLOR_OUTPUT_PIN
        if self.isSelected():
            painter.setBrush(QBrush(color.lighter(130)))
        else:
            painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(130), 1.5))

        center = QPointF(0, 0)
        painter.drawEllipse(center, PIN_RADIUS, PIN_RADIUS)

        # 绘制标签
        if self._label_visible:
            painter.setFont(QFont("Consolas", 9))
            painter.setPen(QColor("#FFFFFF"))
            if self.pin_type == "INPUT":
                painter.drawText(QPointF(PIN_RADIUS + 4, 4), self.label)
            else:
                fm = QFontMetrics(QFont("Consolas", 9))
                tw = fm.width(self.label)
                painter.drawText(QPointF(-PIN_RADIUS - 4 - tw, 4), self.label)

    @property
    def var_type(self) -> str:
        """获取变量类型"""
        return self._var_type

    @var_type.setter
    def var_type(self, value: str):
        """设置变量类型"""
        if value in ("bool", "int", "float", "string"):
            self._var_type = value

    def _set_label(self, label: str):
        """设置标签并更新可见性"""
        self.label = label
        self._label_visible = bool(label)
        self.prepareGeometryChange()
        self.update()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.ItemPositionHasChanged:
            # 通知关联的连线更新路径
            for wire in self.connections:
                wire.update_path()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        """双击编辑标签"""
        if self.pin_type in ("INPUT", "OUTPUT"):
            new_label, ok = QInputDialog.getText(
                None, "编辑引脚标签", "输入标签:",
                text=self.label
            )
            if ok:
                self._set_label(new_label)
        super().mouseDoubleClickEvent(event)


# ════════════════════════════════════════════════════════════════
# LogicGateItem
# ════════════════════════════════════════════════════════════════


class LogicGateItem(QGraphicsItem):
    """逻辑门图形项"""

    GATE_TYPES = GATE_TYPES

    def __init__(self, gate_type: str, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)
        self.gate_id = _next_id("gate")
        self.gate_type = gate_type.upper()
        self.input_pins: list[LogicPinItem] = []
        self.output_pins: list[LogicPinItem] = []
        self._init_pins()

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

    def _init_pins(self):
        """根据门类型创建输入/输出引脚"""
        info = GATE_TYPES.get(self.gate_type, GATE_TYPES["AND"])
        n_inputs = info["inputs"]
        n_outputs = info["outputs"]

        # 创建输入引脚（左侧）
        for i in range(n_inputs):
            # 计算垂直位置
            if n_inputs == 1:
                y = GATE_HEIGHT / 2
            else:
                y = GATE_HEIGHT * (i + 1) / (n_inputs + 1)
            pin = LogicPinItem("INPUT", parent=self)
            pin.setPos(-PIN_RADIUS - 2, y - GATE_HEIGHT / 2)
            self.input_pins.append(pin)

        # 创建输出引脚（右侧）
        for i in range(n_outputs):
            if n_outputs == 1:
                y = GATE_HEIGHT / 2
            else:
                y = GATE_HEIGHT * (i + 1) / (n_outputs + 1)
            pin = LogicPinItem("OUTPUT", parent=self)
            pin.setPos(GATE_WIDTH + PIN_RADIUS + 2, y - GATE_HEIGHT / 2)
            self.output_pins.append(pin)

    def _rebuild_pins(self):
        """根据当前 gate_type 重建引脚数量（修复重命名后引脚不匹配的问题）"""
        info = GATE_TYPES.get(self.gate_type, GATE_TYPES["AND"])
        n_inputs = info["inputs"]
        n_outputs = info["outputs"]

        # 如果现有引脚数已匹配，无需重建
        if len(self.input_pins) == n_inputs and len(self.output_pins) == n_outputs:
            return

        # 保存旧引脚的连接信息
        old_connections = {}
        for pin in self.input_pins + self.output_pins:
            if pin.connections:
                old_connections[pin.pin_id] = list(pin.connections)

        # 从场景中移除旧引脚
        for pin in self.input_pins + self.output_pins:
            pin.connections.clear()
            scene = pin.scene()
            if scene:
                scene.removeItem(pin)

        self.input_pins.clear()
        self.output_pins.clear()

        # 重新创建引脚
        self._init_pins()

        # 尝试重新连接老连线（仅连接数不变时）
        # 简单起见，旧的连线断开后丢弃

    def boundingRect(self) -> QRectF:
        margin = PIN_RADIUS + 10
        return QRectF(-margin, -margin, GATE_WIDTH + 2 * margin, GATE_HEIGHT + 2 * margin)

    def paint(self, painter: QPainter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)

        fill = COLOR_GATE_FILL
        border = COLOR_GATE_BORDER

        if self.isSelected():
            border = border.lighter(140)

        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(border, 2))

        rect = QRectF(0, 0, GATE_WIDTH, GATE_HEIGHT)
        info = GATE_TYPES.get(self.gate_type, GATE_TYPES["AND"])

        # 根据门类型绘制不同的形状
        if self.gate_type == "AND":
            self._draw_and_shape(painter, rect)
        elif self.gate_type == "OR":
            self._draw_or_shape(painter, rect)
        elif self.gate_type == "NOT":
            self._draw_not_shape(painter, rect)
        elif self.gate_type == "NAND":
            self._draw_and_shape(painter, rect)
            self._draw_inversion_circle(painter, QPointF(GATE_WIDTH, GATE_HEIGHT / 2))
        elif self.gate_type == "NOR":
            self._draw_or_shape(painter, rect)
            self._draw_inversion_circle(painter, QPointF(GATE_WIDTH, GATE_HEIGHT / 2))
        elif self.gate_type == "XOR":
            self._draw_xor_shape(painter, rect)

        # 绘制门内符号
        painter.setFont(QFont("Consolas", 11, QFont.Bold))
        painter.setPen(COLOR_GATE_TEXT)
        symbol = info["symbol"]

        fm_local = QFontMetrics(QFont("Consolas", 11, QFont.Bold))
        tw = fm_local.width(symbol)
        th = fm_local.height()
        tx = max(0, (GATE_WIDTH - tw) / 2)
        ty = max(0, (GATE_HEIGHT + th / 2) / 2)
        painter.drawText(QPointF(tx, ty), symbol)

    def _draw_and_shape(self, painter: QPainter, rect: QRectF):
        """绘制 AND 门形状（左侧直线，右侧半圆）"""
        path = QPainterPath()
        w = rect.width()
        h = rect.height()
        r = h / 2  # 右侧半圆半径
        # 右侧半圆中心
        cx = w - r
        cy = h / 2

        # 起始点：左上
        path.moveTo(0, 0)
        # 上边直线
        path.lineTo(cx, 0)
        # 右侧半圆弧（从顶部到底部）
        path.arcTo(cx - r, 0, h, h, 90, -180)
        # 下边直线
        path.lineTo(0, h)
        path.closeSubpath()
        painter.drawPath(path)

    def _draw_or_shape(self, painter: QPainter, rect: QRectF):
        """绘制 OR 门形状（左侧弧形凹面，右侧尖点）"""
        path = QPainterPath()
        w = rect.width()
        h = rect.height()
        cx = w
        cy = h / 2

        # OR 门由三段贝塞尔曲线构成：
        # 左上凹弧：从 (0,0) 到 (w, h/2)
        path.moveTo(0, 0)
        path.cubicTo(w * 0.3, 0, w * 0.7, h * 0.15, cx, cy)
        # 右下凹弧：从 (w, h/2) 到 (0, h)
        path.cubicTo(w * 0.7, h * 0.85, w * 0.3, h, 0, h)
        # 尾部（底部弧线连接到顶部）
        path.cubicTo(w * 0.1, h * 0.7, w * 0.1, h * 0.3, 0, 0)
        path.closeSubpath()
        painter.drawPath(path)

    def _draw_not_shape(self, painter: QPainter, rect: QRectF):
        """绘制 NOT 门形状（三角形）"""
        w = rect.width()
        h = rect.height()
        triangle = QPolygonF([
            QPointF(0, 0),
            QPointF(w - h / 2, h / 2),
            QPointF(0, h),
        ])
        painter.drawPolygon(triangle)
        # 输出端小圆圈
        self._draw_inversion_circle(painter, QPointF(w - h / 2, h / 2))

    def _draw_xor_shape(self, painter: QPainter, rect: QRectF):
        """绘制 XOR 门形状（OR 加额外左侧弧线）"""
        path = QPainterPath()
        w = rect.width()
        h = rect.height()
        cx = w
        cy = h / 2

        # 主体（同 OR）
        path.moveTo(h * 0.25, 0)
        path.cubicTo(w * 0.3, 0, w * 0.7, h * 0.15, cx, cy)
        path.cubicTo(w * 0.7, h * 0.85, w * 0.3, h, h * 0.25, h)
        path.cubicTo(w * 0.35, h * 0.7, w * 0.35, h * 0.3, h * 0.25, 0)
        path.closeSubpath()
        painter.drawPath(path)

        # 额外的左侧弧线
        extra = QPainterPath()
        extra.moveTo(0, 0)
        extra.cubicTo(h * 0.15, h * 0.3, h * 0.15, h * 0.7, 0, h)
        painter.setPen(QPen(COLOR_GATE_BORDER, 2))
        painter.drawPath(extra)

    def _draw_inversion_circle(self, painter: QPainter, center: QPointF):
        """在指定位置绘制反相小圆圈"""
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(COLOR_GATE_BORDER, 1.5))
        painter.drawEllipse(center, PIN_RADIUS + 1, PIN_RADIUS + 1)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.ItemPositionHasChanged:
            # 引脚是门的子节点，父节点移动时子节点局部坐标不变，
            # 因此 PinItem.itemChange 不会被触发，须在此手动通知所有连线更新路径
            for pin in self.input_pins + self.output_pins:
                for wire in pin.connections:
                    wire.update_path()
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = menu.addAction("删除")
        rename_action = menu.addAction("重命名")
        menu.addSeparator()
        props_action = menu.addAction("属性")

        action = menu.exec(event.screenPos())
        if action == delete_action:
            self._remove_from_scene()
        elif action == rename_action:
            new_name, ok = QInputDialog.getText(
                None, "重命名门", "新名称:",
                text=self.gate_type
            )
            if ok and new_name and new_name.upper() in GATE_TYPES:
                self.gate_type = new_name.upper()
                self._rebuild_pins()
                self.update()
        elif action == props_action:
            QMessageBox.information(None, "门属性",
                                    f"类型: {self.gate_type}\n"
                                    f"ID: {self.gate_id}\n"
                                    f"输入引脚: {len(self.input_pins)}\n"
                                    f"输出引脚: {len(self.output_pins)}")

    def _remove_from_scene(self):
        """从场景中安全移除自身（修复：增加 try/except 保护）"""
        try:
            for pin in self.input_pins + self.output_pins:
                if pin is None:
                    continue
                try:
                    for wire in list(pin.connections):
                        if wire is not None:
                            wire._remove_from_scene()
                except (RuntimeError, Exception):
                    pass
        except (RuntimeError, Exception):
            pass

        try:
            scene = self.scene()
            if scene is not None:
                scene.removeItem(self)
        except (RuntimeError, Exception):
            pass


# ════════════════════════════════════════════════════════════════
# LogicWireItem
# ════════════════════════════════════════════════════════════════


class LogicWireItem(QGraphicsItem):
    """连线（从源引脚到目标引脚的正交折线）"""

    def __init__(self, source_pin: LogicPinItem, target_pin: LogicPinItem,
                 parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)
        self.wire_id = _next_id("wire")
        self.source_pin = source_pin
        self.target_pin = target_pin
        self._path = QPainterPath()

        # 注册到引脚
        source_pin.connections.append(self)
        target_pin.connections.append(self)

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(-1)  # 连线在门下方

        self.update_path()

    def update_path(self):
        """计算并更新正交路径"""
        if not self.source_pin or not self.target_pin:
            return

        p1 = self.source_pin.scenePos()
        p2 = self.target_pin.scenePos()

        path = QPainterPath()
        path.moveTo(p1)

        # 计算出线的方向
        if self.source_pin.pin_type == "OUTPUT":
            # 源是输出，向右出线
            dx1 = 40
        else:
            dx1 = -40

        if self.target_pin.pin_type == "INPUT":
            dx2 = -40
        else:
            dx2 = 40

        # 正交折线路径
        mid_x = (p1.x() + dx1 + p2.x() + dx2) / 2

        path.lineTo(p1.x() + dx1, p1.y())
        path.lineTo(mid_x, p1.y())
        path.lineTo(mid_x, p2.y())
        path.lineTo(p2.x() + dx2, p2.y())
        path.lineTo(p2)

        self.prepareGeometryChange()
        self._path = path
        self.update()

    def boundingRect(self) -> QRectF:
        return self._path.boundingRect().adjusted(-5, -5, 5, 5)

    def paint(self, painter: QPainter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        color = COLOR_WIRE_SELECTED if self.isSelected() else COLOR_WIRE
        painter.setPen(QPen(color, 2.5))
        painter.drawPath(self._path)

    def _remove_from_scene(self):
        """安全移除自身（修复：增加 try/except 保护）"""
        try:
            if self.source_pin is not None:
                try:
                    if self in self.source_pin.connections:
                        self.source_pin.connections.remove(self)
                except (RuntimeError, ValueError):
                    pass
        except RuntimeError:
            pass

        try:
            if self.target_pin is not None:
                try:
                    if self in self.target_pin.connections:
                        self.target_pin.connections.remove(self)
                except (RuntimeError, ValueError):
                    pass
        except RuntimeError:
            pass

        try:
            scene = self.scene()
            if scene is not None:
                scene.removeItem(self)
        except (RuntimeError, Exception):
            pass


# ════════════════════════════════════════════════════════════════
# VariableManagerDialog — 变量管理对话框
# ════════════════════════════════════════════════════════════════

VALID_VAR_TYPES = ("bool", "int", "float", "string")


class VariableManagerDialog(QDialog):
    """变量管理对话框：管理独立输入/输出引脚"""

    def __init__(self, inputs, outputs, logic_diagram, parent=None):
        super().__init__(parent)
        self.inputs = inputs
        self.outputs = outputs
        self.logic_diagram = logic_diagram

        self.setWindowTitle("变量管理")
        self.setMinimumSize(480, 360)
        self.setStyleSheet(
            "background-color: #2B2B2B; color: #CCCCCC;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 说明标签
        label = QLabel("独立引脚（输入/输出变量）列表：")
        label.setStyleSheet("color: #FFFFFF; font-size: 13px;")
        layout.addWidget(label)

        # 表格控件
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["名称", "类型", "方向"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setStyleSheet(
            "QTableWidget { background-color: #1E1E1E; border: 1px solid #3C3C3C; "
            "gridline-color: #3C3C3C; }"
            "QTableWidget::item { padding: 4px 6px; }"
            "QTableWidget::item:selected { background-color: #264F78; }"
            "QHeaderView::section { background-color: #333333; color: #FFFFFF; "
            "border: 1px solid #3C3C3C; padding: 4px; }"
        )
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        self.table.itemDoubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        btn_style = (
            "QPushButton { background-color: #3C3C3C; color: #FFFFFF; "
            "border: 1px solid #454545; border-radius: 3px; "
            "padding: 5px 12px; }"
            "QPushButton:hover { background-color: #4A4A4A; }"
            "QPushButton:pressed { background-color: #2D2D2D; }"
        )

        self.btn_add_input = QPushButton("新增输入变量")
        self.btn_add_input.setStyleSheet(btn_style)
        self.btn_add_input.clicked.connect(lambda: self._add_variable("INPUT"))

        self.btn_add_output = QPushButton("新增输出变量")
        self.btn_add_output.setStyleSheet(btn_style)
        self.btn_add_output.clicked.connect(lambda: self._add_variable("OUTPUT"))

        self.btn_delete = QPushButton("删除")
        self.btn_delete.setStyleSheet(btn_style)
        self.btn_delete.clicked.connect(self._delete_selected)

        self.btn_rename = QPushButton("重命名")
        self.btn_rename.setStyleSheet(btn_style)
        self.btn_rename.clicked.connect(self._rename_selected)

        btn_layout.addWidget(self.btn_add_input)
        btn_layout.addWidget(self.btn_add_output)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_rename)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        self._refresh_table()

    # ── 内部辅助 ──

    def _get_all_pins(self):
        """返回所有独立引脚的 (pin, direction) 列表"""
        pins = []
        for pin in self.inputs:
            pins.append((pin, "INPUT"))
        for pin in self.outputs:
            pins.append((pin, "OUTPUT"))
        return pins

    def _get_selected_pin(self):
        """获取当前选中行对应的引脚"""
        row = self.table.currentRow()
        if row < 0:
            return None, None
        pins = self._get_all_pins()
        if row < len(pins):
            return pins[row]
        return None, None

    def _refresh_table(self):
        """刷新表格内容"""
        self.table.setRowCount(0)
        pins = self._get_all_pins()
        self.table.setRowCount(len(pins))

        for i, (pin, direction) in enumerate(pins):
            name_item = QTableWidgetItem(pin.label or "(未命名)")
            type_item = QTableWidgetItem(getattr(pin, '_var_type', 'bool'))
            dir_item = QTableWidgetItem("输入" if direction == "INPUT" else "输出")
            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, type_item)
            self.table.setItem(i, 2, dir_item)

    # ── 交互操作 ──

    def _add_variable(self, direction: str):
        """新增变量（INPUT 或 OUTPUT）"""
        name, ok = QInputDialog.getText(
            self, "新增变量",
            f"输入{'输入' if direction == 'INPUT' else '输出'}变量名:"
        )
        if ok and name:
            if direction == "INPUT":
                self.logic_diagram.add_input_pin(name, "bool")
            else:
                self.logic_diagram.add_output_pin(name, "bool")
            self._refresh_table()

    def _delete_selected(self):
        """删除选中的变量"""
        pin, direction = self._get_selected_pin()
        if pin is None:
            QMessageBox.warning(self, "提示", "请先选择一个变量")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除变量 \"{pin.label or '(未命名)'}\" 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.logic_diagram._remove_variable(pin, direction)
        self._refresh_table()

    def _rename_selected(self):
        """重命名选中的变量"""
        pin, direction = self._get_selected_pin()
        if pin is None:
            QMessageBox.warning(self, "提示", "请先选择一个变量")
            return

        new_name, ok = QInputDialog.getText(
            self, "重命名变量", "新名称:",
            text=pin.label
        )
        if ok:
            pin._set_label(new_name)
            self._refresh_table()
            self.logic_diagram._emit_changed()

    def _change_type(self, new_type: str):
        """修改选中变量的类型"""
        pin, direction = self._get_selected_pin()
        if pin is None:
            return

        if new_type not in VALID_VAR_TYPES:
            return

        pin.var_type = new_type
        self._refresh_table()
        self.logic_diagram._emit_changed()

    def _on_double_click(self, item: QTableWidgetItem):
        """双击重命名"""
        if item.column() == 0:  # 名称列
            self._rename_selected()

    def _on_context_menu(self, pos):
        """右键菜单"""
        item = self.table.itemAt(pos)
        if item is None:
            return
        self.table.selectRow(item.row())

        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background-color: #2B2B2B; color: #CCCCCC; border: 1px solid #454545; }"
            "QMenu::item { padding: 5px 30px 5px 20px; }"
            "QMenu::item:selected { background-color: #264F78; }"
        )

        rename_action = menu.addAction("重命名")
        delete_action = menu.addAction("删除")

        menu.addSeparator()

        # 类型切换子菜单
        type_menu = menu.addMenu("修改类型")
        current_type = "bool"
        pin, _ = self._get_selected_pin()
        if pin is not None:
            current_type = getattr(pin, '_var_type', 'bool')

        for t in VALID_VAR_TYPES:
            type_action = type_menu.addAction(t)
            if t == current_type:
                type_action.setEnabled(False)  # 当前类型不可选
            type_action.triggered.connect(
                lambda checked, vt=t: self._change_type(vt)
            )

        action = menu.exec(self.table.viewport().mapToGlobal(pos))

        if action == rename_action:
            self._rename_selected()
        elif action == delete_action:
            self._delete_selected()


# ════════════════════════════════════════════════════════════════
# LogicDiagramWidget
# ════════════════════════════════════════════════════════════════


class LogicDiagramWidget(QWidget):
    """逻辑门图形编辑器主控件"""

    diagram_changed = pyqtSignal()
    conversion_to_text_requested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        # 加载 UI
        uic.loadUi(os.path.join(os.path.dirname(__file__), "LogicDiagramWidget.ui"), self)

        # 初始化场景
        self.scene = GridScene(self)
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)

        # 配置视图
        self.view = self.findChild(QGraphicsView, "gate_canvas")
        self.view.setScene(self.scene)
        self.view.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # 数据
        self.gates: list[LogicGateItem] = []
        self.inputs: list[LogicPinItem] = []
        self.outputs: list[LogicPinItem] = []
        self.wires: list[LogicWireItem] = []
        self.wire_mode = False
        self.select_mode = True
        self.current_wire: Optional[LogicWireItem] = None
        self._first_pin: Optional[LogicPinItem] = None

        # 挂载场景变化监听
        self.scene.changed.connect(self._on_scene_changed)

        # 设置工具栏按钮图标
        self._setup_toolbar_icons()

        # 连接工具栏信号
        self._connect_toolbar_signals()

        # 安装键盘事件过滤
        self.view.installEventFilter(self)

    # ── 信号发射辅助 ──

    def _emit_changed(self):
        """发射 diagram_changed 信号"""
        self.diagram_changed.emit()

    def _on_scene_changed(self, changes):
        """场景变化回调"""
        self._emit_changed()

    # ── 工具栏图标设置 ──

    def _setup_toolbar_icons(self):
        """为工具栏按钮设置图标"""
        # 门按钮已通过 UI 设置 ToolButtonTextOnly
        # 非门按钮使用 QStyle.StandardPixmap

        # 输入引脚
        btn = self.findChild(QToolButton, "toolbar_input_btn")
        if btn:
            btn.setIcon(qApp.style().standardIcon(QStyle.SP_ArrowRight))
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setToolTip("添加输入引脚")

        btn = self.findChild(QToolButton, "toolbar_output_btn")
        if btn:
            btn.setIcon(qApp.style().standardIcon(QStyle.SP_ArrowLeft))
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setToolTip("添加输出引脚")

        btn = self.findChild(QToolButton, "toolbar_wire_btn")
        if btn:
            btn.setIcon(qApp.style().standardIcon(QStyle.SP_ArrowForward))
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setToolTip("连线模式")
            btn.setCheckable(True)

        btn = self.findChild(QToolButton, "toolbar_select_btn")
        if btn:
            btn.setIcon(qApp.style().standardIcon(QStyle.SP_FileDialogDetailedView))
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setToolTip("选中模式")
            btn.setCheckable(True)
            btn.setChecked(True)

        btn = self.findChild(QToolButton, "toolbar_clear_btn")
        if btn:
            btn.setIcon(qApp.style().standardIcon(QStyle.SP_DialogCloseButton))
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setToolTip("清除全部")

        btn = self.findChild(QToolButton, "toolbar_to_text_btn")
        if btn:
            btn.setIcon(qApp.style().standardIcon(QStyle.SP_FileIcon))
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setToolTip("导出为文本")

        # ★ 程序化添加「变量管理」按钮
        toolbar_widget = self.findChild(QWidget, "toolbar_widget")
        if toolbar_widget:
            toolbar_layout = toolbar_widget.layout()
            if toolbar_layout:
                self._toolbar_var_btn = QToolButton()
                self._toolbar_var_btn.setObjectName("toolbar_var_btn")
                self._toolbar_var_btn.setIcon(qApp.style().standardIcon(QStyle.SP_FileDialogContentsView))
                self._toolbar_var_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
                self._toolbar_var_btn.setToolTip("变量管理")
                self._toolbar_var_btn.setMinimumSize(30, 28)
                self._toolbar_var_btn.setStyleSheet(
                    "color: #FFFFFF; background-color: #3C3C3C; "
                    "border: 1px solid #454545; border-radius: 3px; padding: 2px 4px;"
                )
                self._toolbar_var_btn.clicked.connect(self._open_variable_manager)
                # 在 toolbar_to_text_btn 之后、spacer 之前插入
                to_text_btn = self.findChild(QToolButton, "toolbar_to_text_btn")
                if to_text_btn:
                    idx = toolbar_layout.indexOf(to_text_btn)
                    if idx >= 0:
                        toolbar_layout.insertWidget(idx + 1, self._toolbar_var_btn)
                        return
                # fallback: add at end
                toolbar_layout.addWidget(self._toolbar_var_btn)

    def _connect_toolbar_signals(self):
        """连接所有工具栏按钮的信号"""
        btn = self.findChild(QToolButton, "toolbar_and_btn")
        if btn:
            btn.clicked.connect(lambda: self.add_gate("AND"))

        btn = self.findChild(QToolButton, "toolbar_or_btn")
        if btn:
            btn.clicked.connect(lambda: self.add_gate("OR"))

        btn = self.findChild(QToolButton, "toolbar_not_btn")
        if btn:
            btn.clicked.connect(lambda: self.add_gate("NOT"))

        btn = self.findChild(QToolButton, "toolbar_nand_btn")
        if btn:
            btn.clicked.connect(lambda: self.add_gate("NAND"))

        btn = self.findChild(QToolButton, "toolbar_nor_btn")
        if btn:
            btn.clicked.connect(lambda: self.add_gate("NOR"))

        btn = self.findChild(QToolButton, "toolbar_xor_btn")
        if btn:
            btn.clicked.connect(lambda: self.add_gate("XOR"))

        btn = self.findChild(QToolButton, "toolbar_input_btn")
        if btn:
            btn.clicked.connect(lambda: self.add_input_pin(""))

        btn = self.findChild(QToolButton, "toolbar_output_btn")
        if btn:
            btn.clicked.connect(lambda: self.add_output_pin(""))

        btn = self.findChild(QToolButton, "toolbar_wire_btn")
        if btn:
            btn.clicked.connect(self._toggle_wire_mode)

        btn = self.findChild(QToolButton, "toolbar_select_btn")
        if btn:
            btn.clicked.connect(self._toggle_select_mode)

        btn = self.findChild(QToolButton, "toolbar_clear_btn")
        if btn:
            btn.clicked.connect(self.clear_all)

        btn = self.findChild(QToolButton, "toolbar_to_text_btn")
        if btn:
            btn.clicked.connect(self._on_export_to_text)

        # 安装场景鼠标事件来支持连线模式
        self.scene.installEventFilter(self)

    def eventFilter(self, obj, event):
        """事件过滤器：处理键盘事件和连线模式鼠标点击"""
        # 视图键盘事件
        if obj is self.view and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Delete or key == Qt.Key_Backspace:
                self._delete_selected()
                return True
            elif key == Qt.Key_Escape:
                self._cancel_wire()
                if self.wire_mode:
                    self._toggle_select_mode()
                return True
            return False

        # 连线模式下场景鼠标点击
        if obj is self.scene and self.wire_mode:
            if event.type() == QEvent.GraphicsSceneMousePress:
                me = event
                if me.button() == Qt.LeftButton:
                    self._on_scene_click_for_wire(me.scenePos())
                    return True
        return super().eventFilter(obj, event)

    def _on_scene_click_for_wire(self, scene_pos: QPointF):
        """连线模式下的场景点击处理（修复：增加空指针保护）"""
        try:
            # 查找点击位置下的引脚
            items = self.scene.items(scene_pos)
        except Exception:
            self._cancel_wire()
            return

        clicked_pin = None
        for item in items:
            try:
                if isinstance(item, LogicPinItem) and item.scene() is not None:
                    clicked_pin = item
                    break
            except RuntimeError:
                continue

        if clicked_pin is None:
            self._cancel_wire()
            return

        # ★ 确保引脚还没被删除（scene 检查）
        try:
            if clicked_pin.scene() is None:
                self._cancel_wire()
                return
        except RuntimeError:
            self._cancel_wire()
            return

        if self._first_pin is None:
            self._first_pin = clicked_pin
            try:
                clicked_pin.setSelected(True)
            except RuntimeError:
                self._first_pin = None
        else:
            if clicked_pin != self._first_pin:
                self._create_wire(self._first_pin, clicked_pin)
            try:
                self._first_pin.setSelected(False)
            except RuntimeError:
                pass
            self._first_pin = None

    def _create_wire(self, pin_a: LogicPinItem, pin_b: LogicPinItem):
        """在引脚 A 和引脚 B 之间创建连线（修复：增加空指针和场景检查）"""
        # 安全检查：引脚必须有效且在场景中
        for p in (pin_a, pin_b):
            try:
                if p is None or p.scene() is None:
                    return
            except RuntimeError:
                return

        # 检查是否已存在相同连线
        for wire in list(self.wires):
            try:
                if (wire.source_pin is pin_a and wire.target_pin is pin_b) or \
                   (wire.source_pin is pin_b and wire.target_pin is pin_a):
                    return
            except RuntimeError:
                continue

        # 确定方向：输出→输入
        try:
            if pin_a.pin_type == "OUTPUT" and pin_b.pin_type == "INPUT":
                source, target = pin_a, pin_b
            elif pin_b.pin_type == "OUTPUT" and pin_a.pin_type == "INPUT":
                source, target = pin_b, pin_a
            else:
                source, target = pin_a, pin_b
        except Exception:
            return

        try:
            wire = LogicWireItem(source, target)
            self.scene.addItem(wire)
            self.wires.append(wire)
            self._emit_changed()
        except Exception as e:
            print(f"创建连线失败: {e}")

    def _cancel_wire(self):
        """取消连线操作（修复：增加场景检查）"""
        if self._first_pin:
            try:
                if self._first_pin.scene() is not None:
                    self._first_pin.setSelected(False)
            except RuntimeError:
                pass
            self._first_pin = None

    def _toggle_wire_mode(self):
        """切换连线模式"""
        self.wire_mode = True
        self.select_mode = False
        self.view.setDragMode(QGraphicsView.NoDrag)
        self.view.setCursor(Qt.CrossCursor)

        btn = self.findChild(QToolButton, "toolbar_wire_btn")
        if btn:
            btn.setChecked(True)
        btn_sel = self.findChild(QToolButton, "toolbar_select_btn")
        if btn_sel:
            btn_sel.setChecked(False)

    def _toggle_select_mode(self):
        """切换选中模式"""
        self.wire_mode = False
        self.select_mode = True
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setCursor(Qt.ArrowCursor)
        self._cancel_wire()

        btn = self.findChild(QToolButton, "toolbar_select_btn")
        if btn:
            btn.setChecked(True)
        btn_wire = self.findChild(QToolButton, "toolbar_wire_btn")
        if btn_wire:
            btn_wire.setChecked(False)

    def _delete_selected(self):
        """删除所有选中的项（修复：增强健壮性，防止重复删除）"""
        try:
            selected = self.scene.selectedItems()
        except RuntimeError:
            return
        if not selected:
            return

        removed_set = set()

        for item in list(selected):
            if item is None:
                continue
            try:
                if isinstance(item, LogicWireItem):
                    try:
                        item._remove_from_scene()
                    except RuntimeError:
                        pass
                    if item in self.wires:
                        self.wires.remove(item)
                        removed_set.add(id(item))

                elif isinstance(item, LogicPinItem):
                    if item.parentItem() is None:  # 仅独立引脚
                        for wire in list(item.connections):
                            try:
                                wire._remove_from_scene()
                            except RuntimeError:
                                pass
                            if wire in self.wires:
                                self.wires.remove(wire)
                                removed_set.add(id(wire))
                        if item in self.inputs:
                            self.inputs.remove(item)
                        if item in self.outputs:
                            self.outputs.remove(item)
                        try:
                            self.scene.removeItem(item)
                        except RuntimeError:
                            pass

                elif isinstance(item, LogicGateItem):
                    for pin in item.input_pins + item.output_pins:
                        for wire in list(pin.connections):
                            try:
                                wire._remove_from_scene()
                            except RuntimeError:
                                pass
                            if wire in self.wires:
                                self.wires.remove(wire)
                    if item in self.gates:
                        self.gates.remove(item)
                    try:
                        self.scene.removeItem(item)
                    except RuntimeError:
                        pass

            except (RuntimeError, Exception) as e:
                print(f"删除项时出错: {e}")
                continue

        self._emit_changed()

    # ── 公共接口 ──

    def add_gate(self, gate_type: str) -> LogicGateItem:
        """添加指定类型的逻辑门到画布"""
        gate_type = gate_type.upper()
        if gate_type not in GATE_TYPES:
            gate_type = "AND"

        gate = LogicGateItem(gate_type)
        # 放在画布中心偏移
        view_center = self.view.mapToScene(
            self.view.viewport().width() // 2,
            self.view.viewport().height() // 2
        )
        # 随机偏移避免完全重叠
        import random
        offset_x = random.randint(-50, 50)
        offset_y = random.randint(-50, 50)
        gate.setPos(view_center.x() + offset_x, view_center.y() + offset_y)

        self.scene.addItem(gate)
        self.gates.append(gate)
        self._emit_changed()
        return gate

    def add_input_pin(self, label: str = "", var_type: str = "bool") -> LogicPinItem:
        """添加输入引脚"""
        pin = LogicPinItem("INPUT", label or "")
        pin.var_type = var_type
        pin.setPos(50 + len(self.inputs) * 40, 50 + len(self.inputs) * 40)
        self.scene.addItem(pin)
        self.inputs.append(pin)
        self._emit_changed()
        return pin

    def add_output_pin(self, label: str = "", var_type: str = "bool") -> LogicPinItem:
        """添加输出引脚"""
        pin = LogicPinItem("OUTPUT", label or "")
        pin.var_type = var_type
        pin.setPos(50 + len(self.outputs) * 40, 100 + len(self.outputs) * 40)
        self.scene.addItem(pin)
        self.outputs.append(pin)
        self._emit_changed()
        return pin

    def _remove_variable(self, pin: LogicPinItem, direction: str):
        """删除一个变量（独立引脚）并清理关联连线"""
        try:
            # 清理所有关联的连线
            for wire in list(pin.connections):
                try:
                    wire._remove_from_scene()
                except (RuntimeError, Exception):
                    pass
                if wire in self.wires:
                    self.wires.remove(wire)

            # 从集合中移除引脚
            if direction == "INPUT" and pin in self.inputs:
                self.inputs.remove(pin)
            elif direction == "OUTPUT" and pin in self.outputs:
                self.outputs.remove(pin)

            # 从场景中移除引脚
            try:
                if pin.scene() is not None:
                    self.scene.removeItem(pin)
            except (RuntimeError, Exception):
                pass

            self._emit_changed()
        except (RuntimeError, Exception) as e:
            print(f"删除变量出错: {e}")

    def _open_variable_manager(self):
        """打开变量管理对话框"""
        dialog = VariableManagerDialog(
            self.inputs, self.outputs, self, parent=self
        )
        dialog.exec_()

    def clear_all(self):
        """清空画布所有内容"""
        # 删除所有导线
        for wire in list(self.wires):
            wire._remove_from_scene()
        self.wires.clear()

        # 删除所有引脚（断开关联）
        for pin in list(self.inputs) + list(self.outputs):
            for wire in list(pin.connections):
                if wire in self.wires:
                    self.wires.remove(wire)
            self.scene.removeItem(pin)
        self.inputs.clear()
        self.outputs.clear()

        # 删除所有门
        for gate in list(self.gates):
            for pin in gate.input_pins + gate.output_pins:
                for wire in list(pin.connections):
                    if wire in self.wires:
                        self.wires.remove(wire)
                # 不 removeItem(pin) — pin 是 gate 的子图形，自动删除
            self.scene.removeItem(gate)
        self.gates.clear()

        self._cancel_wire()
        self._emit_changed()

    def get_scene_data(self) -> dict:
        """获取画布完整数据结构，供 LogicConverter 使用"""
        gates_data = []
        for gate in self.gates:
            gates_data.append({
                "id": gate.gate_id,
                "gate_type": gate.gate_type,
                "x": gate.pos().x(),
                "y": gate.pos().y(),
                "input_pins": [
                    {
                        "id": pin.pin_id,
                        "label": pin.label,
                        "pin_id": pin.pin_id,
                    }
                    for pin in gate.input_pins
                ],
                "output_pins": [
                    {
                        "id": pin.pin_id,
                        "label": pin.label,
                        "pin_id": pin.pin_id,
                    }
                    for pin in gate.output_pins
                ],
            })

        inputs_data = []
        for pin in self.inputs:
            inputs_data.append({
                "id": pin.pin_id,
                "label": pin.label,
                "x": pin.scenePos().x(),
                "y": pin.scenePos().y(),
                "pin_id": pin.pin_id,
                "var_type": getattr(pin, '_var_type', 'bool'),
            })

        outputs_data = []
        for pin in self.outputs:
            outputs_data.append({
                "id": pin.pin_id,
                "label": pin.label,
                "x": pin.scenePos().x(),
                "y": pin.scenePos().y(),
                "pin_id": pin.pin_id,
                "var_type": getattr(pin, '_var_type', 'bool'),
            })

        wires_data = []
        for wire in self.wires:
            wires_data.append({
                "id": wire.wire_id,
                "source_pin_id": wire.source_pin.pin_id,
                "target_pin_id": wire.target_pin.pin_id,
            })

        return {
            "gates": gates_data,
            "inputs": inputs_data,
            "outputs": outputs_data,
            "wires": wires_data,
        }

    def to_logic_text(self) -> str:
        """将当前图形逻辑转化为文本逻辑表达式"""
        data = self.get_scene_data()
        return LogicConverter.to_text(data)

    def from_logic_text(self, text: str) -> bool:
        """从文本逻辑表达式重建图形（修复：增加空键保护和异常捕获）"""
        try:
            data = LogicConverter.parse_text(text)
        except Exception as e:
            print(f"解析文本失败: {e}")
            return False

        self.clear_all()

        try:
            # 创建输入引脚
            input_id_map = {}
            for inp in data.get("inputs", []):
                pin = self.add_input_pin(inp.get("label", ""), inp.get("var_type", "bool"))
                pin.setPos(float(inp.get("x", 0)), float(inp.get("y", 0)))
                pin.pin_id = str(inp.get("pin_id", pin.pin_id))
                input_id_map[pin.pin_id] = pin

            # 创建输出引脚
            output_id_map = {}
            for out in data.get("outputs", []):
                pin = self.add_output_pin(out.get("label", ""), out.get("var_type", "bool"))
                pin.setPos(float(out.get("x", 0)), float(out.get("y", 0)))
                pin.pin_id = str(out.get("pin_id", pin.pin_id))
                output_id_map[pin.pin_id] = pin

            # 创建门
            gate_id_map = {}
            for gate_data in data.get("gates", []):
                gate = self.add_gate(gate_data.get("gate_type", "AND"))
                gate.setPos(float(gate_data.get("x", 0)), float(gate_data.get("y", 0)))
                gate.gate_id = str(gate_data.get("id", gate.gate_id))
                gate_id_map[gate.gate_id] = gate

                for i, ip_data in enumerate(gate_data.get("input_pins", [])):
                    if i < len(gate.input_pins):
                        gate.input_pins[i].pin_id = str(ip_data.get("pin_id", gate.input_pins[i].pin_id))
                        gate.input_pins[i]._set_label(ip_data.get("label", ""))

                for i, op_data in enumerate(gate_data.get("output_pins", [])):
                    if i < len(gate.output_pins):
                        gate.output_pins[i].pin_id = str(op_data.get("pin_id", gate.output_pins[i].pin_id))
                        gate.output_pins[i]._set_label(op_data.get("label", ""))

            # 构建所有引脚的完整查找表
            all_pins = {}
            for pin in self.inputs:
                all_pins[pin.pin_id] = pin
            for pin in self.outputs:
                all_pins[pin.pin_id] = pin
            for gate in self.gates:
                for pin in gate.input_pins:
                    all_pins[pin.pin_id] = pin
                for pin in gate.output_pins:
                    all_pins[pin.pin_id] = pin

            # 创建连线
            for wire_data in data.get("wires", []):
                src_pin = all_pins.get(str(wire_data.get("source_pin_id", "")))
                tgt_pin = all_pins.get(str(wire_data.get("target_pin_id", "")))
                if src_pin and tgt_pin:
                    self._create_wire(src_pin, tgt_pin)

        except Exception as e:
            print(f"from_logic_text 出错: {e}")
            import traceback
            traceback.print_exc()
            return False

        self._emit_changed()
        return True

    def _on_export_to_text(self):
        """导出为文本按钮点击处理"""
        text = self.to_logic_text()
        self.conversion_to_text_requested.emit(text)

    def export_image(self, path: str) -> bool:
        """导出画布为 PNG 图片"""
        try:
            rect = self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20)
            image = self.view.grab(self.view.viewport().rect())
            image.save(path, "PNG")
            return True
        except Exception:
            return False
