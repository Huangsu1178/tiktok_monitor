"""
TikTok Monitor - AI Report Page (Refactored)
AI报告主页面容器 - 管理子页面切换
"""

from PyQt6.QtWidgets import (
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.pages.ai_report.ai_report_home_page import AIReportHomePage
from ui.pages.ai_report.single_video_page import SingleVideoPage
from ui.pages.ai_report.batch_analysis_page import BatchAnalysisPage
from ui.pages.ai_report.ab_comparison_page import ABComparisonPage


class AIReportPage(QWidget):
    """AI报告主页面容器"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # 创建子页面实例
        self.home_page = AIReportHomePage()
        self.single_page = SingleVideoPage(main_window)
        self.batch_page = BatchAnalysisPage(main_window)
        self.ab_page = ABComparisonPage(main_window)
        
        self._build_ui()
        self._connect_signals()
    
    def _build_ui(self):
        """构建UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 使用QStackedWidget管理页面切换
        self.stack = QStackedWidget()
        self.stack.addWidget(self.home_page)       # 索引 0: 主页
        self.stack.addWidget(self.single_page)     # 索引 1: 单视频分析
        self.stack.addWidget(self.batch_page)      # 索引 2: 批量规律分析
        self.stack.addWidget(self.ab_page)         # 索引 3: AB对比分析
        
        layout.addWidget(self.stack)
    
    def _connect_signals(self):
        """连接信号"""
        # 主页模式选择信号
        self.home_page.mode_selected.connect(self._on_mode_selected)
        
        # 子页面返回信号
        self.single_page.back_requested.connect(self._go_home)
        self.batch_page.back_requested.connect(self._go_home)
        self.ab_page.back_requested.connect(self._go_home)
    
    def _on_mode_selected(self, mode: str):
        """切换到对应子页面"""
        mode_map = {
            "single": 1,
            "batch": 2,
            "ab_comparison": 3
        }
        index = mode_map.get(mode, 0)
        self.stack.setCurrentIndex(index)
        
        # 如果是AB对比页面，刷新博主列表
        if mode == "ab_comparison":
            self.ab_page.refresh()
    
    def _go_home(self):
        """返回模式选择主界面"""
        self.stack.setCurrentIndex(0)
    
    def refresh(self):
        """刷新当前可见页面"""
        current_index = self.stack.currentIndex()
        
        if current_index == 0:
            # 主页面无需刷新
            pass
        elif current_index == 1:
            self.single_page.refresh()
        elif current_index == 2:
            self.batch_page.refresh()
        elif current_index == 3:
            self.ab_page.refresh()
    
    def set_external_batch_context(self, videos: list, label: str = ""):
        """设置外部批量上下文（从数据视图跳转）"""
        self.batch_page.set_external_context(videos, label)
        # 自动切换到批量分析页面
        self.stack.setCurrentIndex(2)
    
    def open_single_analysis(self, influencer: dict, video: dict):
        """打开单视频分析（从数据视图跳转）"""
        # 切换到单视频页面
        self.stack.setCurrentIndex(1)
        # 设置当前博主和视频
        self.single_page.refresh()
        self.single_page.video_list_manager.add_videos([video])
        # 刷新视频下拉框
        # 自动开始分析
        username = influencer.get("username", "")
        self.single_page.start_analysis(video, username)
    
    def open_batch_analysis(self, influencer: dict, videos: list, label: str = ""):
        """打开批量分析（从数据视图跳转）"""
        # 使用外部批量上下文
        self.batch_page.set_external_context(videos, label or "当前批量范围")
        # 切换到批量分析页面
        self.stack.setCurrentIndex(2)
        # 自动开始分析
        username = influencer.get("username", "") if influencer else ""
        self.batch_page.start_analysis(videos[:10], username)
