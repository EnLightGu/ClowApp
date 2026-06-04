# 入口层：main.py

**文件位置：** `main.py`

---

## 1. 职责

应用启动入口，初始化 QApplication 并创建主窗口。

## 2. 代码

```python
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Qt Dock Widgets Application - New Architecture")
    app.setOrganizationName("MyCompany")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

## 3. 初始化顺序

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | `QApplication(sys.argv)` | 创建 GUI 应用上下文 |
| 2 | `setApplicationName()` | 设置应用名 |
| 3 | `setOrganizationName()` | 设置组织名 |
| 4 | `MainWindow()` | 实例化主窗口（内部递归初始化所有子模块） |
| 5 | `window.show()` | 显示窗口 |
| 6 | `app.exec_()` | 进入 Qt 事件循环 |
