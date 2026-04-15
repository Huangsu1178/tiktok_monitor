"""
TikTok Monitor - AB Comparison Page
AB对比分析子页面
"""

from PyQt6.QtCore import QThread, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.platforms import platform_label
from ui.components.theme import (
    BG_APP,
    BG_MUTED,
    BG_PANEL,
    BG_SURFACE,
    BORDER,
    BORDER_STRONG,
    SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    accent_button_style,
    card_style,
    input_style,
    secondary_button_style,
)
from ui.pages.ai_report.ai_report_widgets import (
    AnalysisCard,
    EmptyState,
    build_script_template_content,
    build_structured_content,
)
from ui.pages.ai_report.report_utils import (
    build_ab_report_markdown,
    build_ab_report_summary,
    build_ab_report_title,
    save_report_markdown,
)
from ui.dialogs.selection_dialog_v2 import show_two_stage_selection
from ui.components.video_list_manager import VideoListManager


PAGE_STYLE = f"""
QWidget {{
    background-color: {BG_APP};
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
{input_style(200)}
"""


class ABComparisonWorker(QThread):
    """AB对比分析工作线程"""
    finished = pyqtSignal(object, dict)
    failed = pyqtSignal(str)

    def __init__(self, analyzer, group_a_videos, group_b_videos, group_a_label, group_b_label):
        super().__init__()
        self.analyzer = analyzer
        self.group_a_videos = group_a_videos
        self.group_b_videos = group_b_videos
        self.group_a_label = group_a_label
        self.group_b_label = group_b_label

    def run(self):
        try:
            result = self.analyzer.analyze_ab_comparison(
                self.group_a_videos, self.group_b_videos,
                self.group_a_label, self.group_b_label
            )
            payload = {
                "group_a_videos": self.group_a_videos,
                "group_b_videos": self.group_b_videos,
                "group_a_label": self.group_a_label,
                "group_b_label": self.group_b_label,
            }
            self.finished.emit(result, payload)
        except Exception as exc:
            self.failed.emit(str(exc))


class ABComparisonPage(QWidget):
    """AB对比分析子页面"""
    
    back_requested = pyqtSignal()
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._worker = None
        self._loading_base = ""
        self._loading_step = 0
        self._current_report_title = ""
        self._current_report_markdown = ""
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._tick_loading)
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
        
        top_bar = self._build_top_bar()
        root.addWidget(top_bar)
        
        controls = self._build_controls()
        root.addWidget(controls)
        
        self.report_scroll = self._create_scroll_container()
        root.addWidget(self.report_scroll, 1)
        
        self._render_empty()
        
        main_scroll.setWidget(main_container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_scroll)
    
    def _build_top_bar(self) -> QWidget:
        """构建顶部导航栏"""
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)
        
        back_btn = QPushButton("← 返回")
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
        
        title = QLabel("AB对比分析")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: 700;")
        top_bar.addWidget(title)
        
        top_bar.addStretch()

        self.history_btn = QPushButton("历史报告")
        self.history_btn.setStyleSheet(secondary_button_style())
        self.history_btn.clicked.connect(self._open_history)
        top_bar.addWidget(self.history_btn)

        self.download_btn = QPushButton("下载报告")
        self.download_btn.setStyleSheet(accent_button_style())
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self._download_current_report)
        top_bar.addWidget(self.download_btn)
        
        widget = QWidget()
        widget.setLayout(top_bar)
        return widget
    
    def _build_controls(self) -> QWidget:
        """构建控制区"""
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
        
        # 视频列表管理器（AB对比模式）
        self.video_list_manager = VideoListManager(mode="ab_comparison")
        self.video_list_manager.videos_changed.connect(self._on_add_videos_requested)
        self.video_list_manager.analyze_requested.connect(self._run_analysis_with_videos)
        layout.addWidget(self.video_list_manager)
        
        return controls

    def _on_add_videos_requested(self, data):
        """添加视频请求"""
        # data 是一个字典，包含 {"group": "A"} 或 {"group": "B"}
        if isinstance(data, dict) and "group" in data:
            group = data["group"]
            self._open_add_dialog_for_group(group)

    def _open_add_dialog_for_group(self, group: str):
        """为指定组打开添加对话框"""
        selected_videos = show_two_stage_selection(
            parent=self,
            title=f"选择{group}组视频",
            allow_multiple=True
        )
        
        if selected_videos:
            self.video_list_manager.add_videos(selected_videos, group=group)
    

    def refresh(self):
        """刷新数据"""
        # 重置视频列表
        if hasattr(self, 'video_list_manager'):
            self.video_list_manager.videos_a = []
            self.video_list_manager.videos_b = []
            self.video_list_manager._render_ab_list()
        self._reset_report_cache()
        self._render_empty()
    
    def _create_scroll_container(self):
        """创建报告容器"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        container._content_layout = layout
        return container
    
    def _set_scroll_content(self, widgets):
        """设置滚动区域内容"""
        layout = self.report_scroll._content_layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for widget in widgets:
            layout.addWidget(widget)
        layout.addStretch()
    
    def _reset_report_cache(self):
        self._current_report_title = ""
        self._current_report_markdown = ""
        if hasattr(self, "download_btn"):
            self.download_btn.setEnabled(False)

    def _open_history(self):
        self.main_window.ai_report_page.show_history()

    def _download_current_report(self):
        if self._current_report_markdown:
            save_report_markdown(self, self._current_report_title, self._current_report_markdown)

    def _update_current_report_cache(self, result: dict, group_a_label: str, group_b_label: str):
        self._current_report_title = build_ab_report_title(group_a_label, group_b_label)
        self._current_report_markdown = build_ab_report_markdown(
            self._current_report_title,
            result or {},
            group_a_label,
            group_b_label,
        )
        if hasattr(self, "download_btn"):
            self.download_btn.setEnabled(bool(self._current_report_markdown))

    def _save_report_history(self, payload: dict, result: dict):
        from data.database import save_ai_report

        group_a_label = payload.get("group_a_label", "A组")
        group_b_label = payload.get("group_b_label", "B组")
        title = build_ab_report_title(group_a_label, group_b_label)
        markdown = build_ab_report_markdown(title, result or {}, group_a_label, group_b_label)
        save_ai_report(
            report_type="ab_comparison",
            title=title,
            subject_label=f"{group_a_label} vs {group_b_label}",
            summary=build_ab_report_summary(result or {}, group_a_label, group_b_label),
            source_payload=payload or {},
            result_payload=result or {},
            export_markdown=markdown,
        )
        self.main_window.ai_report_page.notify_report_saved()

    def load_history_report(self, report: dict):
        source_payload = report.get("source_payload", {}) or {}
        if hasattr(self, "video_list_manager"):
            self.video_list_manager.videos_a = list(source_payload.get("group_a_videos", []) or [])
            self.video_list_manager.videos_b = list(source_payload.get("group_b_videos", []) or [])
            self.video_list_manager._render_ab_list()
        self.show_analysis(
            report.get("result_payload", {}) or {},
            source_payload.get("group_a_label", "A组"),
            source_payload.get("group_b_label", "B组"),
        )
        self._show_status("已载入历史报告", "#6fe0a9")

    def _run_analysis_with_videos(self, video_groups):
        """执行分析（从视频列表管理器调用）"""
        if not isinstance(video_groups, dict):
            return
        
        group_a_videos = video_groups.get("group_a", [])
        group_b_videos = video_groups.get("group_b", [])
        
        if not group_a_videos:
            self._show_status("请至少选择1个A组视频", "#ffb86b")
            return
        if not group_b_videos:
            self._show_status("请至少选择1个B组视频", "#ffb86b")
            return
        
        group_a_label = self._resolve_group_label(group_a_videos, "A组")
        group_b_label = self._resolve_group_label(group_b_videos, "B组")
        
        self._render_loading()
        self._start_worker(
            group_a_videos=group_a_videos,
            group_b_videos=group_b_videos,
            group_a_label=group_a_label,
            group_b_label=group_b_label
        )
    
    def start_analysis(self, group_a_videos, group_b_videos, group_a_label: str = "A组", group_b_label: str = "B组"):
        """开始分析"""
        self._render_loading()
        self._start_worker(
            group_a_videos=group_a_videos,
            group_b_videos=group_b_videos,
            group_a_label=group_a_label,
            group_b_label=group_b_label,
        )
    
    def _start_worker(self, group_a_videos=None, group_b_videos=None, group_a_label: str = "", group_b_label: str = ""):
        """启动工作线程"""
        if self._worker and self._worker.isRunning():
            self._show_status("已有分析任务正在执行，请稍候", "#ffb86b")
            return
        
        self._set_busy(True)
        self._worker = ABComparisonWorker(
            self.main_window.ai_analyzer,
            group_a_videos, group_b_videos,
            group_a_label, group_b_label
        )
        self._worker.finished.connect(self._handle_result)
        self._worker.failed.connect(self._handle_error)
        self._worker.start()
    
    def _handle_result(self, result, payload):
        """处理分析结果"""
        self._set_busy(False)
        if not result:
            self._handle_error("AI 返回为空，请检查模型配置")
            return
        
        from data.database import save_ab_comparison
        
        group_a_videos = payload.get("group_a_videos", [])
        group_b_videos = payload.get("group_b_videos", [])
        group_a_label = payload.get("group_a_label", "A组")
        group_b_label = payload.get("group_b_label", "B组")
        
        group_a_ids = [v["id"] for v in group_a_videos]
        group_b_ids = [v["id"] for v in group_b_videos]
        save_ab_comparison(group_a_ids, group_b_ids, result, group_a_label, group_b_label)
        self._save_report_history(payload, result)
        
        self.show_analysis(result, group_a_label, group_b_label)
        self._show_status("AB对比分析已完成", "#6fe0a9")
    
    def _handle_error(self, error: str):
        """处理分析错误"""
        self._set_busy(False)
        self._show_status(f"分析失败：{error}", "#ff8b8b")
        error_state = EmptyState("分析失败", error or "未知错误")
        self._set_scroll_content([error_state])
    
    def _set_busy(self, busy: bool):
        """设置忙状态"""
        if hasattr(self, 'video_list_manager'):
            self.video_list_manager.analyze_btn.setEnabled(not busy)
        
        if busy:
            self._loading_base = "AB对比分析中"
            self._loading_step = 0
            self._loading_timer.start(380)
            self._tick_loading()
        else:
            self._loading_timer.stop()
    
    def _tick_loading(self):
        """加载动画"""
        dots = "." * (self._loading_step % 4)
        # 这里需要status_badge，但AB页面没有，我们可以跳过或使用其他方式
        self._loading_step += 1
    
    def _show_status(self, text: str, color: str):
        """显示状态 - AB页面可以通过analyze_btn文本显示"""
        # 简化处理：实际可以添加status_badge
        print(f"[AB对比] {text}")
    
    def _render_loading(self):
        """渲染加载状态"""
        panel = EmptyState("正在进行AB对比分析", "正在诊断两组视频在流量、结构和互动上的差异，并整理成“是什么、为什么、怎么做”的报告。")
        note = QLabel("AI 正在生成结构化报告，界面会保持响应，完成后自动展示结果。")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {SUCCESS}; font-size: 13px; padding-top: 12px;")
        panel.layout().addWidget(note)
        self._set_scroll_content([panel])
    
    def _render_empty(self):
        """渲染空状态"""
        self._set_scroll_content(
            [EmptyState(
                "AB对比分析",
                "选择两组视频进行诊断分析，例如高流量组 vs 低流量组、不同选题组或不同内容风格组，找出差异、原因和可执行动作。",
            )]
        )

    def _resolve_group_label(self, videos: list, fallback: str) -> str:
        usernames = []
        for video in videos:
            username = (video or {}).get("influencer_username", "")
            if username and username not in usernames:
                usernames.append(username)

        if len(usernames) == 1:
            return usernames[0]
        return fallback
    
    def show_analysis(self, result: dict, group_a_label: str = "A组", group_b_label: str = "B组"):
        """展示分析结果"""
        self._update_current_report_cache(result, group_a_label, group_b_label)
        widgets = []

        winner = result.get("winner", "")
        diagnosis_summary = result.get("diagnosis_summary", {})
        performance_gap_summary = result.get("performance_gap_summary", {})

        widgets.append(self._build_hero(group_a_label, group_b_label, diagnosis_summary, winner))

        if diagnosis_summary:
            widgets.append(self._build_diagnosis_summary(diagnosis_summary))

        if performance_gap_summary:
            widgets.append(self._build_gap_summary(performance_gap_summary, winner, group_a_label, group_b_label))

        widgets.append(self._build_overview(result, group_a_label, group_b_label, winner))

        key_differences = result.get("key_differences", [])
        if key_differences:
            widgets.append(self._build_key_differences_section(key_differences))

        dimension_comparisons = result.get("dimension_comparisons", [])
        if dimension_comparisons:
            dim_section = self._build_dimension_comparison_section(dimension_comparisons, group_a_label, group_b_label)
            widgets.append(dim_section)

        root_causes = result.get("root_causes", [])
        if root_causes:
            root_causes_widget = self._build_root_causes_section(root_causes)
            widgets.append(root_causes_widget)

        optimization_suggestions = result.get("optimization_suggestions", [])
        if optimization_suggestions:
            suggestions_widget = self._build_optimization_suggestions(optimization_suggestions)
            widgets.append(suggestions_widget)

        start_comparison = result.get("start_comparison", {})
        if start_comparison:
            start_widget = self._build_start_comparison(start_comparison, group_a_label, group_b_label)
            widgets.append(start_widget)

        script_template = result.get("script_template", "")
        if script_template:
            script_widget = self._build_script_template_widget(script_template)
            widgets.append(script_widget)

        self._set_scroll_content(widgets)

    def _winner_badge_text(self, winner: str, group_a_label: str, group_b_label: str) -> str:
        if winner == "A":
            return f"当前整体表现更强: {group_a_label}"
        if winner == "B":
            return f"当前整体表现更强: {group_b_label}"
        return "两组各有优势，建议按维度迁移"

    def _build_hero(self, group_a_label: str, group_b_label: str, diagnosis_summary: dict, winner: str):
        """构建英雄区"""
        frame = QFrame()
        accent_color = "#ffd700" if winner else "#8fa6c9"
        frame.setStyleSheet(card_style(accent_color))
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        title = QLabel("AB对比诊断报告")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 28px; font-weight: 800;")
        layout.addWidget(title)

        subtitle = QLabel(f"{group_a_label} vs {group_b_label}")
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 16px; font-weight: 600;")
        layout.addWidget(subtitle)

        description = QLabel("目标不是简单判断谁赢，而是定位流量差异来自哪里、为什么会这样，以及下一步怎么追。")
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; line-height: 1.75;")
        layout.addWidget(description)

        badge = QLabel(self._winner_badge_text(winner, group_a_label, group_b_label))
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

        what_text = diagnosis_summary.get("what", "")
        if what_text:
            insight = QLabel(what_text)
            insight.setWordWrap(True)
            insight.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 17px; font-weight: 600; line-height: 1.7;")
            layout.addWidget(insight)

        return frame

    def _build_diagnosis_summary(self, diagnosis_summary: dict):
        """构建先看结论区"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("先看结论")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        cards = QWidget()
        cards_layout = QHBoxLayout(cards)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(12)
        cards_layout.addWidget(self._build_simple_info_card("是什么", diagnosis_summary.get("what", ""), "#63a4ff"), 1)
        cards_layout.addWidget(self._build_simple_info_card("为什么", diagnosis_summary.get("why", ""), "#ff8a65"), 1)
        cards_layout.addWidget(self._build_simple_info_card("怎么做", diagnosis_summary.get("how", ""), "#52c58b"), 1)
        layout.addWidget(cards)

        return container

    def _build_gap_summary(self, gap_summary: dict, winner: str, group_a_label: str, group_b_label: str):
        """构建差距摘要区"""
        accent_color = "#ffd700" if winner else "#8fa6c9"
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #162235, stop:1 #101a29);
                border: 1px solid {accent_color}44;
                border-radius: 16px;
            }}
            """
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title = QLabel("差距摘要")
        title.setStyleSheet(f"color: {accent_color}; font-size: 14px; font-weight: 700;")
        layout.addWidget(title)

        core_gap = QLabel(gap_summary.get("core_gap", ""))
        core_gap.setWordWrap(True)
        core_gap.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 17px; font-weight: 600; line-height: 1.7;")
        layout.addWidget(core_gap)

        metric_focus = gap_summary.get("metric_focus", "")
        if metric_focus:
            metric_label = QLabel(f"重点指标: {metric_focus}")
            metric_label.setWordWrap(True)
            metric_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
            layout.addWidget(metric_label)

        recommended_direction = gap_summary.get("recommended_direction", "")
        if recommended_direction:
            direction_label = QLabel(f"建议方向: {recommended_direction}")
            direction_label.setWordWrap(True)
            direction_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; line-height: 1.75;")
            layout.addWidget(direction_label)

        return frame

    def _build_simple_info_card(self, title_text: str, body: str, accent: str):
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {accent}44;
                border-radius: 14px;
            }}
            """
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title = QLabel(title_text)
        title.setStyleSheet(f"color: {accent}; font-size: 14px; font-weight: 700;")
        layout.addWidget(title)

        layout.addWidget(build_structured_content(body, accent, "暂无内容"))
        return frame

    def _build_overview(self, result: dict, group_a_label: str, group_b_label: str, winner: str):
        """构建组别画像区"""
        container = QWidget()
        outer_layout = QVBoxLayout(container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(12)

        title = QLabel("组别画像")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 700;")
        outer_layout.addWidget(title)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        group_a_data = result.get("group_a_overview", {})
        a_border_color = "#52c58b" if winner == "A" else BORDER
        a_card = self._build_group_overview_card(group_a_label, group_a_data, a_border_color, winner == "A")
        layout.addWidget(a_card, 1)

        group_b_data = result.get("group_b_overview", {})
        b_border_color = "#63a4ff" if winner == "B" else BORDER
        b_card = self._build_group_overview_card(group_b_label, group_b_data, b_border_color, winner == "B")
        layout.addWidget(b_card, 1)
        outer_layout.addLayout(layout)

        return container

    def _build_group_overview_card(self, label: str, data: dict, border_color: str, is_winner: bool):
        """构建组概览卡片"""
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

        header = QLabel(label)
        header.setStyleSheet(f"color: {border_color}; font-size: 16px; font-weight: 700;")
        layout.addWidget(header)

        if is_winner:
            winner_label = QLabel("当前整体更强")
            winner_label.setStyleSheet(
                """
                QLabel {
                    background-color: #ffd70022;
                    color: #ffd700;
                    border: 1px solid #ffd70044;
                    border-radius: 8px;
                    padding: 4px 10px;
                    font-size: 12px;
                    font-weight: 700;
                }
                """
            )
            winner_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            layout.addWidget(winner_label)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)
        stats_row.addWidget(self._build_metric_pill("样本", str(data.get("sample_count", "-")), border_color))
        stats_row.addWidget(self._build_metric_pill("平均播放", str(data.get("avg_plays", "-")), border_color))
        stats_row.addWidget(self._build_metric_pill("互动率", str(data.get("avg_engagement_rate", "-")), border_color))
        stats_row.addStretch()
        layout.addLayout(stats_row)

        extra_stats_row = QHBoxLayout()
        extra_stats_row.setSpacing(8)
        extra_stats_row.addWidget(self._build_metric_pill("中位播放", str(data.get("median_plays", "-")), "#8fa6c9"))
        extra_stats_row.addWidget(self._build_metric_pill("最高播放", str(data.get("top_play_count", "-")), "#8fa6c9"))
        extra_stats_row.addStretch()
        layout.addLayout(extra_stats_row)

        hook_type = data.get("hook_type", "")
        if hook_type:
            hook_widget = QLabel(f"主要钩子: {hook_type}")
            hook_widget.setWordWrap(True)
            hook_widget.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
            layout.addWidget(hook_widget)

        content_pattern = data.get("content_pattern", "")
        if content_pattern:
            pattern_widget = QLabel(f"内容模式: {content_pattern}")
            pattern_widget.setWordWrap(True)
            pattern_widget.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.7;")
            layout.addWidget(pattern_widget)

        strengths = self._ensure_text_list(data.get("strengths", []))
        if strengths:
            strengths_label = QLabel("当前有效动作")
            strengths_label.setStyleSheet("color: #52c58b; font-size: 13px; font-weight: 700;")
            layout.addWidget(strengths_label)
            layout.addWidget(build_structured_content("\n".join(f"- {item}" for item in strengths), "#52c58b", "暂无"))

        weaknesses = self._ensure_text_list(data.get("weaknesses", []))
        if weaknesses:
            weaknesses_label = QLabel("当前短板")
            weaknesses_label.setStyleSheet("color: #ff8a65; font-size: 13px; font-weight: 700;")
            layout.addWidget(weaknesses_label)
            layout.addWidget(build_structured_content("\n".join(f"- {item}" for item in weaknesses), "#ff8a65", "暂无"))

        return frame

    def _build_metric_pill(self, title: str, value: str, accent: str):
        label = QLabel(f"{title}: {value}")
        label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {accent}22;
                color: {accent};
                border: 1px solid {accent}44;
                border-radius: 10px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: 700;
            }}
            """
        )
        return label

    def _ensure_text_list(self, value):
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if value:
            return [str(value).strip()]
        return []

    def _build_key_differences_section(self, key_differences: list):
        """构建关键差异区"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("关键差异")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        for item in key_differences[:5]:
            if isinstance(item, dict):
                dimension = item.get("dimension", "关键差异")
                difference = item.get("difference", "")
                impact = item.get("impact", "")
            else:
                dimension = "关键差异"
                difference = str(item)
                impact = ""

            card = QFrame()
            card.setStyleSheet(card_style("#63a4ff"))
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(8)

            header = QLabel(dimension)
            header.setStyleSheet("color: #63a4ff; font-size: 14px; font-weight: 700;")
            card_layout.addWidget(header)
            card_layout.addWidget(build_structured_content(difference, "#63a4ff", "暂无差异说明"))

            if impact:
                impact_label = QLabel(f"影响: {impact}")
                impact_label.setWordWrap(True)
                impact_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.7;")
                card_layout.addWidget(impact_label)

            layout.addWidget(card)

        return container

    def _build_dimension_comparison_section(self, comparisons: list, group_a_label: str, group_b_label: str):
        """构建维度对比区"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("逐维度拆解")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 700;")
        layout.addWidget(title)
        
        for comp in comparisons:
            card = self._build_dimension_card(comp, group_a_label, group_b_label)
            layout.addWidget(card)
        
        return container
    
    def _build_dimension_card(self, comp: dict, group_a_label: str, group_b_label: str):
        """构建维度卡片"""
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
        
        header = QHBoxLayout()
        dim_label = QLabel(dimension)
        dim_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 700;")
        header.addWidget(dim_label)
        header.addStretch()
        
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
        
        if gap_analysis:
            gap_label = QLabel(f"差距分析: {gap_analysis}")
            gap_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; font-style: italic;")
            gap_label.setWordWrap(True)
            layout.addWidget(gap_label)
        
        return frame
    
    def _build_start_comparison(self, start_comparison: dict, group_a_label: str, group_b_label: str):
        """构建 S.T.A.R.T 对比区"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("策略迁移参考")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 700;")
        layout.addWidget(title)
        
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
            
            stage_title = QLabel(f"{letter} · {stage_name}")
            stage_title.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 700;")
            card_layout.addWidget(stage_title)
            
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

        title = QLabel("根本原因分析")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        for idx, cause in enumerate(root_causes[:3], 1):
            if isinstance(cause, dict):
                title_text = cause.get("title", f"原因 {idx}")
                reason = cause.get("reason", "")
                mechanism = cause.get("mechanism", "")
                body = reason
                if mechanism:
                    body = f"{reason}\n\n机制: {mechanism}" if reason else f"机制: {mechanism}"
            else:
                title_text = f"原因 {idx}"
                body = str(cause)

            card = AnalysisCard(title_text, body, "#ff7b65")
            layout.addWidget(card)

        return container

    def _build_optimization_suggestions(self, suggestions: list):
        """构建优化建议区"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("下一步怎么做")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 700;")
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
                target_group = suggestion.get("target_group", "")
                why_this_matters = suggestion.get("why_this_matters", "")
                expected_impact = suggestion.get("expected_impact", "")
                how_to_execute = suggestion.get("how_to_execute", "")
            else:
                content = str(suggestion)
                priority = "中"
                target_group = ""
                why_this_matters = ""
                expected_impact = ""
                how_to_execute = ""

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
            if target_group:
                target_label = QLabel(f"对象: {target_group}")
                target_label.setStyleSheet(
                    f"""
                    QLabel {{
                        color: {TEXT_SECONDARY};
                        font-size: 12px;
                        font-weight: 600;
                    }}
                    """
                )
                header.addWidget(target_label)
            card_layout.addLayout(header)

            card_layout.addWidget(build_structured_content(content, color, "暂无建议内容"))

            if why_this_matters:
                why_label = QLabel(f"为什么做: {why_this_matters}")
                why_label.setWordWrap(True)
                why_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.7;")
                card_layout.addWidget(why_label)

            if how_to_execute:
                how_label = QLabel(f"怎么做: {how_to_execute}")
                how_label.setWordWrap(True)
                how_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.7;")
                card_layout.addWidget(how_label)

            if expected_impact:
                impact_label = QLabel(f"预期效果: {expected_impact}")
                impact_label.setWordWrap(True)
                impact_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
                card_layout.addWidget(impact_label)

            layout.addWidget(card)

        return container
    
    def _build_script_template_widget(self, script_template: str):
        """构建脚本模板组件"""
        container = QFrame()
        container.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-left: 4px solid #ffd700;
                border-radius: 16px;
            }}
            """
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        
        title_label = QLabel("S.T.A.R.T 仿写脚本模板")
        title_label.setStyleSheet("color: #ffd700; font-size: 16px; font-weight: 700;")
        layout.addWidget(title_label)
        
        content_frame = QFrame()
        content_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SURFACE};
                border-left: 3px solid #ffd700;
                border-radius: 8px;
            }}
            """
        )
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(16, 14, 16, 14)
        content_layout.setSpacing(8)
        
        content_layout.addWidget(build_script_template_content(script_template, "#ffd700", "暂无脚本模板"))

        layout.addWidget(content_frame)
        return container
