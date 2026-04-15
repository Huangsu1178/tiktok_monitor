"""
TikTok Monitor - Single Video Analysis Page
单视频分析子页面
"""

from PyQt6.QtCore import QThread, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
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

from core.platforms import platform_label
from ui.components.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_PANEL,
    BG_SURFACE,
    BORDER,
    SUCCESS,
    TEAL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    VIOLET,
    accent_button_style,
    card_style,
    input_style,
    secondary_button_style,
)
from ui.pages.ai_report.ai_report_widgets import (
    MetricChip,
    AnalysisCard,
    EmptyState,
    build_script_template_content,
    build_structured_content,
    format_number,
    get_subject_label,
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
{input_style(220)}
"""


class SingleVideoWorker(QThread):
    """单视频分析工作线程"""
    finished = pyqtSignal(object, object, str)
    failed = pyqtSignal(str)

    def __init__(self, analyzer, video, username: str = ""):
        super().__init__()
        self.analyzer = analyzer
        self.video = video
        self.username = username

    def run(self):
        try:
            result = self.analyzer.analyze_video(self.video, self.username)
            self.finished.emit(result, self.video, self.username)
        except Exception as exc:
            self.failed.emit(str(exc))


class SingleVideoPage(QWidget):
    """单视频分析子页面"""
    
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
        
        # 主滚动区域
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
        
        # 主容器
        main_container = QWidget()
        root = QVBoxLayout(main_container)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)
        
        # 顶部导航栏
        top_bar = self._build_top_bar()
        root.addWidget(top_bar)
        
        # 头部控制区
        header = self._build_header()
        root.addWidget(header)
        
        # 报告展示区
        self.report_scroll = self._create_scroll_container()
        root.addWidget(self.report_scroll, 1)
        
        # 初始显示空状态
        self._render_empty()
        
        main_scroll.setWidget(main_container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_scroll)
    
    def _build_top_bar(self) -> QWidget:
        """构建顶部导航栏"""
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)
        
        # 返回按钮
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
        
        # 标题
        title = QLabel("单视频分析")
        title.setStyleSheet("color: #f4f8ff; font-size: 20px; font-weight: 700;")
        top_bar.addWidget(title)
        
        top_bar.addStretch()
        
        widget = QWidget()
        widget.setLayout(top_bar)
        return widget
    
    def _build_header(self) -> QWidget:
        """构建头部控制区"""
        header = QFrame()
        header.setStyleSheet(
            """
            QFrame {
                background-color: rgba(8, 14, 25, 0.28);
                border: 1px solid #35507e;
                border-radius: 18px;
            }
            """
        )
        controls_layout = QVBoxLayout(header)
        controls_layout.setContentsMargins(18, 18, 18, 18)
        controls_layout.setSpacing(14)
        
        # 视频列表管理器（单视频模式）
        self.video_list_manager = VideoListManager(mode="single")
        self.video_list_manager.videos_changed.connect(self._on_add_videos_requested)
        self.video_list_manager.analyze_requested.connect(self._run_analysis_with_videos)
        controls_layout.addWidget(self.video_list_manager)

        self.status_badge = QLabel("鍑嗗灏辩华")
        self.status_badge.setStyleSheet(
            """
            QLabel {
                background-color: #152136;
                color: #a9c2e8;
                border: 1px solid #2f476b;
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 700;
            }
            """
        )
        controls_layout.addWidget(self.status_badge)
        
        return header
    
    def _on_add_videos_requested(self, data):
        """添加视频请求"""
        # 打开两阶段选择弹窗
        selected_videos = show_two_stage_selection(
            parent=self,
            title="选择要分析的视频",
            allow_multiple=False  # 单视频模式，但弹窗内部可以多选
        )
        
        if selected_videos:
            # 添加到视频列表（单视频模式会自动只保留最后一个）
            self.video_list_manager.add_videos(selected_videos)
    
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
    
    def refresh(self):
        """刷新数据"""
        # 清空视频列表
        if hasattr(self, 'video_list_manager'):
            self.video_list_manager.videos = []
            self.video_list_manager._render_single_list()
        self._show_status("鍑嗗灏辩华", "#a9c2e8")
        self._render_empty()
    
    def _run_analysis_with_videos(self, videos):
        """执行分析（从视频列表管理器调用）"""
        if not videos:
            return
        
        # 单视频模式：只取第一个视频
        video = videos[0] if isinstance(videos, list) else videos
        username = ""
        
        # 从视频中获取博主信息
        if "influencer_username" in video:
            username = video["influencer_username"]
        
        self.start_analysis(video, username)
    
    def start_analysis(self, video: dict, username: str = ""):
        """开始分析"""
        self._render_loading()
        self._start_worker(video=video, username=username)
    
    def _start_worker(self, video=None, username: str = ""):
        """启动工作线程"""
        if self._worker and self._worker.isRunning():
            self._show_status("已有分析任务正在执行，请稍候", "#ffb86b")
            return
        
        self._set_busy(True)
        self._worker = SingleVideoWorker(self.main_window.ai_analyzer, video, username)
        self._worker.finished.connect(self._handle_result)
        self._worker.failed.connect(self._handle_error)
        self._worker.start()
    
    def _handle_result(self, result, video, username: str):
        """处理分析结果"""
        self._set_busy(False)
        if not result:
            self._handle_error("AI 返回为空，请检查模型配置")
            return
        
        from data.database import save_ai_analysis
        save_ai_analysis(video["id"], result)
        self.show_analysis(video, result, username)
        self._show_status("单视频分析已完成", "#6fe0a9")
    
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
            self._loading_base = "单视频分析中"
            self._loading_step = 0
            self._loading_timer.start(380)
            self._tick_loading()
        else:
            self._loading_timer.stop()
    
    def _tick_loading(self):
        """加载动画"""
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
        """显示状态"""
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
    
    def _render_loading(self):
        """渲染加载状态"""
        panel = EmptyState("正在进行单视频分析", "正在拆解开场钩子、内容结构、文案风格和可复用策略，请稍候。")
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
                "单视频分析",
                '选择一个博主和视频后点击"开始单视频分析"，这里会展示拆解后的开场钩子、内容结构、视觉风格和复用建议。',
            )]
        )
    
    def show_analysis(self, video: dict, analysis: dict, username: str = ""):
        """展示分析结果"""
        desc = video.get("description") or video.get("title") or "无描述"
        subject = get_subject_label(username)
        metrics = [
            MetricChip("播放量", format_number(video.get("play_count", 0)), "#ffb86b"),
            MetricChip("点赞数", format_number(video.get("like_count", 0)), "#ff7f96"),
            MetricChip("评论数", format_number(video.get("comment_count", 0)), "#6fe0a9"),
            MetricChip("分享数", format_number(video.get("share_count", 0)), "#84b6ff"),
        ]
        
        hero = self._build_report_hero(
            f"{subject} 的单视频分析",
            desc,
            "单条视频拆解结果",
            "#ff7b65",
            extra_text=f"发布时间：{video.get('published_at') or '未知'}    时长：{video.get('duration') or 0}s",
        )
        metrics_frame = self._wrap_metric_row(metrics)
        
        hook_banner = self._build_hook_banner(analysis)
        start_widget = self._build_start_framework_widget(analysis.get("start_framework", {}))
        benchmark_widget = self._build_benchmark_widget(analysis.get("performance_benchmark", {}))
        
        grid_frame = self._build_analysis_grid(analysis)
        script_widget = self._build_script_template_widget(analysis.get("script_template", ""))
        
        widgets = [hero, metrics_frame, hook_banner]
        if start_widget:
            widgets.append(start_widget)
        if benchmark_widget:
            widgets.append(benchmark_widget)
        widgets.append(grid_frame)
        if script_widget:
            widgets.append(script_widget)
        
        self._set_scroll_content(widgets)
    
    def _build_report_hero(self, title: str, desc: str, badge: str, accent: str, extra_text: str = ""):
        """构建报告英雄区"""
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
        """包装指标行"""
        frame = QWidget()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        for metric in metrics:
            layout.addWidget(metric)
        return frame
    
    def _build_hook_banner(self, analysis: dict):
        """构建钩子横幅"""
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
        hook_layout.addWidget(build_structured_content(analysis.get("hook_description", ""), VIOLET, "暂无钩子描述"))
        
        return hook_banner
    
    def _build_start_framework_widget(self, start_framework: dict):
        """构建 S.T.A.R.T 框架"""
        if not start_framework:
            return None
            
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
        
        title_label = QLabel("S.T.A.R.T 框架拆解")
        title_label.setStyleSheet("color: #f4f8ff; font-size: 16px; font-weight: 700;")
        layout.addWidget(title_label)
        
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
    
    def _build_benchmark_widget(self, benchmark: dict):
        """构建基准对比组件"""
        if not benchmark:
            return None
            
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
        
        title_label = QLabel("爆款达标线对比")
        title_label.setStyleSheet("color: #f4f8ff; font-size: 16px; font-weight: 700;")
        layout.addWidget(title_label)
        
        engagement_rate = benchmark.get("engagement_rate", 0)
        rate_value = QLabel(f"{engagement_rate}%")
        rate_value.setStyleSheet("color: #f4f8ff; font-size: 32px; font-weight: 800;")
        layout.addWidget(rate_value)
        
        is_passed = "达标" in benchmark.get("verdict", "") or "通过" in benchmark.get("verdict", "")
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
        layout.addWidget(status_label)
        
        verdict_text = benchmark.get("verdict", "")
        if verdict_text:
            verdict_label = QLabel(verdict_text)
            verdict_label.setWordWrap(True)
            verdict_label.setStyleSheet("color: #d4e0f3; font-size: 14px; line-height: 1.6;")
            layout.addWidget(verdict_label)
        
        return container
    
    def _build_analysis_grid(self, analysis: dict):
        """构建分析网格"""
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
        
        return grid_frame
    
    def _build_script_template_widget(self, script_template: str):
        """构建脚本模板组件"""
        if not script_template:
            return None
            
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
