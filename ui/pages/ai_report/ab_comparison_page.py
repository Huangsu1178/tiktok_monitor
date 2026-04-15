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
    BG_PANEL,
    BG_SURFACE,
    BORDER,
    SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    card_style,
    input_style,
)
from ui.pages.ai_report.ai_report_widgets import (
    AnalysisCard,
    EmptyState,
    build_script_template_content,
    build_structured_content,
)
from ui.dialogs.selection_dialog_v2 import show_two_stage_selection
from ui.components.video_list_manager import VideoListManager


PAGE_STYLE = f"""
QWidget {{
    background-color: #0d1522;
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
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._tick_loading)
        self._build_ui()
    
    def _build_ui(self):
        self.setStyleSheet(PAGE_STYLE)
        
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #152136;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #2f476b;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #3d5a80;
            }
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
        title.setStyleSheet("color: #f4f8ff; font-size: 20px; font-weight: 700;")
        top_bar.addWidget(title)
        
        top_bar.addStretch()
        
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
        
        group_a_label = "A组"
        group_b_label = "B组"
        
        # 从视频中获取博主信息
        if group_a_videos and "influencer_username" in group_a_videos[0]:
            group_a_label = group_a_videos[0]["influencer_username"]
        if group_b_videos and "influencer_username" in group_b_videos[0]:
            group_b_label = group_b_videos[0]["influencer_username"]
        
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
        panel = EmptyState("正在进行AB对比分析", "正在对比两组视频的表现差异、分析原因并生成优化建议，请稍候。")
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
                "选择两组视频进行对比分析，找出表现差异的根本原因和优化建议。",
            )]
        )
    
    def show_analysis(self, result: dict, group_a_label: str = "A组", group_b_label: str = "B组"):
        """展示分析结果"""
        widgets = []
        
        winner = result.get("winner", "")
        winner_badge = ""
        if winner == "A":
            winner_badge = f"🏆 {group_a_label} 胜出"
        elif winner == "B":
            winner_badge = f"🏆 {group_b_label} 胜出"
        else:
            winner_badge = "🤝 两组持平"
        
        hero = self._build_hero(group_a_label, group_b_label, winner_badge, winner)
        widgets.append(hero)
        
        overview = self._build_overview(result, group_a_label, group_b_label, winner)
        widgets.append(overview)
        
        winner_reason = result.get("winner_reason", "")
        if winner_reason:
            reason_widget = self._build_winner_reason(winner_reason, winner)
            widgets.append(reason_widget)
        
        dimension_comparisons = result.get("dimension_comparisons", [])
        if dimension_comparisons:
            dim_section = self._build_dimension_comparison_section(dimension_comparisons, group_a_label, group_b_label)
            widgets.append(dim_section)
        
        start_comparison = result.get("start_comparison", {})
        if start_comparison:
            start_widget = self._build_start_comparison(start_comparison, group_a_label, group_b_label)
            widgets.append(start_widget)
        
        root_causes = result.get("root_causes", [])
        if root_causes:
            root_causes_widget = self._build_root_causes_section(root_causes)
            widgets.append(root_causes_widget)
        
        optimization_suggestions = result.get("optimization_suggestions", [])
        if optimization_suggestions:
            suggestions_widget = self._build_optimization_suggestions(optimization_suggestions)
            widgets.append(suggestions_widget)
        
        script_template = result.get("script_template", "")
        if script_template:
            script_widget = self._build_script_template_widget(script_template)
            widgets.append(script_widget)
        
        self._set_scroll_content(widgets)
    
    def _build_hero(self, group_a_label: str, group_b_label: str, winner_badge: str, winner: str):
        """构建英雄区"""
        frame = QFrame()
        accent_color = "#ffd700" if winner else "#8fa6c9"
        frame.setStyleSheet(card_style(accent_color))
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)
        
        title = QLabel("AB对比分析报告")
        title.setStyleSheet("color: #f3f7ff; font-size: 28px; font-weight: 800;")
        layout.addWidget(title)
        
        subtitle = QLabel(f"{group_a_label} vs {group_b_label}")
        subtitle.setStyleSheet("color: #8fa6c9; font-size: 16px; font-weight: 600;")
        layout.addWidget(subtitle)
        
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
    
    def _build_overview(self, result: dict, group_a_label: str, group_b_label: str, winner: str):
        """构建概览区"""
        container = QWidget()
        layout = QHBoxLayout(container)
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
            winner_label = QLabel("🏆 胜出")
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
        
        hook_type = data.get("hook_type", "")
        if hook_type:
            hook_widget = QLabel(f"主要钩子: {hook_type}")
            hook_widget.setStyleSheet("color: #c6d5ea; font-size: 13px;")
            layout.addWidget(hook_widget)
        
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
        """构建维度对比区"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        title = QLabel("逐维度对比分析")
        title.setStyleSheet("color: #f3f7ff; font-size: 16px; font-weight: 700;")
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
        dim_label.setStyleSheet("color: #f3f7ff; font-size: 14px; font-weight: 700;")
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
            gap_label.setStyleSheet("color: #8fa6c9; font-size: 12px; font-style: italic;")
            gap_label.setWordWrap(True)
            layout.addWidget(gap_label)
        
        return frame
    
    def _build_start_comparison(self, start_comparison: dict, group_a_label: str, group_b_label: str):
        """构建 S.T.A.R.T 对比区"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        title = QLabel("S.T.A.R.T 框架对比")
        title.setStyleSheet("color: #f3f7ff; font-size: 16px; font-weight: 700;")
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
            else:
                content = str(suggestion)
                priority = "中"
            
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
            card_layout.addLayout(header)
            
            card_layout.addWidget(build_structured_content(content, color, "暂无建议内容"))
            
            layout.addWidget(card)
        
        return container
    
    def _build_script_template_widget(self, script_template: str):
        """构建脚本模板组件"""
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
        
        title_label = QLabel("S.T.A.R.T 仿写脚本模板")
        title_label.setStyleSheet("color: #ffd700; font-size: 16px; font-weight: 700;")
        layout.addWidget(title_label)
        
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
        
        content_layout.addWidget(build_script_template_content(script_template, "#ffd700", "暂无脚本模板"))

        layout.addWidget(content_frame)
        return container
