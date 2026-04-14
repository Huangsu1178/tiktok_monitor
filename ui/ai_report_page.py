"""
TikTok Monitor - AI Report Page
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt6.QtCore import QThread, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.platforms import platform_label
from ui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_PANEL,
    BG_SURFACE,
    BG_SURFACE_HOVER,
    BORDER,
    SUCCESS,
    TEAL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    VIOLET,
    accent_button_style,
    card_style,
    input_style,
    page_background_style,
    secondary_button_style,
)


PAGE_STYLE = f"""
QWidget {{
    {page_background_style()}
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
{input_style(220)}
QComboBox::drop-down {{
    border: none;
    width: 26px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    selection-background-color: #22324a;
}}
QPushButton {{
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 700;
}}
"""


class AnalysisWorker(QThread):
    finished = pyqtSignal(str, object, object, str)
    failed = pyqtSignal(str)

    def __init__(self, mode: str, analyzer, video=None, videos=None, username: str = "",
                 group_a_videos=None, group_b_videos=None, group_a_label: str = "", group_b_label: str = ""):
        super().__init__()
        self.mode = mode
        self.analyzer = analyzer
        self.video = video
        self.videos = videos or []
        self.username = username
        self.group_a_videos = group_a_videos or []
        self.group_b_videos = group_b_videos or []
        self.group_a_label = group_a_label
        self.group_b_label = group_b_label

    def run(self):
        try:
            if self.mode == "single":
                result = self.analyzer.analyze_video(self.video, self.username)
                self.finished.emit(self.mode, result, self.video, self.username)
                return

            if self.mode == "ab_comparison":
                result = self.analyzer.analyze_ab_comparison(
                    self.group_a_videos, self.group_b_videos,
                    self.group_a_label, self.group_b_label
                )
                self.finished.emit(self.mode, result, {
                    "group_a_videos": self.group_a_videos,
                    "group_b_videos": self.group_b_videos,
                    "group_a_label": self.group_a_label,
                    "group_b_label": self.group_b_label,
                }, "")
                return

            result = self.analyzer.analyze_batch(self.videos, self.username)
            self.finished.emit(self.mode, result, self.videos, self.username)
        except Exception as exc:
            self.failed.emit(str(exc))


class MetricChip(QFrame):
    def __init__(self, label: str, value: str, accent: str):
        super().__init__()
        self.setStyleSheet(card_style(accent))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        title = QLabel(label)
        title.setStyleSheet("color: #8fa6c9; font-size: 12px;")
        layout.addWidget(title)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {accent}; font-size: 18px; font-weight: 700;")
        layout.addWidget(value_label)


class AnalysisCard(QFrame):
    def __init__(self, title: str, content: str, accent: str):
        super().__init__()
        self.setStyleSheet(card_style(accent))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {accent}; font-size: 13px; font-weight: 700;")
        layout.addWidget(title_label)

        content_label = QLabel(content or "暂无分析内容")
        content_label.setWordWrap(True)
        content_label.setStyleSheet("color: #e6eefb; font-size: 14px; line-height: 1.7;")
        layout.addWidget(content_label)


class EmptyState(QFrame):
    def __init__(self, title: str, desc: str):
        super().__init__()
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px dashed {BORDER};
                border-radius: 18px;
            }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 40, 32, 40)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #edf4ff; font-size: 18px; font-weight: 700;")
        layout.addWidget(title_label)

        desc_label = QLabel(desc)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #8fa6c9; font-size: 14px; line-height: 1.8;")
        layout.addWidget(desc_label)


class AIReportPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._current_influencer = None
        self._current_videos = []
        self._external_batch_context = None
        self._worker = None
        self._loading_base = ""
        self._loading_step = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._tick_loading)
        # AB对比相关状态
        self._group_a_videos = []
        self._group_b_videos = []
        self._current_ab_tab = "single"  # single, batch, ab_comparison
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.setStyleSheet(PAGE_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        header = QFrame()
        header.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #122033, stop:0.45 #18283d, stop:1 #223752);
                border: 1px solid #355071;
                border-radius: 24px;
            }
            """
        )
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 24, 24, 24)
        header_layout.setSpacing(14)

        title = QLabel("AI 分析报告中心")
        title.setStyleSheet("color: #f4f8ff; font-size: 28px; font-weight: 800;")
        header_layout.addWidget(title)

        subtitle = QLabel("支持单视频拆解与批量规律分析，分析过程中会展示实时等待状态，结果会自动展示在下方报告区。")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #bfd0ea; font-size: 14px; line-height: 1.7;")
        header_layout.addWidget(subtitle)

        controls = QFrame()
        controls.setStyleSheet(
            """
            QFrame {
                background-color: rgba(8, 14, 25, 0.28);
                border: 1px solid #35507e;
                border-radius: 18px;
            }
            """
        )
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(18, 18, 18, 18)
        controls_layout.setSpacing(14)

        selectors = QHBoxLayout()
        selectors.setSpacing(12)

        self.influencer_combo = QComboBox()
        self.influencer_combo.currentIndexChanged.connect(self._on_influencer_changed)
        selectors.addWidget(self.influencer_combo)

        self.video_combo = QComboBox()
        selectors.addWidget(self.video_combo)

        refresh_btn = QPushButton("刷新数据")
        refresh_btn.setStyleSheet(secondary_button_style())
        refresh_btn.clicked.connect(self._handle_refresh_clicked)
        selectors.addWidget(refresh_btn)
        selectors.addStretch()
        controls_layout.addLayout(selectors)

        actions = QHBoxLayout()
        actions.setSpacing(12)

        self.single_btn = QPushButton("单视频分析")
        self.single_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: white; }} QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        self.single_btn.clicked.connect(self._run_selected_single_analysis)
        actions.addWidget(self.single_btn)

        self.batch_btn = QPushButton("批量规律分析")
        self.batch_btn.setStyleSheet(accent_button_style())
        self.batch_btn.clicked.connect(self._run_selected_batch_analysis)
        actions.addWidget(self.batch_btn)

        self.status_badge = QLabel("等待分析")
        self.status_badge.setStyleSheet(
            """
            QLabel {
                background-color: #152136;
                color: #a9c2e8;
                border: 1px solid #2f476b;
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 600;
            }
            """
        )
        actions.addWidget(self.status_badge)
        actions.addStretch()
        controls_layout.addLayout(actions)
        header_layout.addWidget(controls)

        root.addWidget(header)

        self.tabs_row = QHBoxLayout()
        self.tabs_row.setSpacing(10)
        self.single_tab_btn = QPushButton("单视频报告")
        self.single_tab_btn.clicked.connect(lambda: self._switch_report("single"))
        self.batch_tab_btn = QPushButton("批量规律报告")
        self.batch_tab_btn.clicked.connect(lambda: self._switch_report("batch"))
        self.ab_tab_btn = QPushButton("AB对比报告")
        self.ab_tab_btn.clicked.connect(lambda: self._switch_report("ab_comparison"))
        self.tabs_row.addWidget(self.single_tab_btn)
        self.tabs_row.addWidget(self.batch_tab_btn)
        self.tabs_row.addWidget(self.ab_tab_btn)
        self.tabs_row.addStretch()
        root.addLayout(self.tabs_row)

        # AB对比控制区（默认隐藏）
        self.ab_controls = self._build_ab_controls()
        root.addWidget(self.ab_controls)

        self.report_stack = QWidget()
        stack_layout = QVBoxLayout(self.report_stack)
        stack_layout.setContentsMargins(0, 0, 0, 0)

        self.single_scroll = self._create_scroll_container()
        self.batch_scroll = self._create_scroll_container()
        self.ab_scroll = self._create_scroll_container()
        stack_layout.addWidget(self.single_scroll)
        stack_layout.addWidget(self.batch_scroll)
        stack_layout.addWidget(self.ab_scroll)
        root.addWidget(self.report_stack, 1)

        self._render_single_empty()
        self._render_batch_empty()
        self._render_ab_empty()
        self._switch_report("single")

    def _create_scroll_container(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        scroll.setWidget(content)
        scroll._content_layout = layout
        return scroll

    def _build_ab_controls(self):
        """构建AB对比控制区"""
        controls = QFrame()
        controls.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
            """
        )
        layout = QVBoxLayout(controls)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # 标题
        title = QLabel("AB分组选择")
        title.setStyleSheet("color: #f4f8ff; font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        # 双组选择区
        groups_layout = QHBoxLayout()
        groups_layout.setSpacing(16)

        # A组选择区
        group_a_widget = self._build_group_selector("A", "#52c58b")
        self.group_a_combo = group_a_widget.findChild(QComboBox, "group_a_combo")
        self.group_a_list = group_a_widget.findChild(QListWidget, "group_a_list")
        self.group_a_count_label = group_a_widget.findChild(QLabel, "group_a_count")
        groups_layout.addWidget(group_a_widget, 1)

        # VS 标签
        vs_label = QLabel("VS")
        vs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vs_label.setStyleSheet("color: #8fa6c9; font-size: 18px; font-weight: 800; padding: 0 10px;")
        groups_layout.addWidget(vs_label)

        # B组选择区
        group_b_widget = self._build_group_selector("B", "#63a4ff")
        self.group_b_combo = group_b_widget.findChild(QComboBox, "group_b_combo")
        self.group_b_list = group_b_widget.findChild(QListWidget, "group_b_list")
        self.group_b_count_label = group_b_widget.findChild(QLabel, "group_b_count")
        groups_layout.addWidget(group_b_widget, 1)

        layout.addLayout(groups_layout)

        # 分析按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.ab_analyze_btn = QPushButton("开始AB对比分析")
        self.ab_analyze_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {VIOLET};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #92a0ff;
            }}
            """
        )
        self.ab_analyze_btn.clicked.connect(self._run_ab_comparison)
        btn_layout.addWidget(self.ab_analyze_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        controls.setVisible(False)
        return controls

    def _build_group_selector(self, group_name: str, accent_color: str):
        """构建单个分组选择器（A组或B组）"""
        widget = QFrame()
        widget.setStyleSheet(
            f"""
            QFrame {{
                background-color: #0d1522;
                border: 1px solid {BORDER};
                border-left: 3px solid {accent_color};
                border-radius: 12px;
            }}
            """
        )
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 组标题
        header = QLabel(f"{group_name}组")
        header.setStyleSheet(f"color: {accent_color}; font-size: 14px; font-weight: 700;")
        layout.addWidget(header)

        # 博主选择下拉框
        combo = QComboBox()
        combo.setObjectName(f"group_{group_name.lower()}_combo")
        combo.setStyleSheet(input_style(200))
        combo.addItem(f"选择{group_name}组博主", None)
        combo.currentIndexChanged.connect(lambda idx, g=group_name: self._on_group_influencer_changed(g, idx))
        layout.addWidget(combo)

        # 视频多选列表
        list_widget = QListWidget()
        list_widget.setObjectName(f"group_{group_name.lower()}_list")
        list_widget.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 8px;
                color: {TEXT_PRIMARY};
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {BORDER};
            }}
            QListWidget::item:hover {{
                background-color: {BG_SURFACE};
            }}
            QListWidget::item:selected {{
                background-color: {BG_SURFACE_HOVER};
            }}
            """
        )
        list_widget.setMaximumHeight(180)
        list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        list_widget.itemChanged.connect(lambda item, g=group_name: self._on_group_video_selection_changed(g))
        layout.addWidget(list_widget)

        # 已选数量标签
        count_label = QLabel("已选: 0")
        count_label.setObjectName(f"group_{group_name.lower()}_count")
        count_label.setStyleSheet("color: #8fa6c9; font-size: 12px;")
        layout.addWidget(count_label)

        return widget

    def _on_group_influencer_changed(self, group: str, index: int):
        """当AB分组的博主选择改变时"""
        from data.database import get_videos_by_influencer

        combo = self.group_a_combo if group == "A" else self.group_b_combo
        list_widget = self.group_a_list if group == "A" else self.group_b_list
        count_label = self.group_a_count_label if group == "A" else self.group_b_count_label

        influencer = combo.itemData(index)
        list_widget.clear()

        if influencer:
            videos = get_videos_by_influencer(influencer["id"], 50)
            for video in videos:
                desc = (video.get("description") or video.get("title") or "无描述").replace("\n", " ")
                label = f"{desc[:40]}{'...' if len(desc) > 40 else ''}"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, video)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                list_widget.addItem(item)

        count_label.setText("已选: 0")

    def _on_group_video_selection_changed(self, group: str):
        """当AB分组的视频选择改变时"""
        list_widget = self.group_a_list if group == "A" else self.group_b_list
        count_label = self.group_a_count_label if group == "A" else self.group_b_count_label

        selected_count = 0
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_count += 1

        count_label.setText(f"已选: {selected_count}")

    def _get_selected_group_videos(self, group: str) -> list:
        """获取指定组选中的视频列表"""
        list_widget = self.group_a_list if group == "A" else self.group_b_list
        videos = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                video = item.data(Qt.ItemDataRole.UserRole)
                if video:
                    videos.append(video)
        return videos

    def _refresh_ab_controls(self):
        """刷新AB对比控制区的博主列表"""
        from data.database import get_all_influencers
        from core.platforms import platform_label

        influencers = get_all_influencers()

        for combo in [self.group_a_combo, self.group_b_combo]:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("选择博主", None)
            for influencer in influencers:
                label = f"{platform_label(influencer.get('platform'))} | @{influencer['username']}"
                combo.addItem(label, influencer)
            combo.blockSignals(False)

    def _set_scroll_content(self, scroll: QScrollArea, widgets):
        layout = scroll._content_layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for widget in widgets:
            layout.addWidget(widget)
        layout.addStretch()

    def _switch_report(self, mode: str):
        self._current_ab_tab = mode
        single_active = mode == "single"
        batch_active = mode == "batch"
        ab_active = mode == "ab_comparison"

        self.single_scroll.setVisible(single_active)
        self.batch_scroll.setVisible(batch_active)
        self.ab_scroll.setVisible(ab_active)

        # 控制区显示/隐藏
        self.ab_controls.setVisible(ab_active)

        active_style = f"QPushButton {{ background-color: {TEXT_PRIMARY}; color: #0d1730; }}"
        idle_style = f"QPushButton {{ background-color: {BG_PANEL}; color: {TEXT_SECONDARY}; border: 1px solid {BORDER}; }} QPushButton:hover {{ background-color: #17243a; }}"
        self.single_tab_btn.setStyleSheet(active_style if single_active else idle_style)
        self.batch_tab_btn.setStyleSheet(active_style if batch_active else idle_style)
        self.ab_tab_btn.setStyleSheet(active_style if ab_active else idle_style)

        # 当切换到AB对比Tab时，刷新博主列表
        if ab_active:
            self._refresh_ab_controls()

    def _is_external_batch_context(self) -> bool:
        return bool(self._external_batch_context)

    def _clear_external_batch_context(self):
        self._external_batch_context = None

    def _handle_refresh_clicked(self):
        if self._is_external_batch_context():
            self._clear_external_batch_context()
            self._show_status("已退出批量聚合范围，恢复普通选择模式", "#a9c2e8")
        self.refresh()

    def _update_controls_for_context(self):
        external_batch = self._is_external_batch_context()
        self.video_combo.setEnabled(not external_batch)
        self.single_btn.setEnabled(not external_batch)

        if external_batch:
            self.influencer_combo.setToolTip("当前上下文来自数据视图的批量聚合分析")
            self.video_combo.setToolTip("聚合范围没有单条视频下拉上下文")
            self.single_btn.setToolTip("请返回数据视图选择单条视频后再执行单视频分析")
        else:
            self.influencer_combo.setToolTip("")
            self.video_combo.setToolTip("")
            self.single_btn.setToolTip("")

    def _apply_external_batch_context(self):
        context = self._external_batch_context or {}
        label = context.get("label", "当前批量范围")
        videos = list(context.get("videos", []))

        self.influencer_combo.blockSignals(True)
        self.influencer_combo.clear()
        self.influencer_combo.addItem(f"批量范围：{label}", None)
        self.influencer_combo.setCurrentIndex(0)
        self.influencer_combo.blockSignals(False)

        self.video_combo.blockSignals(True)
        self.video_combo.clear()
        self.video_combo.addItem(f"已聚合 {len(videos)} 条视频", None)
        self.video_combo.blockSignals(False)

        self._current_influencer = None
        self._current_videos = videos
        self._update_controls_for_context()

    def refresh(self):
        from data.database import get_all_influencers, get_videos_by_influencer

        if self._is_external_batch_context():
            self._apply_external_batch_context()
            return

        influencers = get_all_influencers()
        selected_influencer_id = self._current_influencer.get("id") if self._current_influencer else None
        selected_video_id = self.video_combo.currentData()

        self.influencer_combo.blockSignals(True)
        self.influencer_combo.clear()
        self.influencer_combo.addItem("选择博主", None)
        selected_index = 0
        for idx, influencer in enumerate(influencers, start=1):
            label = f"{platform_label(influencer.get('platform'))} | @{influencer['username']}"
            self.influencer_combo.addItem(label, influencer)
            if influencer["id"] == selected_influencer_id:
                selected_index = idx
        self.influencer_combo.setCurrentIndex(selected_index)
        self.influencer_combo.blockSignals(False)

        if selected_index > 0:
            self._current_influencer = self.influencer_combo.currentData()
            self._current_videos = get_videos_by_influencer(self._current_influencer["id"], 100)
        else:
            self._current_influencer = None
            self._current_videos = []

        self._reload_video_combo(selected_video_id)
        self._update_controls_for_context()

    def _on_influencer_changed(self, index: int):
        from data.database import get_videos_by_influencer

        self._clear_external_batch_context()
        self._current_influencer = self.influencer_combo.itemData(index)
        if self._current_influencer:
            self._current_videos = get_videos_by_influencer(self._current_influencer["id"], 100)
        else:
            self._current_videos = []
        self._reload_video_combo()
        self._update_controls_for_context()

    def _reload_video_combo(self, selected_video_id=None):
        self.video_combo.clear()
        if not self._current_videos:
            self.video_combo.addItem("选择视频", None)
            return

        chosen_index = 0
        for idx, video in enumerate(self._current_videos):
            desc = (video.get("description") or video.get("title") or "无描述").replace("\n", " ")
            label = f"{idx + 1}. {desc[:52]}{'...' if len(desc) > 52 else ''}"
            self.video_combo.addItem(label, video["id"])
            if selected_video_id and video["id"] == selected_video_id:
                chosen_index = idx
        self.video_combo.setCurrentIndex(chosen_index)

    def open_single_analysis(self, influencer: dict, video: dict):
        self._clear_external_batch_context()
        self.refresh()
        self._select_context(influencer, video)
        self._switch_report("single")
        self.start_single_analysis(video, influencer.get("username", ""))

    def open_batch_analysis(self, influencer: dict | None, videos: list, username: str = ""):
        if influencer is None and username:
            self._external_batch_context = {
                "label": username,
                "videos": list(videos),
            }
        else:
            self._clear_external_batch_context()

        self.refresh()
        video = videos[0] if videos else None
        self._select_context(influencer, video)
        self._switch_report("batch")
        subject = username or (influencer.get("username", "") if influencer else "")
        self.start_batch_analysis(videos, subject)

    def _select_context(self, influencer: dict | None, video: dict | None):
        if self._is_external_batch_context():
            return

        if influencer:
            for idx in range(self.influencer_combo.count()):
                item = self.influencer_combo.itemData(idx)
                if item and item.get("id") == influencer.get("id"):
                    self.influencer_combo.setCurrentIndex(idx)
                    break

        if video:
            for idx in range(self.video_combo.count()):
                if self.video_combo.itemData(idx) == video.get("id"):
                    self.video_combo.setCurrentIndex(idx)
                    break

    def _run_selected_single_analysis(self):
        if self._is_external_batch_context():
            self._show_status("当前为批量聚合范围，请返回数据视图选择单条视频后再分析", "#ffb86b")
            return

        video = self._get_selected_video()
        if not video:
            self._show_status("请先选择一个视频后再开始单视频分析", "#ffb86b")
            return

        username = self._current_influencer.get("username", "") if self._current_influencer else ""
        self.start_single_analysis(video, username)

    def _run_selected_batch_analysis(self):
        if self._is_external_batch_context():
            videos = self._external_batch_context.get("videos", [])
            label = self._external_batch_context.get("label", "当前批量范围")
            if not videos:
                self._show_status("当前批量范围暂无可分析的视频", "#ff8b8b")
                return
            self.start_batch_analysis(videos[:10], label)
            return

        if not self._current_influencer:
            self._show_status("请先选择博主后再开始批量规律分析", "#ffb86b")
            return

        if not self._current_videos:
            self._show_status("当前博主暂无视频数据，无法执行批量规律分析", "#ff8b8b")
            return

        username = self._current_influencer.get("username", "")
        self.start_batch_analysis(self._current_videos[:10], username)

    def _get_selected_video(self):
        selected_id = self.video_combo.currentData()
        for video in self._current_videos:
            if video["id"] == selected_id:
                return video
        return None

    def _get_subject_label(self, username: str) -> str:
        if not username:
            return "当前范围"
        if username.startswith("已选 "):
            return username
        return f"@{username}"

    def start_single_analysis(self, video: dict, username: str = ""):
        self._render_loading(
            mode="single",
            title="正在进行单视频分析",
            desc="正在拆解开场钩子、内容结构、文案风格和可复用策略，请稍候。",
        )
        self._start_worker("single", video=video, username=username)

    def start_batch_analysis(self, videos: list, username: str = ""):
        self._render_loading(
            mode="batch",
            title="正在进行批量规律分析",
            desc="正在汇总 Top 视频的共性结构、爆款公式、BGM 与标签策略，请稍候。",
        )
        self._start_worker("batch", videos=videos, username=username)

    def _start_worker(self, mode: str, video=None, videos=None, username: str = "",
                        group_a_videos=None, group_b_videos=None, group_a_label: str = "", group_b_label: str = ""):
        if self._worker and self._worker.isRunning():
            self._show_status("已有分析任务正在执行，请稍候完成后再发起新任务", "#ffb86b")
            return

        self._set_busy(True, mode)
        self._worker = AnalysisWorker(
            mode, self.main_window.ai_analyzer,
            video=video, videos=videos, username=username,
            group_a_videos=group_a_videos, group_b_videos=group_b_videos,
            group_a_label=group_a_label, group_b_label=group_b_label
        )
        self._worker.finished.connect(self._handle_analysis_result)
        self._worker.failed.connect(self._handle_analysis_error)
        self._worker.start()

    def _handle_analysis_result(self, mode: str, result, payload, username: str):
        self._set_busy(False, mode)
        if not result:
            self._handle_analysis_error("AI 返回为空，请检查模型配置或稍后重试。")
            return

        if mode == "single":
            from data.database import save_ai_analysis

            video = payload
            save_ai_analysis(video["id"], result)
            self.show_analysis(video, result, username)
            self._show_status("单视频分析已完成", "#6fe0a9")
            return

        if mode == "ab_comparison":
            from data.database import save_ab_comparison

            group_a_videos = payload.get("group_a_videos", [])
            group_b_videos = payload.get("group_b_videos", [])
            group_a_label = payload.get("group_a_label", "A组")
            group_b_label = payload.get("group_b_label", "B组")

            # 保存到数据库
            group_a_ids = [v["id"] for v in group_a_videos]
            group_b_ids = [v["id"] for v in group_b_videos]
            save_ab_comparison(group_a_ids, group_b_ids, result, group_a_label, group_b_label)

            self.show_ab_comparison(result, group_a_label, group_b_label)
            self._show_status("AB对比分析已完成", "#6fe0a9")
            return

        self.show_batch_analysis(result, username)
        self._show_status("批量规律分析已完成", "#6fe0a9")

    def _handle_analysis_error(self, error: str):
        self._set_busy(False, "")
        self._show_status(f"分析失败：{error}", "#ff8b8b")
        error_state = EmptyState("分析失败", error or "未知错误")
        if self.single_scroll.isVisible():
            self._set_scroll_content(self.single_scroll, [error_state])
        elif self.ab_scroll.isVisible():
            self._set_scroll_content(self.ab_scroll, [error_state])
        else:
            self._set_scroll_content(self.batch_scroll, [error_state])

    def _set_busy(self, busy: bool, mode: str):
        self.influencer_combo.setEnabled(not busy and not self._is_external_batch_context())
        self.batch_btn.setEnabled(not busy)

        if self._is_external_batch_context():
            self.video_combo.setEnabled(False)
            self.single_btn.setEnabled(False)
        else:
            self.video_combo.setEnabled(not busy)
            self.single_btn.setEnabled(not busy)

        # AB对比控制区状态
        self.ab_analyze_btn.setEnabled(not busy)
        self.group_a_combo.setEnabled(not busy)
        self.group_b_combo.setEnabled(not busy)
        self.group_a_list.setEnabled(not busy)
        self.group_b_list.setEnabled(not busy)

        if busy:
            if mode == "single":
                self._loading_base = "单视频分析中"
            elif mode == "ab_comparison":
                self._loading_base = "AB对比分析中"
            else:
                self._loading_base = "批量规律分析中"
            self._loading_step = 0
            self._loading_timer.start(380)
            self._tick_loading()
        else:
            self._loading_timer.stop()
            self._update_controls_for_context()

    def _tick_loading(self):
        dots = "." * (self._loading_step % 4)
        self.status_badge.setText(f"{self._loading_base}{dots}")
        self.status_badge.setStyleSheet(
            """
            QLabel {
                background-color: #1f2a3d;
                color: #ffd38b;
                border: 1px solid #556885;
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 700;
            }
            """
        )
        self._loading_step += 1

    def _show_status(self, text: str, color: str):
        self.status_badge.setText(text)
        self.status_badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: #152136;
                color: {color};
                border: 1px solid #2f476b;
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 700;
            }}
            """
        )

    def _render_loading(self, mode: str, title: str, desc: str):
        panel = EmptyState(title, desc)
        note = QLabel("AI 正在生成结构化报告，界面会保持响应，完成后自动展示结果。")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {SUCCESS}; font-size: 13px; padding-top: 12px;")
        panel.layout().addWidget(note)

        if mode == "single":
            self._set_scroll_content(self.single_scroll, [panel])
            self._switch_report("single")
        elif mode == "ab_comparison":
            self._set_scroll_content(self.ab_scroll, [panel])
            self._switch_report("ab_comparison")
        else:
            self._set_scroll_content(self.batch_scroll, [panel])
            self._switch_report("batch")

    def _render_single_empty(self):
        self._set_scroll_content(
            self.single_scroll,
            [
                EmptyState(
                    "单视频分析",
                    "选择一个博主和视频后点击“单视频分析”，这里会展示拆解后的开场钩子、内容结构、视觉风格和复用建议。",
                )
            ],
        )

    def _render_batch_empty(self):
        self._set_scroll_content(
            self.batch_scroll,
            [
                EmptyState(
                    "批量规律分析",
                    "选择博主后点击\"批量规律分析\"，系统会基于当前范围内表现最好的视频总结爆款规律与创作公式。",
                )
            ],
        )
    
    def _render_ab_empty(self):
        self._set_scroll_content(
            self.ab_scroll,
            [
                EmptyState(
                    "AB对比分析",
                    "选择两组视频进行对比分析，找出表现差异的根本原因和优化建议。",
                )
            ],
        )
    
    def _run_ab_comparison(self):
        """执行AB对比分析"""
        group_a_videos = self._get_selected_group_videos("A")
        group_b_videos = self._get_selected_group_videos("B")
    
        # 验证两组都至少选择了1个视频
        if not group_a_videos:
            self._show_status("请至少选择1个A组视频", "#ffb86b")
            return
        if not group_b_videos:
            self._show_status("请至少选择1个B组视频", "#ffb86b")
            return
    
        # 获取组标签
        group_a_label = "A组"
        group_b_label = "B组"
        if self.group_a_combo.currentData():
            group_a_label = self.group_a_combo.currentData().get("username", "A组")
        if self.group_b_combo.currentData():
            group_b_label = self.group_b_combo.currentData().get("username", "B组")
    
        self._render_loading(
            mode="ab_comparison",
            title="正在进行AB对比分析",
            desc="正在对比两组视频的表现差异、分析原因并生成优化建议，请稍候。",
        )
        self._start_worker(
            "ab_comparison",
            group_a_videos=group_a_videos,
            group_b_videos=group_b_videos,
            group_a_label=group_a_label,
            group_b_label=group_b_label,
        )
    
    def show_analysis(self, video: dict, analysis: dict, username: str = ""):
        desc = video.get("description") or video.get("title") or "无描述"
        subject = self._get_subject_label(username)
        metrics = [
            MetricChip("播放量", self._format_number(video.get("play_count", 0)), "#ffb86b"),
            MetricChip("点赞数", self._format_number(video.get("like_count", 0)), "#ff7f96"),
            MetricChip("评论数", self._format_number(video.get("comment_count", 0)), "#6fe0a9"),
            MetricChip("分享数", self._format_number(video.get("share_count", 0)), "#84b6ff"),
        ]

        hero = self._build_report_hero(
            f"{subject} 的单视频分析",
            desc,
            "单条视频拆解结果",
            "#ff7b65",
            extra_text=f"发布时间：{video.get('published_at') or '未知'}    时长：{video.get('duration') or 0}s",
        )
        metrics_frame = self._wrap_metric_row(metrics)

        hook_banner = QFrame()
        hook_banner.setStyleSheet(card_style(VIOLET))
        hook_layout = QVBoxLayout(hook_banner)
        hook_layout.setContentsMargins(20, 18, 20, 18)
        hook_layout.setSpacing(8)

        hook_label = QLabel("核心钩子类型")
        hook_label.setStyleSheet("color: #8fa6c9; font-size: 12px; font-weight: 600;")
        hook_layout.addWidget(hook_label)

        hook_value = QLabel(analysis.get("hook_type", "未知"))
        hook_value.setStyleSheet("color: #f6f8ff; font-size: 24px; font-weight: 800;")
        hook_layout.addWidget(hook_value)

        hook_desc = QLabel(analysis.get("hook_description", "暂无钩子描述"))
        hook_desc.setWordWrap(True)
        hook_desc.setStyleSheet("color: #d4e0f3; font-size: 14px; line-height: 1.7;")
        hook_layout.addWidget(hook_desc)

        # S.T.A.R.T 框架拆解区域
        start_framework = analysis.get("start_framework", {})
        start_widget = None
        if start_framework:
            start_widget = self._build_start_framework_widget(start_framework)

        # 爆款达标线对比区域
        benchmark = analysis.get("performance_benchmark", {})
        benchmark_widget = None
        if benchmark:
            benchmark_widget = self._build_benchmark_widget(benchmark)

        grid_frame = QWidget()
        grid = QGridLayout(grid_frame)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        cards = [
            ("开场脚本", analysis.get("opening_script", ""), "#ff9e63"),
            ("内容结构", analysis.get("content_structure", ""), "#6fe0a9"),
            ("BGM 策略", analysis.get("bgm_strategy", ""), "#79a8ff"),
            ("视觉风格", analysis.get("visual_style", ""), "#c29dff"),
            ("文案风格", analysis.get("copywriting_style", ""), "#ffd270"),
            ("复用建议", analysis.get("replication_suggestions", ""), "#7ae0d3"),
        ]
        for idx, (title, content, accent) in enumerate(cards):
            grid.addWidget(AnalysisCard(title, content, accent), idx // 2, idx % 2)

        # 仿写脚本模板区域
        script_template = analysis.get("script_template", "")
        script_widget = None
        if script_template:
            script_widget = self._build_script_template_widget(script_template)

        # 组装所有组件
        widgets = [hero, metrics_frame, hook_banner]
        if start_widget:
            widgets.append(start_widget)
        if benchmark_widget:
            widgets.append(benchmark_widget)
        widgets.append(grid_frame)
        if script_widget:
            widgets.append(script_widget)

        self._set_scroll_content(self.single_scroll, widgets)
        self._switch_report("single")

    def show_batch_analysis(self, analysis: dict, username: str = ""):
        count = analysis.get("analyzed_videos_count", 0)
        subject = self._get_subject_label(username)
        hero = self._build_report_hero(
            f"{subject} 的批量规律分析",
            f"基于表现最好的 {count} 条视频，提炼可复用的内容结构、钩子模型与选题策略。",
            "批量规律总结",
            "#6176ff",
            extra_text="建议将下方公式与建议结合具体赛道做二次改写，不要直接照搬。",
        )

        formula = QFrame()
        formula.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #142238, stop:1 #203752);
                border: 1px solid #4d6b93;
                border-radius: 20px;
            }
            """
        )
        formula_layout = QVBoxLayout(formula)
        formula_layout.setContentsMargins(20, 18, 20, 18)
        formula_layout.setSpacing(8)

        formula_title = QLabel("爆款内容公式")
        formula_title.setStyleSheet("color: #aab8ff; font-size: 13px; font-weight: 700;")
        formula_layout.addWidget(formula_title)

        formula_content = QLabel(analysis.get("hook_formula", "暂无总结"))
        formula_content.setWordWrap(True)
        formula_content.setStyleSheet("color: #f2f5ff; font-size: 20px; font-weight: 700; line-height: 1.7;")
        formula_layout.addWidget(formula_content)

        # S.T.A.R.T 共同模式区域
        start_patterns = analysis.get("common_start_patterns", {})
        start_section = None
        if start_patterns and isinstance(start_patterns, dict):
            start_section = self._build_start_patterns_section(start_patterns)

        grid_frame = QWidget()
        grid = QGridLayout(grid_frame)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        cards = [
            ("共同钩子策略", analysis.get("common_hooks", ""), "#ff8b7a"),
            ("高频内容模式", analysis.get("top_patterns", ""), "#7ad6a5"),
            ("BGM 洞察", analysis.get("bgm_insights", ""), "#83b2ff"),
            ("标签策略", analysis.get("hashtag_strategy", ""), "#ffc56f"),
            ("内容优化建议", analysis.get("content_recommendations", ""), "#87f1d7"),
        ]
        for idx, (title, content, accent) in enumerate(cards):
            grid.addWidget(AnalysisCard(title, content, accent), idx // 2, idx % 2)

        # 通用仿写模板区域
        script_template = analysis.get("script_template", "")
        template_section = None
        if script_template and isinstance(script_template, str):
            template_section = self._build_script_template_section(script_template)

        # 组装所有组件
        widgets = [hero, formula]
        if start_section:
            widgets.append(start_section)
        widgets.append(grid_frame)
        if template_section:
            widgets.append(template_section)

        self._set_scroll_content(self.batch_scroll, widgets)
        self._switch_report("batch")

    def _build_start_patterns_section(self, patterns: dict) -> QWidget:
        """构建 S.T.A.R.T 共同模式展示区域"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 区域标题
        title_label = QLabel("S.T.A.R.T 共同策略模式")
        title_label.setStyleSheet("color: #f3f7ff; font-size: 16px; font-weight: 700;")
        layout.addWidget(title_label)

        # S.T.A.R.T 阶段定义
        start_stages = [
            ("S", "Stop · 钩子", "stop", "#ff6b6b"),
            ("T", "Tension · 悬念", "tension", "#ffa94d"),
            ("A", "Authority · 信任", "authority", "#51cf66"),
            ("R", "Reveal · 交付", "reveal", "#339af0"),
            ("T", "Transfer · 引导", "transfer", "#cc5de8"),
        ]

        for letter, stage_name, key, color in start_stages:
            card = QFrame()
            card.setStyleSheet(
                f"""
                QFrame {{
                    background-color: #1a1e24;
                    border: 1px solid #2a3441;
                    border-left: 4px solid {color};
                    border-radius: 12px;
                }}
                """
            )
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(12)

            # 左侧字母标记
            letter_label = QLabel(letter)
            letter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            letter_label.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {color};
                    color: #ffffff;
                    border-radius: 8px;
                    padding: 4px 10px;
                    font-size: 16px;
                    font-weight: 800;
                }}
                """
            )
            letter_label.setFixedSize(36, 36)
            card_layout.addWidget(letter_label)

            # 右侧内容区域
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(4)

            stage_label = QLabel(stage_name)
            stage_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 700;")
            content_layout.addWidget(stage_label)

            pattern_text = patterns.get(key, "暂无数据")
            desc_label = QLabel(pattern_text)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #c6d5ea; font-size: 14px; line-height: 1.6;")
            content_layout.addWidget(desc_label)

            card_layout.addWidget(content_widget, 1)
            layout.addWidget(card)

        return container

    def _build_script_template_section(self, template: str) -> QWidget:
        """构建通用仿写模板展示区域"""
        container = QFrame()
        container.setStyleSheet(
            """
            QFrame {
                background-color: #1a1e24;
                border: 1px solid #2a3441;
                border-left: 4px solid #ffd700;
                border-radius: 12px;
            }
            """
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel("通用 S.T.A.R.T 创作模板")
        title_label.setStyleSheet("color: #ffd700; font-size: 15px; font-weight: 700;")
        layout.addWidget(title_label)

        # 内容区域
        content_frame = QFrame()
        content_frame.setStyleSheet(
            """
            QFrame {
                background-color: #141820;
                border-radius: 8px;
            }
            """
        )
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(16, 14, 16, 14)
        content_layout.setSpacing(8)

        # 按行显示模板内容
        lines = template.split("\n")
        for line in lines:
            if line.strip():
                line_label = QLabel(line.strip())
                line_label.setWordWrap(True)
                line_label.setStyleSheet(
                    "color: #e6eefb; font-size: 14px; line-height: 1.7; font-family: Consolas, Monaco, monospace;"
                )
                content_layout.addWidget(line_label)

        layout.addWidget(content_frame)
        return container

    def _build_report_hero(self, title: str, desc: str, badge: str, accent: str, extra_text: str = ""):
        frame = QFrame()
        frame.setStyleSheet(card_style(accent))
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        badge_label = QLabel(badge)
        badge_label.setStyleSheet(
            f"""
            QLabel {{
                background-color: rgba({QColor(accent).red()}, {QColor(accent).green()}, {QColor(accent).blue()}, 45);
                color: {accent};
                border-radius: 12px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 700;
            }}
            """
        )
        badge_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        layout.addWidget(badge_label)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #f3f7ff; font-size: 24px; font-weight: 800;")
        layout.addWidget(title_label)

        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #c6d5ea; font-size: 14px; line-height: 1.75;")
        layout.addWidget(desc_label)

        if extra_text:
            extra_label = QLabel(extra_text)
            extra_label.setWordWrap(True)
            extra_label.setStyleSheet("color: #8ea7ca; font-size: 12px;")
            layout.addWidget(extra_label)

        return frame

    def _wrap_metric_row(self, metrics: list):
        frame = QWidget()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        for metric in metrics:
            layout.addWidget(metric)
        return frame

    def _format_number(self, value):
        value = value or 0
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{value / 1_000:.1f}K"
        return str(value)

    def _build_start_framework_widget(self, start_framework: dict) -> QFrame:
        """构建 S.T.A.R.T 框架拆解区域"""
        container = QFrame()
        container.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
            """
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # 区域标题
        title_label = QLabel("S.T.A.R.T 框架拆解")
        title_label.setStyleSheet("color: #f4f8ff; font-size: 16px; font-weight: 700;")
        layout.addWidget(title_label)

        # S.T.A.R.T 阶段定义
        start_stages = [
            ("S", "Stop · 钩子", "stop", "#ff6b6b"),
            ("T", "Tension · 悬念", "tension", "#ffa94d"),
            ("A", "Authority · 信任", "authority", "#51cf66"),
            ("R", "Reveal · 交付", "reveal", "#339af0"),
            ("T", "Transfer · 引导", "transfer", "#cc5de8"),
        ]

        for letter, stage_name, key, color in start_stages:
            stage_card = QFrame()
            stage_card.setStyleSheet(
                f"""
                QFrame {{
                    background-color: #1a1e24;
                    border-left: 4px solid {color};
                    border-radius: 10px;
                }}
                """
            )
            card_layout = QHBoxLayout(stage_card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(12)

            # 左侧字母标记（圆形）
            letter_label = QLabel(letter)
            letter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            letter_label.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {color};
                    color: #ffffff;
                    border-radius: 14px;
                    font-size: 14px;
                    font-weight: 800;
                    min-width: 28px;
                    max-width: 28px;
                    min-height: 28px;
                    max-height: 28px;
                }}
                """
            )
            card_layout.addWidget(letter_label)

            # 右侧内容区域
            content_layout = QVBoxLayout()
            content_layout.setSpacing(4)

            stage_title = QLabel(stage_name)
            stage_title.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 700;")
            content_layout.addWidget(stage_title)

            stage_content = QLabel(start_framework.get(key, "暂无内容"))
            stage_content.setWordWrap(True)
            stage_content.setStyleSheet("color: #c6d5ea; font-size: 13px; line-height: 1.6;")
            content_layout.addWidget(stage_content)

            card_layout.addLayout(content_layout, 1)
            layout.addWidget(stage_card)

        return container

    def _build_benchmark_widget(self, benchmark: dict) -> QFrame:
        """构建爆款达标线对比区域"""
        container = QFrame()
        container.setStyleSheet(
            """
            QFrame {
                background-color: #1e2227;
                border: 1px solid #2f3a4a;
                border-radius: 16px;
            }
            """
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel("爆款达标线对比")
        title_label.setStyleSheet("color: #f4f8ff; font-size: 16px; font-weight: 700;")
        layout.addWidget(title_label)

        # 互动率与达标状态行
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        # 互动率数值
        engagement_rate = benchmark.get("engagement_rate", 0)
        rate_value = QLabel(f"{engagement_rate}%")
        rate_value.setStyleSheet("color: #f4f8ff; font-size: 32px; font-weight: 800;")
        top_row.addWidget(rate_value)

        # 达标状态标签
        is_passed = benchmark.get("verdict", "").startswith("✓") or benchmark.get("verdict", "").startswith("✔")
        if not is_passed:
            verdict = benchmark.get("verdict", "")
            is_passed = "达标" in verdict or "通过" in verdict or "成功" in verdict

        status_color = "#51cf66" if is_passed else "#ffa94d"
        status_icon = "✓" if is_passed else "✗"
        status_text = "已达标" if is_passed else "未达标"

        status_label = QLabel(f"{status_icon} {status_text}")
        status_label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {status_color}22;
                color: {status_color};
                border: 1px solid {status_color}44;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 700;
            }}
            """
        )
        top_row.addWidget(status_label)
        top_row.addStretch()
        layout.addLayout(top_row)

        # 基准线说明
        benchmark_8pct = benchmark.get("benchmark_8pct", "8%")
        benchmark_label = QLabel(f"爆款达标线：{benchmark_8pct}")
        benchmark_label.setStyleSheet("color: #8fa6c9; font-size: 12px;")
        layout.addWidget(benchmark_label)

        # 综合评价
        verdict_text = benchmark.get("verdict", "")
        if verdict_text:
            verdict_label = QLabel(verdict_text)
            verdict_label.setWordWrap(True)
            verdict_label.setStyleSheet("color: #d4e0f3; font-size: 14px; line-height: 1.6;")
            layout.addWidget(verdict_label)

        # 改进建议
        improvement_tips = benchmark.get("improvement_tips", "")
        if improvement_tips:
            tips_frame = QFrame()
            tips_frame.setStyleSheet(
                """
                QFrame {
                    background-color: #141820;
                    border-radius: 10px;
                }
                """
            )
            tips_layout = QVBoxLayout(tips_frame)
            tips_layout.setContentsMargins(14, 12, 14, 12)

            tips_title = QLabel("改进建议")
            tips_title.setStyleSheet("color: #ffa94d; font-size: 12px; font-weight: 700;")
            tips_layout.addWidget(tips_title)

            tips_content = QLabel(improvement_tips)
            tips_content.setWordWrap(True)
            tips_content.setStyleSheet("color: #c6d5ea; font-size: 13px; line-height: 1.6;")
            tips_layout.addWidget(tips_content)

            layout.addWidget(tips_frame)

        return container

    def _build_script_template_widget(self, script_template: str) -> QFrame:
        """构建仿写脚本模板区域"""
        container = QFrame()
        container.setStyleSheet(
            f"""
            QFrame {{
                background-color: #1a1e24;
                border: 1px solid {BORDER};
                border-left: 4px solid #ffd700;
                border-radius: 16px;
            }}
            """
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel("S.T.A.R.T 仿写脚本模板")
        title_label.setStyleSheet("color: #ffd700; font-size: 16px; font-weight: 700;")
        layout.addWidget(title_label)

        # 脚本内容区域（引用块风格）
        content_frame = QFrame()
        content_frame.setStyleSheet(
            """
            QFrame {
                background-color: #141820;
                border-left: 3px solid #ffd700;
                border-radius: 8px;
            }
            """
        )
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(16, 14, 16, 14)
        content_layout.setSpacing(8)

        # 按行分割脚本模板
        lines = script_template.split("\n")
        for line in lines:
            line = line.strip()
            if line:
                line_label = QLabel(line)
                line_label.setWordWrap(True)
                line_label.setStyleSheet("color: #e6eefb; font-size: 14px; line-height: 1.8; font-family: 'Consolas', 'Monaco', monospace;")
                content_layout.addWidget(line_label)

        layout.addWidget(content_frame)
        return container

    def show_ab_comparison(self, result: dict, group_a_label: str = "A组", group_b_label: str = "B组"):
        """渲染AB对比分析报告"""
        widgets = []

        # 4.1 标题英雄区
        winner = result.get("winner", "")
        winner_badge = ""
        if winner == "A":
            winner_badge = f"🏆 {group_a_label} 胜出"
        elif winner == "B":
            winner_badge = f"🏆 {group_b_label} 胜出"
        else:
            winner_badge = "🤝 两组持平"

        hero = self._build_ab_hero(group_a_label, group_b_label, winner_badge, winner)
        widgets.append(hero)

        # 4.2 双组概览区
        overview = self._build_ab_overview(result, group_a_label, group_b_label, winner)
        widgets.append(overview)

        # 4.3 胜出原因区
        winner_reason = result.get("winner_reason", "")
        if winner_reason:
            reason_widget = self._build_winner_reason(winner_reason, winner)
            widgets.append(reason_widget)

        # 4.4 逐维度对比区
        dimension_comparisons = result.get("dimension_comparisons", [])
        if dimension_comparisons:
            dim_section = self._build_dimension_comparison_section(dimension_comparisons, group_a_label, group_b_label)
            widgets.append(dim_section)

        # 4.5 S.T.A.R.T框架对比区
        start_comparison = result.get("start_comparison", {})
        if start_comparison:
            start_widget = self._build_ab_start_comparison(start_comparison, group_a_label, group_b_label)
            widgets.append(start_widget)

        # 4.6 根本原因分析区
        root_causes = result.get("root_causes", [])
        if root_causes:
            root_causes_widget = self._build_root_causes_section(root_causes)
            widgets.append(root_causes_widget)

        # 4.7 优化建议区
        optimization_suggestions = result.get("optimization_suggestions", [])
        if optimization_suggestions:
            suggestions_widget = self._build_optimization_suggestions(optimization_suggestions)
            widgets.append(suggestions_widget)

        # 4.8 优化版仿写脚本区
        script_template = result.get("script_template", "")
        if script_template:
            script_widget = self._build_script_template_widget(script_template)
            widgets.append(script_widget)

        self._set_scroll_content(self.ab_scroll, widgets)
        self._switch_report("ab_comparison")

    def _build_ab_hero(self, group_a_label: str, group_b_label: str, winner_badge: str, winner: str):
        """构建AB对比报告标题英雄区"""
        frame = QFrame()
        accent_color = "#ffd700" if winner else "#8fa6c9"
        frame.setStyleSheet(card_style(accent_color))
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        # 大标题
        title = QLabel("AB对比分析报告")
        title.setStyleSheet("color: #f3f7ff; font-size: 28px; font-weight: 800;")
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel(f"{group_a_label} vs {group_b_label}")
        subtitle.setStyleSheet("color: #8fa6c9; font-size: 16px; font-weight: 600;")
        layout.addWidget(subtitle)

        # 胜出方徽章
        badge = QLabel(winner_badge)
        badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {accent_color}22;
                color: {accent_color};
                border: 1px solid {accent_color}44;
                border-radius: 12px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 700;
            }}
            """
        )
        badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        layout.addWidget(badge)

        return frame

    def _build_ab_overview(self, result: dict, group_a_label: str, group_b_label: str, winner: str):
        """构建双组概览区（左右并排两个卡片）"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # A组概览
        group_a_data = result.get("group_a_overview", {})
        a_border_color = "#52c58b" if winner == "A" else BORDER
        a_card = self._build_group_overview_card(group_a_label, group_a_data, a_border_color, winner == "A")
        layout.addWidget(a_card, 1)

        # B组概览
        group_b_data = result.get("group_b_overview", {})
        b_border_color = "#63a4ff" if winner == "B" else BORDER
        b_card = self._build_group_overview_card(group_b_label, group_b_data, b_border_color, winner == "B")
        layout.addWidget(b_card, 1)

        return container

    def _build_group_overview_card(self, label: str, data: dict, border_color: str, is_winner: bool):
        """构建单个组的概览卡片"""
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 2px solid {border_color};
                border-radius: 16px;
            }}
            """
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # 组标题
        header = QLabel(label)
        header.setStyleSheet(f"color: {border_color}; font-size: 16px; font-weight: 700;")
        layout.addWidget(header)

        # 胜出标记
        if is_winner:
            winner_label = QLabel("🏆 胜出")
            winner_label.setStyleSheet(
                f"""
                QLabel {{
                    background-color: #ffd70022;
                    color: #ffd700;
                    border: 1px solid #ffd70044;
                    border-radius: 8px;
                    padding: 4px 10px;
                    font-size: 12px;
                    font-weight: 700;
                }}
                """
            )
            winner_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            layout.addWidget(winner_label)

        # 指标网格
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(8)

        metrics = [
            ("平均播放量", self._format_number(data.get("avg_plays", 0)), "#ffb86b"),
            ("平均互动率", f"{data.get('avg_engagement_rate', 0)}%", "#6fe0a9"),
        ]

        for idx, (metric_label, value, color) in enumerate(metrics):
            metric_frame = QFrame()
            metric_frame.setStyleSheet(
                f"""
                QFrame {{
                    background-color: #0d1522;
                    border-radius: 8px;
                }}
                """
            )
            metric_layout = QVBoxLayout(metric_frame)
            metric_layout.setContentsMargins(10, 8, 10, 8)
            metric_layout.setSpacing(4)

            label_widget = QLabel(metric_label)
            label_widget.setStyleSheet("color: #8fa6c9; font-size: 11px;")
            metric_layout.addWidget(label_widget)

            value_widget = QLabel(value)
            value_widget.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 700;")
            metric_layout.addWidget(value_widget)

            metrics_grid.addWidget(metric_frame, idx // 2, idx % 2)

        layout.addLayout(metrics_grid)

        # 主要钩子类型
        hook_type = data.get("hook_type", "")
        if hook_type:
            hook_widget = QLabel(f"主要钩子: {hook_type}")
            hook_widget.setStyleSheet("color: #c6d5ea; font-size: 13px;")
            layout.addWidget(hook_widget)

        # 内容模式
        content_pattern = data.get("content_pattern", "")
        if content_pattern:
            pattern_widget = QLabel(f"内容模式: {content_pattern}")
            pattern_widget.setStyleSheet("color: #c6d5ea; font-size: 13px;")
            layout.addWidget(pattern_widget)

        # 优势列表
        strengths = data.get("strengths", [])[:3]
        if strengths:
            strengths_title = QLabel("核心优势")
            strengths_title.setStyleSheet("color: #8fa6c9; font-size: 12px; margin-top: 8px;")
            layout.addWidget(strengths_title)

            for strength in strengths:
                strength_label = QLabel(f"• {strength}")
                strength_label.setStyleSheet("color: #e6eefb; font-size: 12px; line-height: 1.5;")
                strength_label.setWordWrap(True)
                layout.addWidget(strength_label)

        return frame

    def _build_winner_reason(self, reason: str, winner: str):
        """构建胜出原因区"""
        frame = QFrame()
        accent = "#ffd700" if winner else "#8fa6c9"
        frame.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a2a1a, stop:1 #1a2a3a);
                border: 1px solid {accent}44;
                border-radius: 16px;
            }}
            """
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title = QLabel("胜出关键因素")
        title.setStyleSheet(f"color: {accent}; font-size: 14px; font-weight: 700;")
        layout.addWidget(title)

        reason_label = QLabel(reason)
        reason_label.setWordWrap(True)
        reason_label.setStyleSheet("color: #f3f7ff; font-size: 18px; font-weight: 600; line-height: 1.6;")
        layout.addWidget(reason_label)

        return frame

    def _build_dimension_comparison_section(self, comparisons: list, group_a_label: str, group_b_label: str):
        """构建逐维度对比区"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 区域标题
        title = QLabel("逐维度对比分析")
        title.setStyleSheet("color: #f3f7ff; font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        for comp in comparisons:
            card = self._build_dimension_card(comp, group_a_label, group_b_label)
            layout.addWidget(card)

        return container

    def _build_dimension_card(self, comp: dict, group_a_label: str, group_b_label: str):
        """构建单个维度对比卡片"""
        dimension = comp.get("dimension", "")
        a_performance = comp.get("group_a_performance", "")
        b_performance = comp.get("group_b_performance", "")
        gap_analysis = comp.get("gap_analysis", "")
        verdict = comp.get("verdict", "")

        frame = QFrame()
        frame.setStyleSheet(card_style())
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # 维度名称和判定
        header = QHBoxLayout()
        dim_label = QLabel(dimension)
        dim_label.setStyleSheet("color: #f3f7ff; font-size: 14px; font-weight: 700;")
        header.addWidget(dim_label)
        header.addStretch()

        # 判定标签
        if verdict == "A优":
            verdict_style = "background-color: #52c58b22; color: #52c58b; border: 1px solid #52c58b44;"
        elif verdict == "B优":
            verdict_style = "background-color: #63a4ff22; color: #63a4ff; border: 1px solid #63a4ff44;"
        else:
            verdict_style = "background-color: #8fa6c922; color: #8fa6c9; border: 1px solid #8fa6c944;"

        verdict_label = QLabel(verdict)
        verdict_label.setStyleSheet(
            f"""
            QLabel {{
                {verdict_style}
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 700;
            }}
            """
        )
        header.addWidget(verdict_label)
        layout.addLayout(header)

        # 两组表现
        perf_layout = QHBoxLayout()
        perf_layout.setSpacing(12)

        a_widget = QLabel(f"{group_a_label}: {a_performance}")
        a_widget.setStyleSheet("color: #52c58b; font-size: 13px;")
        a_widget.setWordWrap(True)
        perf_layout.addWidget(a_widget, 1)

        b_widget = QLabel(f"{group_b_label}: {b_performance}")
        b_widget.setStyleSheet("color: #63a4ff; font-size: 13px;")
        b_widget.setWordWrap(True)
        perf_layout.addWidget(b_widget, 1)

        layout.addLayout(perf_layout)

        # 差距分析
        if gap_analysis:
            gap_label = QLabel(f"差距分析: {gap_analysis}")
            gap_label.setStyleSheet("color: #8fa6c9; font-size: 12px; font-style: italic;")
            gap_label.setWordWrap(True)
            layout.addWidget(gap_label)

        return frame

    def _build_ab_start_comparison(self, start_comparison: dict, group_a_label: str, group_b_label: str):
        """构建S.T.A.R.T框架对比区"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 区域标题
        title = QLabel("S.T.A.R.T 框架对比")
        title.setStyleSheet("color: #f3f7ff; font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        # S.T.A.R.T 阶段定义
        start_stages = [
            ("S", "Stop · 钩子", "stop", "#ff6b6b"),
            ("T", "Tension · 悬念", "tension", "#ffa94d"),
            ("A", "Authority · 信任", "authority", "#51cf66"),
            ("R", "Reveal · 交付", "reveal", "#339af0"),
            ("T", "Transfer · 引导", "transfer", "#cc5de8"),
        ]

        for letter, stage_name, key, color in start_stages:
            stage_data = start_comparison.get(key, {})
            if not stage_data:
                continue

            card = QFrame()
            card.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {BG_PANEL};
                    border: 1px solid {BORDER};
                    border-left: 4px solid {color};
                    border-radius: 12px;
                }}
                """
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(10)

            # 阶段标题
            stage_title = QLabel(f"{letter} · {stage_name}")
            stage_title.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 700;")
            card_layout.addWidget(stage_title)

            # 两组对比
            comparison_layout = QHBoxLayout()
            comparison_layout.setSpacing(12)

            a_content = stage_data.get("group_a", "暂无数据")
            a_widget = QLabel(f"{group_a_label}: {a_content}")
            a_widget.setStyleSheet("color: #52c58b; font-size: 13px; line-height: 1.5;")
            a_widget.setWordWrap(True)
            comparison_layout.addWidget(a_widget, 1)

            b_content = stage_data.get("group_b", "暂无数据")
            b_widget = QLabel(f"{group_b_label}: {b_content}")
            b_widget.setStyleSheet("color: #63a4ff; font-size: 13px; line-height: 1.5;")
            b_widget.setWordWrap(True)
            comparison_layout.addWidget(b_widget, 1)

            card_layout.addLayout(comparison_layout)

            # 判定
            verdict = stage_data.get("verdict", "")
            if verdict:
                if verdict == "A优":
                    verdict_color = "#52c58b"
                elif verdict == "B优":
                    verdict_color = "#63a4ff"
                else:
                    verdict_color = "#8fa6c9"

                verdict_label = QLabel(f"判定: {verdict}")
                verdict_label.setStyleSheet(f"color: {verdict_color}; font-size: 12px; font-weight: 700;")
                card_layout.addWidget(verdict_label)

            layout.addWidget(card)

        return container

    def _build_root_causes_section(self, root_causes: list):
        """构建根本原因分析区"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 区域标题
        title = QLabel("根本原因分析")
        title.setStyleSheet("color: #f3f7ff; font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        for idx, cause in enumerate(root_causes[:3], 1):
            card = AnalysisCard(f"原因 {idx}", cause, "#ff7b65")
            layout.addWidget(card)

        return container

    def _build_optimization_suggestions(self, suggestions: list):
        """构建优化建议区"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 区域标题
        title = QLabel("优化建议")
        title.setStyleSheet("color: #f3f7ff; font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        priority_colors = {
            "高": ("#f47f8b", "#f47f8b22"),
            "中": ("#f2b265", "#f2b26522"),
            "低": ("#52c58b", "#52c58b22"),
        }

        for suggestion in suggestions[:5]:
            if isinstance(suggestion, dict):
                content = suggestion.get("suggestion", "")
                priority = suggestion.get("priority", "中")
                impact = suggestion.get("expected_impact", "")
            else:
                content = str(suggestion)
                priority = "中"
                impact = ""

            color, bg_color = priority_colors.get(priority, ("#f2b265", "#f2b26522"))

            card = QFrame()
            card.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {bg_color};
                    border: 1px solid {color}44;
                    border-radius: 12px;
                }}
                """
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(8)

            # 优先级标签
            header = QHBoxLayout()
            priority_label = QLabel(f"优先级: {priority}")
            priority_label.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {color}33;
                    color: {color};
                    border-radius: 6px;
                    padding: 3px 10px;
                    font-size: 11px;
                    font-weight: 700;
                }}
                """
            )
            header.addWidget(priority_label)
            header.addStretch()
            card_layout.addLayout(header)

            # 建议内容
            content_label = QLabel(content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet("color: #e6eefb; font-size: 14px; line-height: 1.6;")
            card_layout.addWidget(content_label)

            # 预期影响
            if impact:
                impact_label = QLabel(f"预期影响: {impact}")
                impact_label.setStyleSheet("color: #8fa6c9; font-size: 12px; font-style: italic;")
                impact_label.setWordWrap(True)
                card_layout.addWidget(impact_label)

            layout.addWidget(card)

        return container
