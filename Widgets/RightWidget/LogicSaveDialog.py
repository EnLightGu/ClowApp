"""
LogicSaveDialog — 保存逻辑表达式对话框

将当前逻辑表达式保存到数据库。
用户输入名称、描述、标签后，返回结构化的保存数据。
"""

import os

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QDialogButtonBox


class LogicSaveDialog(QDialog):
    """保存逻辑表达式对话框"""

    def __init__(self, parent=None, name_hint: str = ""):
        """
        Args:
            parent: 父窗口
            name_hint: 名称输入框的初始建议值
        """
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), "LogicSaveDialog.ui")
        uic.loadUi(ui_path, self)

        # 窗口属性
        self.setWindowTitle("保存逻辑表达式")
        self.setModal(True)

        # 如果提供了名称提示，自动填入
        if name_hint:
            self.name_edit.setText(name_hint)

        # 连接信号
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)

    def _on_accept(self):
        """确定按钮点击：验证名称不为空"""
        name = self.name_edit.text().strip()
        if not name:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "输入错误", "逻辑名称不能为空！")
            return
        self.accept()

    def get_data(self) -> dict:
        """
        获取用户输入的保存数据

        Returns:
            dict: {
                "name": str,         # 逻辑名称
                "description": str,  # 描述
                "tags": list[str]    # 标签列表
            }
        """
        name = self.name_edit.text().strip()
        description = self.desc_edit.text().strip()
        tags_raw = self.tags_edit.text().strip()

        # 解析逗号分隔标签，过滤空白
        tags = []
        if tags_raw:
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        return {
            "name": name,
            "description": description,
            "tags": tags,
        }
