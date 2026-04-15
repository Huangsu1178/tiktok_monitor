"""
TikTok Monitor - Database Module
SQLite 数据库管理，支持 TikTok / 抖音双平台账号、视频与分析结果存储
"""
import json
import os
import sqlite3

# 使用 config.py 中的数据库配置
from config import get_db_path

DB_PATH = get_db_path()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(column["name"] == column_name for column in columns)


def _recreate_influencers_table(conn):
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE influencers RENAME TO influencers_legacy")
    cursor.execute(
        """
        CREATE TABLE influencers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL DEFAULT 'tiktok',
            username TEXT NOT NULL,
            display_name TEXT,
            avatar_url TEXT,
            follower_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            video_count INTEGER DEFAULT 0,
            bio TEXT,
            profile_url TEXT,
            is_active INTEGER DEFAULT 1,
            last_fetched_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(platform, username)
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO influencers (
            id, platform, username, display_name, avatar_url, follower_count,
            following_count, video_count, bio, profile_url, is_active,
            last_fetched_at, created_at
        )
        SELECT
            id,
            'tiktok',
            username,
            display_name,
            avatar_url,
            follower_count,
            following_count,
            video_count,
            bio,
            profile_url,
            is_active,
            last_fetched_at,
            created_at
        FROM influencers_legacy
        """
    )
    cursor.execute("DROP TABLE influencers_legacy")


def _recreate_videos_table(conn):
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE videos RENAME TO videos_legacy")
    cursor.execute(
        """
        CREATE TABLE videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            influencer_id INTEGER NOT NULL,
            platform TEXT NOT NULL DEFAULT 'tiktok',
            video_id TEXT NOT NULL,
            title TEXT,
            description TEXT,
            video_url TEXT,
            thumbnail_url TEXT,
            play_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            share_count INTEGER DEFAULT 0,
            duration INTEGER DEFAULT 0,
            hashtags TEXT,
            music_name TEXT,
            published_at TEXT,
            local_file_path TEXT,
            fetched_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (influencer_id) REFERENCES influencers(id),
            UNIQUE(platform, video_id)
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO videos (
            id, influencer_id, platform, video_id, title, description, video_url,
            thumbnail_url, play_count, like_count, comment_count, share_count,
            duration, hashtags, music_name, published_at, local_file_path, fetched_at
        )
        SELECT
            id,
            influencer_id,
            'tiktok',
            video_id,
            title,
            description,
            video_url,
            thumbnail_url,
            play_count,
            like_count,
            comment_count,
            share_count,
            duration,
            hashtags,
            music_name,
            published_at,
            local_file_path,
            fetched_at
        FROM videos_legacy
        """
    )
    cursor.execute("DROP TABLE videos_legacy")


def _ensure_schema(conn):
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS influencers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL DEFAULT 'tiktok',
            username TEXT NOT NULL,
            display_name TEXT,
            avatar_url TEXT,
            follower_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            video_count INTEGER DEFAULT 0,
            bio TEXT,
            profile_url TEXT,
            is_active INTEGER DEFAULT 1,
            last_fetched_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(platform, username)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            influencer_id INTEGER NOT NULL,
            platform TEXT NOT NULL DEFAULT 'tiktok',
            video_id TEXT NOT NULL,
            title TEXT,
            description TEXT,
            video_url TEXT,
            thumbnail_url TEXT,
            play_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            share_count INTEGER DEFAULT 0,
            duration INTEGER DEFAULT 0,
            hashtags TEXT,
            music_name TEXT,
            published_at TEXT,
            local_file_path TEXT,
            fetched_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (influencer_id) REFERENCES influencers(id),
            UNIQUE(platform, video_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            hook_type TEXT,
            hook_description TEXT,
            opening_script TEXT,
            content_structure TEXT,
            bgm_strategy TEXT,
            visual_style TEXT,
            copywriting_style TEXT,
            replication_suggestions TEXT,
            raw_response TEXT,
            analyzed_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fetch_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            influencer_id INTEGER,
            status TEXT,
            message TEXT,
            videos_found INTEGER DEFAULT 0,
            videos_new INTEGER DEFAULT 0,
            started_at TEXT,
            finished_at TEXT,
            FOREIGN KEY (influencer_id) REFERENCES influencers(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS hook_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hook_type TEXT NOT NULL,
            hook_description TEXT,
            video_id TEXT NOT NULL,
            video_url TEXT,
            play_count INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0,
            opening_script TEXT,
            content_structure TEXT,
            replication_suggestions TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ab_comparison (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_a_video_ids TEXT,
            group_b_video_ids TEXT,
            group_a_label TEXT DEFAULT 'A组',
            group_b_label TEXT DEFAULT 'B组',
            winner TEXT,
            comparison_result TEXT,
            analyzed_at TEXT DEFAULT (datetime('now'))
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT NOT NULL,
            title TEXT NOT NULL,
            subject_label TEXT,
            summary TEXT,
            source_payload TEXT,
            result_payload TEXT,
            export_markdown TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )


def _migrate_legacy_schema(conn):
    if _table_exists(conn, "influencers") and not _column_exists(conn, "influencers", "platform"):
        _recreate_influencers_table(conn)

    if _table_exists(conn, "videos") and not _column_exists(conn, "videos", "platform"):
        _recreate_videos_table(conn)


def init_database():
    conn = get_connection()
    _migrate_legacy_schema(conn)
    _ensure_schema(conn)

    defaults = [
        ("openai_api_key", ""),
        ("openai_api_base", ""),
        ("openai_model", "gpt-4.1-mini"),
        ("fetch_interval_hours", "1"),
        ("download_path", os.path.expanduser("~/Downloads/TikTok_Monitor")),
        ("proxy_url", ""),
        ("auto_fetch_enabled", "0"),
        ("max_videos_per_fetch", "20"),
    ]
    for key, value in defaults:
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )

    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at: {DB_PATH}")


def add_influencer(username: str, display_name: str = "", profile_url: str = "", platform: str = "tiktok") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    username = (username or "").strip()
    profile_url = (profile_url or "").strip()
    platform = (platform or "tiktok").strip().lower()

    if platform == "douyin" and profile_url:
        existing = conn.execute(
            "SELECT id FROM influencers WHERE platform=? AND profile_url=?",
            (platform, profile_url),
        ).fetchone()
        if existing:
            conn.close()
            return 0

    cursor.execute(
        """
        INSERT OR IGNORE INTO influencers (platform, username, display_name, profile_url)
        VALUES (?, ?, ?, ?)
        """,
        (platform, username, display_name, profile_url),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_all_influencers(platform: str = ""):
    conn = get_connection()
    if platform:
        rows = conn.execute(
            "SELECT * FROM influencers WHERE platform=? ORDER BY created_at DESC",
            (platform,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM influencers ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_active_influencers(platform: str = ""):
    conn = get_connection()
    if platform:
        rows = conn.execute(
            "SELECT * FROM influencers WHERE is_active=1 AND platform=? ORDER BY created_at DESC",
            (platform,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM influencers WHERE is_active=1 ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_influencer_profile(influencer_id: int, data: dict):
    if not data:
        return
    conn = get_connection()
    fields = ", ".join([f"{k}=?" for k in data.keys()])
    values = list(data.values()) + [influencer_id]
    conn.execute(f"UPDATE influencers SET {fields} WHERE id=?", values)
    conn.commit()
    conn.close()


def delete_influencer(influencer_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM influencers WHERE id=?", (influencer_id,))
    conn.execute("DELETE FROM videos WHERE influencer_id=?", (influencer_id,))
    conn.commit()
    conn.close()


def toggle_influencer_active(influencer_id: int, is_active: bool):
    conn = get_connection()
    conn.execute("UPDATE influencers SET is_active=? WHERE id=?", (1 if is_active else 0, influencer_id))
    conn.commit()
    conn.close()


def save_video(influencer_id: int, video_data: dict) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    platform = video_data.get("platform", "tiktok")
    existing = cursor.execute(
        "SELECT id FROM videos WHERE platform=? AND video_id=?",
        (platform, video_data.get("video_id")),
    ).fetchone()

    if existing:
        cursor.execute(
            """
            UPDATE videos SET
                title=?, description=?, video_url=?, thumbnail_url=?,
                play_count=?, like_count=?, comment_count=?, share_count=?,
                duration=?, hashtags=?, music_name=?, published_at=?,
                fetched_at=datetime('now')
            WHERE platform=? AND video_id=?
            """,
            (
                video_data.get("title", ""),
                video_data.get("description", ""),
                video_data.get("video_url", ""),
                video_data.get("thumbnail_url", ""),
                video_data.get("play_count", 0),
                video_data.get("like_count", 0),
                video_data.get("comment_count", 0),
                video_data.get("share_count", 0),
                video_data.get("duration", 0),
                video_data.get("hashtags", ""),
                video_data.get("music_name", ""),
                video_data.get("published_at", ""),
                platform,
                video_data.get("video_id"),
            ),
        )
        conn.commit()
        conn.close()
        return False

    cursor.execute(
        """
        INSERT INTO videos (
            influencer_id, platform, video_id, title, description, video_url,
            thumbnail_url, play_count, like_count, comment_count, share_count,
            duration, hashtags, music_name, published_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            influencer_id,
            platform,
            video_data.get("video_id"),
            video_data.get("title", ""),
            video_data.get("description", ""),
            video_data.get("video_url", ""),
            video_data.get("thumbnail_url", ""),
            video_data.get("play_count", 0),
            video_data.get("like_count", 0),
            video_data.get("comment_count", 0),
            video_data.get("share_count", 0),
            video_data.get("duration", 0),
            video_data.get("hashtags", ""),
            video_data.get("music_name", ""),
            video_data.get("published_at", ""),
        ),
    )
    conn.commit()
    conn.close()
    return True


def get_videos_by_influencer(influencer_id: int, limit: int = 50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM videos WHERE influencer_id=? ORDER BY play_count DESC LIMIT ?",
        (influencer_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_videos_by_influencer_ids(influencer_ids: list[int], limit: int = 100):
    influencer_ids = [int(influencer_id) for influencer_id in influencer_ids if influencer_id]
    if not influencer_ids:
        return []

    placeholders = ",".join("?" for _ in influencer_ids)
    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT
            v.*,
            i.username AS influencer_username,
            i.display_name AS influencer_display_name,
            i.platform AS influencer_platform
        FROM videos v
        JOIN influencers i ON i.id = v.influencer_id
        WHERE v.influencer_id IN ({placeholders})
        ORDER BY v.play_count DESC
        LIMIT ?
        """,
        (*influencer_ids, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_video_by_id(video_db_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM videos WHERE id=?", (video_db_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_video_local_path(video_db_id: int, local_path: str):
    conn = get_connection()
    conn.execute("UPDATE videos SET local_file_path=? WHERE id=?", (local_path, video_db_id))
    conn.commit()
    conn.close()


def save_ai_analysis(video_db_id: int, analysis: dict):
    conn = get_connection()
    conn.execute(
        """
        INSERT OR REPLACE INTO ai_analysis
        (video_id, hook_type, hook_description, opening_script, content_structure,
        bgm_strategy, visual_style, copywriting_style, replication_suggestions, raw_response)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            video_db_id,
            analysis.get("hook_type", ""),
            analysis.get("hook_description", ""),
            analysis.get("opening_script", ""),
            analysis.get("content_structure", ""),
            analysis.get("bgm_strategy", ""),
            analysis.get("visual_style", ""),
            analysis.get("copywriting_style", ""),
            analysis.get("replication_suggestions", ""),
            analysis.get("raw_response", ""),
        ),
    )
    conn.commit()
    conn.close()


def get_ai_analysis(video_db_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM ai_analysis WHERE video_id=?", (video_db_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_setting(key: str, default: str = "") -> str:
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def add_fetch_log(
    influencer_id: int,
    status: str,
    message: str,
    videos_found: int = 0,
    videos_new: int = 0,
    started_at: str = "",
    finished_at: str = "",
):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO fetch_logs (influencer_id, status, message, videos_found, videos_new, started_at, finished_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (influencer_id, status, message, videos_found, videos_new, started_at, finished_at),
    )
    conn.commit()
    conn.close()


def get_recent_logs(limit: int = 50):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT fl.*, i.username, i.platform FROM fetch_logs fl
        LEFT JOIN influencers i ON fl.influencer_id = i.id
        ORDER BY fl.id DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_hook_entry(entry: dict):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO hook_library
        (hook_type, hook_description, video_id, video_url, play_count,
         engagement_rate, opening_script, content_structure, replication_suggestions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry.get("hook_type", ""),
            entry.get("hook_description", ""),
            entry.get("video_id", ""),
            entry.get("video_url", ""),
            entry.get("play_count", 0),
            entry.get("engagement_rate", 0),
            entry.get("opening_script", ""),
            entry.get("content_structure", ""),
            entry.get("replication_suggestions", ""),
        ),
    )
    conn.commit()
    conn.close()


def get_hook_library(hook_type: str = "", limit: int = 50):
    conn = get_connection()
    if hook_type:
        rows = conn.execute(
            "SELECT * FROM hook_library WHERE hook_type=? ORDER BY play_count DESC LIMIT ?",
            (hook_type, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM hook_library ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_hook_statistics():
    conn = get_connection()
    type_stats = conn.execute(
        """
        SELECT hook_type, COUNT(*) as count, AVG(play_count) as avg_plays, AVG(engagement_rate) as avg_engagement
        FROM hook_library
        GROUP BY hook_type
        ORDER BY count DESC
        """
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) as count FROM hook_library").fetchone()
    conn.close()
    return {
        "total_hooks": total["count"] if total else 0,
        "by_type": [dict(r) for r in type_stats],
    }


def save_ab_comparison(
    group_a_ids: list,
    group_b_ids: list,
    result: dict,
    group_a_label: str = "A组",
    group_b_label: str = "B组",
) -> int:
    """保存AB对比分析结果，返回记录ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        group_a_video_ids = ",".join(str(vid) for vid in group_a_ids) if group_a_ids else ""
        group_b_video_ids = ",".join(str(vid) for vid in group_b_ids) if group_b_ids else ""
        winner = result.get("winner", "")
        comparison_result = json.dumps(result, ensure_ascii=False)

        cursor.execute(
            """
            INSERT INTO ab_comparison
            (group_a_video_ids, group_b_video_ids, group_a_label, group_b_label, winner, comparison_result)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                group_a_video_ids,
                group_b_video_ids,
                group_a_label,
                group_b_label,
                winner,
                comparison_result,
            ),
        )
        conn.commit()
        row_id = cursor.lastrowid
        return row_id
    except Exception as e:
        print(f"[DB] 保存AB对比分析失败: {e}")
        return 0
    finally:
        conn.close()


def get_ab_comparisons(limit: int = 20) -> list:
    """获取历史AB对比记录列表，按时间倒序"""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, group_a_label, group_b_label, winner, analyzed_at
            FROM ab_comparison
            ORDER BY analyzed_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[DB] 获取AB对比记录列表失败: {e}")
        return []
    finally:
        conn.close()


def get_ab_comparison(comparison_id: int) -> dict:
    """获取单条AB对比详情，包含完整的comparison_result（反序列化为dict）"""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM ab_comparison WHERE id=?",
            (comparison_id,),
        ).fetchone()
        if not row:
            return None

        result = dict(row)
        if result.get("comparison_result"):
            try:
                result["comparison_result"] = json.loads(result["comparison_result"])
            except json.JSONDecodeError:
                result["comparison_result"] = {}
        return result
    except Exception as e:
        print(f"[DB] 获取AB对比详情失败: {e}")
        return None
    finally:
        conn.close()


def save_ai_report(
    report_type: str,
    title: str,
    result_payload: dict,
    source_payload: dict | None = None,
    subject_label: str = "",
    summary: str = "",
    export_markdown: str = "",
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO ai_reports
            (report_type, title, subject_label, summary, source_payload, result_payload, export_markdown)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (report_type or "").strip(),
                (title or "").strip() or "AI 分析报告",
                subject_label or "",
                summary or "",
                json.dumps(source_payload or {}, ensure_ascii=False),
                json.dumps(result_payload or {}, ensure_ascii=False),
                export_markdown or "",
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as exc:
        print(f"[DB] 保存 AI 报告失败: {exc}")
        return 0
    finally:
        conn.close()


def get_ai_reports(limit: int = 50, report_type: str = "") -> list:
    conn = get_connection()
    try:
        if report_type:
            rows = conn.execute(
                """
                SELECT id, report_type, title, subject_label, summary, created_at
                FROM ai_reports
                WHERE report_type=?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (report_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, report_type, title, subject_label, summary, created_at
                FROM ai_reports
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[DB] 获取 AI 报告列表失败: {exc}")
        return []
    finally:
        conn.close()


def get_ai_report(report_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM ai_reports WHERE id=?", (report_id,)).fetchone()
        if not row:
            return None

        result = dict(row)
        for key in ("source_payload", "result_payload"):
            raw = result.get(key)
            if raw:
                try:
                    result[key] = json.loads(raw)
                except json.JSONDecodeError:
                    result[key] = {}
            else:
                result[key] = {}
        return result
    except Exception as exc:
        print(f"[DB] 获取 AI 报告详情失败: {exc}")
        return None
    finally:
        conn.close()
