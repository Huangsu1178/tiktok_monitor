"""
AI report page container.
"""

from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from ui.pages.ai_report.ab_comparison_page import ABComparisonPage
from ui.pages.ai_report.ai_report_home_page import AIReportHomePage
from ui.pages.ai_report.batch_analysis_page import BatchAnalysisPage
from ui.pages.ai_report.report_history_page import ReportHistoryPage
from ui.pages.ai_report.single_video_page import SingleVideoPage


class AIReportPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.home_page = AIReportHomePage()
        self.single_page = SingleVideoPage(main_window)
        self.batch_page = BatchAnalysisPage(main_window)
        self.ab_page = ABComparisonPage(main_window)
        self.history_page = ReportHistoryPage(main_window)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.single_page)
        self.stack.addWidget(self.batch_page)
        self.stack.addWidget(self.ab_page)
        self.stack.addWidget(self.history_page)
        layout.addWidget(self.stack)

    def _connect_signals(self):
        self.home_page.mode_selected.connect(self._on_mode_selected)

        self.single_page.back_requested.connect(self._go_home)
        self.batch_page.back_requested.connect(self._go_home)
        self.ab_page.back_requested.connect(self._go_home)
        self.history_page.back_requested.connect(self._go_home)
        self.history_page.open_report_requested.connect(self.open_saved_report)

    def _on_mode_selected(self, mode: str):
        mode_map = {
            "single": 1,
            "batch": 2,
            "ab_comparison": 3,
            "history": 4,
        }
        self.stack.setCurrentIndex(mode_map.get(mode, 0))

        if mode == "ab_comparison":
            self.ab_page.refresh()
        elif mode == "history":
            self.history_page.refresh()

    def _go_home(self):
        self.stack.setCurrentIndex(0)

    def refresh(self):
        current_index = self.stack.currentIndex()
        if current_index == 1:
            self.single_page.refresh()
        elif current_index == 2:
            self.batch_page.refresh()
        elif current_index == 3:
            self.ab_page.refresh()
        elif current_index == 4:
            self.history_page.refresh()

    def show_history(self):
        self.history_page.refresh()
        self.stack.setCurrentIndex(4)

    def notify_report_saved(self):
        self.history_page.refresh()

    def set_external_batch_context(self, videos: list, label: str = ""):
        self.batch_page.set_external_context(videos, label)
        self.stack.setCurrentIndex(2)

    def open_single_analysis(self, influencer: dict, video: dict):
        self.stack.setCurrentIndex(1)
        self.single_page.refresh()
        self.single_page.video_list_manager.add_videos([video])
        username = influencer.get("username", "")
        self.single_page.start_analysis(video, username)

    def open_batch_analysis(self, influencer: dict, videos: list, label: str = ""):
        self.batch_page.set_external_context(videos, label or "当前批量范围")
        self.stack.setCurrentIndex(2)
        username = influencer.get("username", "") if influencer else ""
        self.batch_page.start_analysis(videos[:10], username)

    def open_saved_report(self, report_id: int):
        from data.database import get_ai_report

        report = get_ai_report(report_id)
        if not report:
            return

        report_type = report.get("report_type")
        if report_type == "single":
            self.stack.setCurrentIndex(1)
            self.single_page.load_history_report(report)
        elif report_type == "batch":
            self.stack.setCurrentIndex(2)
            self.batch_page.load_history_report(report)
        elif report_type == "ab_comparison":
            self.stack.setCurrentIndex(3)
            self.ab_page.load_history_report(report)
