"""
TikTok Monitor - Data View Page
数据视图页面
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from core.platforms import platform_label


TABLE_STYLE = """
QTableWidget {
    background-color: #1a1a2e;
    border: 1px solid #2d3748;
    border-radius: 8px;
    color: #e2e8f0;
    gridline-color: #2d3748;
    font-size: 13px;
}
QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #2d3748;
}
QTableWidget::item:selected {
    background-color: #2d3748;
}
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

COMBO_STYLE = """
QComboBox {
    background-color: #2d3748;
    color: #e2e8f0;
    border: 1px solid #4a5568;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-width: 200px;
}
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #2d3748;
    color: #e2e8f0;
    border: 1px solid #4a5568;
    selection-background-color: #4a5568;
}
"""


class DataViewPage(QWidget):
    """数据视图页面"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._current_influencer = None
        self._metrics_helper = None
        self._videos = []
        self._build_ui()
        self.refresh()

    def _get_metrics_helper(self):
        if self._metrics_helper is None:
            from skills import TikTokAIAnalysisSkill

            self._metrics_helper = TikTokAIAnalysisSkill()
        return self._metrics_helper

    def _build_ui(self):
        self.setStyleSheet("background-color: #0f0f1a;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("数据视图")
        title.setStyleSheet("color: #e2e8f0; font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        filter_row = QHBoxLayout()
        filter_label = QLabel("选择博主：")
        filter_label.setStyleSheet("color: #a0aec0; font-size: 14px;")
        filter_row.addWidget(filter_label)

        self.influencer_combo = QComboBox()
        self.influencer_combo.setStyleSheet(COMBO_STYLE)
        self.influencer_combo.currentIndexChanged.connect(self._on_influencer_changed)
        filter_row.addWidget(self.influencer_combo)
        filter_row.addStretch()

        analyze_all_btn = QPushButton("批量 AI 分析（Top10）")
        analyze_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #6b46c1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #553c9a; }
            """
        )
        analyze_all_btn.clicked.connect(self._analyze_batch)
        filter_row.addWidget(analyze_all_btn)
        layout.addLayout(filter_row)

        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(12)
        for attr, label, color in [
            ("stat_total", "总视频数: 0", "#4299e1"),
            ("stat_avg_play", "平均播放: 0", "#48bb78"),
            ("stat_max_play", "最高播放: 0", "#ed8936"),
            ("stat_avg_like", "平均点赞: 0", "#9f7aea"),
            ("stat_avg_engage", "平均互动率: 0%", "#f6ad55"),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"""
                background-color: #1a1a2e;
                color: {color};
                border: 1px solid #2d3748;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 600;
                """
            )
            setattr(self, attr, lbl)
            self.stats_row.addWidget(lbl)
        self.stats_row.addStretch()
        layout.addLayout(self.stats_row)

        self.table = QTableWidget()
        self.table.setStyleSheet(TABLE_STYLE + "QTableWidget { alternate-background-color: #16213e; }")
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            ["#", "视频描述", "播放量", "点赞数", "评论数", "分享数", "互动率", "BGM", "发布时间", "操作"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in range(2, 8):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def set_influencer(self, influencer: dict):
        self._current_influencer = influencer
        self.refresh()

    def refresh(self):
        from data.database import get_all_influencers

        influencers = get_all_influencers()

        self.influencer_combo.blockSignals(True)
        self.influencer_combo.clear()
        self.influencer_combo.addItem("-- 请选择博主 --", None)
        for influencer in influencers:
            self.influencer_combo.addItem(f"{platform_label(influencer.get('platform'))} · @{influencer['username']}", influencer)

        if self._current_influencer:
            for i in range(self.influencer_combo.count()):
                data = self.influencer_combo.itemData(i)
                if data and data.get("id") == self._current_influencer.get("id"):
                    self.influencer_combo.setCurrentIndex(i)
                    break

        self.influencer_combo.blockSignals(False)
        self._load_videos()

    def _on_influencer_changed(self, index: int):
        self._current_influencer = self.influencer_combo.itemData(index)
        self._load_videos()

    def _load_videos(self):
        if not self._current_influencer:
            self._videos = []
            self.table.setRowCount(0)
            self.stat_total.setText("总视频数: 0")
            self.stat_avg_play.setText("平均播放: 0")
            self.stat_max_play.setText("最高播放: 0")
            self.stat_avg_like.setText("平均点赞: 0")
            self.stat_avg_engage.setText("平均互动率: 0%")
            return

        from data.database import get_videos_by_influencer

        videos = get_videos_by_influencer(self._current_influencer["id"], 100)
        self._videos = videos

        if videos:
            total = len(videos)
            avg_play = sum(v.get("play_count", 0) for v in videos) / total
            max_play = max(v.get("play_count", 0) for v in videos)
            avg_like = sum(v.get("like_count", 0) for v in videos) / total

            temp_analyzer = self._get_metrics_helper()
            engagement_rates = [
                temp_analyzer.calculate_engagement_metrics(video)["engagement_rate"] for video in videos
            ]
            avg_engage = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0

            self.stat_total.setText(f"总视频数: {total}")
            self.stat_avg_play.setText(f"平均播放: {self._format_number(avg_play)}")
            self.stat_max_play.setText(f"最高播放: {self._format_number(max_play)}")
            self.stat_avg_like.setText(f"平均点赞: {self._format_number(avg_like)}")
            self.stat_avg_engage.setText(f"平均互动率: {avg_engage:.2f}%")

        self.table.setRowCount(len(videos))

        for row, video in enumerate(videos):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

            desc = video.get("description") or video.get("title") or "无描述"
            self.table.setItem(row, 1, QTableWidgetItem(desc[:80] + "..." if len(desc) > 80 else desc))

            play_item = QTableWidgetItem(self._format_number(video.get("play_count", 0)))
            if (video.get("play_count") or 0) > 1_000_000:
                play_item.setForeground(QColor("#f6ad55"))
            self.table.setItem(row, 2, play_item)
            self.table.setItem(row, 3, QTableWidgetItem(self._format_number(video.get("like_count", 0))))
            self.table.setItem(row, 4, QTableWidgetItem(self._format_number(video.get("comment_count", 0))))
            self.table.setItem(row, 5, QTableWidgetItem(self._format_number(video.get("share_count", 0))))

            metrics = self._get_metrics_helper().calculate_engagement_metrics(video)
            engage_rate = metrics["engagement_rate"]
            engage_item = QTableWidgetItem(f"{engage_rate:.2f}%")
            if engage_rate >= 10:
                engage_item.setForeground(QColor("#68d391"))
            elif engage_rate >= 5:
                engage_item.setForeground(QColor("#f6ad55"))
            else:
                engage_item.setForeground(QColor("#fc8181"))
            self.table.setItem(row, 6, engage_item)

            self.table.setItem(row, 7, QTableWidgetItem(video.get("music_name") or ""))
            self.table.setItem(row, 8, QTableWidgetItem(video.get("published_at") or ""))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            analyze_btn = QPushButton("AI 分析")
            analyze_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #6b46c1;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #553c9a; }
                """
            )
            analyze_btn.clicked.connect(lambda _, vid=video: self._analyze_single(vid))
            btn_layout.addWidget(analyze_btn)

            if video.get("video_url"):
                dl_btn = QPushButton("下载")
                dl_btn.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #2d6a4f;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-size: 11px;
                    }
                    QPushButton:hover { background-color: #1b4332; }
                    """
                )
                dl_btn.clicked.connect(lambda _, vid=video: self._download_video(vid))
                btn_layout.addWidget(dl_btn)

            self.table.setCellWidget(row, 9, btn_widget)
            self.table.setRowHeight(row, 48)

    def _analyze_single(self, video: dict):
        """分析单个视频"""
        if not self._current_influencer:
            QMessageBox.warning(self, "提示", "请先选择一个博主")
            return

        self.main_window.navigate_to(3)
        self.main_window.ai_report_page.open_single_analysis(self._current_influencer, video)

    def _analyze_batch(self):
        """批量分析当前博主的 Top10 视频"""
        if not self._current_influencer:
            QMessageBox.warning(self, "提示", "请先选择一个博主")
            return

        from data.database import get_videos_by_influencer

        videos = get_videos_by_influencer(self._current_influencer["id"], 10)
        if not videos:
            QMessageBox.warning(self, "提示", "该博主暂无视频数据，请先抓取")
            return

        self.main_window.navigate_to(3)
        self.main_window.ai_report_page.open_batch_analysis(self._current_influencer, videos)

    def _download_video(self, video: dict):
        """下载视频"""
        from data.database import get_setting, update_video_local_path

        download_path = get_setting("download_path", os.path.expanduser("~/Downloads/TikTok_Monitor"))
        username = self._current_influencer.get("username", "unknown") if self._current_influencer else "unknown"
        platform = self._current_influencer.get("platform", "tiktok") if self._current_influencer else "tiktok"
        output_dir = os.path.join(download_path, platform, username)

        QMessageBox.information(
            self,
            "开始下载",
            f"正在下载视频到：\n{output_dir}\n\n下载完成后将提示。",
        )

        video_url = video.get("video_url", "")
        video_id = video.get("video_id", "")
        local_path = self.main_window.scraper.download_video_no_watermark(
            video_url, output_dir, f"{platform}_{video_id}"
        )

        if local_path:
            update_video_local_path(video["id"], local_path)
            QMessageBox.information(self, "下载完成", f"视频已保存到：\n{local_path}")
            return

        QMessageBox.warning(self, "下载失败", "视频下载失败，请检查网络连接或视频 URL 是否有效。")

    def _format_number(self, value):
        value = value or 0
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{value / 1_000:.0f}K"
        return str(int(value))
