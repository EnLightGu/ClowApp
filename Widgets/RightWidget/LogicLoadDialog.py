"""
LogicLoadDialog — 从数据库加载逻辑表达式对话框

支持搜索、标签筛选、双击选择。
返回选中的表达式记录数据。
"""

import os

from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QTableWidgetItem, QHeaderView, QAbstractItemView
)


class LogicLoadDialog(QDialog):
    """从数据库加载逻辑表达式对话框"""

    # 表格列索引
    COL_NAME = 0
    COL_DESC = 1
    COL_TAGS = 2
    COL_UPDATED = 3

    def __init__(self, db, parent=None):
        """
        Args:
            db: LogicDatabase 实例
            parent: 父窗口
        """
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), "LogicLoadDialog.ui")
        uic.loadUi(ui_path, self)

        self._db = db
        self._selected_data = None

        # 窗口属性
        self.setWindowTitle("从数据库加载")
        self.setModal(True)

        # 初始化表格
        self._init_table()

        # 连接信号
        self.search_btn.clicked.connect(self._on_search)
        self.search_edit.returnPressed.connect(self._on_search)
        self.tag_filter.currentIndexChanged.connect(self._on_tag_filter_changed)
        self.result_table.cellDoubleClicked.connect(self._on_double_click)
        self.result_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)

        # 加载标签列表
        self._load_tags()

        # 初始加载所有记录
        QTimer.singleShot(0, self._load_all_data)

    def _init_table(self):
        """初始化表格列宽"""
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_DESC, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_TAGS, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_UPDATED, QHeaderView.ResizeToContents)

    def _load_tags(self):
        """从数据库加载所有标签到筛选下拉框"""
        try:
            tags = self._db.get_all_tags()
        except Exception:
            tags = []

        self.tag_filter.clear()
        self.tag_filter.addItem("全部标签", None)  # None = 不筛选
        for tag in tags:
            self.tag_filter.addItem(tag, tag)

    def _load_all_data(self):
        """加载所有表达式记录"""
        try:
            records = self._db.list_all()
        except Exception:
            records = []
        self._populate_table(records)

    def _on_search(self):
        """搜索按钮/回车触发"""
        keyword = self.search_edit.text().strip()
        if not keyword:
            self._load_all_data()
            return
        try:
            records = self._db.search(keyword)
        except Exception:
            records = []
        self._populate_table(records)

    def _on_tag_filter_changed(self, index):
        """标签筛选变更"""
        tag = self.tag_filter.itemData(index)
        keyword = self.search_edit.text().strip()

        try:
            if tag:
                records = self._db.list_all(tag=tag)
            elif keyword:
                records = self._db.search(keyword)
            else:
                records = self._db.list_all()
        except Exception:
            records = []

        self._populate_table(records)

    def _populate_table(self, records: list):
        """填充表格数据"""
        self.result_table.setRowCount(0)  # 清空
        self.result_table.setRowCount(len(records))

        for row, record in enumerate(records):
            # 名称
            name_item = QTableWidgetItem(record.get("name", ""))
            name_item.setData(Qt.UserRole, record)  # 存储完整记录
            self.result_table.setItem(row, self.COL_NAME, name_item)

            # 描述
            desc = record.get("description", "") or ""
            self.result_table.setItem(row, self.COL_DESC, QTableWidgetItem(desc))

            # 标签
            tags = record.get("tags", [])
            tags_text = ", ".join(tags) if tags else ""
            self.result_table.setItem(row, self.COL_TAGS, QTableWidgetItem(tags_text))

            # 更新时间
            updated = record.get("updated_at", "") or ""
            self.result_table.setItem(row, self.COL_UPDATED, QTableWidgetItem(updated))

        # 更新计数
        self.count_label.setText(f"共 {len(records)} 条")

    def _on_double_click(self, row, column):
        """双击行：直接接受"""
        item = self.result_table.item(row, self.COL_NAME)
        if item:
            self._selected_data = item.data(Qt.UserRole)
            self.accept()

    def _on_selection_changed(self):
        """选择变更：记录选中数据"""
        rows = self.result_table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            item = self.result_table.item(row, self.COL_NAME)
            if item:
                self._selected_data = item.data(Qt.UserRole)
        else:
            self._selected_data = None

    def _on_accept(self):
        """确定按钮：确保有选中项"""
        if self._selected_data is None:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "选择错误", "请先选择一条表达式记录！")
            return
        self.accept()

    def get_selected(self) -> Optional[dict]:
        """
        获取用户选中的表达式记录

        Returns:
            dict | None: 选中记录的完整数据，未选择时返回 None

            返回格式:
            {
                "id": int,
                "name": str,
                "expression": str,
                "variable_map": dict,
                "description": str,
                "tags": list[str],
                "created_at": str,
                "updated_at": str
            }
        """
        return self._selected_data
