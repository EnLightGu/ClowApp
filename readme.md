# EnApp — 跨平台模块化桌面应用

> **版本：** 0.02 | **框架：** PyQt5 | **Python：** 3.8+ | **更新：** 2026-06-07

一个用 PyQt5 构建的跨平台模块化桌面应用，支持**文件编辑预览**、**逻辑门图形编辑**、**文本逻辑表达式编辑**等功能。

---

## 📸 界面概览

```
┌─────────────────────────────────────────────────────┐
│                  Topbar (自定义标题栏)                │
├──────┬───────────────────────────┬──────────────────┤
│ 左侧 │      CenterWidgetManage    │    右侧         │
│ 边栏 │  ┌────────┬────────────┐  │    边栏          │
│(80px)│  │左面板   │  主内容     │  │   (80px)        │
│      │  │FileMgt │MultiFormat  │  │                 │
│ button│  │        │Viewer      │  │ 预览/逻辑门     │
│ 列表  │  │        │(可编辑)     │  │ /文本逻辑       │
│      │  ├────────┴────────────┤  │                 │
│      │  │  右侧面板(可拖拽)    │  │                 │
│      │  │ 预览 / 逻辑门 / 文本 │  │                 │
├──────┴──┴─────────────────────┴──┴──────────────────┤
│              FilePathBar (底部路径栏)                 │
└─────────────────────────────────────────────────────┘

所有内容面板属于中心窗口内部，可拖拽调整大小。
左右边栏固定 80px，通过按钮切换中心面板显隐。
</pre>

---

## ✨ 功能特性

### 📄 多文件编辑与预览（MultiFormatViewer）
- 基于标签页的多文件编辑，支持语法高亮
- 代码折叠、行号显示
- 支持文本、代码、Markdown 等格式
- 文件修改指示器（圆点标记）

### 🔧 左侧文件管理（FileManage）
- 文件目录树浏览，文件夹/文件图标区分
- 排序代理（文件夹优先）
- 文件系统自动监听刷新
- 双击文件在中央编辑器打开

### 🔌 逻辑门图形编辑器（LogicDiagramWidget）
- AND / OR / NOT / NAND / NOR / XOR 六种逻辑门
- 拖放式添加逻辑门到画布
- 引脚间连线（正交折线），连线跟随模型移动
- 图形 ↔ 文本双向转换
- 变量管理对话框（新增/删除/重命名/修改类型）
- 导出为文本表达式或图片

### 📝 文本逻辑编辑器（LogicTextWidget）
- 逻辑表达式编辑，带语法高亮
- 支持关键字（`AND` / `OR` / `NOT` / `NAND` / `NOR` / `XOR`）
- 支持速记符号（`+` = OR、`*` = AND、`!`/`~` = NOT）
- 支持数值变量（int/float）和字符串变量
- 支持比较表达式（`==`、`!=`、`<`、`>`、`<=`、`>=`）
- 变量映射表，可编辑变量类型（bool/int/float/string）
- 语法检查/格式化/保存到数据库/从数据库加载

### 🗄️ 逻辑数据库（LogicDatabase）
- SQLite 存储逻辑表达式记录
- 支持标签分类搜索
- 历史版本追踪

---

## 📁 项目结构

```
EnApp-0.02/
├── main.py                         # 入口文件
├── MainWindow.py                   # 主窗口（布局 + 面板管理）
├── MainWindow.ui                   # Qt Designer 布局文件
│
├── Widgets/
│   ├── Sidebars/                   # 边栏组件
│   │   ├── Topbar.py / .ui         #   自定义标题栏
│   │   ├── LeftSidebar.py / .ui    #   左侧按钮面板
│   │   ├── RightSidebar.py / .ui   #   右侧按钮面板
│   │   └── FilePathBar.py          #   底部路径栏
│   │
│   ├── CenterWidget/               # 中央区域
│   │   ├── CenterWidgetManage.py   #   中央管理器（左右面板容器）
│   │   ├── MultiFormatViewer.py    #   多格式文件编辑器
│   │   └── CodeEditor.py           #   代码编辑器组件
│   │
│   ├── LeftWidget/
│   │   └── FileManage.py / .ui     #   文件管理器
│   │
│   ├── RightWidget/                # 右侧功能面板
│   │   ├── SingleTextPreview.py    #   单文本预览
│   │   ├── LogicDiagramWidget.py   #   逻辑门图形编辑器
│   │   ├── LogicTextWidget.py      #   文本逻辑编辑器
│   │   ├── LogicConverter.py       #   逻辑表达式↔图形转化器
│   │   ├── LogicDatabase.py        #   逻辑数据库
│   │   ├── LogicSaveDialog.py      #   保存到数据库对话框
│   │   └── LogicLoadDialog.py      #   从数据库加载对话框
│   │
│   └── shared_constants.py         #   共享常量
│
├── docs/architecture/              # 架构文档
│   ├── overview.md                 #   整体架构
│   ├── module-mainwindow.md        #   主窗口模块
│   ├── module-logic-diagram.md     #   逻辑门图形模块
│   ├── module-logic-text.md        #   文本逻辑模块
│   ├── module-logic-db.md          #   逻辑数据库模块
│   └── ...                         #   其他模块文档
│
├── filefortest/                    # 测试文件
│   ├── run_final_test.py           #   最终集成测试 (36项)
│   ├── run_runtime_tests.py        #   运行时逻辑测试 (33项)
│   ├── run_tests.py                #   PyQt GUI 测试
│   ├── test_all_modules.py         #   模块导入测试
│   └── test_logic_diagram_detail.py # 逻辑门详情测试
│
├── examples/                       # 示例文件
├── build/                          # 构建输出
├── THEEXE/                         # 打包可执行文件
│
├── requirements.txt                # 依赖清单
├── build_exe.py                    # PyInstaller 构建脚本
├── MainApp.spec                    # 打包配置
└── readme.md                       # 本文件
```

---

## 🚀 快速开始

### 环境要求
- Python 3.8+
- PyQt5 5.15+

### 安装
```bash
cd EnApp-0.02
pip install -r requirements.txt
```

### 运行
```bash
python main.py
```

### 测试
```bash
cd filefortest
python run_runtime_tests.py     # 逻辑转换器测试 (33项)
python run_final_test.py        # 整体集成测试 (36项)
python run_tests.py             # PyQt GUI 测试
```

### 打包
```bash
python build_exe.py
```

---

## 🧪 测试状态

| 测试套件 | 项数 | 状态 |
|---------|------|------|
| 运行时测试（LogicConverter R3+R4） | 33 | ✅ 全部通过 |
| 最终集成测试（全模块） | 36 | ✅ 全部通过 |
| **合计** | **69** | **✅ 全部通过** |

---

## 🔧 技术栈

| 技术 | 用途 |
|------|------|
| **Python 3.8+** | 开发语言 |
| **PyQt5** | GUI 框架（Qt Designer 布局） |
| **QGraphicsView** | 逻辑门图形画布 |
| **QPlainTextEdit** | 文本编辑器 + 语法高亮 |
| **SQLite** | 逻辑数据库存储 |
| **PyInstaller** | 打包为可执行文件 |
| **QPaint / QPainterPath** | 自定义门图形绘制 |

---

## 🏗️ 架构设计原则

| 原则 | 说明 |
|------|------|
| **UI 与逻辑分离** | 布局由 Qt Designer（`.ui` 文件）定义，业务逻辑在 `.py` 中实现 |
| **组件化** | 每个 Widget 独立封装类，通过主窗口集成 |
| **职责单一** | 每个组件聚焦一个功能领域 |
| **灰色调统一配色** | 全部界面采用不同层次的灰色背景 + 白色文字 |
| **跨平台适配** | 通过 `platform.system()` 差异化处理 Windows 与 Linux 窗口样式 |

### 统一色彩方案

| 色名 | 色值 | 用途 |
|------|------|------|
| 主背景 | `#1E1E1E` | 中央编辑器、画布 |
| 面板背景 | `#252526` | Dock 面板、侧面板容器 |
| 侧栏背景 | `#2D2D2D` | 左右侧边栏 |
| 顶栏背景 | `#333333` | Topbar、工具栏 |
| 高亮/hover | `#3C3C3C` | 按钮悬停、列表选中 |
| 边框/分隔 | `#454545` | 分割线、边框 |
| 强调色 | `#007ACC` | 选中项、焦点边框 |

---

## 🔮 扩展方向

- 真值表生成 — 根据逻辑图自动生成真值表
- 逻辑化简 — 集成 Quine-McCluskey 算法
- 逻辑仿真 — 输入值实时计算输出
- HDL 导出 — Verilog / VHDL 导出
- 多用户共享 — SQLite → PostgreSQL 迁移

---

## 📜 许可

本项目用于个人学习，仅供学习参考。
