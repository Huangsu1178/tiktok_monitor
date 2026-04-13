"""
TikTok Monitor - AI Report Page
AI 分析报告页面
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
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.platforms import format_account_identity, platform_label


PAGE_STYLE = """
QWidget {
    background-color: #0b1220;
    color: #e5eefc;
}
QScrollArea {
    border: none;
    background: transparent;
}
QComboBox {
    background-color: #162033;
    color: #ecf4ff;
    border: 1px solid #2d405f;
    border-radius: 10px;
    padding: 10px 14px;
    min-width: 220px;
    font-size: 13px;
}
QComboBox::drop-down {
    border: none;
    width: 26px;
}
QComboBox QAbstractItemView {
    background-color: #162033;
    color: #ecf4ff;
    border: 1px solid #2d405f;
    selection-background-color: #2e4a77;
}
QPushButton {
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 600;
}
"""


class AnalysisWorker(QThread):
    """后台分析线程"""

    finished = pyqtSignal(str, object, object, str)
    failed = pyqtSignal(str)

    def __init__(self, mode: str, analyzer, video=None, videos=None, username: str = ""):
        super().__init__()
        self.mode = mode
        self.analyzer = analyzer
        self.video = video
        self.videos = videos or []
        self.username = username

    def run(self):
        try:
            if self.mode == "single":
                result = self.analyzer.analyze_video(self.video, self.username)
                self.finished.emit(self.mode, result, self.video, self.username)
                return

            result = self.analyzer.analyze_batch(self.videos, self.username)
            self.finished.emit(self.mode, result, self.videos, self.username)
        except Exception as exc:
            self.failed.emit(str(exc))


class MetricChip(QFrame):
    def __init__(self, label: str, value: str, accent: str):
        super().__init__()
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: #10192b;
                border: 1px solid #24324b;
                border-radius: 14px;
            }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #8fa6c9; font-size: 12px;")
        layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"color: {accent}; font-size: 18px; font-weight: 700;")
        layout.addWidget(value_widget)


class AnalysisCard(QFrame):
    def __init__(self, title: str, content: str, accent: str):
        super().__init__()
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: #10192b;
                border: 1px solid #22314b;
                border-radius: 18px;
            }}
            """
        )
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
            """
            QFrame {
                background-color: #10192b;
                border: 1px dashed #304566;
                border-radius: 18px;
            }
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
    """AI 分析报告页面"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._current_influencer = None
        self._current_videos = []
        self._worker = None
        self._loading_base = ""
        self._loading_step = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._tick_loading)
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
                    stop:0 #13203a, stop:0.45 #16284a, stop:1 #203a64);
                border: 1px solid #2d436d;
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

        subtitle = QLabel("支持单视频拆解与批量规律分析，分析过程中会展示实时等待状态，结果会自动落在下方报告区。")
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
        refresh_btn.setStyleSheet("QPushButton { background-color: #294166; color: white; } QPushButton:hover { background-color: #35517d; }")
        refresh_btn.clicked.connect(self.refresh)
        selectors.addWidget(refresh_btn)
        selectors.addStretch()
        controls_layout.addLayout(selectors)

        actions = QHBoxLayout()
        actions.setSpacing(12)

        self.single_btn = QPushButton("单视频分析")
        self.single_btn.setStyleSheet("QPushButton { background-color: #ef6b57; color: white; } QPushButton:hover { background-color: #ff7b65; }")
        self.single_btn.clicked.connect(self._run_selected_single_analysis)
        actions.addWidget(self.single_btn)

        self.batch_btn = QPushButton("批量规律分析")
        self.batch_btn.setStyleSheet("QPushButton { background-color: #4d63ff; color: white; } QPushButton:hover { background-color: #6176ff; }")
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
        self.tabs_row.addWidget(self.single_tab_btn)
        self.tabs_row.addWidget(self.batch_tab_btn)
        self.tabs_row.addStretch()
        root.addLayout(self.tabs_row)

        self.report_stack = QWidget()
        stack_layout = QVBoxLayout(self.report_stack)
        stack_layout.setContentsMargins(0, 0, 0, 0)

        self.single_scroll = self._create_scroll_container()
        self.batch_scroll = self._create_scroll_container()

        stack_layout.addWidget(self.single_scroll)
        stack_layout.addWidget(self.batch_scroll)
        root.addWidget(self.report_stack, 1)

        self._render_single_empty()
        self._render_batch_empty()
        self._switch_report("single")

    def _create_scroll_container(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        scroll.setWidget(content)
        scroll._content_widget = content
        scroll._content_layout = layout
        return scroll

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
        single_active = mode == "single"
        self.single_scroll.setVisible(single_active)
        self.batch_scroll.setVisible(not single_active)

        active_style = "QPushButton { background-color: #e6eefc; color: #0d1730; }"
        idle_style = "QPushButton { background-color: #111b2d; color: #9fb6d7; border: 1px solid #263a59; } QPushButton:hover { background-color: #17243a; }"
        self.single_tab_btn.setStyleSheet(active_style if single_active else idle_style)
        self.batch_tab_btn.setStyleSheet(active_style if not single_active else idle_style)

    def refresh(self):
        from data.database import get_all_influencers, get_videos_by_influencer

        influencers = get_all_influencers()
        selected_influencer_id = self._current_influencer.get("id") if self._current_influencer else None
        selected_video_id = self.video_combo.currentData()

        self.influencer_combo.blockSignals(True)
        self.influencer_combo.clear()
        self.influencer_combo.addItem("选择博主", None)
        selected_index = 0
        for idx, influencer in enumerate(influencers, start=1):
            self.influencer_combo.addItem(f"{platform_label(influencer.get('platform'))} · @{influencer['username']}", influencer)
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

        self._reload_video_combo(selected_video_id=selected_video_id)

    def _on_influencer_changed(self, index: int):
        from data.database import get_videos_by_influencer

        self._current_influencer = self.influencer_combo.itemData(index)
        if self._current_influencer:
            self._current_videos = get_videos_by_influencer(self._current_influencer["id"], 100)
        else:
            self._current_videos = []
        self._reload_video_combo()

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
        self.refresh()
        self._select_context(influencer, video)
        self._switch_report("single")
        self.start_single_analysis(video, influencer.get("username", ""))

    def open_batch_analysis(self, influencer: dict | None, videos: list, username: str = ""):
        self.refresh()
        video = videos[0] if videos else None
        self._select_context(influencer, video)
        self._switch_report("batch")
        self.start_batch_analysis(videos, username or (influencer.get("username", "") if influencer else ""))

    def _select_context(self, influencer: dict, video: dict | None):
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
        video = self._get_selected_video()
        if not video:
            self._show_status("请先选择一个视频后再开始单视频分析", "#ffb86b")
            return
        username = self._current_influencer.get("username", "") if self._current_influencer else ""
        self.start_single_analysis(video, username)

    def _run_selected_batch_analysis(self):
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

    def _format_analysis_subject(self, username: str):
        if not username:
            return "当前范围"
        if username.startswith("已选 "):
            return username
        return f"@{username}"

    def start_single_analysis(self, video: dict, username: str = ""):
        self._render_loading(
            mode="single",
            title="正在进行单视频分析",
            desc="我们正在拆解开头钩子、内容结构、文案风格和可复用策略，请稍候。",
        )
        self._start_worker("single", video=video, username=username)

    def start_batch_analysis(self, videos: list, username: str = ""):
        self._render_loading(
            mode="batch",
            title="正在进行批量规律分析",
            desc="正在汇总 Top 视频的共性结构、爆款公式、BGM 与标签策略，请稍候。",
        )
        self._start_worker("batch", videos=videos, username=username)

    def _start_worker(self, mode: str, video=None, videos=None, username: str = ""):
        if self._worker and self._worker.isRunning():
            self._show_status("已有分析任务正在执行，请稍候完成后再发起新任务", "#ffb86b")
            return

        self._set_busy(True, mode)
        self._worker = AnalysisWorker(mode, self.main_window.ai_analyzer, video=video, videos=videos, username=username)
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

        self.show_batch_analysis(result, username)
        self._show_status("批量规律分析已完成", "#6fe0a9")

    def _handle_analysis_error(self, error: str):
        self._set_busy(False, "")
        self._show_status(f"分析失败：{error}", "#ff8b8b")
        error_state = EmptyState("分析失败", error or "未知错误")
        if self.single_scroll.isVisible():
            self._set_scroll_content(self.single_scroll, [error_state])
        else:
            self._set_scroll_content(self.batch_scroll, [error_state])

    def _set_busy(self, busy: bool, mode: str):
        self.single_btn.setEnabled(not busy)
        self.batch_btn.setEnabled(not busy)
        self.influencer_combo.setEnabled(not busy)
        self.video_combo.setEnabled(not busy)

        if busy:
            self._loading_base = "单视频分析中" if mode == "single" else "批量规律分析中"
            self._loading_step = 0
            self._loading_timer.start(380)
            self._tick_loading()
        else:
            self._loading_timer.stop()

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
        note.setStyleSheet("color: #6fdbb0; font-size: 13px; padding-top: 12px;")
        panel.layout().addWidget(note)

        if mode == "single":
            self._set_scroll_content(self.single_scroll, [panel])
            self._switch_report("single")
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
                    "选择博主后点击“批量规律分析”，系统会基于当前博主播放表现最好的视频总结爆款规律与创作公式。",
                )
            ],
        )

    def show_analysis(self, video: dict, analysis: dict, username: str = ""):
        desc = video.get("description") or video.get("title") or "无描述"
        metrics = [
            MetricChip("播放量", self._format_number(video.get("play_count", 0)), "#ffb86b"),
            MetricChip("点赞数", self._format_number(video.get("like_count", 0)), "#ff7f96"),
            MetricChip("评论数", self._format_number(video.get("comment_count", 0)), "#6fe0a9"),
            MetricChip("分享数", self._format_number(video.get("share_count", 0)), "#84b6ff"),
        ]

        hero = self._build_report_hero(
            f"@{username} 的单视频分析",
            desc,
            "单条视频拆解结果",
            "#ff7b65",
            extra_text=f"发布时间：{video.get('published_at') or '未知'}    时长：{video.get('duration') or 0}s",
        )
        metrics_frame = self._wrap_metric_row(metrics)

        hook_banner = QFrame()
        hook_banner.setStyleSheet(
            """
            QFrame {
                background-color: #111d31;
                border: 1px solid #314769;
                border-radius: 18px;
            }
            """
        )
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
            card = AnalysisCard(title, content, accent)
            grid.addWidget(card, idx // 2, idx % 2)

        self._set_scroll_content(self.single_scroll, [hero, metrics_frame, hook_banner, grid_frame])
        self._switch_report("single")

    def show_batch_analysis(self, analysis: dict, username: str = ""):
        count = analysis.get("analyzed_videos_count", 0)
        hero = self._build_report_hero(
            f"@{username} 的批量规律分析",
            f"基于表现最好的 {count} 条视频，提炼可复用的内容结构、钩子模型与账号选题策略。",
            "批量规律总结",
            "#6176ff",
            extra_text="建议将下方公式与建议结合具体赛道做二次改写，不要直接照搬。",
        )

        formula = QFrame()
        formula.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #141f36, stop:1 #2b2f6d);
                border: 1px solid #586eff;
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

        self._set_scroll_content(self.batch_scroll, [hero, formula, grid_frame])
        self._switch_report("batch")

    def _build_report_hero(self, title: str, desc: str, badge: str, accent: str, extra_text: str = ""):
        frame = QFrame()
        frame.setStyleSheet(
            """
            QFrame {
                background-color: #10192b;
                border: 1px solid #243452;
                border-radius: 22px;
            }
            """
        )
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
