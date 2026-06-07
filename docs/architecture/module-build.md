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
  │     ├── UI 文件 (12 个):               ← 更新
  │     │   ├── MainWindow.ui
  │     │   ├── Topbar.ui
  │     │   ├── LeftSidebar.ui
  │     │   ├── RightSidebar.ui
  │     │   ├── FileManage.ui
  │     │   ├── FilePathBar.ui
  │     │   ├── MultiFormatViewer.ui
  │     │   ├── SingleTextPreview.ui
  │     │   ├── LogicDiagramWidget.ui      ← 🆕
  │     │   ├── LogicTextWidget.ui          ← 🆕
  │     │   ├── LogicSaveDialog.ui          ← 🆕
  │     │   └── LogicLoadDialog.ui          ← 🆕
  │     │
  │     ├── 图标文件:                       ← 更新
  │     │   ├── [策略说明] 所有工具栏按钮优先使用
  │     │   │   QStyle.StandardPixmap 内置图标（零依赖），
  │     │   │   仅在无合适内置图标时使用自定义图标文件
  │     │   ├──
  │     │   ├── 侧栏按钮图标（已有）:
  │     │   │   ├── icon1.ico ~ icon4.ico
  │     │   ├──
  │     │   ├── 自定义图标文件:
  │     │   │   ├── icon_logic_gate.ico    # 🆕 逻辑门编辑器
  │     │   │   └── icon_logic_txt.ico     # 🆕 文本逻辑编辑器
  │     │   └──
  │     └── [备注] LogicDiagramWidget 和 LogicTextWidget 的
  │             工具栏按钮全部使用 QStyle.StandardPixmap 内置图标，
  │             具体映射方案见各模块文档
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

| 来源 | 目标目录 | 备注 |
|------|----------|------|
| `icon.ico` | `.` | 应用图标 |
| `MainWindow.ui` | `.` | 主窗口布局 |

**Sidebars**
| `Widgets/Sidebars/Topbar.ui` | `Widgets/Sidebars/` | 标题栏 |
| `Widgets/Sidebars/LeftSidebar.ui` | `Widgets/Sidebars/` | 左侧栏 |
| `Widgets/Sidebars/RightSidebar.ui` | `Widgets/Sidebars/` | 右侧栏 |
| `Widgets/Sidebars/FilePathBar.ui` | `Widgets/Sidebars/` | 底部路径栏 |

**LeftWidget**
| `Widgets/LeftWidget/FileManage.ui` | `Widgets/LeftWidget/` | 文件管理 |

**CenterWidget**
| `Widgets/CenterWidget/MultiFormatViewer.ui` | `Widgets/CenterWidget/` | 多文件编辑预览 |

**RightWidget**
| `Widgets/RightWidget/SingleTextPreview.ui` | `Widgets/RightWidget/` | 单文本预览 |
| `Widgets/RightWidget/LogicDiagramWidget.ui` | `Widgets/RightWidget/` | 🆕 逻辑门图形编辑器 |
| `Widgets/RightWidget/LogicTextWidget.ui` | `Widgets/RightWidget/` | 🆕 文本逻辑编辑器 |
| `Widgets/RightWidget/LogicSaveDialog.ui` | `Widgets/RightWidget/` | 🆕 数据库保存对话框 |
| `Widgets/RightWidget/LogicLoadDialog.ui` | `Widgets/RightWidget/` | 🆕 数据库加载对话框 |

**图标文件**
| — | `Widgets/Sidebars/icons/` | 工具栏图标目录（建议统一存放） |
| `Widgets/Sidebars/icon1.ico ~ icon4.ico` | `Widgets/Sidebars/` | 已有侧栏按钮图标 |
| `Widgets/Sidebars/icon_logic_gate.ico` | `Widgets/Sidebars/` | 🆕 逻辑门编辑器按钮 |
| `Widgets/Sidebars/icon_logic_txt.ico` | `Widgets/Sidebars/` | 🆕 文本逻辑按钮 |

> **图标策略说明：** LogicDiagramWidget 和 LogicTextWidget 的 18 个工具栏按钮
> **全部优先使用 `QStyle.StandardPixmap` 内置图标**（零文件依赖），
> 无须为每个工具栏按钮准备单独的自定义图标文件。
> 仅在无合适内置图标时才使用 `Widgets/Sidebars/icons/` 目录下的自定义图标。
> 各按钮的 `QStyle.StandardPixmap` 映射见各模块文档。

> `LogicConverter.py` 和 `LogicDatabase.py` 无 UI 文件，无需添加到 data 列表。

### 隐藏导入列表

```
PyQt5, PyQt5.QtCore, PyQt5.QtGui, PyQt5.QtWidgets, PyQt5.uic,
ctypes, ctypes.wintypes, platform, os, sys,
chardet,           # 编码检测
sqlite3,           # 逻辑数据库
json               # 变量映射序列化
```

---

## 3. 运行方式

| 模式 | 命令 |
|------|------|
| 开发运行 | `python main.py` |
| 打包 | `python build_exe.py` |

### 输出产物

```
THEEXE/
└── MainApp.exe    ← 单文件可执行程序（含所有依赖和数据文件）
```
