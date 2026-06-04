# 整体架构

> **版本：** 0.02（新版架构）｜ **框架：** PyQt5 ｜ **Python：** 3.8+ ｜ **更新：** 2026-06-04

---

## 1. 项目定位

ClowApp 是一个**跨平台模块化桌面应用**，采用**自定义无边框窗体 + 面板式中央布局**架构。核心设计理念是让应用功能以独立 Widget 的形式通过侧栏按钮动态切换。中央区域默认提供**多文件文本预览器（MultiFileEditor）**，左侧面板用于文件管理等辅助工具。

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
                    │  ┌──────┬────────────────┐     │
                    │  │ Left │   Center       │     │
                    │  │Side  │  Widget        │     │
                    │  │ bar  │  Manage        │     │
                    │  │(80px)│  (QWidget)     │     │
                    │  │      │ ┌────┬────────┐│     │
                    │  │button│ │左  │MultiFile││     │  ← 左侧面板可选（如 FileManage）
                    │  │①→②→ │ │面板│Editor  ││     │  ← MultiFileEditor 常驻中央
                    │  │      │ └────┴────────┘│     │
                    │  └──────┴───────────────┴┘     │
                    │              │                  │
                    └──────────────┴──────────────────┘
                        Linux: FramelessWindowHint
                        Windows: Win32 API 去标题栏
```

---

## 3. 核心设计原则

| 原则 | 说明 |
|------|------|
| **UI 与逻辑分离** | 布局由 Qt Designer（`.ui` 文件）定义，业务逻辑在 `.py` 中实现 |
| **组件化** | 每个 Widget 独立封装类，通过组合方式集成到主窗口 |
| **面板式布局** | 中央区域为 `QWidget`，左面板（可选）+ 中央编辑器（常驻），避免 QMainWindow 嵌套 |
| **职责单一** | LeftSidebar 仅负责按钮→面板切换；MainWindow 统一管理组件创建和信号连接 |
| **多文件预览** | 中央区域默认提供基于标签页的文本文件预览，支持同时打开多个文件 |
| **跨平台适配** | 通过 `platform.system()` 差异化处理 Windows 与 Linux 窗口样式 |

---

## 4. 统一色彩方案

为避免各组件颜色冲突，定义以下统一的调色板：

| 色名 | 色值 | 用途 |
|------|------|------|
| 背景色 - 主区域 | `#1E1E1E` | CentralWidget、MultiFileEditor 背景 |
| 背景色 - 面板 | `#252526` | FileManage、侧边面板、行号区域 |
| 背景色 - 侧栏 | `#2D2D2D` | LeftSidebar、RightSidebar |
| 背景色 - 顶栏 | `#F6F2EE` | Topbar |
| 背景色 - 文件管理 | `#252526` | FileManage 主区域（与面板一致） |
| 前景色 - 文字 | `#CCCCCC` | 默认文字 |
| 前景色 - 亮色 | `#FFFFFF` | 高亮文字、当前行号 |
| 强调色 | `#007ACC` | 选中项、焦点边框 |

> 各组件模块的颜色统一引用此表，不再各自定义独立色值。

---

## 5. 模块层次结构

```
ClowApp/
├── 入口层
│   └── main.py                    # QApplication 初始化，创建主窗口
│
├── 主窗口层
│   ├── MainWindow.py              # 窗口管理 + 跨平台去标题栏 + 组件组装 + 信号连接
│   └── MainWindow.ui              # 四分区布局（顶栏/左栏/中栏/右栏）
│
├── 组件层 (Widgets/)
│   ├── Sidebars/                  # 顶栏 + 左栏 + 右栏
│   │   ├── Topbar.py              # 自定义标题栏
│   │   ├── LeftSidebar.py         # 左侧按钮面板（仅切换面板显隐，不参与组件创建）
│   │   └── RightSidebar.py        # 右侧工具栏（预留）
│   │
│   ├── CenterWidget/              # 中央区域
│   │   ├── CenterWidgetManage.py  # QWidget 面板管理器 + MultiFileEditor
│   │   └── MultiFileEditor.py     # 多文件文本预览器（QTabWidget + QPlainTextEdit）
│   │
│   ├── LeftWidget/                # 左侧组件
│   │   └── FileManage.py          # 文件浏览器（仅 treeView + 目录优先排序）
│   │
│   ├── RightWidget/               # (预留)
│   └── BottomWidget/              # (预留)
│
└── 构建层
    ├── build_exe.py               # PyInstaller 打包脚本
    └── MainApp.spec               # 打包配置
```

### 相较 v0.01 的变更

| 变更 | 模块 | 说明 |
|------|------|------|
| ✂️ 移除 | `FileManage` | 移除 `listView`（列表视图），仅保留 `treeView` |
| 🆕 新增 | `CenterWidget/MultiFileEditor.py` | 多标签文本文件预览器 |
| 🔄 重构 | `CenterWidgetManage` | `QMainWindow` → `QWidget`，消除嵌套；改为面板式布局 |
| 🔄 重构 | `MainWindow` | 接管组件创建和信号连接，`LeftSidebar` 回归纯按钮职责 |
| 🆕 新增 | FileManage → MainWindow → CenterWidget | 信号链路闭环 |
| 🎨 统一 | 色彩方案 | 全局调色板，各模块颜色统一 |

---

## 6. 核心交互流程

### 6.1 应用启动

```
main()
  │
  └── MainWindow()
        ├── uic.loadUi("MainWindow.ui")         # 加载四分区布局
        ├── 平台判断 + 移除原生标题栏              # Linux / Windows / macOS(暂不支持)
        ├── setWindowTitle("Main Window")
        ├── _init_topbar()                       # ① 初始化自定义标题栏
        ├── _init_center_widget()                # ② 中央区域管理器（必须在 sidebars 之前）
        └── _init_sidebars()                     # ③ 初始化左右侧栏 + 注入 manager 引用
              ├── 创建 CenterWidgetManage(QWidget)
              │   ├── 左面板容器（默认隐藏）
              │   └── MultiFileEditor（常驻中央）
              ├── 注册 FileManage 面板         ← 预创建但默认隐藏
              └── 连接 file_double_clicked 信号  ← 统一管理
```

### 6.2 面板开关流程

```
用户点击左侧栏 button1
  │
  └── LeftSidebar._on_button1_clicked()
        └── toggle_panel("file_manage")
              └── CenterWidgetManage 切换左面板可见性
```

### 6.3 文件预览流程

```
用户双击 treeView 中的文本文件
  │
  ├── FileManage._on_tree_item_double_clicked()
  │     ├── 文本文件 → emit file_double_clicked(file_path)
  │     └── 其他 → print 日志
  │
  ▼
MainWindow._on_file_manage_double_clicked()
  │
  ├── center_widget_manager.open_file_in_editor(file_path)
  │     └── return (success, error_msg)
  │
  ▼
CenterWidgetManage
  │
  └── MultiFileEditor.open_file(file_path)
        ├── 文件已打开 → 切换到已有标签页
        │
        ├── 文件 > 10MB → 弹出确认对话框
        │     ├── 确认 → 继续加载
        │     └── 取消 → return (False, "用户取消")
        │
        └── 未打开（且 ≤ 10MB）→ 编码检测
              ├── chardet 自动检测
              ├── fallback 链: UTF-8 → GBK → Latin-1
              ├── 全部失败 → return (False, "编码错误")
              └── 成功 → 新建标签页 + QPlainTextEdit（只读 + 行号）
```

---

## 7. 跨平台方案

| 平台 | 去标题栏方式 | 保留功能 | 状态 |
|------|-------------|----------|------|
| **Linux** | `setWindowFlags(Qt.FramelessWindowHint)` | 无（靠 Topbar 实现窗口控制） | ✅ 已实现 |
| **Windows** | Win32 API: `SetWindowLongPtrW` + `SetWindowPos` | 缩放边框、最小/最大按钮、系统菜单 | ✅ 已实现 |
| **macOS** | — | — | ❌ 暂不支持（需 PyObjC 桥接） |

---

## 8. 构建部署

- **运行时：** `python main.py`
- **打包：** `python build_exe.py` → 产出一个 `THEEXE/MainApp.exe` 单文件
- **工具链：** PyInstaller `--onefile --windowed`
- **UI 数据文件：** 6 个 `.ui` 文件（`CenterWidgetManage` 使用代码初始化，无需 `.ui` 文件）

---

## 9. 扩展点

| 扩展方向 | 操作方式 |
|----------|----------|
| 新增面板组件 | 创建 widget → `register_panel()` 注册 → 侧栏按钮绑定 `toggle_panel()` |
| 新增侧边栏按钮 | 编辑对应 `.ui` 文件 + `.py` 绑定信号 |
| 文本编辑器增强 | 在 `MultiFileEditor` 中添加语法高亮、搜索、编码选择等 |
| 编码自动检测 | 引入 `chardet` 或 `cchardet` |
| 文件管理增强 | 添加右键菜单（删除/重命名/新建） |
| 状态持久化 | 打开的文件列表持久化到 `QSettings` |
| 国际化 | 引入 `QTranslator` |
