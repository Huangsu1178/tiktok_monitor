"""
TikTok Monitor - Two Stage Selection Dialog
"""

from PyQt6.QtCore import QSignalBlocker, QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QWidget,
)

from core.platforms import platform_label
from ui.components.theme import (
    ACCENT,
    BG_PANEL,
    BG_SURFACE,
    BG_SURFACE_HOVER,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    accent_button_style,
    input_style,
    secondary_button_style,
)


class VideoPrefetchThread(QThread):
    """Load videos for selected influencers in the background."""

    influencer_loaded = pyqtSignal(object, object)
    batch_finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, influencers):
        super().__init__()
        self.influencers = [dict(item) for item in influencers]
        self.influencer_ids = [
            influencer.get("id")
            for influencer in self.influencers
            if isinstance(influencer, dict) and influencer.get("id") is not None
        ]

    def run(self):
        try:
            from data.database import get_videos_by_influencer

            for influencer in self.influencers:
                if self.isInterruptionRequested():
                    return

                influencer_id = influencer.get("id")
                if influencer_id is None:
                    continue

                raw_videos = get_videos_by_influencer(influencer_id, 100)
                videos = []
                for raw_video in raw_videos:
                    if self.isInterruptionRequested():
                        return

                    video = dict(raw_video)
                    video["influencer_username"] = influencer.get("username", "")
                    video["influencer_platform"] = influencer.get("platform", "")
                    videos.append(video)

                self.influencer_loaded.emit(dict(influencer), videos)

            self.batch_finished.emit(self.influencer_ids)
        except Exception as exc:
            self.error.emit(str(exc))


class TwoStageSelectionDialog(QDialog):
    """Select influencers first, then select videos."""

    videos_selected = pyqtSignal(list)

    def __init__(self, parent=None, title="选择视频", allow_multiple=True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(800, 600)
        self.setModal(True)

        self.allow_multiple = allow_multiple
        self.all_influencers = []
        self.all_videos = []
        self.selected_influencers = []
        self.selected_videos = []
        self.selected_influencer_keys = set()
        self.selected_video_keys = set()

        self.video_cache = {}
        self.loaded_influencer_ids = set()
        self.loading_influencer_ids = set()
        self.pending_accept = False

        self.loader_thread = None
        self.current_loader_ids = []
        self.influencer_checkbox_by_key = {}
        self.video_checkbox_by_key = {}

        self.pending_influencer_changes = []
        self.pending_video_changes = []

        self.influencer_checkbox_timer = QTimer(self)
        self.influencer_checkbox_timer.setSingleShot(True)
        self.influencer_checkbox_timer.setInterval(0)
        self.influencer_checkbox_timer.timeout.connect(self._process_influencer_checkbox_changes)

        self.video_checkbox_timer = QTimer(self)
        self.video_checkbox_timer.setSingleShot(True)
        self.video_checkbox_timer.setInterval(0)
        self.video_checkbox_timer.timeout.connect(self._process_video_checkbox_changes)

        self._build_ui()
        self._load_influencers()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        self.step_label = QLabel("第一步：选择博主")
        self.step_label.setStyleSheet("color: #f4f8ff; font-size: 18px; font-weight: 700;")
        layout.addWidget(self.step_label)

        self.stacked = QStackedWidget()
        self.step1_widget = self._build_step1()
        self.step2_widget = self._build_step2()
        self.stacked.addWidget(self.step1_widget)
        self.stacked.addWidget(self.step2_widget)
        layout.addWidget(self.stacked)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.back_btn = QPushButton("← 返回上一步")
        self.back_btn.setStyleSheet(secondary_button_style())
        self.back_btn.clicked.connect(self._go_back)
        self.back_btn.hide()
        button_layout.addWidget(self.back_btn)

        button_layout.addStretch()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet(secondary_button_style())
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.next_btn = QPushButton("下一步 →")
        self.next_btn.setStyleSheet(accent_button_style())
        self.next_btn.clicked.connect(self._go_next)
        button_layout.addWidget(self.next_btn)

        layout.addLayout(button_layout)

    def _build_step1(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(10)

        sort_label = QLabel("排序:")
        sort_label.setStyleSheet("color: #8fa6c9; font-size: 13px;")
        sort_layout.addWidget(sort_label)

        self.influencer_sort_combo = QComboBox()
        self.influencer_sort_combo.addItem("默认", "default")
        self.influencer_sort_combo.addItem("粉丝数 ↓", "followers_desc")
        self.influencer_sort_combo.addItem("粉丝数 ↑", "followers_asc")
        self.influencer_sort_combo.addItem("最高播放 ↓", "top_video_desc")
        self.influencer_sort_combo.addItem("用户名 A-Z", "username_asc")
        self.influencer_sort_combo.addItem("用户名 Z-A", "username_desc")
        self.influencer_sort_combo.setStyleSheet(input_style(200))
        self.influencer_sort_combo.currentIndexChanged.connect(self._filter_influencers)
        sort_layout.addWidget(self.influencer_sort_combo)

        sort_layout.addStretch()
        layout.addLayout(sort_layout)

        self.influencer_search = QLineEdit()
        self.influencer_search.setPlaceholderText("搜索博主用户名或平台...")
        self.influencer_search.setStyleSheet(input_style(200))
        self.influencer_search.textChanged.connect(self._filter_influencers)
        layout.addWidget(self.influencer_search)

        self.influencer_table = QTableWidget()
        self.influencer_table.setColumnCount(4)
        self.influencer_table.setHorizontalHeaderLabels(["选择", "平台", "用户名", "粉丝数"])
        self.influencer_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.influencer_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.influencer_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.influencer_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.influencer_table.setColumnWidth(0, 60)
        self.influencer_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.influencer_table.setAlternatingRowColors(True)
        self.influencer_table.setStyleSheet(self._table_style())
        layout.addWidget(self.influencer_table)

        self.influencer_count_label = QLabel("已选: 0 个博主")
        self.influencer_count_label.setStyleSheet("color: #8fa6c9; font-size: 13px;")
        layout.addWidget(self.influencer_count_label)

        return widget

    def _build_step2(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.selected_influencers_label = QLabel("已选博主: -")
        self.selected_influencers_label.setStyleSheet("color: #52c58b; font-size: 13px; font-weight: 600;")
        layout.addWidget(self.selected_influencers_label)

        self.loading_progress = QProgressBar()
        self.loading_progress.setVisible(False)
        self.loading_progress.setFixedHeight(4)
        self.loading_progress.setTextVisible(False)
        self.loading_progress.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {BG_PANEL};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT};
                border-radius: 2px;
            }}
            """
        )
        layout.addWidget(self.loading_progress)

        self.loading_label = QLabel("")
        self.loading_label.setVisible(False)
        self.loading_label.setStyleSheet("color: #8fa6c9; font-size: 12px; font-style: italic;")
        layout.addWidget(self.loading_label)

        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(10)

        sort_label = QLabel("排序:")
        sort_label.setStyleSheet("color: #8fa6c9; font-size: 13px;")
        sort_layout.addWidget(sort_label)

        self.video_sort_combo = QComboBox()
        self.video_sort_combo.addItem("默认", "default")
        self.video_sort_combo.addItem("播放量 ↓", "play_count_desc")
        self.video_sort_combo.addItem("播放量 ↑", "play_count_asc")
        self.video_sort_combo.addItem("点赞数 ↓", "like_count_desc")
        self.video_sort_combo.addItem("点赞数 ↑", "like_count_asc")
        self.video_sort_combo.addItem("评论数 ↓", "comment_count_desc")
        self.video_sort_combo.addItem("发布时间 ↓", "published_at_desc")
        self.video_sort_combo.addItem("发布时间 ↑", "published_at_asc")
        self.video_sort_combo.setStyleSheet(input_style(200))
        self.video_sort_combo.currentIndexChanged.connect(self._filter_videos)
        sort_layout.addWidget(self.video_sort_combo)

        sort_layout.addStretch()
        layout.addLayout(sort_layout)

        self.video_search = QLineEdit()
        self.video_search.setPlaceholderText("搜索视频描述或博主...")
        self.video_search.setStyleSheet(input_style(200))
        self.video_search.textChanged.connect(self._filter_videos)
        layout.addWidget(self.video_search)

        self.video_table = QTableWidget()
        self.video_table.setColumnCount(5)
        self.video_table.setHorizontalHeaderLabels(["选择", "博主", "视频描述", "播放量", "点赞数"])
        self.video_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.video_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.video_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.video_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.video_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.video_table.setColumnWidth(0, 60)
        self.video_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.video_table.setAlternatingRowColors(True)
        self.video_table.setStyleSheet(self._table_style())
        layout.addWidget(self.video_table)

        self.video_count_label = QLabel("已选: 0 个视频")
        self.video_count_label.setStyleSheet("color: #8fa6c9; font-size: 13px;")
        layout.addWidget(self.video_count_label)

        return widget

    def _table_style(self):
        return f"""
            QTableWidget {{
                background-color: {BG_PANEL};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                gridline-color: {BORDER};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {BG_SURFACE_HOVER};
            }}
            QHeaderView::section {{
                background-color: {BG_SURFACE};
                color: {TEXT_SECONDARY};
                padding: 8px;
                border: none;
                font-weight: 600;
            }}
        """

    def _load_influencers(self):
        from data.database import get_all_influencers

        self.all_influencers = get_all_influencers()
        self._filter_influencers()

    def _influencer_key(self, influencer):
        return influencer.get("id") if isinstance(influencer, dict) else None

    def _video_key(self, video):
        if not isinstance(video, dict):
            return None
        return video.get("id") or (video.get("influencer_id"), video.get("video_id"))

    def _is_influencer_selected(self, influencer):
        key = self._influencer_key(influencer)
        return key in self.selected_influencer_keys

    def _is_video_selected(self, video):
        key = self._video_key(video)
        return key in self.selected_video_keys

    def _flush_pending_influencer_changes(self):
        if not self.pending_influencer_changes:
            return
        self.influencer_checkbox_timer.stop()
        self._process_influencer_checkbox_changes()

    def _flush_pending_video_changes(self):
        if not self.pending_video_changes:
            return
        self.video_checkbox_timer.stop()
        self._process_video_checkbox_changes()

    def _selected_influencer_ids(self):
        return {
            self._influencer_key(influencer)
            for influencer in self.selected_influencers
            if self._influencer_key(influencer) is not None
        }

    def _pending_video_influencer_ids(self):
        return {
            influencer_id
            for influencer_id in self._selected_influencer_ids()
            if influencer_id not in self.loaded_influencer_ids
        }

    def _has_pending_video_loads(self):
        return bool(self._pending_video_influencer_ids())

    def _refresh_selected_influencer_text(self):
        if not self.selected_influencers:
            self.selected_influencers_label.setText("已选博主: -")
            return

        names = ", ".join(f"@{item.get('username', '')}" for item in self.selected_influencers)
        self.selected_influencers_label.setText(f"已选博主: {names}")

    def _rebuild_video_pool(self):
        videos = []
        for influencer in self.selected_influencers:
            influencer_id = self._influencer_key(influencer)
            videos.extend(self.video_cache.get(influencer_id, []))
        self.all_videos = videos

    def _prune_selected_videos(self):
        valid_keys = {
            self._video_key(video)
            for video in self.all_videos
            if self._video_key(video) is not None
        }
        self.selected_videos = [
            video
            for video in self.selected_videos
            if self._video_key(video) in valid_keys
        ]
        self.selected_video_keys = {
            self._video_key(video)
            for video in self.selected_videos
            if self._video_key(video) is not None
        }

    def _update_counts(self):
        self.influencer_count_label.setText(f"已选: {len(self.selected_influencers)} 个博主")
        self.video_count_label.setText(f"已选: {len(self.selected_videos)} 个视频")

    def _update_loading_ui(self):
        total = len(self._selected_influencer_ids())
        loaded = total - len(self._pending_video_influencer_ids())

        if self.stacked.currentIndex() != 1 or total == 0:
            self.loading_progress.setVisible(False)
            self.loading_label.setVisible(False)
            return

        if loaded < total:
            self.loading_progress.setVisible(True)
            self.loading_progress.setRange(0, max(total, 1))
            self.loading_progress.setValue(loaded)
            self.loading_label.setVisible(True)
            if self.pending_accept:
                self.loading_label.setText(f"正在完成剩余加载，已完成 {loaded}/{total} 个博主，完成后自动导入...")
            else:
                self.loading_label.setText(f"后台加载中：已完成 {loaded}/{total} 个博主的视频，可继续勾选已显示内容")
        else:
            self.loading_progress.setVisible(False)
            self.loading_label.setVisible(True)
            self.loading_label.setText(f"已加载完成，共 {len(self.all_videos)} 个视频")

    def _refresh_step2(self):
        self._refresh_selected_influencer_text()
        self._rebuild_video_pool()
        self._prune_selected_videos()
        self._update_counts()
        if self.stacked.currentIndex() == 1:
            self._filter_videos()
        self._update_loading_ui()
        self._update_action_state()

    def _update_action_state(self):
        if self.stacked.currentIndex() == 0:
            self.next_btn.setEnabled(True)
            self.next_btn.setText("下一步 →")
            self.back_btn.setEnabled(True)
            return

        self.back_btn.setVisible(True)
        if self.pending_accept:
            self.next_btn.setEnabled(False)
            self.back_btn.setEnabled(False)
            self.next_btn.setText("等待加载完成...")
            return

        self.next_btn.setEnabled(True)
        self.back_btn.setEnabled(True)
        if self._has_pending_video_loads():
            self.next_btn.setText("确认添加")
        else:
            self.next_btn.setText("确认添加 ✓")

    def _set_checkbox_state(self, checkbox, checked: bool):
        if checkbox is None or checkbox.isChecked() == checked:
            return
        blocker = QSignalBlocker(checkbox)
        checkbox.setChecked(checked)
        del blocker

    def _sync_visible_video_checkboxes(self):
        for key, checkbox in self.video_checkbox_by_key.items():
            self._set_checkbox_state(checkbox, key in self.selected_video_keys)

    def _render_influencer_table(self, influencers):
        self.influencer_table.setUpdatesEnabled(False)
        try:
            self.influencer_checkbox_by_key = {}
            self.influencer_table.clearContents()
            self.influencer_table.setRowCount(len(influencers))
            for row, influencer in enumerate(influencers):
                checkbox = QCheckBox()
                checkbox.setChecked(self._is_influencer_selected(influencer))
                checkbox.stateChanged.connect(
                    lambda state, inf=influencer: self._on_influencer_checkbox(state, inf)
                )
                self.influencer_table.setCellWidget(row, 0, checkbox)
                key = self._influencer_key(influencer)
                if key is not None:
                    self.influencer_checkbox_by_key[key] = checkbox

                platform_item = QTableWidgetItem(platform_label(influencer.get("platform")))
                platform_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.influencer_table.setItem(row, 1, platform_item)

                username_item = QTableWidgetItem(influencer.get("username", ""))
                self.influencer_table.setItem(row, 2, username_item)

                follower_count = influencer.get("follower_count", 0)
                follower_item = QTableWidgetItem(f"{follower_count:,}" if follower_count else "N/A")
                follower_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.influencer_table.setItem(row, 3, follower_item)
        finally:
            self.influencer_table.setUpdatesEnabled(True)

    def _render_video_table(self, videos):
        self.video_table.setUpdatesEnabled(False)
        try:
            self.video_checkbox_by_key = {}
            self.video_table.clearContents()
            self.video_table.setRowCount(len(videos))
            for row, video in enumerate(videos):
                checkbox = QCheckBox()
                checkbox.setChecked(self._is_video_selected(video))
                checkbox.stateChanged.connect(
                    lambda state, item=video: self._on_video_checkbox(state, item)
                )
                self.video_table.setCellWidget(row, 0, checkbox)
                key = self._video_key(video)
                if key is not None:
                    self.video_checkbox_by_key[key] = checkbox

                username = video.get("influencer_username", "")
                platform = platform_label(video.get("influencer_platform", ""))
                influencer_item = QTableWidgetItem(f"{platform} @{username}")
                influencer_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.video_table.setItem(row, 1, influencer_item)

                desc = (video.get("description") or video.get("title") or "无描述").replace("\n", " ")
                desc_item = QTableWidgetItem(desc[:80] + ("..." if len(desc) > 80 else ""))
                self.video_table.setItem(row, 2, desc_item)

                play_count = video.get("play_count", 0)
                play_item = QTableWidgetItem(f"{play_count:,}" if play_count else "0")
                play_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.video_table.setItem(row, 3, play_item)

                like_count = video.get("like_count", 0)
                like_item = QTableWidgetItem(f"{like_count:,}" if like_count else "0")
                like_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.video_table.setItem(row, 4, like_item)
        finally:
            self.video_table.setUpdatesEnabled(True)

    def _sort_influencer_data(self, influencers):
        sort_key = self.influencer_sort_combo.currentData()
        data = list(influencers)

        if sort_key == "followers_desc":
            data.sort(key=lambda item: item.get("follower_count", 0) or 0, reverse=True)
        elif sort_key == "followers_asc":
            data.sort(key=lambda item: item.get("follower_count", 0) or 0)
        elif sort_key == "top_video_desc":
            data.sort(key=lambda item: item.get("max_play_count", 0) or 0, reverse=True)
        elif sort_key == "username_asc":
            data.sort(key=lambda item: item.get("username", ""))
        elif sort_key == "username_desc":
            data.sort(key=lambda item: item.get("username", ""), reverse=True)

        return data

    def _sort_video_data(self, videos):
        sort_key = self.video_sort_combo.currentData()
        data = list(videos)

        if sort_key == "play_count_desc":
            data.sort(key=lambda item: item.get("play_count", 0) or 0, reverse=True)
        elif sort_key == "play_count_asc":
            data.sort(key=lambda item: item.get("play_count", 0) or 0)
        elif sort_key == "like_count_desc":
            data.sort(key=lambda item: item.get("like_count", 0) or 0, reverse=True)
        elif sort_key == "like_count_asc":
            data.sort(key=lambda item: item.get("like_count", 0) or 0)
        elif sort_key == "comment_count_desc":
            data.sort(key=lambda item: item.get("comment_count", 0) or 0, reverse=True)
        elif sort_key == "published_at_desc":
            data.sort(key=lambda item: item.get("published_at", "") or "", reverse=True)
        elif sort_key == "published_at_asc":
            data.sort(key=lambda item: item.get("published_at", "") or "")

        return data

    def _filter_influencers(self):
        self._flush_pending_influencer_changes()
        keyword = self.influencer_search.text().strip().lower()

        if keyword:
            filtered = [
                influencer
                for influencer in self.all_influencers
                if keyword in influencer.get("username", "").lower()
                or keyword in platform_label(influencer.get("platform")).lower()
            ]
        else:
            filtered = list(self.all_influencers)

        self._render_influencer_table(self._sort_influencer_data(filtered))

    def _filter_videos(self):
        self._flush_pending_video_changes()
        keyword = self.video_search.text().strip().lower()

        if keyword:
            filtered = [
                video
                for video in self.all_videos
                if keyword in (video.get("description") or video.get("title") or "").lower()
                or keyword in video.get("influencer_username", "").lower()
            ]
        else:
            filtered = list(self.all_videos)

        self._render_video_table(self._sort_video_data(filtered))

    def _on_influencer_checkbox(self, state, influencer):
        self.pending_influencer_changes.append((state, influencer))
        self.influencer_checkbox_timer.stop()
        self.influencer_checkbox_timer.start()

    def _process_influencer_checkbox_changes(self):
        selected_by_key = {
            self._influencer_key(item): item
            for item in self.selected_influencers
            if self._influencer_key(item) is not None
        }

        for state, influencer in self.pending_influencer_changes:
            key = self._influencer_key(influencer)
            if key is None:
                continue

            if state == Qt.CheckState.Checked.value:
                selected_by_key[key] = influencer
            else:
                selected_by_key.pop(key, None)

        self.selected_influencers = list(selected_by_key.values())
        self.selected_influencer_keys = set(selected_by_key.keys())
        self.pending_influencer_changes.clear()
        self._update_counts()

        if self.stacked.currentIndex() == 1:
            self._refresh_step2()
            self._schedule_video_prefetch()
        else:
            self._update_action_state()

    def _on_video_checkbox(self, state, video):
        self.pending_video_changes.append((state, video))
        self.video_checkbox_timer.stop()
        self.video_checkbox_timer.start()

    def _process_video_checkbox_changes(self):
        if not self.allow_multiple:
            selected_by_key = {}
        else:
            selected_by_key = {
                self._video_key(item): item
                for item in self.selected_videos
                if self._video_key(item) is not None
            }

        for state, video in self.pending_video_changes:
            key = self._video_key(video)
            if key is None:
                continue

            if state == Qt.CheckState.Checked.value:
                if self.allow_multiple:
                    selected_by_key[key] = video
                else:
                    selected_by_key = {key: video}
            else:
                selected_by_key.pop(key, None)

        self.selected_videos = list(selected_by_key.values())
        self.selected_video_keys = set(selected_by_key.keys())
        self.pending_video_changes.clear()
        self._update_counts()

        if not self.allow_multiple:
            self._sync_visible_video_checkboxes()

    def _start_video_loader(self, influencers):
        if not influencers or self.loader_thread is not None:
            return

        self.current_loader_ids = [
            influencer.get("id")
            for influencer in influencers
            if influencer.get("id") is not None
        ]
        self.loading_influencer_ids.update(self.current_loader_ids)

        self.loader_thread = VideoPrefetchThread(influencers)
        self.loader_thread.influencer_loaded.connect(self._on_influencer_videos_loaded)
        self.loader_thread.batch_finished.connect(self._on_loader_batch_finished)
        self.loader_thread.error.connect(self._on_loader_error)
        self.loader_thread.start()
        self._update_loading_ui()
        self._update_action_state()

    def _schedule_video_prefetch(self):
        pending_influencers = [
            influencer
            for influencer in self.selected_influencers
            if self._influencer_key(influencer) not in self.loaded_influencer_ids
            and self._influencer_key(influencer) not in self.loading_influencer_ids
        ]

        if self.loader_thread is None and pending_influencers:
            self._start_video_loader(pending_influencers)
            return

        self._update_loading_ui()
        self._update_action_state()

    def _on_influencer_videos_loaded(self, influencer, videos):
        influencer_id = self._influencer_key(influencer)
        if influencer_id is None:
            return

        self.video_cache[influencer_id] = list(videos)
        self.loaded_influencer_ids.add(influencer_id)
        self._refresh_step2()

    def _cleanup_loader_thread(self):
        if self.loader_thread is None:
            return
        self.loader_thread.deleteLater()
        self.loader_thread = None
        self.current_loader_ids = []

    def _on_loader_batch_finished(self, influencer_ids):
        self.loading_influencer_ids.difference_update(set(influencer_ids or []))
        self._cleanup_loader_thread()
        self._refresh_step2()
        self._schedule_video_prefetch()
        self._complete_pending_accept_if_ready()

    def _on_loader_error(self, error_msg):
        self.loading_influencer_ids.difference_update(set(self.current_loader_ids))
        self._cleanup_loader_thread()

        if self.pending_accept:
            self.pending_accept = False

        self._refresh_step2()
        QMessageBox.critical(self, "加载失败", f"加载视频数据时出错：\n{error_msg}")

    def _stop_loader_thread(self):
        if self.loader_thread is None:
            return

        if self.loader_thread.isRunning():
            self.loader_thread.requestInterruption()
            self.loader_thread.wait(3000)

        self.loading_influencer_ids.difference_update(set(self.current_loader_ids))
        self._cleanup_loader_thread()

    def _go_next(self):
        if self.stacked.currentIndex() == 0:
            self._flush_pending_influencer_changes()
            if not self.selected_influencers:
                QMessageBox.warning(self, "提示", "请至少选择一个博主")
                return

            self.stacked.setCurrentIndex(1)
            self.step_label.setText("第二步：选择视频")
            self.back_btn.show()
            self._refresh_step2()
            self._schedule_video_prefetch()
            return

        self.accept()

    def _go_back(self):
        if self.stacked.currentIndex() != 1 or self.pending_accept:
            return

        self.stacked.setCurrentIndex(0)
        self.step_label.setText("第一步：选择博主")
        self.back_btn.hide()
        self._update_action_state()

    def _complete_pending_accept_if_ready(self):
        if not self.pending_accept or self._has_pending_video_loads():
            return

        self.pending_accept = False
        self._update_action_state()
        self._finalize_accept()

    def _finalize_accept(self):
        self.videos_selected.emit(self.selected_videos)
        self._stop_loader_thread()
        super().accept()

    def accept(self):
        if self.stacked.currentIndex() == 0:
            QMessageBox.information(self, "提示", "请先选择博主，然后进入下一步选择视频")
            return

        self._flush_pending_video_changes()
        if not self.selected_videos:
            QMessageBox.warning(self, "提示", "请至少选择一个视频")
            return

        if self._has_pending_video_loads():
            self.pending_accept = True
            self._update_loading_ui()
            self._update_action_state()
            return

        self._finalize_accept()

    def get_selected_videos(self):
        return self.selected_videos[:]

    def reject(self):
        self.pending_accept = False
        self._stop_loader_thread()
        super().reject()

    def closeEvent(self, event):
        self.pending_accept = False
        self._stop_loader_thread()
        super().closeEvent(event)


def show_two_stage_selection(parent=None, title="选择视频", allow_multiple=True):
    """Show the two-stage selection dialog."""

    dialog = TwoStageSelectionDialog(
        parent=parent,
        title=title,
        allow_multiple=allow_multiple,
    )
    result = dialog.exec()
    if result == QDialog.DialogCode.Accepted:
        return dialog.get_selected_videos()
    return []
