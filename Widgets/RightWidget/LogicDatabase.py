"""
LogicDatabase — 逻辑表达式持久化存储模块

基于 Python 内置 sqlite3 实现，不使用 ORM。
负责逻辑表达式的 CRUD、标签管理、版本历史记录。
"""

import json
import os
import sqlite3
from typing import Dict, List, Optional, Union

# ── 数据库路径配置 ──────────────────────────────────────────────────────────
DB_DIR = os.path.expanduser("~/.enapp")
DB_PATH = os.path.join(DB_DIR, "logic_db.sqlite")

# ── DDL：四张核心表 ────────────────────────────────────────────────────────
DDL_SQL = """
CREATE TABLE IF NOT EXISTS logic_expressions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    description   TEXT DEFAULT '',
    expression    TEXT NOT NULL,
    variable_map  TEXT DEFAULT '{}',
    created_at    TEXT DEFAULT (datetime('now','localtime')),
    updated_at    TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS logic_tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS logic_expression_tags (
    expression_id INTEGER NOT NULL REFERENCES logic_expressions(id) ON DELETE CASCADE,
    tag_id        INTEGER NOT NULL REFERENCES logic_tags(id) ON DELETE CASCADE,
    PRIMARY KEY (expression_id, tag_id)
);

CREATE TABLE IF NOT EXISTS logic_expression_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    expression_id INTEGER NOT NULL REFERENCES logic_expressions(id) ON DELETE CASCADE,
    expression    TEXT NOT NULL,
    variable_map  TEXT DEFAULT '{}',
    changed_at    TEXT DEFAULT (datetime('now','localtime')),
    change_note   TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_expr_name      ON logic_expressions(name);
CREATE INDEX IF NOT EXISTS idx_expr_updated   ON logic_expressions(updated_at);
CREATE INDEX IF NOT EXISTS idx_history_expr   ON logic_expression_history(expression_id);
"""


class LogicDatabase:
    """逻辑表达式数据库：持久化存储、检索、标签与版本历史管理。"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._ensure_tables()

    # ── 内部工具方法 ──────────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """获取连接，已配置 WAL 模式和强制外键约束。"""
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _ensure_tables(self):
        """自动创建 / 确保表结构存在。"""
        conn = self._get_conn()
        try:
            conn.executescript(DDL_SQL)
            conn.commit()
        finally:
            conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> Optional[dict]:
        """将 sqlite3.Row 转换为标准 dict，并自动解析 variable_map 和 tags。"""
        if row is None:
            return None
        d = dict(row)
        # 解析 JSON 字段
        if isinstance(d.get("variable_map"), str):
            d["variable_map"] = json.loads(d["variable_map"])
        # 移除纯内部字段（tags 另行填充，history 单独获取）
        d.pop("id_in_tags", None)
        return d

    def _fetch_tags(self, conn: sqlite3.Connection, expr_id: int) -> List[str]:
        """查询指定表达式的所有标签名称。"""
        rows = conn.execute(
            """
            SELECT t.name
              FROM logic_tags t
              JOIN logic_expression_tags et ON et.tag_id = t.id
             WHERE et.expression_id = ?
             ORDER BY t.name
            """,
            (expr_id,),
        ).fetchall()
        return [r["name"] for r in rows]

    def _get_or_create_tag(self, conn: sqlite3.Connection, tag: str) -> int:
        """获取标签 ID，不存在则自动创建，返回 ID。"""
        row = conn.execute(
            "SELECT id FROM logic_tags WHERE name = ?", (tag,)
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute("INSERT INTO logic_tags (name) VALUES (?)", (tag,))
        return cur.lastrowid

    # ── CRUD ─────────────────────────────────────────────────────────────

    def save(self, name: str, expression: str,
             variable_map: Optional[dict] = None,
             description: str = "",
             tags: Optional[List[str]] = None) -> int:
        """
        保存 / 更新逻辑表达式。

        - 同名已存在 → 先自动保存旧版历史，再 UPDATE
        - 不存在      → INSERT
        - 自动处理标签关联

        Args:
            name: 表达式唯一名称
            expression: 逻辑表达式文本
            variable_map: 变量映射字典
            description: 描述文字
            tags: 标签名称列表

        Returns:
            表达式 ID
        """
        if variable_map is None:
            variable_map = {}
        if tags is None:
            tags = []
        variable_map_json = json.dumps(variable_map, ensure_ascii=False)

        conn = self._get_conn()
        try:
            # 检查是否已存在同名记录
            existing = conn.execute(
                "SELECT id, expression, variable_map FROM logic_expressions WHERE name = ?",
                (name,),
            ).fetchone()

            if existing:
                expr_id = existing["id"]
                # 保存旧版到历史
                conn.execute(
                    """
                    INSERT INTO logic_expression_history
                        (expression_id, expression, variable_map, change_note)
                    VALUES (?, ?, ?, '自动保存')
                    """,
                    (expr_id, existing["expression"], existing["variable_map"]),
                )
                # UPDATE 现有记录
                conn.execute(
                    """
                    UPDATE logic_expressions
                       SET expression = ?, variable_map = ?, description = ?,
                           updated_at = datetime('now','localtime')
                     WHERE id = ?
                    """,
                    (expression, variable_map_json, description, expr_id),
                )
            else:
                cur = conn.execute(
                    """
                    INSERT INTO logic_expressions
                        (name, description, expression, variable_map)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, description, expression, variable_map_json),
                )
                expr_id = cur.lastrowid

            # ── 处理标签 ─────────────────────────────────────────────
            # 清除旧标签关联
            conn.execute(
                "DELETE FROM logic_expression_tags WHERE expression_id = ?",
                (expr_id,),
            )
            # 写入新标签关联
            for tag in tags:
                tag = tag.strip()
                if not tag:
                    continue
                tag_id = self._get_or_create_tag(conn, tag)
                conn.execute(
                    "INSERT OR IGNORE INTO logic_expression_tags (expression_id, tag_id) VALUES (?, ?)",
                    (expr_id, tag_id),
                )

            conn.commit()
            return expr_id
        finally:
            conn.close()

    def load(self, name: str) -> Optional[dict]:
        """按名称加载表达式。返回完整 dict（含 tags），不存在返回 None。"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM logic_expressions WHERE name = ?", (name,)
            ).fetchone()
            if row is None:
                return None
            d = self._row_to_dict(row)
            d["tags"] = self._fetch_tags(conn, d["id"])
            return d
        finally:
            conn.close()

    def load_by_id(self, expr_id: int) -> Optional[dict]:
        """按 ID 加载表达式。"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM logic_expressions WHERE id = ?", (expr_id,)
            ).fetchone()
            if row is None:
                return None
            d = self._row_to_dict(row)
            d["tags"] = self._fetch_tags(conn, d["id"])
            return d
        finally:
            conn.close()

    def delete(self, name: str) -> bool:
        """
        删除表达式及其关联的标签和历史。
        外键 ON DELETE CASCADE 自动处理关联表。
        """
        conn = self._get_conn()
        try:
            cur = conn.execute(
                "DELETE FROM logic_expressions WHERE name = ?", (name,)
            )
            deleted = cur.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()

    def list_all(self, tag: Optional[str] = None) -> List[dict]:
        """
        列出所有表达式，可选按标签过滤。

        Args:
            tag: 标签名称，None 表示不过滤

        Returns:
            dict 列表，每项含完整字段（含 tags）
        """
        conn = self._get_conn()
        try:
            if tag:
                rows = conn.execute(
                    """
                    SELECT e.*
                      FROM logic_expressions e
                      JOIN logic_expression_tags et ON et.expression_id = e.id
                      JOIN logic_tags t ON t.id = et.tag_id
                     WHERE t.name = ?
                     ORDER BY e.updated_at DESC
                    """,
                    (tag,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM logic_expressions ORDER BY updated_at DESC"
                ).fetchall()

            results = []
            for row in rows:
                d = self._row_to_dict(row)
                d["tags"] = self._fetch_tags(conn, d["id"])
                results.append(d)
            return results
        finally:
            conn.close()

    def search(self, keyword: str) -> List[dict]:
        """
        按名称 / 描述 / 表达式模糊搜索。

        LIKE %keyword% 匹配 name、description、expression 字段。
        """
        conn = self._get_conn()
        try:
            pattern = f"%{keyword}%"
            rows = conn.execute(
                """
                SELECT * FROM logic_expressions
                 WHERE name LIKE ?
                    OR description LIKE ?
                    OR expression LIKE ?
                 ORDER BY updated_at DESC
                """,
                (pattern, pattern, pattern),
            ).fetchall()

            results = []
            for row in rows:
                d = self._row_to_dict(row)
                d["tags"] = self._fetch_tags(conn, d["id"])
                results.append(d)
            return results
        finally:
            conn.close()

    # ── 标签管理 ─────────────────────────────────────────────────────────

    def add_tag(self, expr_id: int, tag: str) -> bool:
        """
        为表达式添加标签（标签不存在则自动创建）。

        Returns:
            True 表示标签已添加（含已存在的情况），False 表示表达式不存在
        """
        conn = self._get_conn()
        try:
            # 确认表达式存在
            row = conn.execute(
                "SELECT 1 FROM logic_expressions WHERE id = ?", (expr_id,)
            ).fetchone()
            if row is None:
                return False
            tag_id = self._get_or_create_tag(conn, tag)
            conn.execute(
                "INSERT OR IGNORE INTO logic_expression_tags (expression_id, tag_id) VALUES (?, ?)",
                (expr_id, tag_id),
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def remove_tag(self, expr_id: int, tag: str) -> bool:
        """
        移除表达式的指定标签。

        Returns:
            True 表示成功移除，False 表示表达式或标签不存在
        """
        conn = self._get_conn()
        try:
            # 获取标签 ID
            tag_row = conn.execute(
                "SELECT id FROM logic_tags WHERE name = ?", (tag,)
            ).fetchone()
            if tag_row is None:
                return False
            cur = conn.execute(
                "DELETE FROM logic_expression_tags WHERE expression_id = ? AND tag_id = ?",
                (expr_id, tag_row["id"]),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def get_all_tags(self) -> List[str]:
        """获取系统中所有标签名称（按名称排序）。"""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT name FROM logic_tags ORDER BY name"
            ).fetchall()
            return [r["name"] for r in rows]
        finally:
            conn.close()

    # ── 版本历史 ─────────────────────────────────────────────────────────

    def save_history(self, expr_id: int, old_expression: str,
                     old_variable_map: Optional[dict] = None,
                     note: str = "") -> int:
        """
        保存修改前的快照到历史表。

        Args:
            expr_id: 表达式 ID
            old_expression: 修改前的表达式文本
            old_variable_map: 修改前的变量映射（可选）
            note: 变更说明

        Returns:
            历史记录 ID
        """
        if old_variable_map is None:
            old_variable_map = {}
        variable_map_json = json.dumps(old_variable_map, ensure_ascii=False)

        conn = self._get_conn()
        try:
            cur = conn.execute(
                """
                INSERT INTO logic_expression_history
                    (expression_id, expression, variable_map, change_note)
                VALUES (?, ?, ?, ?)
                """,
                (expr_id, old_expression, variable_map_json, note),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_history(self, expr_id: int) -> List[dict]:
        """获取指定表达式的修改历史（按时间升序）。"""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT * FROM logic_expression_history
                 WHERE expression_id = ?
                 ORDER BY changed_at ASC
                """,
                (expr_id,),
            ).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                if isinstance(d.get("variable_map"), str):
                    d["variable_map"] = json.loads(d["variable_map"])
                results.append(d)
            return results
        finally:
            conn.close()
