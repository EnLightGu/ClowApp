#!/usr/bin/env python3
"""
简单打包脚本 - 将所有文件打包到THEEXE文件夹
"""
import os
import sys
import shutil
import subprocess


def clean_previous_build():
    """清理之前的构建文件"""
    build_dirs = ['build', 'dist', 'THEEXE']
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)

    # 清理.spec文件
    spec_files = [f for f in os.listdir('.') if f.endswith('.spec')]
    for spec_file in spec_files:
        print(f"删除文件: {spec_file}")
        os.remove(spec_file)


def collect_data_files():
    """收集所有数据文件（UI文件等）"""
    data_files = []

    # 添加主图标文件
    if os.path.exists('icon.ico'):
        data_files.append(('icon.ico', '.'))

    # 添加UI文件 - 共5个UI文件（MultiFormatViewer 纯代码无.ui文件）
    ui_files = [
        'MainWindow.ui',
        'Widgets/Sidebars/Topbar.ui',
        'Widgets/Sidebars/LeftSidebar.ui',
        'Widgets/Sidebars/RightSidebar.ui',
        'Widgets/LeftWidget/FileManage.ui',
    ]

    for ui_file in ui_files:
        if os.path.exists(ui_file):
            # 保持目录结构
            dest_dir = os.path.dirname(ui_file)
            if not dest_dir:
                dest_dir = '.'
            data_files.append((ui_file, dest_dir))
        else:
            print(f"警告: UI文件不存在: {ui_file}")

    # 添加图标文件（从Sidebars目录）
    icon_files = [
        'Widgets/Sidebars/icon1.ico',
        'Widgets/Sidebars/icon2.ico',
        'Widgets/Sidebars/icon3.ico',
        'Widgets/Sidebars/icon4.ico'
    ]

    for icon_file in icon_files:
        if os.path.exists(icon_file):
            dest_dir = os.path.dirname(icon_file)
            data_files.append((icon_file, dest_dir))
        else:
            print(f"警告: 图标文件不存在: {icon_file}")

    return data_files


def build_with_pyinstaller():
    """使用PyInstaller构建单个可执行文件"""
    print("开始构建单个可执行文件...")

    # 收集数据文件
    data_files = collect_data_files()

    # 构建PyInstaller命令 - 使用--onefile生成单个exe
    cmd = [
        'pyinstaller',
        '--name=MainApp',
        '--windowed',           # 隐藏控制台窗口
        '--onefile',            # 生成单个可执行文件
        '--clean',
        '--noconfirm',
        '--distpath=THEEXE',    # 输出到THEEXE目录
        '--workpath=build',
        '--specpath=.'
    ]

    # 添加图标
    if os.path.exists('icon.ico'):
        cmd.append('--icon=icon.ico')

    # 添加数据文件
    for src, dst in data_files:
        cmd.append(f'--add-data={src};{dst}')

    # 添加隐藏导入
    hidden_imports = [
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.uic',
        'ctypes',
        'ctypes.wintypes',
        'platform',
        'os',
        'sys',
    ]

    for imp in hidden_imports:
        cmd.append(f'--hidden-import={imp}')

    # 添加主文件
    cmd.append('main.py')

    print("执行命令:", ' '.join(cmd))

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建输出:")
        print(result.stdout)
        if result.stderr:
            print("错误信息:")
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"标准输出: {e.stdout}")
        print(f"标准错误: {e.stderr}")
        return False


def organize_output():
    """整理输出文件"""
    print("\n整理输出文件...")

    theexe_dir = 'THEEXE'
    if not os.path.exists(theexe_dir):
        print(f"错误: {theexe_dir} 目录不存在")
        return

    # 检查可执行文件
    exe_files = [f for f in os.listdir(theexe_dir) if f.endswith('.exe')]
    if not exe_files:
        print("警告: 未找到可执行文件")
    else:
        print(f"找到可执行文件: {exe_files[0]}")
        exe_path = os.path.join(theexe_dir, exe_files[0])
        exe_size = os.path.getsize(exe_path)
        print(f"文件大小: {exe_size / (1024*1024):.2f} MB")

    # 显示目录内容
    print(f"\n{theexe_dir} 目录内容:")
    for item in os.listdir(theexe_dir):
        item_path = os.path.join(theexe_dir, item)
        if os.path.isfile(item_path):
            size = os.path.getsize(item_path)
            print(f"  {item} ({size / (1024*1024):.2f} MB)")
        else:
            print(f"  {item}/")


def main():
    """主函数"""
    print("=" * 50)
    print("简单打包脚本 - 将项目打包为单个EXE安装包")
    print("=" * 50)

    # 清理之前的构建
    clean_previous_build()

    # 构建可执行文件
    success = build_with_pyinstaller()

    if success:
        # 整理输出
        organize_output()

        print("\n" + "=" * 50)
        print("打包完成！")
        print("单个可执行文件位于: THEEXE/ 文件夹")
        print("注意: 这是单个EXE安装包，所有依赖已打包到文件中")
        print("=" * 50)
    else:
        print("\n打包失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()