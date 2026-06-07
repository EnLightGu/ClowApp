# 整体架构

> **版本：** 0.02（精化版）｜ **框架：** PyQt5 + QDockWidget ｜ **Python：** 3.8+ ｜ **更新：** 2026-06-07

---

## 1. 项目定位

EnApp 是一个**跨平台模块化桌面应用**，采用**自定义无边框窗体 + QDockWidget 面板式布局**架构。核心设计理念是让功能以独立 Widget + Dock 的形式通过侧栏按钮动态切换。

中央区域提供**多文件可编辑文本预览器（MultiFormatViewer）**，左侧面板文件管理通过 `CenterWidgetManage` 以内部面板形式管理（非 QDockWidget），右侧 Dock 提供预览 + 逻辑分析模块（逻辑门图形编辑器 + 文本逻辑编辑器 + 逻辑数据库）。

---

## 2. 架构全景图

```
                     main.py (入口)
                         │
                    MainWindow (QMainWindow)
               ┌──────────────────────────────────────┐
               │          Topbar (#333333)              │
               ├────────┬───────────────────┬──────────┤
               │LeftSide│  中央区域          │RightSide │
               │bar Dock│  CenterWidgetManage│bar Dock  │
               │(80px)  │  ├─ FileManage     │(80px)    │
               │  #2D2D │  └─ MultiFormatView│  #2D2D   │
               │        │  (可编辑)           │          │
               │        │                    ├──────────┤
               │        │                    │预览 Dock │
               │        │                    │逻辑图示  │
               │        │                    │文本逻辑  │
               └────────┴────────────────────┴──────────┘
               ┌──────────────────────────────────────┐
               │          底部 Dock (FilePathBar)       │
               └──────────────────────────────────────┘
```

---

## 3. 核心设计原则

| 原则 | 说明 |
|------|------|
| **UI 与逻辑分离** | 布局由 Qt Designer（`.ui` 文件）定义，业务逻辑在 `.py` 中实现 |
| **组件化** | 每个 Widget 独立封装类，通过 QDockWidget 集成到主窗口 |
| **Dock 面板式布局** | 以 QDockWidget 管理所有侧栏面板，灵活切换/停靠/浮动 |
| **职责单一** | 每个组件聚焦一个功能领域 |
| **多文件编辑** | 中央区域提供基于标签页的可编辑文本编辑器，支持语法高亮 |
| **灰色调统一配色** | 全部界面采用不同层次的灰色背景 + 白色文字 |
| **跨平台适配** | 通过 `platform.system()` 差异化处理 Windows 与 Linux 窗口样式 |

---

## 4. 统一色彩方案

全部界面采用**灰色调背景 + 白色文字**，以下为完整调色板：

| 色名 | 色值 | 用途 |
|------|------|------|
| 背景色 - 主区域 | `#1E1E1E` | 中央编辑器、画布等最深灰背景 |
| 背景色 - 面板 | `#252526` | Dock 面板、侧面板容器、表区域 |
| 背景色 - 侧栏 | `#2D2D2D` | LeftSidebar、RightSidebar |
| 背景色 - 顶栏/工具栏 | `#333333` | Topbar、工具栏背景 |
| 背景色 - 高亮/hover | `#3C3C3C` | 按钮悬停、列表选中 |
| 背景色 - 边框/分隔 | `#454545` | 分割线、边框、更亮 hover |
| 前景色 - 亮白 | `#FFFFFF` | 主要文字、标题、标签 |
| 前景色 - 浅灰 | `#CCCCCC` | 次要文字、说明 |
| 前景色 - 中灰 | `#888888` | 禁用文字、行号、占位符 |
| 强调色 | `#007ACC` | 选中项、焦点边框、超链接 |
| 次强调色 | `#569CD6` | 语法关键字高亮（蓝色系） |

### 文档内引用

所有模块文档中的颜色值统一引用此表，不再各自定义独立色值。

🔍 **逻辑分析模块域专用色：** 逻辑门填充 `#2D4A7A`、引脚青色 `#4EC9B0`、
连线米白 `#DCDCAA`、选中金色 `#FFD700`，参见 [`module-logic-diagram.md`](module-logic-diagram.md)。

---

## 5. 模块层次结构

```
ClowApp/
├── 入口层
│   └── main.py                         # QApplication 初始化，创建主窗口
│
├── 主窗口层
│   ├── MainWindow.py                   # 窗口管理 + 跨平台去标题栏
│   └── MainWindow.ui                   # 四分区布局（顶栏/左栏/中栏/右栏）
│
├── 组件层 (Widgets/)
│   ├── Sidebars/                       # 顶栏 + 左栏 + 右栏
│   │   ├── Topbar.py + Topbar.ui       # 自定义标题栏
│   │   ├── LeftSidebar.py + .ui        # 左侧按钮面板
│   │   ├── RightSidebar.py + .ui       # 右侧工具按钮
│   │   └── FilePathBar.py + .ui        # 底部路径栏
│   │
│   ├── CenterWidget/                   # 中央区域
│   │   └── MultiFormatViewer.py + .ui  # 多文件可编辑文本预览器
│   │
│   ├── LeftWidget/                     # 左侧组件
│   │   └── FileManage.py + .ui         # 文件浏览器
│   │
│   └── RightWidget/                    # 右侧组件
│       ├── SingleTextPreview.py + .ui  # 单文本预览
│       ├── LogicDiagramWidget.py + .ui  # 🆕 逻辑门图形编辑器
│       ├── LogicTextWidget.py + .ui     # 🆕 文本逻辑编辑器
│       ├── LogicConverter.py            # 🆕 双向转化器（无 UI）
│       ├── LogicDatabase.py             # 🆕 逻辑数据库（无 UI）
│       ├── LogicSaveDialog.py + .ui     # 🆕 保存对话框
│       └── LogicLoadDialog.py + .ui     # 🆕 加载对话框
│
├── 图标文件
│   ├── icon1.ico ~ icon4.ico           # 已有
│   ├── icon_logic_gate.ico              # 🆕 逻辑门图标
│   └── icon_logic_txt.ico               # 🆕 文本逻辑图标
│
└── 构建层
    ├── build_exe.py                    # PyInstaller 打包
    └── MainApp.spec                    # 打包配置
```

---

## 6. 核心交互流程

### 6.1 应用启动

```
main()
  └── MainWindow()
        ├── uic.loadUi("MainWindow.ui")
        ├── 平台判断 + 跨平台去标题栏
        ├── _init_topbar()
        ├── _init_center_widget()
        ├── _init_sidebars()
        └── _init_docks()    ← 创建所有 QDockWidget
```

### 6.2 文件编辑流程

```
用户双击 treeView 中的文本文件
  │
  ├── FileManage emit file_double_clicked(path)
  │
  ▼
MainWindow._on_file_manage_double_clicked()
  │
  ├── multi_format_viewer.open_file(path)     # 中央可编辑打开
  └── single_text_preview.open_file(path)     # 右侧预览
```

### 6.3 逻辑分析交互

```
用户点击右边栏 button2 (逻辑门编辑器)
  │
  ├── MainWindow.toggle_logic_diagram_dock()
  │
  ▼
LogicDiagramWidget 显示
  ├── 拖放 AND/OR/NOT 门
  ├── 连线 → 自动生成文本逻辑
  ├── 保存到数据库
  │
  ▼ (双向转化)
LogicTextWidget 同步显示文本表达式
```

### 6.4 面板开关流程

```
用户点击侧边栏按钮
  │
  └── RightSidebar._on_buttonN_clicked()
        └── main_window.toggle_xxx_dock()
              └── QDockWidget.setVisible(not visible)
```

---

## 7. 跨平台方案

| 平台 | 去标题栏方式 | 保留功能 | 状态 |
|------|-------------|----------|------|
| **Linux** | `setWindowFlags(Qt.FramelessWindowHint)` | 无（靠 Topbar 实现窗口控制） | ✅ |
| **Windows** | Win32 API `SetWindowLongPtrW` + `SetWindowPos` | 缩放边框、系统菜单 | ✅ |
| **macOS** | — | — | ❌ 暂不支持 |

---

## 8. 构建部署

- **运行时：** `python main.py`
- **打包：** `python build_exe.py` → `THEEXE/MainApp.exe` 单文件
- **工具链：** PyInstaller `--onefile --windowed`

---

## 9. 架构文档索引

| 层级 | 文档 | 内容 |
|------|------|------|
| **整体架构** | `overview.md` | ✅ 本文档 |
| **入口层** | `module-entry.md` | `main.py` |
| **主窗口层** | `module-mainwindow.md` | `MainWindow` + QDockWidget 集成 |
| **标题栏** | `module-topbar.md` | `Topbar` |
| **左侧边栏** | `module-leftsidebar.md` | `LeftSidebar` |
| **右侧边栏** | `module-rightsidebar.md` | `RightSidebar`（含新按钮） |
| **中央区域管理** | `module-center-manage.md` 🆕 | `CenterWidgetManage` — 面板注册与切换 |
| **中央区域** | `module-centerwidget.md` | `MultiFormatViewer` 可编辑预览 |
| **文件管理** | `module-filemanage.md` | `FileManage` |
| **逻辑门图形** | `module-logic-diagram.md` 🆕 | `LogicDiagramWidget` |
| **文本逻辑** | `module-logic-text.md` 🆕 | `LogicTextWidget` + `LogicConverter` |
| **逻辑数据库** | `module-logic-db.md` 🆕 | `LogicDatabase` |
| **构建部署** | `module-build.md` | `build_exe.py` 打包 |

---

## 10. 扩展点

| 扩展方向 | 说明 |
|----------|------|
| 中央区域管理器 | [`module-center-manage.md`](module-center-manage.md) 🆕 — `CenterWidgetManage` 面板注册与切换 |
| 新增 Dock 面板 | 创建 Widget + .ui → MainWindow._init_docks() 注册 → 侧栏按钮控制 |
| 逻辑门类型扩展 | 在 `LogicGateItem.GATE_TYPES` 中添加新门 |
| 真值表生成 | 根据逻辑图自动生成真值表 |
| 逻辑化简 | 集成 Quine-McCluskey 算法 |
| 仿真 | 输入值实时计算输出 |
| 导出 HDL | Verilog / VHDL 导出 |
| 多用户共享 | SQLite → PostgreSQL 迁移 |
