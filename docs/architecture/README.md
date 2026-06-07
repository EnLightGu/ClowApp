# 📐 架构文档索引

| 层级 | 文档 | 内容 |
|------|------|------|
| **整体架构** | [`overview.md`](overview.md) | 架构全景、核心原则、灰色统一色彩方案、模块层次、交互流程、跨平台方案 |
| **入口层** | [`module-entry.md`](module-entry.md) | `main.py` — 应用启动入口 |
| **主窗口层** | [`module-mainwindow.md`](module-mainwindow.md) | `MainWindow` — 窗口管理、QDockWidget 集成、双向转化信号 |
| **标题栏** | [`module-topbar.md`](module-topbar.md) | `Topbar` — 自定义标题栏（灰色调）、窗口拖拽 |
| **左侧边栏** | [`module-leftsidebar.md`](module-leftsidebar.md) | `LeftSidebar` — 纯按钮面板 |
| **中央区域管理** | [`module-center-manage.md`](module-center-manage.md) 🆕 | `CenterWidgetManage` — 面板注册与切换 |
| **右侧边栏** | [`module-rightsidebar.md`](module-rightsidebar.md) | `RightSidebar` — 三按钮（预览/逻辑门/文本逻辑） |
| **中央区域** | [`module-centerwidget.md`](module-centerwidget.md) | `MultiFormatViewer` — 多文件可编辑文本预览器 |
| **文件管理** | [`module-filemanage.md`](module-filemanage.md) | `FileManage` — 文件浏览器、目录优先排序、自动刷新 |
| **逻辑门图形** | [`module-logic-diagram.md`](module-logic-diagram.md) 🆕 | `LogicDiagramWidget` — 图形化门逻辑编辑器（拖放 AND/OR/NOT） |
| **文本逻辑** | [`module-logic-text.md`](module-logic-text.md) 🆕 | `LogicTextWidget` + `LogicConverter` — 文本逻辑编辑与双向转化 |
| **逻辑数据库** | [`module-logic-db.md`](module-logic-db.md) 🆕 | `LogicDatabase` — SQLite 逻辑表达式持久化存储 |
| **构建部署** | [`module-build.md`](module-build.md) | `build_exe.py` — PyInstaller 打包（含 12 个 .ui 文件） |

---

## 模块文件分布

```
docs/architecture/
├── README.md                 # 本文档 — 索引
├── overview.md               # 整体架构 + 灰度配色系统
├── module-entry.md           # 入口
├── module-mainwindow.md      # 主窗口
├── module-topbar.md          # 标题栏
├── module-leftsidebar.md     # 左侧边栏
├── module-center-manage.md   # 🆕 中央区域管理器
├── module-rightsidebar.md    # 右侧边栏（含扩展）
├── module-centerwidget.md    # 中央编辑器
├── module-filemanage.md      # 文件管理
├── module-logic-diagram.md   # 🆕 逻辑门图形编辑器
├── module-logic-text.md      # 🆕 文本逻辑编辑器
├── module-logic-db.md        # 🆕 逻辑数据库
└── module-build.md           # 构建部署
```

## 设计规范

- **UI 与逻辑分离：** 每个 Widget 有独立的 `.ui`（Qt Designer）和 `.py`（业务逻辑）文件
- **灰色调 + 白色文字：** 全部界面使用不同层次的灰色背景 + 白色前景，详见 [overview.md#4](overview.md#4)
- **QDockWidget：** 面板以 QDockWidget 管理，支持停靠/浮动/关闭
