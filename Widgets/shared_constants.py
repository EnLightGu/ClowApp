"""
shared_constants — 跨模块共享常量定义

集中管理多个模块共同使用的常量，避免重复定义。
"""

# ════════════════════════════════════════════════════════════════
# 文本文件扩展名（在 FileManage 和 MultiFormatViewer 间共享）
# ════════════════════════════════════════════════════════════════

TEXT_EXTENSIONS = {
    '.txt', '.md', '.py', '.js', '.ts', '.json', '.xml', '.yaml', '.yml',
    '.html', '.css', '.scss', '.less', '.c', '.cpp', '.h', '.hpp', '.java',
    '.sql', '.csv', '.log', '.sh', '.bat', '.ini', '.cfg', '.conf', '.toml',
    '.env', '.gitignore',
}
