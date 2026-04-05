AI:
# Qt Dock Widgets Application - 项目结构文档

## 项目概述

这是一个基于PyQt5的桌面应用程序，采用新的架构设计。项目主要特点包括：
- 自定义无边框窗口
- 模块化的侧边栏设计
- 可停靠的中心组件管理
- 支持Windows和Linux系统
- 提供可执行文件打包功能

## 目录结构

```
.
├── main.py                          # 应用程序主入口文件
├── MainWindow.py                    # 主窗口类实现
├── MainWindow.ui                    # 主窗口UI设计文件
├── MainWindow - 副本.py             # 主窗口备份文件
├── build_exe.py                     # 可执行文件构建脚本
├── icon.ico                         # 应用程序图标
├── readme20260315.md                # 项目说明文档
├── __pycache__/                     # Python字节码缓存目录
│
├── THEEXE/                          # 可执行文件输出目录
│   └── MainApp/                     # 打包后的应用程序
│       ├── MainApp.exe              # 可执行文件
│       └── _internal/               # 内部依赖文件
│
└── Widgets/                         # 组件模块目录
    ├── __pycache__/                 # 组件字节码缓存
    │
    ├── Sidebars/                    # 侧边栏组件
    │   ├── __init__.py              # 包初始化文件
    │   ├── __pycache__/             # 侧边栏字节码缓存
    │   ├── Topbar.py                # 顶部标题栏组件
    │   ├── Topbar.ui                # 顶部标题栏UI设计
    │   ├── LeftSidebar.py           # 左侧边栏组件
    │   ├── LeftSidebar.ui           # 左侧边栏UI设计
    │   ├── RightSidebar.py          # 右侧边栏组件
    │   ├── RightSidebar.ui          # 右侧边栏UI设计
    │   ├── icon1.ico                # 图标文件1
    │   ├── icon2.ico                # 图标文件2
    │   ├── icon3.ico                # 图标文件3
    │   └── icon4.ico                # 图标文件4
    │
    ├── LeftWidget/                  # 左侧组件
    │   ├── __pycache__/             # 左侧组件字节码缓存
    │   ├── FileManage.py            # 文件管理组件
    │   └── FileManage.ui            # 文件管理UI设计
    │
    ├── CenterWidget/                # 中心组件
    │   ├── __pycache__/             # 中心组件字节码缓存
    │   ├── CenterWidgetManage.py    # 中心组件管理器
    │   └── CenterWidgetManage.ui    # 中心组件管理器UI设计
    │
    ├── RightWidget/                 # 右侧组件（空目录）
    └── BottomWidget/                # 底部组件（空目录）
```

## 主要文件说明

### 核心文件

1. **main.py** - 应用程序主入口
   - 初始化QApplication
   - 创建并显示主窗口
   - 设置应用程序名称和组织信息

2. **MainWindow.py** - 主窗口类
   - 继承自QMainWindow
   - 加载MainWindow.ui文件
   - 实现跨平台窗口样式（Windows/Linux）
   - 初始化标题栏、侧边栏和中心组件
   - 处理窗口最小化、最大化和关闭事件

3. **MainWindow.ui** - 主窗口UI设计
   - Qt Designer创建的界面文件
   - 定义窗口布局和组件位置

### 组件文件

4. **Widgets/Sidebars/Topbar.py** - 自定义标题栏
   - 实现窗口控制按钮（最小化、最大化、关闭）
   - 显示窗口标题
   - 支持窗口状态更新

5. **Widgets/Sidebars/LeftSidebar.py** - 左侧边栏
   - 提供导航功能
   - 与中心组件管理器交互
   - 添加可停靠组件到中心区域

6. **Widgets/Sidebars/RightSidebar.py** - 右侧边栏
   - 提供额外的工具或信息显示

7. **Widgets/CenterWidget/CenterWidgetManage.py** - 中心组件管理器
   - 管理可停靠的中心组件
   - 提供组件添加、删除和布局功能

8. **Widgets/LeftWidget/FileManage.py** - 文件管理组件（可隐藏）
   - 文件操作相关功能
   - 可作为可停靠组件添加到中心区域

### 构建和配置

9. **build_exe.py** - 打包脚本（AI编写）
   - 使用PyInstaller打包应用程序
   - 自动收集UI文件和数据文件
   - 清理之前的构建文件
   - 输出到THEEXE目录

10. **icon.ico** - 应用程序图标
    - Windows应用程序图标文件
    - 在打包时自动包含

## 构建说明

### 依赖项
- Python 3.x
- PyQt5
- PyInstaller（用于打包）

### 运行应用程序
```bash
python main.py
```

### 打包为可执行文件
```bash
python build_exe.py
```

打包后的文件将位于`THEEXE/MainApp/`目录中，包含：
- `MainApp.exe` - 可执行文件
- `_internal/` - 运行时依赖文件

## 架构特点

1. **模块化设计**：各个组件独立，便于维护和扩展
2. **跨平台支持**：适配Windows和Linux系统
3. **自定义窗口**：移除系统标题栏，实现自定义窗口控制
4. **可停靠组件**：中心区域支持可停靠的组件管理
5. **UI与逻辑分离**：使用.ui文件定义界面，.py文件实现逻辑

## 扩展说明

- **添加新组件**：在Widgets目录下创建新的组件模块
- **修改界面**：使用Qt Designer编辑.ui文件
- **添加功能**：在相应的组件类中添加方法
- **打包配置**：修改build_exe.py中的参数调整打包行为

## 注意事项

1. 项目包含备份文件`MainWindow - 副本.py`可删除
2. `__pycache__`目录包含Python字节码，可安全删除
3. `examples`目录当前为空，可用于存放示例代码
4. `RightWidget`和`BottomWidget`目录当前为空，可用于扩展
5. 打包时需要确保所有依赖的UI文件路径正确

---
*文档生成时间：2026年/4/5*
*项目版本：新版架构*
```
