"""
Main window for the dual-platform monitor.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from config import DEFAULT_AI_MODEL
from ui.ai_report_page import AIReportPage
from ui.dashboard_page import DashboardPage
from ui.data_view_page import DataViewPage
from ui.influencer_page import InfluencerPage
from ui.settings_page import SettingsPage


SIDEBAR_STYLE = """
QWidget#sidebar {
    background-color: #1a1a2e;
    border-right: 1px solid #16213e;
}
"""

NAV_BTN_STYLE = """
QPushButton {
    background-color: transparent;
    color: #a0aec0;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #2d3748;
    color: #e2e8f0;
}
QPushButton:checked {
    background-color: #e53e3e;
    color: white;
}
"""

MAIN_STYLE = """
QMainWindow { background-color: #0f0f1a; }
QWidget#main_content { background-color: #0f0f1a; }
"""


class WorkerSignals(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)


class FetchWorker(QThread):
    def __init__(self, fetch_func, *args, **kwargs):
        super().__init__()
        self.signals = WorkerSignals()
        self.fetch_func = fetch_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fetch_func(*self.args, **self.kwargs)
            self.signals.finished.emit(result if isinstance(result, dict) else {"status": "done"})
        except BaseException as exc:
            self.signals.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Short Video Monitor - TikTok / 抖音")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)
        self._init_core()
        self._build_ui()
        self._start_scheduler()

    def _init_core(self):
        from core.ai_analyzer import AIAnalyzer
        from core.scheduler import MonitorScheduler
        from core.scraper import FetchTask, MultiPlatformScraper
        from data.database import get_setting, init_database
        from skills import initialize_skills

        init_database()

        proxy_url = get_setting("proxy_url", "")
        self.scraper = MultiPlatformScraper(proxy_url=proxy_url, headless=True)
        self.fetch_task = FetchTask(self.scraper)

        api_key = get_setting("openai_api_key", "") or os.environ.get("OPENAI_API_KEY", "")
        api_base = get_setting("openai_api_base", "") or os.environ.get("OPENAI_API_BASE", "")
        model = get_setting("openai_model", DEFAULT_AI_MODEL)
        self.ai_analyzer = AIAnalyzer(api_key=api_key, api_base=api_base, model=model)
        self.skill_registry = initialize_skills(api_key, api_base, model)

        self.scheduler = MonitorScheduler()
        self.scheduler.set_status_callback(self._on_scheduler_status)

    def _build_ui(self):
        self.setStyleSheet(
            MAIN_STYLE
            + """
            QScrollBar:vertical {
                background: #1a1a2e;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #4a5568;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #718096;
            }
            """
        )

        central = QWidget()
        central.setObjectName("main_content")
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background-color: #0f0f1a; }")
        layout.addWidget(self.stack, 1)

        self.dashboard_page = DashboardPage(self)
        self.influencer_page = InfluencerPage(self)
        self.data_view_page = DataViewPage(self)
        self.ai_report_page = AIReportPage(self)
        self.settings_page = SettingsPage(self)

        for page in [
            self.dashboard_page,
            self.influencer_page,
            self.data_view_page,
            self.ai_report_page,
            self.settings_page,
        ]:
            self.stack.addWidget(page)

        self._nav_btns[0].setChecked(True)
        self.stack.setCurrentIndex(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(SIDEBAR_STYLE)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        logo_widget = QWidget()
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(8, 0, 8, 0)
        logo_icon = QLabel("SV")
        logo_icon.setFont(QFont("Arial", 20))
        logo_icon.setStyleSheet("color: #f6ad55; font-weight: bold;")
        logo_layout.addWidget(logo_icon)
        logo_text = QLabel("Short Video\nMonitor")
        logo_text.setStyleSheet("color: #e2e8f0; font-size: 16px; font-weight: bold; line-height: 1.2;")
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        layout.addWidget(logo_widget)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #2d3748; margin: 12px 0;")
        line.setFixedHeight(1)
        layout.addWidget(line)

        nav_items = [
            ("仪表盘", 0),
            ("账号管理", 1),
            ("数据视图", 2),
            ("AI分析报告", 3),
            ("设置", 4),
        ]

        self._nav_btns = []
        for text, idx in nav_items:
            btn = QPushButton(f"  {text}")
            btn.setStyleSheet(NAV_BTN_STYLE)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            layout.addWidget(btn)
            self._nav_btns.append(btn)

        layout.addStretch()
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #68d391; font-size: 12px; padding: 8px;")
        layout.addWidget(self.status_label)

        version_label = QLabel("v2.0 双平台版")
        version_label.setStyleSheet("color: #4a5568; font-size: 11px; padding: 4px 8px;")
        layout.addWidget(version_label)
        return sidebar

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.dashboard_page.refresh()
        elif index == 1:
            self.influencer_page.refresh()
        elif index == 2:
            self.data_view_page.refresh()
        elif index == 3:
            self.ai_report_page.refresh()

    def _start_scheduler(self):
        from data.database import get_setting

        auto_fetch = get_setting("auto_fetch_enabled", "0") == "1"
        if auto_fetch:
            interval = float(get_setting("fetch_interval_hours", "1"))
            self.scheduler.start()
            self.scheduler.add_global_fetch_job(self.fetch_all_active, interval)
            self.status_label.setText(f"自动监控中 ({interval}h)")
            self.status_label.setStyleSheet("color: #68d391; font-size: 12px; padding: 8px;")

    def fetch_all_active(self):
        from data.database import get_active_influencers, get_setting

        influencers = get_active_influencers()
        max_videos = int(get_setting("max_videos_per_fetch", "20"))
        results = []
        for influencer in influencers:
            results.append(self.fetch_task.run(influencer, max_videos))
        self.dashboard_page.refresh()
        return {"status": "done", "results": results}

    def fetch_single(self, influencer: dict):
        from core.platforms import format_account_identity, platform_label
        from data.database import get_setting

        max_videos = int(get_setting("max_videos_per_fetch", "20"))
        account_text = format_account_identity(
            influencer.get("platform"),
            influencer.get("username", ""),
            influencer.get("profile_url", ""),
        )
        self.status_label.setText(f"抓取中: {platform_label(influencer.get('platform'))} {account_text}")
        self.status_label.setStyleSheet("color: #f6ad55; font-size: 12px; padding: 8px;")

        worker = FetchWorker(self.fetch_task.run, influencer, max_videos)
        worker.signals.finished.connect(self._on_fetch_done)
        worker.signals.error.connect(self._on_fetch_error)
        worker.start()
        self._current_worker = worker

    def _on_fetch_done(self, result: dict):
        if result.get("status") == "error":
            self._on_fetch_error(result.get("error", "未知错误"))
            return
        videos_new = result.get("videos_new", 0)
        self.status_label.setText(f"就绪 (新增 {videos_new} 个视频)")
        self.status_label.setStyleSheet("color: #68d391; font-size: 12px; padding: 8px;")
        self.influencer_page.refresh()
        self.data_view_page.refresh()
        self.dashboard_page.refresh()
        self.ai_report_page.refresh()

    def _on_fetch_error(self, error: str):
        self.status_label.setText(f"鎶撳彇鍑洪敊: {error}")
        self.status_label.setText("抓取出错")
        self.status_label.setStyleSheet("color: #fc8181; font-size: 12px; padding: 8px;")
        self.status_label.setText(f"抓取出错: {error}")

    def _on_scheduler_status(self, msg: str):
        self.status_label.setText(msg)

    def update_skills_config(self, api_key: str, api_base: str = "", model: str = ""):
        if hasattr(self, "skill_registry"):
            self.skill_registry.update_all_configs(api_key, api_base, model)
            self.ai_analyzer.update_config(api_key, api_base, model)

    def navigate_to(self, page_index: int):
        self._nav_btns[page_index].setChecked(True)
        self._switch_page(page_index)

    def closeEvent(self, event):
        self.scheduler.stop()
        event.accept()
