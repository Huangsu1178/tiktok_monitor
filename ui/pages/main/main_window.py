"""
Main window for the dual-platform monitor.
"""
import os

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
from ui.pages.ai_report.ai_report_page import AIReportPage
from ui.pages.dashboard.dashboard_page import DashboardPage
from ui.pages.data_view.data_view_page import DataViewPage
from ui.pages.influencer.influencer_page import InfluencerPage
from ui.pages.settings.settings_page import SettingsPage
from ui.components.theme import (
    ACCENT,
    BG_APP,
    BORDER,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    WARNING,
    global_stylesheet,
    nav_button_style,
    sidebar_style,
)


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
        from data.database import init_database
        from skills import initialize_skills

        init_database()
        
        print("[MainWindow] 初始化核心模块...")

        # 从环境变量加载代理配置
        proxy_url = os.environ.get("PROXY_URL", os.environ.get("HTTP_PROXY", ""))
        print(f"[MainWindow] 代理配置: {proxy_url or '未设置'}")
        self.scraper = MultiPlatformScraper(proxy_url=proxy_url, headless=True)
        self.fetch_task = FetchTask(self.scraper)

        # 从环境变量加载 AI 配置
        api_key = os.environ.get("GEMINI_API_KEY", "")
        model = os.environ.get("GEMINI_MODEL", DEFAULT_AI_MODEL)
        
        print(f"[MainWindow] AI配置: api_key={'已设置' if api_key else '未设置'}, model={model}")
        
        self.ai_analyzer = AIAnalyzer(api_key=api_key, api_base="", model=model)
        self.skill_registry = initialize_skills(api_key, "", model)

        # 从环境变量加载调度器配置
        auto_fetch_enabled = os.environ.get("AUTO_FETCH_ENABLED", "0") == "1"
        fetch_interval = float(os.environ.get("FETCH_INTERVAL", "1"))
        
        print(f"[MainWindow] 调度器: auto_fetch={auto_fetch_enabled}, interval={fetch_interval}h")
        
        self.scheduler = MonitorScheduler()
        self.scheduler.set_status_callback(self._on_scheduler_status)

    def _build_ui(self):
        self.setStyleSheet(global_stylesheet())

        central = QWidget()
        central.setObjectName("main_content")
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"QStackedWidget {{ background-color: {BG_APP}; }}")
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
        sidebar.setFixedWidth(232)
        sidebar.setStyleSheet(sidebar_style())

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        logo_widget = QWidget()
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(8, 0, 8, 0)
        logo_icon = QLabel("SV")
        logo_icon.setFont(QFont("Segoe UI", 21, 700))
        logo_icon.setStyleSheet(f"color: {ACCENT}; font-weight: 800; letter-spacing: 1px;")
        logo_layout.addWidget(logo_icon)
        logo_text = QLabel("Short Video\nMonitor")
        logo_text.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 17px; font-weight: 800; line-height: 1.2;")
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        layout.addWidget(logo_widget)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {BORDER}; margin: 12px 0;")
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
            btn.setStyleSheet(nav_button_style())
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            layout.addWidget(btn)
            self._nav_btns.append(btn)

        layout.addStretch()
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(f"color: {SUCCESS}; font-size: 12px; padding: 8px;")
        layout.addWidget(self.status_label)

        version_label = QLabel("v2.0 双平台版")
        version_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding: 4px 8px;")
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
        # 从环境变量读取调度器配置
        auto_fetch = os.environ.get("AUTO_FETCH_ENABLED", "0") == "1"
        if auto_fetch:
            interval = float(os.environ.get("FETCH_INTERVAL", "1"))
            self.scheduler.start()
            self.scheduler.add_global_fetch_job(self.fetch_all_active, interval)
            self.status_label.setText(f"自动监控中 ({interval}h)")
            self.status_label.setStyleSheet(f"color: {SUCCESS}; font-size: 12px; padding: 8px;")

    def fetch_all_active(self):
        from data.database import get_active_influencers

        influencers = get_active_influencers()
        # 从环境变量读取最大视频数配置
        max_videos = int(os.environ.get("MAX_VIDEOS_PER_FETCH", "20"))
        results = []
        for influencer in influencers:
            results.append(self.fetch_task.run(influencer, max_videos))
        self.dashboard_page.refresh()
        return {"status": "done", "results": results}

    def fetch_single(self, influencer: dict):
        from core.platforms import format_account_identity, platform_label

        # 从环境变量读取最大视频数配置
        max_videos = int(os.environ.get("MAX_VIDEOS_PER_FETCH", "20"))
        
        account_text = format_account_identity(
            influencer.get("platform"),
            influencer.get("username", ""),
            influencer.get("profile_url", ""),
        )
        self.status_label.setText(f"抓取中: {platform_label(influencer.get('platform'))} {account_text}")
        self.status_label.setStyleSheet(f"color: {WARNING}; font-size: 12px; padding: 8px;")

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
        self.status_label.setStyleSheet(f"color: {SUCCESS}; font-size: 12px; padding: 8px;")
        self.influencer_page.refresh()
        self.data_view_page.refresh()
        self.dashboard_page.refresh()
        self.ai_report_page.refresh()

    def _on_fetch_error(self, error: str):
        self.status_label.setText(f"抓取出错: {error}")
        self.status_label.setStyleSheet(f"color: {ACCENT}; font-size: 12px; padding: 8px;")

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
