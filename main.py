#!/usr/bin/env python3
"""
主程序入口 - 新版架构
"""
import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow


def main():
    """应用程序主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("Qt Dock Widgets Application - New Architecture")
    app.setOrganizationName("MyCompany")

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()