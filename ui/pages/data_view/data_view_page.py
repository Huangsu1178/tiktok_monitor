"""
TikTok Monitor - Data View Page
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.platforms import platform_label
from ui.components.theme import (
    SUCCESS,
    TEAL,
    TEXT_MUTED,
    VIOLET,
    accent_button_style,
    page_background_style,
    page_title_style,
    secondary_button_style,
    selector_style,
    table_button_style,
    table_style,
)

TEXT_TITLE = "\u6570\u636e\u89c6\u56fe"
TEXT_FILTER = "\u9009\u62e9\u535a\u4e3b\uff1a"
TEXT_SELECT_PLACEHOLDER = "\u8bf7\u9009\u62e9\u535a\u4e3b"
TEXT_SELECT_ALL = "\u5168\u9009"
TEXT_CLEAR = "\u6e05\u7a7a"
TEXT_BATCH_ANALYZE = "\u6279\u91cf AI \u5206\u6790\uff08Top10\uff09"
TEXT_NO_INFLUENCERS = "\u6682\u65e0\u535a\u4e3b"
TEXT_ALL_SELECTED = "\u5df2\u5168\u9009 {count} \u4e2a\u535a\u4e3b"
TEXT_SELECTED_COUNT = "\u5df2\u9009\u62e9 {count} \u4e2a\u535a\u4e3b"
TEXT_SCOPE_LABEL = "\u5df2\u9009 {count} \u4e2a\u535a\u4e3b"

TEXT_STAT_TOTAL = "\u603b\u89c6\u9891\u6570: {value}"
TEXT_STAT_AVG_PLAY = "\u5e73\u5747\u64ad\u653e: {value}"
TEXT_STAT_MAX_PLAY = "\u6700\u9ad8\u64ad\u653e: {value}"
TEXT_STAT_AVG_LIKE = "\u5e73\u5747\u70b9\u8d5e: {value}"
TEXT_STAT_AVG_ENGAGE = "\u5e73\u5747\u4e92\u52a8\u7387: {value}%"

TEXT_HEADERS = [
    "#",
    "\u535a\u4e3b",
    "\u89c6\u9891\u63cf\u8ff0",
    "\u64ad\u653e\u91cf",
    "\u70b9\u8d5e\u6570",
    "\u8bc4\u8bba\u6570",
    "\u5206\u4eab\u6570",
    "\u4e92\u52a8\u7387",
    "BGM",
    "\u53d1\u5e03\u65f6\u95f4",
    "\u64cd\u4f5c",
]

TEXT_NO_DESC = "\u65e0\u63cf\u8ff0"
TEXT_AI_ANALYZE = "AI \u5206\u6790"
TEXT_DOWNLOAD = "\u4e0b\u8f7d"

TEXT_PROMPT = "\u63d0\u793a"
TEXT_WARN_NO_VIDEO_INFLUENCER = "\u672a\u627e\u5230\u8be5\u89c6\u9891\u5bf9\u5e94\u7684\u535a\u4e3b\u4fe1\u606f"
TEXT_WARN_SELECT_ONE = "\u8bf7\u5148\u9009\u62e9\u81f3\u5c11\u4e00\u4e2a\u535a\u4e3b"
TEXT_WARN_NO_VIDEOS = "\u6240\u9009\u535a\u4e3b\u6682\u65e0\u89c6\u9891\u6570\u636e\uff0c\u8bf7\u5148\u6293\u53d6"

TEXT_DOWNLOAD_START = "\u5f00\u59cb\u4e0b\u8f7d"
TEXT_DOWNLOAD_START_BODY = "\u6b63\u5728\u4e0b\u8f7d\u89c6\u9891\u5230\uff1a\n{path}\n\n\u4e0b\u8f7d\u5b8c\u6210\u540e\u5c06\u63d0\u793a\u3002"
TEXT_DOWNLOAD_DONE = "\u4e0b\u8f7d\u5b8c\u6210"
TEXT_DOWNLOAD_DONE_BODY = "\u89c6\u9891\u5df2\u4fdd\u5b58\u5230\uff1a\n{path}"
TEXT_DOWNLOAD_FAILED = "\u4e0b\u8f7d\u5931\u8d25"
TEXT_DOWNLOAD_FAILED_BODY = (
    "\u89c6\u9891\u4e0b\u8f7d\u5931\u8d25\uff0c\u8bf7\u68c0\u67e5\u7f51\u7edc\u8fde\u63a5\u6216\u89c6\u9891 URL \u662f\u5426\u6709\u6548\u3002"
)


class DataViewPage(QWidget):
    """Data view page."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._current_influencer = None
        self._metrics_helper = None
        self._videos = []
        self._influencers = []
        self._influencer_by_id = {}
        self._selected_influencer_ids = set()
        self._menu_actions = {}
        self._build_ui()
        self.refresh()

    def _get_metrics_helper(self):
        if self._metrics_helper is None:
            from skills import TikTokAIAnalysisSkill

            self._metrics_helper = TikTokAIAnalysisSkill()
        return self._metrics_helper

    def _build_ui(self):
        self.setStyleSheet(page_background_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(TEXT_TITLE)
        title.setStyleSheet(page_title_style())
        layout.addWidget(title)

        filter_row = QHBoxLayout()
        filter_label = QLabel(TEXT_FILTER)
        filter_label.setStyleSheet("color: #a0aec0; font-size: 14px;")
        filter_row.addWidget(filter_label)

        self.influencer_menu = QMenu(self)
        self.influencer_menu.setStyleSheet(selector_style())

        self.influencer_selector = QToolButton()
        self.influencer_selector.setText(TEXT_SELECT_PLACEHOLDER)
        self.influencer_selector.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.influencer_selector.setMenu(self.influencer_menu)
        self.influencer_selector.setStyleSheet(selector_style())
        filter_row.addWidget(self.influencer_selector)

        select_all_btn = QPushButton(TEXT_SELECT_ALL)
        select_all_btn.setStyleSheet(secondary_button_style())
        select_all_btn.clicked.connect(self._select_all_influencers)
        filter_row.addWidget(select_all_btn)

        clear_btn = QPushButton(TEXT_CLEAR)
        clear_btn.setStyleSheet(secondary_button_style())
        clear_btn.clicked.connect(self._clear_selected_influencers)
        filter_row.addWidget(clear_btn)

        filter_row.addStretch()

        analyze_all_btn = QPushButton(TEXT_BATCH_ANALYZE)
        analyze_all_btn.setStyleSheet(accent_button_style())
        analyze_all_btn.clicked.connect(self._analyze_batch)
        filter_row.addWidget(analyze_all_btn)
        layout.addLayout(filter_row)

        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(12)
        for attr, label, color in [
            ("stat_total", TEXT_STAT_TOTAL.format(value=0), "#4299e1"),
            ("stat_avg_play", TEXT_STAT_AVG_PLAY.format(value=0), "#48bb78"),
            ("stat_max_play", TEXT_STAT_MAX_PLAY.format(value=0), "#ed8936"),
            ("stat_avg_like", TEXT_STAT_AVG_LIKE.format(value=0), "#9f7aea"),
            ("stat_avg_engage", TEXT_STAT_AVG_ENGAGE.format(value=0), "#f6ad55"),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"""
                background-color: #121c2b;
                color: {color};
                border: 1px solid #263a56;
                border-radius: 12px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 700;
                """
            )
            setattr(self, attr, lbl)
            self.stats_row.addWidget(lbl)
        self.stats_row.addStretch()
        layout.addLayout(self.stats_row)

        self.table = QTableWidget()
        self.table.setStyleSheet(table_style())
        self.table.setColumnCount(len(TEXT_HEADERS))
        self.table.setHorizontalHeaderLabels(TEXT_HEADERS)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for index in range(3, 8):
            header.setSectionResizeMode(index, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(8, 120)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(10, 180)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)  # 启用文本换行
        layout.addWidget(self.table)

    def set_influencer(self, influencer: dict):
        self._current_influencer = influencer
        influencer_id = influencer.get("id") if influencer else None
        self._selected_influencer_ids = {influencer_id} if influencer_id else set()
        self.refresh()

    def refresh(self):
        from data.database import get_all_influencers

        self._influencers = get_all_influencers()
        self._influencer_by_id = {influencer["id"]: influencer for influencer in self._influencers}

        preserved_ids = {
            influencer_id
            for influencer_id in self._selected_influencer_ids
            if influencer_id in self._influencer_by_id
        }
        if not preserved_ids and self._current_influencer and self._current_influencer.get("id") in self._influencer_by_id:
            preserved_ids = {self._current_influencer["id"]}
        self._selected_influencer_ids = preserved_ids

        self._rebuild_influencer_menu()
        self._sync_current_influencer()
        self._load_videos()

    def _rebuild_influencer_menu(self):
        self.influencer_menu.clear()
        self._menu_actions = {}

        if not self._influencers:
            empty_action = QAction(TEXT_NO_INFLUENCERS, self)
            empty_action.setEnabled(False)
            self.influencer_menu.addAction(empty_action)
            self._update_selector_text()
            return

        for influencer in self._influencers:
            label = f"{platform_label(influencer.get('platform'))} | @{influencer['username']}"
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(influencer["id"] in self._selected_influencer_ids)
            action.toggled.connect(
                lambda checked, influencer_id=influencer["id"]: self._toggle_influencer_selection(influencer_id, checked)
            )
            self.influencer_menu.addAction(action)
            self._menu_actions[influencer["id"]] = action

        self._update_selector_text()

    def _toggle_influencer_selection(self, influencer_id: int, checked: bool):
        if checked:
            self._selected_influencer_ids.add(influencer_id)
        else:
            self._selected_influencer_ids.discard(influencer_id)
        self._sync_current_influencer()
        self._update_selector_text()
        self._load_videos()

    def _set_selected_influencer_ids(self, influencer_ids):
        self._selected_influencer_ids = {
            influencer_id for influencer_id in influencer_ids if influencer_id in self._influencer_by_id
        }
        for influencer_id, action in self._menu_actions.items():
            action.blockSignals(True)
            action.setChecked(influencer_id in self._selected_influencer_ids)
            action.blockSignals(False)
        self._sync_current_influencer()
        self._update_selector_text()
        self._load_videos()

    def _select_all_influencers(self):
        self._set_selected_influencer_ids(self._influencer_by_id.keys())

    def _clear_selected_influencers(self):
        self._set_selected_influencer_ids([])

    def _sync_current_influencer(self):
        if len(self._selected_influencer_ids) == 1:
            influencer_id = next(iter(self._selected_influencer_ids))
            self._current_influencer = self._influencer_by_id.get(influencer_id)
        else:
            self._current_influencer = None

    def _update_selector_text(self):
        selected_ids = list(self._selected_influencer_ids)
        count = len(selected_ids)
        total = len(self._influencers)

        if count == 0:
            self.influencer_selector.setText(TEXT_SELECT_PLACEHOLDER)
            return
        if count == total and total > 0:
            self.influencer_selector.setText(TEXT_ALL_SELECTED.format(count=total))
            return
        if count == 1:
            influencer = self._influencer_by_id.get(selected_ids[0])
            if influencer:
                self.influencer_selector.setText(
                    f"{platform_label(influencer.get('platform'))} | @{influencer['username']}"
                )
                return
        self.influencer_selector.setText(TEXT_SELECTED_COUNT.format(count=count))

    def _reset_stats(self):
        self.stat_total.setText(TEXT_STAT_TOTAL.format(value=0))
        self.stat_avg_play.setText(TEXT_STAT_AVG_PLAY.format(value=0))
        self.stat_max_play.setText(TEXT_STAT_MAX_PLAY.format(value=0))
        self.stat_avg_like.setText(TEXT_STAT_AVG_LIKE.format(value=0))
        self.stat_avg_engage.setText(TEXT_STAT_AVG_ENGAGE.format(value=0))

    def _load_videos(self):
        if not self._selected_influencer_ids:
            self._videos = []
            self.table.setRowCount(0)
            self._reset_stats()
            return

        from data.database import get_videos_by_influencer_ids

        videos = get_videos_by_influencer_ids(sorted(self._selected_influencer_ids), 100)
        self._videos = videos

        if not videos:
            self.table.setRowCount(0)
            self._reset_stats()
            return

        total = len(videos)
        avg_play = sum(v.get("play_count", 0) for v in videos) / total
        max_play = max(v.get("play_count", 0) for v in videos)
        avg_like = sum(v.get("like_count", 0) for v in videos) / total

        temp_analyzer = self._get_metrics_helper()
        engagement_rates = [
            temp_analyzer.calculate_engagement_metrics(video)["engagement_rate"] for video in videos
        ]
        avg_engage = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0

        self.stat_total.setText(TEXT_STAT_TOTAL.format(value=total))
        self.stat_avg_play.setText(TEXT_STAT_AVG_PLAY.format(value=self._format_number(avg_play)))
        self.stat_max_play.setText(TEXT_STAT_MAX_PLAY.format(value=self._format_number(max_play)))
        self.stat_avg_like.setText(TEXT_STAT_AVG_LIKE.format(value=self._format_number(avg_like)))
        self.stat_avg_engage.setText(TEXT_STAT_AVG_ENGAGE.format(value=f"{avg_engage:.2f}"))

        self.table.setRowCount(len(videos))

        for row, video in enumerate(videos):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

            account_text = f"{platform_label(video.get('influencer_platform'))} | @{video.get('influencer_username', '')}"
            self.table.setItem(row, 1, QTableWidgetItem(account_text))

            desc = video.get("description") or video.get("title") or TEXT_NO_DESC
            self.table.setItem(row, 2, QTableWidgetItem(desc[:80] + "..." if len(desc) > 80 else desc))

            play_item = QTableWidgetItem(self._format_number(video.get("play_count", 0)))
            if (video.get("play_count") or 0) > 1_000_000:
                play_item.setForeground(QColor("#f6ad55"))
            self.table.setItem(row, 3, play_item)
            self.table.setItem(row, 4, QTableWidgetItem(self._format_number(video.get("like_count", 0))))
            self.table.setItem(row, 5, QTableWidgetItem(self._format_number(video.get("comment_count", 0))))
            self.table.setItem(row, 6, QTableWidgetItem(self._format_number(video.get("share_count", 0))))

            metrics = self._get_metrics_helper().calculate_engagement_metrics(video)
            engage_rate = metrics["engagement_rate"]
            engage_item = QTableWidgetItem(f"{engage_rate:.2f}%")
            if engage_rate >= 10:
                engage_item.setForeground(QColor(SUCCESS))
            elif engage_rate >= 5:
                engage_item.setForeground(QColor("#f6ad55"))
            else:
                engage_item.setForeground(QColor("#fc8181"))
            self.table.setItem(row, 7, engage_item)

            self.table.setItem(row, 8, QTableWidgetItem(video.get("music_name") or ""))
            self.table.setItem(row, 9, QTableWidgetItem(video.get("published_at") or ""))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 1, 2, 1)
            btn_layout.setSpacing(4)

            analyze_btn = QPushButton(TEXT_AI_ANALYZE)
            analyze_btn.setStyleSheet(table_button_style())
            analyze_btn.clicked.connect(lambda _, vid=video: self._analyze_single(vid))
            btn_layout.addWidget(analyze_btn)

            if video.get("video_url"):
                dl_btn = QPushButton(TEXT_DOWNLOAD)
                dl_btn.setStyleSheet(table_button_style())
                dl_btn.clicked.connect(lambda _, vid=video: self._download_video(vid))
                btn_layout.addWidget(dl_btn)

            self.table.setCellWidget(row, 10, btn_widget)
            self.table.setRowHeight(row, 36)

    def _get_video_influencer(self, video: dict):
        influencer = self._influencer_by_id.get(video.get("influencer_id"))
        if influencer:
            return influencer

        username = video.get("influencer_username", "")
        platform = video.get("influencer_platform", "tiktok")
        if not username:
            return None
        return {
            "id": video.get("influencer_id"),
            "username": username,
            "platform": platform,
            "display_name": video.get("influencer_display_name", ""),
        }

    def _selected_scope_label(self):
        if len(self._selected_influencer_ids) == 1 and self._current_influencer:
            return self._current_influencer.get("username", "")
        return TEXT_SCOPE_LABEL.format(count=len(self._selected_influencer_ids))

    def _analyze_single(self, video: dict):
        influencer = self._get_video_influencer(video)
        if not influencer:
            QMessageBox.warning(self, TEXT_PROMPT, TEXT_WARN_NO_VIDEO_INFLUENCER)
            return

        self.main_window.navigate_to(3)
        self.main_window.ai_report_page.open_single_analysis(influencer, video)

    def _analyze_batch(self):
        if not self._selected_influencer_ids:
            QMessageBox.warning(self, TEXT_PROMPT, TEXT_WARN_SELECT_ONE)
            return

        videos = self._videos[:10]
        if not videos:
            QMessageBox.warning(self, TEXT_PROMPT, TEXT_WARN_NO_VIDEOS)
            return

        self.main_window.navigate_to(3)
        self.main_window.ai_report_page.open_batch_analysis(
            self._current_influencer,
            videos,
            self._selected_scope_label(),
        )

    def _download_video(self, video: dict):
        from data.database import update_video_local_path

        influencer = self._get_video_influencer(video)
        username = influencer.get("username", "unknown") if influencer else "unknown"
        platform = influencer.get("platform", "tiktok") if influencer else "tiktok"

        # 从环境变量读取下载路径
        download_path = os.environ.get("DOWNLOAD_PATH", os.path.expanduser("~/Downloads/TikTok_Monitor"))
        output_dir = os.path.join(download_path, platform, username)

        QMessageBox.information(
            self,
            TEXT_DOWNLOAD_START,
            TEXT_DOWNLOAD_START_BODY.format(path=output_dir),
        )

        video_url = video.get("video_url", "")
        video_id = video.get("video_id", "")
        local_path = self.main_window.scraper.download_video_no_watermark(
            video_url, output_dir, f"{platform}_{video_id}"
        )

        if local_path:
            update_video_local_path(video["id"], local_path)
            QMessageBox.information(
                self,
                TEXT_DOWNLOAD_DONE,
                TEXT_DOWNLOAD_DONE_BODY.format(path=local_path),
            )
            return

        QMessageBox.warning(self, TEXT_DOWNLOAD_FAILED, TEXT_DOWNLOAD_FAILED_BODY)

    def _format_number(self, value):
        value = value or 0
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{value / 1_000:.0f}K"
        return str(int(value))
