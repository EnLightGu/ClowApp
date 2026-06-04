# 📐 架构文档索引

| 层级 | 文档 | 内容 |
|------|------|------|
| **整体架构** | [`overview.md`](overview.md) | 架构全景、模块层次、核心流程、跨平台方案、扩展点 |
| **入口层** | [`module-entry.md`](module-entry.md) | `main.py` — 应用启动入口 |
| **主窗口层** | [`module-mainwindow.md`](module-mainwindow.md) | `MainWindow` — 窗口管理、跨平台去标题栏、子模块组装 |
| **标题栏** | [`module-topbar.md`](module-topbar.md) | `Topbar` — 自定义标题栏、信号定义、拖拽移动 |
| **左侧边栏** | [`module-leftsidebar.md`](module-leftsidebar.md) | `LeftSidebar` — 工具栏、Dock 开关逻辑 |
| **右侧边栏** | [`module-rightsidebar.md`](module-rightsidebar.md) | `RightSidebar` — 预留工具按钮 |
| **中央 Dock 管理器** | [`module-centerwidget.md`](module-centerwidget.md) | `CenterWidgetManage` — Dock 注册/查找/切换 |
| **文件管理** | [`module-filemanage.md`](module-filemanage.md) | `FileManage` — 文件浏览器实现 |
| **构建部署** | [`module-build.md`](module-build.md) | `build_exe.py` — PyInstaller 打包 |
