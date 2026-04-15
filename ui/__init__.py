"""
TikTok Monitor UI Package

向后兼容的导入 - 将所有页面和组件重导出到旧路径
"""

# 页面导入（向后兼容）
from ui.pages.main.main_window import MainWindow
from ui.pages.dashboard.dashboard_page import DashboardPage
from ui.pages.influencer.influencer_page import InfluencerPage
from ui.pages.data_view.data_view_page import DataViewPage
from ui.pages.settings.settings_page import SettingsPage
from ui.pages.ai_report.ai_report_page import AIReportPage
from ui.pages.ai_report.ai_report_home_page import AIReportHomePage
from ui.pages.ai_report.single_video_page import SingleVideoPage
from ui.pages.ai_report.batch_analysis_page import BatchAnalysisPage
from ui.pages.ai_report.ab_comparison_page import ABComparisonPage
from ui.pages.ai_report.ai_report_widgets import MetricChip, AnalysisCard, EmptyState, format_number, get_subject_label

# 组件导入（向后兼容）
from ui.components.theme import *
from ui.components.video_list_manager import VideoListManager

# 对话框导入（向后兼容）
from ui.dialogs.selection_dialog import InfluencerSelectionStep, SelectionDialog
from ui.dialogs.selection_dialog_v2 import TwoStageSelectionDialog, show_two_stage_selection
