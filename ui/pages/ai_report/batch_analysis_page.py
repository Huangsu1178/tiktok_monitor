"""
TikTok Monitor - Batch Analysis Page
"""

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.components.theme import (
    BG_APP,
    BG_PANEL,
    BG_SURFACE,
    BG_MUTED,
    BORDER,
    BORDER_STRONG,
    SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    input_style,
    card_style,
)
from ui.components.video_list_manager import VideoListManager
from ui.dialogs.selection_dialog_v2 import show_two_stage_selection
from ui.pages.ai_report.ai_report_widgets import (
    AnalysisCard,
    EmptyState,
    build_script_template_content,
    get_subject_label,
)


PAGE_STYLE = f"""
QWidget {{
    background-color: {BG_APP};
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
{input_style(220)}
"""


class BatchAnalysisWorker(QThread):
    finished = pyqtSignal(object, list, str)
    failed = pyqtSignal(str)

    def __init__(self, analyzer, videos, username: str = ""):
        super().__init__()
        self.analyzer = analyzer
        self.videos = videos
        self.username = username

    def run(self):
        try:
            result = self.analyzer.analyze_batch(self.videos, self.username)
            self.finished.emit(result, self.videos, self.username)
        except Exception as exc:
            self.failed.emit(str(exc))


class BatchAnalysisPage(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._external_batch_context = None
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(PAGE_STYLE)

        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setStyleSheet(
            f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {BG_PANEL};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {BG_MUTED};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {BORDER_STRONG};
            }}
            """
        )

        main_container = QWidget()
        root = QVBoxLayout(main_container)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        root.addWidget(self._build_top_bar())
        root.addWidget(self._build_header())

        self.report_scroll = self._create_scroll_container()
        root.addWidget(self.report_scroll, 1)
        self._render_empty()

        main_scroll.setWidget(main_container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_scroll)

    def _build_top_bar(self) -> QWidget:
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        back_btn = QPushButton("返回")
        back_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {BG_PANEL};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {BG_SURFACE};
            }}
            """
        )
        back_btn.clicked.connect(self.back_requested.emit)
        top_bar.addWidget(back_btn)

        title = QLabel("批量规律分析")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: 700;")
        top_bar.addWidget(title)
        top_bar.addStretch()

        widget = QWidget()
        widget.setLayout(top_bar)
        return widget

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 18px;
            }}
            """
        )

        layout = QVBoxLayout(header)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        self.video_list_manager = VideoListManager(mode="batch")
        self.video_list_manager.videos_changed.connect(self._on_add_videos_requested)
        self.video_list_manager.analyze_requested.connect(self._run_analysis_with_videos)
        layout.addWidget(self.video_list_manager)

        self.context_badge = QLabel("当前范围：未选择")
        self.context_badge.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12px; font-weight: 600; padding: 2px 2px 0 2px;"
        )
        layout.addWidget(self.context_badge)

        self.status_badge = QLabel("准备就绪")
        self.status_badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {BG_SURFACE};
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 700;
            }}
            """
        )
        layout.addWidget(self.status_badge)

        return header

    def _create_scroll_container(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        container._content_layout = layout
        return container

    def _set_scroll_content(self, widgets):
        layout = self.report_scroll._content_layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for widget in widgets:
            layout.addWidget(widget)
        layout.addStretch()

    def _is_external_batch_context(self) -> bool:
        return bool(self._external_batch_context)

    def _clear_external_batch_context(self):
        self._external_batch_context = None

    def set_external_context(self, videos: list, label: str = ""):
        videos = list(videos or [])
        self._external_batch_context = {
            "videos": videos,
            "label": label or get_subject_label(""),
        }

        self.video_list_manager.videos = []
        self.video_list_manager.add_videos(videos)
        self.context_badge.setText("当前范围：" + str(self._external_batch_context["label"]))
        self._show_status("已加载批量分析范围", "#a9c2e8")

    def _on_add_videos_requested(self, data):
        selected_videos = show_two_stage_selection(
            parent=self,
            title="选择要批量分析的视频",
            allow_multiple=True,
        )
        if selected_videos:
            self.video_list_manager.add_videos(selected_videos)
            self.context_badge.setText("当前范围：手动选择")

    def refresh(self):
        self._clear_external_batch_context()
        self.video_list_manager.videos = []
        self.video_list_manager._render_single_list()
        self.context_badge.setText("当前范围：未选择")
        self._show_status("准备就绪", "#a9c2e8")
        self._render_empty()

    def _run_analysis_with_videos(self, videos):
        if not videos:
            self._show_status("请先添加视频", "#ffb86b")
            return

        videos_to_analyze = list(videos[:10])
        username = ""
        if videos_to_analyze and isinstance(videos_to_analyze[0], dict):
            username = videos_to_analyze[0].get("influencer_username", "")

        self.start_analysis(videos_to_analyze, username)

    def start_analysis(self, videos: list, username: str = ""):
        self._render_loading()
        self._start_worker(videos=videos, username=username)

    def _start_worker(self, videos=None, username: str = ""):
        if self._worker and self._worker.isRunning():
            self._show_status("已有分析任务正在执行，请稍候", "#ffb86b")
            return

        self._set_busy(True)
        self._worker = BatchAnalysisWorker(self.main_window.ai_analyzer, videos or [], username)
        self._worker.finished.connect(self._handle_result)
        self._worker.failed.connect(self._handle_error)
        self._worker.start()

    def _handle_result(self, result, videos, username: str):
        self._set_busy(False)
        if not result:
            self._handle_error("AI 返回为空，请检查模型配置")
            return

        self.show_analysis(result, username)
        self._show_status("批量规律分析已完成", "#6fe0a9")

    def _handle_error(self, error: str):
        self._set_busy(False)
        self._show_status(f"分析失败：{error}", "#ff8b8b")
        self._set_scroll_content([EmptyState("分析失败", error or "未知错误")])

    def _set_busy(self, busy: bool):
        self.video_list_manager.analyze_btn.setEnabled(not busy)
        if busy:
            self._show_status("批量规律分析中...", "#ffd38b")

    def _show_status(self, text: str, color: str):
        self.status_badge.setText(text)
        self.status_badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {BG_SURFACE};
                color: {color};
                border: 1px solid {BORDER};
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 700;
            }}
            """
        )

    def _render_loading(self):
        panel = EmptyState(
            "正在进行批量规律分析",
            "正在汇总高表现视频的共性结构、钩子与内容策略，请稍候。",
        )
        note = QLabel("分析过程中界面会保持响应，完成后会自动展示结果。")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {SUCCESS}; font-size: 13px; padding-top: 12px;")
        panel.layout().addWidget(note)
        self._set_scroll_content([panel])

    def _render_empty(self):
        self._set_scroll_content(
            [
                EmptyState(
                    "批量规律分析",
                    "添加多个视频后开始分析，系统会总结共性结构、爆款公式和优化建议。",
                )
            ]
        )

    def show_analysis(self, analysis: dict, username: str = ""):
        count = analysis.get("analyzed_videos_count", 0)
        subject = get_subject_label(username)

        hero = self._build_hero(
            f"{subject} 的批量规律分析",
            f"基于 {count} 条视频，提炼共性结构、钩子策略和复用建议。",
            "批量规律总结",
            "#6176ff",
        )

        widgets = [hero]

        formula_text = analysis.get("hook_formula", "")
        if formula_text:
            widgets.append(self._build_text_card("爆款内容公式", formula_text, "#aab8ff"))

        start_section = self._build_start_patterns_section(analysis.get("common_start_patterns", {}))
        if start_section is not None:
            widgets.append(start_section)

        grid = self._build_analysis_grid(analysis)
        widgets.append(grid)

        script_template = analysis.get("script_template", "")
        if script_template:
            widgets.append(self._build_script_template_section(script_template))

        self._set_scroll_content(widgets)

    def _build_hero(self, title: str, desc: str, badge: str, accent: str):
        frame = QFrame()
        frame.setStyleSheet(card_style(accent))
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        badge_label = QLabel(badge)
        badge_label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {accent}22;
                color: {accent};
                border-radius: 12px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 700;
            }}
            """
        )
        layout.addWidget(badge_label)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 24px; font-weight: 800;")
        layout.addWidget(title_label)

        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; line-height: 1.8;")
        layout.addWidget(desc_label)

        return frame

    def _build_text_card(self, title: str, content: str, accent: str):
        return AnalysisCard(title, content, accent)

    def _build_start_patterns_section(self, patterns: dict):
        if not patterns or not isinstance(patterns, dict):
            return None

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("S.T.A.R.T 共同模式")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        stage_map = [
            ("stop", "Stop"),
            ("tension", "Tension"),
            ("authority", "Authority"),
            ("reveal", "Reveal"),
            ("transfer", "Transfer"),
        ]

        for key, label in stage_map:
            text = patterns.get(key, "")
            if text:
                layout.addWidget(AnalysisCard(label, text, "#83b2ff"))

        return container

    def _build_analysis_grid(self, analysis: dict):
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
            ("优化建议", analysis.get("content_recommendations", ""), "#87f1d7"),
        ]

        for idx, (title, content, accent) in enumerate(cards):
            grid.addWidget(AnalysisCard(title, content, accent), idx // 2, idx % 2)

        return grid_frame

    def _build_script_template_section(self, template: str):
        container = QFrame()
        container.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-left: 4px solid #ffd700;
                border-radius: 12px;
            }}
            """
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title = QLabel("通用脚本模板")
        title.setStyleSheet("color: #ffd700; font-size: 15px; font-weight: 700;")
        layout.addWidget(title)

        layout.addWidget(build_script_template_content(template, "#ffd700", "暂无脚本模板"))

        return container
