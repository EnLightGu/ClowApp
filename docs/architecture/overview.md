# EnApp-0.02 整体架构

> **版本：** 0.02（新版架构）｜ **框架：** PyQt5 ｜ **Python：** 3.8+ ｜ **更新：** 2026-04-12

---

## 1. 项目定位

EnApp 是一个**跨平台模块化桌面应用**，采用**自定义无边框窗体 + 可停靠组件（QDockWidget）**架构。核心设计理念是让应用功能以独立 Widget 的形式动态接入中央 Dock 容器，类似 IDE 的工作台模式。

---

## 2. 架构全景图

```
                          main.py (入口)
                              │
                         MainWindow (QMainWindow)
                    ┌───────────────────────────────┐
                    │         ┌─────────────┐        │
                    │         │   Topbar    │        │  ← 自定义标题栏（最小化/最大/关闭 + 拖拽）
                    │         └─────────────┘        │
                    │  ┌──────┬──────────────┬──────┐│
                    │  │ Left │   Center     │Right ││
                    │  │Side  │  Widget      │Side  ││  ← 左右侧栏为固定宽度工具栏
                    │  │ bar  │  Manage      │ bar  ││
                    │  │(80px)│ (Dock容器)   │(80px)││
                    │  │      │  ┌────────┐  │      ││
                    │  │ ①→②  │  │Dock A  │  │ ③→④  ││  ← Dock 可拖拽、可浮动
                    │  │      │  │Dock B  │  │      ││
                    │  └──────┴────┬───────┴──┬───┘│
                    │              │           │     │
                    └──────────────┴───────────┴─────┘
                        Linux: FramelessWindowHint
                        Windows: Win32 API 去标题栏
```

---

## 3. 核心架构原则

| 原则 | 说明 |
|------|------|
| **UI 与逻辑分离** | 布局由 Qt Designer（`.ui` 文件）定义，业务逻辑在 `.py` 中实现 |
| **组件化** | 每个 Widget 独立封装类，通过组合方式集成到主窗口 |
| **可停靠架构** | 中央区域作为 Dock 容器，支持动态添加/移除/隐藏子窗口 |
| **跨平台适配** | 通过 `platform.system()` 差异化处理 Windows 与 Linux 窗口样式 |

---

## 4. 模块层次结构

```
EnApp-0.02/
├── 入口层
│   └── main.py                    # QApplication 初始化，创建主窗口
│
├── 主窗口层
│   ├── MainWindow.py              # 窗口管理 + 跨平台去标题栏 + 子模块组装
│   └── MainWindow.ui              # 四分区布局（顶栏/左栏/中栏/右栏）
│
├── 组件层 (Widgets/)
│   ├── Sidebars/                  # 顶栏 + 左栏 + 右栏
│   │   ├── Topbar.py              # 自定义标题栏
│   │   ├── LeftSidebar.py         # 左侧工具栏（触发 Dock 开关）
│   │   └── RightSidebar.py        # 右侧工具栏（预留）
│   │
│   ├── CenterWidget/              # 中央 Dock 容器
│   │   └── CenterWidgetManage.py  # QMainWindow 内嵌，Dock 注册/查找/切换
│   │
│   ├── LeftWidget/                # 左侧组件
│   │   └── FileManage.py          # 文件浏览器（作为 Dock Widget 接入）
│   │
│   ├── RightWidget/               # (预留)
│   └── BottomWidget/              # (预留)
│
└── 构建层
    ├── build_exe.py               # PyInstaller 打包脚本
    └── MainApp.spec               # 打包配置
```

---

## 5. 核心交互流程

### 5.1 应用启动

```
main()
  │
  └── MainWindow()
        ├── uic.loadUi("MainWindow.ui")     # 加载四分区布局
        ├── hide_title_bar()                 # 跨平台移除原生标题栏
        │
        ├── _init_topbar()                   # 初始化自定义标题栏
        ├── _init_sidebars()                 # 初始化左右侧栏
        └── _init_center_widget()            # 初始化中央 Dock 容器
              └── CenterWidgetManage(self)
                    └── addWidget → main_content_widget
```

### 5.2 Dock 动态开关

```
用户点击左侧栏按钮
  │
  └── LeftSidebar._on_button1_clicked()
        │
        ├── get_custom_dock("file_manage")
        │
        ├── [不存在] → 创建 FileManage
        │            → add_custom_widget() 注册到 Dock 容器
        │
        └── [已存在] → toggle_custom_dock() 切换可见性
```

---

## 6. 跨平台方案

| 平台 | 去标题栏方式 | 保留功能 |
|------|-------------|----------|
| **Linux** | `Qt.FramelessWindowHint` | 无（靠 Topbar 实现） |
| **Windows** | Win32 API: `SetWindowLongPtrW` + `SetWindowPos` | 缩放边框、最小/最大按钮、系统菜单 |

---

## 7. 构建部署

- **运行时：** `python main.py`
- **打包：** `python build_exe.py` → 产出一个 `THEEXE/MainApp.exe` 单文件
- **工具链：** PyInstaller `--onefile --windowed`

---

## 8. 扩展点

| 扩展方向 | 操作方式 |
|----------|----------|
| 新增 Dock Widget | 在 `Widgets/` 下创建新组件，通过侧边栏按钮调用 `add_custom_widget()` |
| 新增侧边栏按钮 | 编辑对应 `.ui` 文件 + `.py` 绑定信号 |
| 状态持久化 | 使用 `QMainWindow.saveState()` / `restoreState()` |
| 国际化 | 引入 `QTranslator` |
