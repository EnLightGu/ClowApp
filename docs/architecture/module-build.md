# 构建部署：build_exe.py

**文件位置：** `build_exe.py` + `MainApp.spec`

---

## 1. 打包流程

```
build_exe.py main()
  │
  ├── clean_previous_build()
  │     ├── shutil.rmtree("build")
  │     ├── shutil.rmtree("dist")
  │     ├── shutil.rmtree("THEEXE")
  │     └── os.remove(*.spec)
  │
  ├── collect_data_files()
  │     ├── 主图标: icon.ico
  │     ├── UI 文件 (6 个): MainWindow.ui, Topbar.ui, LeftSidebar.ui,
  │     │                   RightSidebar.ui, FileManage.ui, CenterWidgetManage.ui
  │     └── 图标文件 (4 个): icon1.ico ~ icon4.ico
  │
  ├── build_with_pyinstaller()
  │     └── pyinstaller --name=MainApp --windowed --onefile --clean \
  │                      --noconfirm --distpath=THEEXE \
  │                      --add-data=... --hidden-import=... main.py
  │
  └── organize_output()
        └── 显示 THEEXE/ 目录内容及 MainApp.exe 文件大小
```

---

## 2. 打包配置（`MainApp.spec`）

| 配置项 | 值 |
|--------|-----|
| 入口文件 | `main.py` |
| 输出名称 | `MainApp` |
| 窗口模式 | `console=False`（无控制台窗口） |
| 打包类型 | `EXE`（单文件） |
| 图标 | `icon.ico` |
| 压缩 | `upx=True` |

### 数据文件清单

| 来源 | 目标目录 |
|------|----------|
| `icon.ico` | `.` |
| `MainWindow.ui` | `.` |
| `Widgets/Sidebars/Topbar.ui` | `Widgets/Sidebars/` |
| `Widgets/Sidebars/LeftSidebar.ui` | `Widgets/Sidebars/` |
| `Widgets/Sidebars/RightSidebar.ui` | `Widgets/Sidebars/` |
| `Widgets/LeftWidget/FileManage.ui` | `Widgets/LeftWidget/` |
| `Widgets/CenterWidget/CenterWidgetManage.ui` | `Widgets/CenterWidget/` |
| `Widgets/Sidebars/icon1.ico ~ icon4.ico` | `Widgets/Sidebars/` |

### 隐藏导入列表

`PyQt5`, `PyQt5.QtCore`, `PyQt5.QtGui`, `PyQt5.QtWidgets`, `PyQt5.uic`, `ctypes`, `ctypes.wintypes`, `platform`, `os`, `sys`

---

## 3. 运行方式

| 模式 | 命令 |
|------|------|
| 开发运行 | `python main.py` |
| 打包 | `python build_exe.py` |

### 输出产物

```
THEEXE/
└── MainApp.exe    ← 单文件可执行程序（含所有依赖）
```
