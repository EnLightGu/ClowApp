# 📐 架构文档索引

| 层级 | 文档 | 内容 |
|------|------|------|
| **整体架构** | [`overview.md`](overview.md) | 架构全景、核心原则、统一色彩方案、模块层次、交互流程、跨平台方案、扩展点 |
| **入口层** | [`module-entry.md`](module-entry.md) | `main.py` — 应用启动入口 |
| **主窗口层** | [`module-mainwindow.md`](module-mainwindow.md) | `MainWindow` — 窗口管理、跨平台去标题栏、组件统一组装、信号连接中转 |
| **标题栏** | [`module-topbar.md`](module-topbar.md) | `Topbar` — 自定义标题栏、信号定义、拖拽移动 |
| **左侧边栏** | [`module-leftsidebar.md`](module-leftsidebar.md) | `LeftSidebar` — 纯按钮面板，仅切换面板显隐 |
| **右侧边栏** | [`module-rightsidebar.md`](module-rightsidebar.md) | `RightSidebar` — 预留工具按钮 |
| **中央区域** | [`module-centerwidget.md`](module-centerwidget.md) | `CenterWidgetManage`（QWidget）+ `MultiFileEditor` 多文件文本编辑器 |
| **文件管理** | [`module-filemanage.md`](module-filemanage.md) | `FileManage` — 文件浏览器（仅 treeView + 目录优先排序）、自动刷新 |
| **构建部署** | [`module-build.md`](module-build.md) | `build_exe.py` — PyInstaller 打包 |
