"""
Dashboard page for multi-platform monitoring.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from core.platforms import platform_label


CARD_STYLE = """
QFrame#stat_card {
    background-color: #1a1a2e;
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 16px;
}
"""

TABLE_STYLE = """
QTableWidget {
    background-color: #1a1a2e;
    border: 1px solid #2d3748;
    border-radius: 8px;
    color: #e2e8f0;
    gridline-color: #2d3748;
    font-size: 13px;
}
QTableWidget::item { padding: 8px 12px; border-bottom: 1px solid #2d3748; }
QTableWidget::item:selected { background-color: #2d3748; }
QHeaderView::section {
    background-color: #16213e;
    color: #a0aec0;
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid #2d3748;
    font-size: 12px;
    font-weight: 600;
}
"""


class StatCard(QFrame):
    def __init__(self, icon: str, title: str, value: str, color: str = "#e53e3e"):
        super().__init__()
        self.setObjectName("stat_card")
        self.setStyleSheet(CARD_STYLE + f"QFrame#stat_card {{ border-left: 4px solid {color}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 20))
        header.addWidget(icon_label)
        header.addStretch()

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #a0aec0; font-size: 12px; font-weight: 600;")
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")

        layout.addLayout(header)
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def update_value(self, value: str):
        self.value_label.setText(value)


class DashboardPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.setStyleSheet("background-color: #0f0f1a;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #0f0f1a; }")

        content = QWidget()
        content.setStyleSheet("background-color: #0f0f1a;")
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        title_row = QHBoxLayout()
        title = QLabel("双平台监控仪表盘")
        title.setStyleSheet("color: #e2e8f0; font-size: 22px; font-weight: bold;")
        title_row.addWidget(title)
        title_row.addStretch()

        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("QPushButton { background-color: #2d3748; color: #e2e8f0; border: none; border-radius: 8px; padding: 8px 16px; font-size: 13px; } QPushButton:hover { background-color: #4a5568; }")
        refresh_btn.clicked.connect(self.refresh)
        title_row.addWidget(refresh_btn)
        main_layout.addLayout(title_row)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        self.card_influencers = StatCard("账号", "监控账号数", "0", "#4299e1")
        self.card_videos = StatCard("视频", "已采集视频", "0", "#48bb78")
        self.card_new_today = StatCard("今日", "今日新增视频", "0", "#ed8936")
        self.card_avg_views = StatCard("流量", "平均播放量", "0", "#9f7aea")
        for card in [self.card_influencers, self.card_videos, self.card_new_today, self.card_avg_views]:
            cards_layout.addWidget(card)
        main_layout.addLayout(cards_layout)

        self.platform_summary = QLabel("")
        self.platform_summary.setStyleSheet("color: #a0aec0; font-size: 13px;")
        main_layout.addWidget(self.platform_summary)

        skills_title = QLabel("AI 能力模块")
        skills_title.setStyleSheet("color: #e2e8f0; font-size: 16px; font-weight: bold;")
        main_layout.addWidget(skills_title)
        self.skills_grid = QGridLayout()
        self.skills_grid.setSpacing(12)
        main_layout.addLayout(self.skills_grid)

        log_title = QLabel("最近抓取记录")
        log_title.setStyleSheet("color: #e2e8f0; font-size: 16px; font-weight: bold;")
        main_layout.addWidget(log_title)
        self.log_table = QTableWidget()
        self.log_table.setStyleSheet(TABLE_STYLE + "QTableWidget { alternate-background-color: #16213e; }")
        self.log_table.setColumnCount(7)
        self.log_table.setHorizontalHeaderLabels(["平台", "账号", "状态", "发现视频", "新增视频", "开始时间", "完成时间"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setMinimumHeight(280)
        main_layout.addWidget(self.log_table)

        hot_title = QLabel("热门视频")
        hot_title.setStyleSheet("color: #e2e8f0; font-size: 16px; font-weight: bold;")
        main_layout.addWidget(hot_title)
        self.hot_table = QTableWidget()
        self.hot_table.setStyleSheet(TABLE_STYLE)
        self.hot_table.setColumnCount(6)
        self.hot_table.setHorizontalHeaderLabels(["平台", "账号", "视频描述", "播放量", "点赞数", "发布时间"])
        self.hot_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.hot_table.verticalHeader().setVisible(False)
        self.hot_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.hot_table.setMinimumHeight(220)
        main_layout.addWidget(self.hot_table)

        main_layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        from data.database import get_all_influencers, get_connection, get_recent_logs
        from datetime import date

        influencers = get_all_influencers()
        self.card_influencers.update_value(str(len(influencers)))

        conn = get_connection()
        total_videos = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
        self.card_videos.update_value(f"{total_videos:,}")

        today = date.today().strftime("%Y-%m-%d")
        new_today = conn.execute("SELECT COUNT(*) FROM videos WHERE fetched_at LIKE ?", (f"{today}%",)).fetchone()[0]
        self.card_new_today.update_value(str(new_today))

        avg_views = conn.execute("SELECT AVG(play_count) FROM videos WHERE play_count > 0").fetchone()[0]
        self.card_avg_views.update_value(self._format_number(avg_views or 0))

        platform_rows = conn.execute(
            "SELECT platform, COUNT(*) AS cnt FROM influencers GROUP BY platform ORDER BY cnt DESC"
        ).fetchall()
        summary = " / ".join([f"{platform_label(row['platform'])}: {row['cnt']} 个账号" for row in platform_rows]) or "暂无监控账号"
        self.platform_summary.setText(f"平台分布：{summary}")

        self._update_skills_status()

        logs = get_recent_logs(20)
        self.log_table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            self.log_table.setItem(row, 0, QTableWidgetItem(platform_label(log.get("platform", "tiktok"))))
            self.log_table.setItem(row, 1, QTableWidgetItem(f"@{log.get('username', '未知')}"))
            status = log.get("status", "")
            status_item = QTableWidgetItem("成功" if status == "success" else "失败")
            status_item.setForeground(QColor("#68d391") if status == "success" else QColor("#fc8181"))
            self.log_table.setItem(row, 2, status_item)
            self.log_table.setItem(row, 3, QTableWidgetItem(str(log.get("videos_found", 0))))
            self.log_table.setItem(row, 4, QTableWidgetItem(str(log.get("videos_new", 0))))
            self.log_table.setItem(row, 5, QTableWidgetItem(log.get("started_at", "")))
            self.log_table.setItem(row, 6, QTableWidgetItem(log.get("finished_at", "")))

        hot_videos = conn.execute(
            """
            SELECT i.platform, i.username, v.description, v.play_count, v.like_count, v.published_at
            FROM videos v JOIN influencers i ON v.influencer_id = i.id
            ORDER BY v.play_count DESC LIMIT 10
            """
        ).fetchall()
        conn.close()

        self.hot_table.setRowCount(len(hot_videos))
        for row, video in enumerate(hot_videos):
            self.hot_table.setItem(row, 0, QTableWidgetItem(platform_label(video[0])))
            self.hot_table.setItem(row, 1, QTableWidgetItem(f"@{video[1]}"))
            desc = video[2] or "无描述"
            self.hot_table.setItem(row, 2, QTableWidgetItem(desc[:60] + "..." if len(desc) > 60 else desc))
            self.hot_table.setItem(row, 3, QTableWidgetItem(self._format_number(video[3] or 0)))
            self.hot_table.setItem(row, 4, QTableWidgetItem(f"{(video[4] or 0):,}"))
            self.hot_table.setItem(row, 5, QTableWidgetItem(video[5] or ""))

    def _update_skills_status(self):
        while self.skills_grid.count():
            item = self.skills_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not hasattr(self.main_window, "skill_registry"):
            return

        registry = self.main_window.skill_registry
        skills = registry.list_skills()
        skill_icons = {
            "ai_analysis": ("分析", "#e53e3e"),
            "hook_research": ("钩子", "#ed8936"),
            "format_research": ("格式", "#4299e1"),
            "reel_assembly": ("制作", "#48bb78"),
            "performance_tracker": ("追踪", "#9f7aea"),
            "content_pipeline": ("流水线", "#f6ad55"),
        }

        for idx, skill in enumerate(skills):
            icon, color = skill_icons.get(skill.skill_id, ("模块", "#a0aec0"))
            status = "已启用" if skill.requires_api else "本地可用"
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background-color: #1a1a2e; border: 1px solid #2d3748; border-left: 4px solid {color}; border-radius: 8px; padding: 12px; }}"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            name_label = QLabel(f"{icon} {skill.name}")
            name_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 700;")
            card_layout.addWidget(name_label)
            desc_label = QLabel(skill.description[:50] + "...")
            desc_label.setStyleSheet("color: #a0aec0; font-size: 11px;")
            desc_label.setWordWrap(True)
            card_layout.addWidget(desc_label)
            status_label = QLabel(status)
            status_label.setStyleSheet(f"color: {'#68d391' if skill.requires_api else '#f6ad55'}; font-size: 11px; font-weight: 600;")
            card_layout.addWidget(status_label)
            self.skills_grid.addWidget(card, idx // 3, idx % 3)

    def _format_number(self, value):
        value = value or 0
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{value / 1_000:.0f}K"
        return str(int(value))
