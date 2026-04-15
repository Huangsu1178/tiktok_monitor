"""
TikTok Monitor - Video List Manager
待分析视频列表管理组件
支持添加、删除、显示视频列表
"""

from PyQt6.QtCore import Qt, pyqtSignal
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
from .theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_PANEL,
    BG_SURFACE,
    BG_SURFACE_HOVER,
    BORDER,
    DANGER,
    DANGER_HOVER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    accent_button_style,
    card_style,
    secondary_button_style,
)


class VideoListItem(QWidget):
    """单个视频列表项"""
    
    remove_clicked = pyqtSignal(object)  # 发送要删除的视频数据
    
    def __init__(self, video_data, parent=None):
        super().__init__(parent)
        self.video_data = video_data
        self._build_ui()
    
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # 博主信息
        username = self.video_data.get("influencer_username", "")
        platform = platform_label(self.video_data.get("influencer_platform", ""))
        influencer_label = QLabel(f"{platform} @{username}")
        influencer_label.setStyleSheet(f"color: {ACCENT}; font-size: 12px; font-weight: 600; min-width: 120px;")
        layout.addWidget(influencer_label)
        
        # 视频描述
        desc = (self.video_data.get("description") or self.video_data.get("title") or "无描述").replace("\n", " ")
        desc_label = QLabel(desc[:60] + ("..." if len(desc) > 60 else ""))
        desc_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px;")
        desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(desc_label, 1)
        
        # 播放量
        play_count = self.video_data.get("play_count", 0)
        play_label = QLabel(f"▶ {play_count:,}")
        play_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(play_label)
        
        # 删除按钮
        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {DANGER};
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {DANGER_HOVER};
                color: white;
            }}
        """)
        remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self.video_data))
        layout.addWidget(remove_btn)


class VideoListManager(QWidget):
    """视频列表管理器"""
    
    # 信号
    videos_changed = pyqtSignal(object)  # 视频列表改变
    analyze_requested = pyqtSignal(object)  # 请求分析
    
    def __init__(self, parent=None, mode="single"):
        """
        初始化
        
        Args:
            mode: 模式 - "single"(单视频), "batch"(批量), "ab_comparison"(AB对比)
        """
        super().__init__(parent)
        self.mode = mode
        self.videos = []  # 待分析视频列表
        
        if mode == "ab_comparison":
            self.videos_a = []  # A组视频
            self.videos_b = []  # B组视频
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        if self.mode == "ab_comparison":
            # AB对比模式：两个列表
            self._build_ab_mode(layout)
        else:
            # 单视频/批量模式：单个列表
            self._build_single_list_mode(layout)
    
    def _build_single_list_mode(self, parent_layout):
        """构建单列表模式（单视频/批量）"""
        # 标题栏
        header = QHBoxLayout()
        
        title = QLabel("待分析视频")
        title.setStyleSheet("color: #f4f8ff; font-size: 15px; font-weight: 700;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.count_label = QLabel("0 个视频")
        self.count_label.setStyleSheet("color: #8fa6c9; font-size: 13px;")
        header.addWidget(self.count_label)
        
        parent_layout.addLayout(header)
        
        # 视频列表容器
        self.list_container = QFrame()
        self.list_container.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        list_layout = QVBoxLayout(self.list_container)
        list_layout.setContentsMargins(8, 8, 8, 8)
        list_layout.setSpacing(6)
        
        # 滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(6)
        
        # 空状态提示
        self.empty_label = QLabel('点击"添加视频"按钮添加待分析视频')
        self.empty_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; padding: 20px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_layout.addWidget(self.empty_label)
        
        self.scroll.setWidget(self.scroll_content)
        list_layout.addWidget(self.scroll)
        
        parent_layout.addWidget(self.list_container)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        add_btn = QPushButton("➕ 添加视频")
        add_btn.setStyleSheet(accent_button_style())
        add_btn.clicked.connect(self._on_add_clicked)
        button_layout.addWidget(add_btn)
        
        if self.mode == "batch":
            clear_btn = QPushButton("🗑️ 清空列表")
            clear_btn.setStyleSheet(secondary_button_style())
            clear_btn.clicked.connect(self._on_clear_clicked)
            button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        analyze_btn = QPushButton("🚀 开始分析")
        analyze_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #52c58b;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #45b07a;
            }}
            QPushButton:disabled {{
                background-color: {BG_SURFACE};
                color: {TEXT_SECONDARY};
            }}
        """)
        analyze_btn.clicked.connect(self._on_analyze_clicked)
        analyze_btn.setEnabled(False)
        self.analyze_btn = analyze_btn
        button_layout.addWidget(analyze_btn)
        
        parent_layout.addLayout(button_layout)
    
    def _build_ab_mode(self, parent_layout):
        """构建AB对比模式"""
        # A组
        a_header = QHBoxLayout()
        a_title = QLabel("A组视频")
        a_title.setStyleSheet("color: #52c58b; font-size: 15px; font-weight: 700;")
        a_header.addWidget(a_title)
        a_header.addStretch()
        self.a_count_label = QLabel("0 个视频")
        self.a_count_label.setStyleSheet("color: #8fa6c9; font-size: 13px;")
        a_header.addWidget(self.a_count_label)
        parent_layout.addLayout(a_header)
        
        # A组列表
        self.a_list_container = QFrame()
        self.a_list_container.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-left: 3px solid #52c58b;
                border-radius: 12px;
            }}
        """)
        a_list_layout = QVBoxLayout(self.a_list_container)
        a_list_layout.setContentsMargins(8, 8, 8, 8)
        a_list_layout.setSpacing(6)
        
        self.a_scroll = QScrollArea()
        self.a_scroll.setWidgetResizable(True)
        self.a_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.a_scroll_content = QWidget()
        self.a_scroll_layout = QVBoxLayout(self.a_scroll_content)
        self.a_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.a_scroll_layout.setSpacing(6)
        
        self.a_empty_label = QLabel('点击"添加A组视频"按钮添加视频')
        self.a_empty_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; padding: 20px;")
        self.a_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.a_scroll_layout.addWidget(self.a_empty_label)
        
        self.a_scroll.setWidget(self.a_scroll_content)
        a_list_layout.addWidget(self.a_scroll)
        parent_layout.addWidget(self.a_list_container)
        
        # A组按钮
        a_button_layout = QHBoxLayout()
        a_button_layout.setSpacing(12)
        
        a_add_btn = QPushButton("➕ 添加A组视频")
        a_add_btn.setStyleSheet(accent_button_style())
        a_add_btn.clicked.connect(lambda: self._on_add_clicked("A"))
        a_button_layout.addWidget(a_add_btn)
        
        a_clear_btn = QPushButton("🗑️ 清空A组")
        a_clear_btn.setStyleSheet(secondary_button_style())
        a_clear_btn.clicked.connect(lambda: self._on_clear_clicked("A"))
        a_button_layout.addWidget(a_clear_btn)
        
        parent_layout.addLayout(a_button_layout)
        
        # VS分隔符
        vs_label = QLabel("⚔️ VS")
        vs_label.setStyleSheet("color: #f4f8ff; font-size: 20px; font-weight: 700; padding: 10px 0;")
        vs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        parent_layout.addWidget(vs_label)
        
        # B组
        b_header = QHBoxLayout()
        b_title = QLabel("B组视频")
        b_title.setStyleSheet("color: #63a4ff; font-size: 15px; font-weight: 700;")
        b_header.addWidget(b_title)
        b_header.addStretch()
        self.b_count_label = QLabel("0 个视频")
        self.b_count_label.setStyleSheet("color: #8fa6c9; font-size: 13px;")
        b_header.addWidget(self.b_count_label)
        parent_layout.addLayout(b_header)
        
        # B组列表
        self.b_list_container = QFrame()
        self.b_list_container.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-left: 3px solid #63a4ff;
                border-radius: 12px;
            }}
        """)
        b_list_layout = QVBoxLayout(self.b_list_container)
        b_list_layout.setContentsMargins(8, 8, 8, 8)
        b_list_layout.setSpacing(6)
        
        self.b_scroll = QScrollArea()
        self.b_scroll.setWidgetResizable(True)
        self.b_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.b_scroll_content = QWidget()
        self.b_scroll_layout = QVBoxLayout(self.b_scroll_content)
        self.b_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.b_scroll_layout.setSpacing(6)
        
        self.b_empty_label = QLabel('点击"添加B组视频"按钮添加视频')
        self.b_empty_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; padding: 20px;")
        self.b_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.b_scroll_layout.addWidget(self.b_empty_label)
        
        self.b_scroll.setWidget(self.b_scroll_content)
        b_list_layout.addWidget(self.b_scroll)
        parent_layout.addWidget(self.b_list_container)
        
        # B组按钮
        b_button_layout = QHBoxLayout()
        b_button_layout.setSpacing(12)
        
        b_add_btn = QPushButton("➕ 添加B组视频")
        b_add_btn.setStyleSheet(accent_button_style())
        b_add_btn.clicked.connect(lambda: self._on_add_clicked("B"))
        b_button_layout.addWidget(b_add_btn)
        
        b_clear_btn = QPushButton("🗑️ 清空B组")
        b_clear_btn.setStyleSheet(secondary_button_style())
        b_clear_btn.clicked.connect(lambda: self._on_clear_clicked("B"))
        b_button_layout.addWidget(b_clear_btn)
        
        parent_layout.addLayout(b_button_layout)
        
        # 分析按钮
        analyze_btn = QPushButton("🚀 开始对比分析")
        analyze_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #52c58b;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #45b07a;
            }}
            QPushButton:disabled {{
                background-color: {BG_SURFACE};
                color: {TEXT_SECONDARY};
            }}
        """)
        analyze_btn.clicked.connect(self._on_analyze_clicked)
        analyze_btn.setEnabled(False)
        self.analyze_btn = analyze_btn
        parent_layout.addWidget(analyze_btn)
    
    def _on_add_clicked(self, group=None):
        """添加按钮点击"""
        # 这个信号会被外部页面捕获并打开选择弹窗
        # 发送组别信息
        self.videos_changed.emit({"group": group})
    
    def _on_clear_clicked(self, group=None):
        """清空按钮点击"""
        if group == "A":
            self.videos_a = []
            self._render_ab_list()
        elif group == "B":
            self.videos_b = []
            self._render_ab_list()
        else:
            self.videos = []
            self._render_single_list()
    
    def _on_analyze_clicked(self):
        """分析按钮点击"""
        if self.mode == "ab_comparison":
            self.analyze_requested.emit({
                "group_a": self.videos_a[:],
                "group_b": self.videos_b[:]
            })
        else:
            self.analyze_requested.emit(self.videos[:])
    
    def add_videos(self, videos, group=None):
        """
        添加视频到列表
        
        Args:
            videos: 视频数据列表
            group: 组别（仅AB模式使用，"A"或"B"）
        """
        if self.mode == "ab_comparison":
            if group == "A":
                # 去重
                existing_ids = {v.get("id") for v in self.videos_a}
                new_videos = [v for v in videos if v.get("id") not in existing_ids]
                self.videos_a.extend(new_videos)
                self._render_ab_list()
            elif group == "B":
                existing_ids = {v.get("id") for v in self.videos_b}
                new_videos = [v for v in videos if v.get("id") not in existing_ids]
                self.videos_b.extend(new_videos)
                self._render_ab_list()
        else:
            if self.mode == "single":
                # 单视频模式：只保留最后一个
                self.videos = videos[-1:] if videos else []
            else:
                # 批量模式：追加并去重
                existing_ids = {v.get("id") for v in self.videos}
                new_videos = [v for v in videos if v.get("id") not in existing_ids]
                self.videos.extend(new_videos)
            
            self._render_single_list()
    
    def remove_video(self, video, group=None):
        """删除视频"""
        if self.mode == "ab_comparison":
            if group == "A":
                self.videos_a = [v for v in self.videos_a if v.get("id") != video.get("id")]
                self._render_ab_list()
            elif group == "B":
                self.videos_b = [v for v in self.videos_b if v.get("id") != video.get("id")]
                self._render_ab_list()
        else:
            self.videos = [v for v in self.videos if v.get("id") != video.get("id")]
            self._render_single_list()
    
    def _clear_list_layout(self, layout, placeholder=None):
        """清空列表布局，但保留空状态控件供后续复用"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if not widget:
                continue
            if widget is placeholder:
                widget.hide()
                continue
            widget.deleteLater()

    def _render_single_list(self):
        """渲染单列表"""
        # 清空现有项，但保留空状态提示
        self._clear_list_layout(self.scroll_layout, self.empty_label)
        
        if not self.videos:
            # 显示空状态
            self.scroll_layout.addWidget(self.empty_label)
            self.empty_label.show()
            self.count_label.setText("0 个视频")
            self.analyze_btn.setEnabled(False)
            return
        
        self.empty_label.hide()
        
        # 添加视频项
        for video in self.videos:
            item = VideoListItem(video)
            item.remove_clicked.connect(self.remove_video)
            self.scroll_layout.addWidget(item)
        
        self.count_label.setText(f"{len(self.videos)} 个视频")
        self.analyze_btn.setEnabled(True)
    
    def _render_ab_list(self):
        """渲染AB列表"""
        # A组
        self._clear_list_layout(self.a_scroll_layout, self.a_empty_label)
        
        if not self.videos_a:
            self.a_scroll_layout.addWidget(self.a_empty_label)
            self.a_empty_label.show()
            self.a_count_label.setText("0 个视频")
        else:
            self.a_empty_label.hide()
            for video in self.videos_a:
                item = VideoListItem(video)
                item.remove_clicked.connect(lambda v=video: self.remove_video(v, "A"))
                self.a_scroll_layout.addWidget(item)
            self.a_count_label.setText(f"{len(self.videos_a)} 个视频")
        
        # B组
        self._clear_list_layout(self.b_scroll_layout, self.b_empty_label)
        
        if not self.videos_b:
            self.b_scroll_layout.addWidget(self.b_empty_label)
            self.b_empty_label.show()
            self.b_count_label.setText("0 个视频")
        else:
            self.b_empty_label.hide()
            for video in self.videos_b:
                item = VideoListItem(video)
                item.remove_clicked.connect(lambda v=video: self.remove_video(v, "B"))
                self.b_scroll_layout.addWidget(item)
            self.b_count_label.setText(f"{len(self.videos_b)} 个视频")
        
        # 更新分析按钮状态
        self.analyze_btn.setEnabled(len(self.videos_a) > 0 and len(self.videos_b) > 0)
