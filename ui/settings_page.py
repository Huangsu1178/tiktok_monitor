"""
TikTok Monitor - Settings Page
设置页面
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QGroupBox, QFormLayout, QFileDialog,
    QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt

from config import DEFAULT_AI_MODEL, sync_config_to_env, AI_CONFIG, SCRAPER_CONFIG, SCHEDULER_CONFIG
from ui.theme import (
    SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    body_text_style,
    group_style,
    input_style,
    page_background_style,
    page_title_style,
    primary_button_style,
    secondary_button_style,
    subtle_text_style,
)


INPUT_STYLE = input_style(300)
GROUP_STYLE = group_style()
SAVE_BTN_STYLE = primary_button_style()
LABEL_STYLE = f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600;"
HINT_STYLE = subtle_text_style()


class SettingsPage(QWidget):
    """设置页面"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        self.setStyleSheet(page_background_style())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        content.setStyleSheet(page_background_style())
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # 页面标题
        title = QLabel("系统设置")
        title.setStyleSheet(page_title_style())
        main_layout.addWidget(title)

        # ---- AI配置 ----
        ai_group = QGroupBox("AI 分析配置")
        ai_group.setStyleSheet(GROUP_STYLE)
        ai_form = QFormLayout(ai_group)
        ai_form.setContentsMargins(16, 20, 16, 16)
        ai_form.setSpacing(12)
        ai_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Gemini API Key
        self.gemini_api_key_input = QLineEdit()
        self.gemini_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_api_key_input.setPlaceholderText("Gemini API Key (推荐)")
        self.gemini_api_key_input.setStyleSheet(INPUT_STYLE)

        gemini_key_row = QHBoxLayout()
        gemini_key_row.addWidget(self.gemini_api_key_input)
        show_gemini_key_btn = QPushButton("显示")
        show_gemini_key_btn.setFixedSize(36, 36)
        show_gemini_key_btn.setStyleSheet(secondary_button_style())
        show_gemini_key_btn.clicked.connect(lambda: self._toggle_password_visibility(self.gemini_api_key_input))
        gemini_key_row.addWidget(show_gemini_key_btn)

        gemini_key_label = QLabel("Gemini API Key")
        gemini_key_label.setStyleSheet(LABEL_STYLE)
        ai_form.addRow(gemini_key_label, gemini_key_row)

        gemini_hint = QLabel("优先使用Gemini AI。从 https://aistudio.google.com/apikey 获取。")
        gemini_hint.setStyleSheet(HINT_STYLE)
        gemini_hint.setWordWrap(True)
        ai_form.addRow("", gemini_hint)

        # Gemini Model
        self.gemini_model_input = QLineEdit()
        self.gemini_model_input.setPlaceholderText("gemini-2.0-flash")
        self.gemini_model_input.setStyleSheet(INPUT_STYLE + "QLineEdit { min-width: 200px; }")
        gemini_model_label = QLabel("Gemini 模型")
        gemini_model_label.setStyleSheet(LABEL_STYLE)
        ai_form.addRow(gemini_model_label, self.gemini_model_input)

        model_hint = QLabel(f"默认使用gemini-2.0-flash。支持gemini-2.0-pro, gemini-1.5-pro等模型。")
        model_hint.setStyleSheet(HINT_STYLE)
        model_hint.setWordWrap(True)
        ai_form.addRow("", model_hint)

        main_layout.addWidget(ai_group)

        # ---- 抓取配置 ----
        fetch_group = QGroupBox("数据抓取配置")
        fetch_group.setStyleSheet(GROUP_STYLE)
        fetch_form = QFormLayout(fetch_group)
        fetch_form.setContentsMargins(16, 20, 16, 16)
        fetch_form.setSpacing(12)
        fetch_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.auto_fetch_check = QCheckBox("启用自动定时抓取")
        self.auto_fetch_check.setStyleSheet("color: #e2e8f0; font-size: 13px;")
        fetch_form.addRow("", self.auto_fetch_check)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.5, 24.0)
        self.interval_spin.setSingleStep(0.5)
        self.interval_spin.setSuffix(" 小时")
        self.interval_spin.setStyleSheet(INPUT_STYLE + "QDoubleSpinBox { min-width: 150px; }")
        interval_label = QLabel("抓取间隔")
        interval_label.setStyleSheet(LABEL_STYLE)
        fetch_form.addRow(interval_label, self.interval_spin)

        self.max_videos_spin = QSpinBox()
        self.max_videos_spin.setRange(5, 100)
        self.max_videos_spin.setSingleStep(5)
        self.max_videos_spin.setSuffix(" 个")
        self.max_videos_spin.setStyleSheet(INPUT_STYLE + "QSpinBox { min-width: 150px; }")
        max_videos_label = QLabel("每次最多抓取")
        max_videos_label.setStyleSheet(LABEL_STYLE)
        fetch_form.addRow(max_videos_label, self.max_videos_spin)

        main_layout.addWidget(fetch_group)

        # ---- 下载配置 ----
        dl_group = QGroupBox("视频下载配置")
        dl_group.setStyleSheet(GROUP_STYLE)
        dl_form = QFormLayout(dl_group)
        dl_form.setContentsMargins(16, 20, 16, 16)
        dl_form.setSpacing(12)
        dl_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        dl_path_row = QHBoxLayout()
        self.download_path_input = QLineEdit()
        self.download_path_input.setStyleSheet(INPUT_STYLE)
        dl_path_row.addWidget(self.download_path_input)

        browse_btn = QPushButton("浏览...")
        browse_btn.setStyleSheet(secondary_button_style())
        browse_btn.clicked.connect(self._browse_download_path)
        dl_path_row.addWidget(browse_btn)

        dl_path_label = QLabel("下载保存路径")
        dl_path_label.setStyleSheet(LABEL_STYLE)
        dl_form.addRow(dl_path_label, dl_path_row)

        main_layout.addWidget(dl_group)

        # ---- 网络配置 ----
        net_group = QGroupBox("网络配置")
        net_group.setStyleSheet(GROUP_STYLE)
        net_form = QFormLayout(net_group)
        net_form.setContentsMargins(16, 20, 16, 16)
        net_form.setSpacing(12)
        net_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("例如: http://127.0.0.1:7890 （留空则不使用代理）")
        self.proxy_input.setStyleSheet(INPUT_STYLE)
        proxy_label = QLabel("代理服务器")
        proxy_label.setStyleSheet(LABEL_STYLE)
        net_form.addRow(proxy_label, self.proxy_input)

        proxy_hint = QLabel("建议配置代理以提高TikTok数据抓取的稳定性。支持HTTP/HTTPS/SOCKS5代理。")
        proxy_hint.setStyleSheet(HINT_STYLE)
        proxy_hint.setWordWrap(True)
        net_form.addRow("", proxy_hint)

        main_layout.addWidget(net_group)

        # 保存按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("保存设置")
        save_btn.setStyleSheet(SAVE_BTN_STYLE)
        save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(save_btn)
        main_layout.addLayout(btn_row)

        main_layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _toggle_password_visibility(self, input_widget):
        if input_widget.echoMode() == QLineEdit.EchoMode.Password:
            input_widget.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            input_widget.setEchoMode(QLineEdit.EchoMode.Password)

    def _browse_download_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择下载目录")
        if path:
            self.download_path_input.setText(path)

    def _load_settings(self):
        """从环境变量加载设置"""
        # Gemini 配置
        gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
        self.gemini_api_key_input.setText(gemini_api_key)
        print(f"[Settings] 加载 Gemini API Key: {'已设置' if gemini_api_key else '未设置'}")
        
        gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        self.gemini_model_input.setText(gemini_model)
        print(f"[Settings] 加载 Gemini Model: {gemini_model}")
        
        # 加载自动抓取设置
        auto_fetch = os.environ.get("AUTO_FETCH_ENABLED", "0") == "1"
        self.auto_fetch_check.setChecked(auto_fetch)
        print(f"[Settings] 加载自动抓取: {auto_fetch}")
        
        # 加载抓取间隔
        interval = float(os.environ.get("FETCH_INTERVAL", "1"))
        self.interval_spin.setValue(interval)
        print(f"[Settings] 加载抓取间隔: {interval}h")
        
        # 加载最大视频数
        max_videos = int(os.environ.get("MAX_VIDEOS_PER_FETCH", "20"))
        self.max_videos_spin.setValue(max_videos)
        print(f"[Settings] 加载最大视频数: {max_videos}")
        
        # 加载下载路径
        download_path = os.environ.get("DOWNLOAD_PATH", os.path.expanduser("~/Downloads/TikTok_Monitor"))
        self.download_path_input.setText(download_path)
        print(f"[Settings] 加载下载路径: {download_path}")
        
        # 加载代理设置
        proxy = os.environ.get("PROXY_URL", os.environ.get("HTTP_PROXY", ""))
        self.proxy_input.setText(proxy)
        print(f"[Settings] 加载代理: {proxy or '未设置'}")

    def _save_settings(self):
        """保存设置到 .env 文件"""
        # Gemini 配置
        gemini_api_key = self.gemini_api_key_input.text().strip()
        gemini_model = self.gemini_model_input.text().strip() or "gemini-2.0-flash"
        
        auto_fetch = self.auto_fetch_check.isChecked()
        interval = self.interval_spin.value()
        max_videos = self.max_videos_spin.value()
        download_path = self.download_path_input.text().strip()
        proxy_url = self.proxy_input.text().strip()
        
        # 同步到 .env 文件和内存配置
        sync_config_to_env('AI_CONFIG', 'gemini_api_key', gemini_api_key)
        sync_config_to_env('AI_CONFIG', 'gemini_model', gemini_model)
        sync_config_to_env('SCHEDULER_CONFIG', 'auto_fetch_enabled', auto_fetch)
        sync_config_to_env('SCHEDULER_CONFIG', 'fetch_interval_hours', interval)
        sync_config_to_env('SCRAPER_CONFIG', 'max_videos_per_fetch', max_videos)
        sync_config_to_env('SCRAPER_CONFIG', 'download_path', download_path)
        sync_config_to_env('SCRAPER_CONFIG', 'proxy_url', proxy_url)
        
        # 更新内存中的配置
        AI_CONFIG['gemini_api_key'] = gemini_api_key
        AI_CONFIG['gemini_model'] = gemini_model
        SCHEDULER_CONFIG['auto_fetch_enabled'] = auto_fetch
        SCHEDULER_CONFIG['fetch_interval_hours'] = interval
        SCRAPER_CONFIG['max_videos_per_fetch'] = max_videos
        if download_path:
            SCRAPER_CONFIG['download_path'] = download_path
        SCRAPER_CONFIG['proxy_url'] = proxy_url

        # 更新AI分析器的API Key和模型（使用skill模块的update_config方法）
        if gemini_api_key or gemini_model:
            self.main_window.ai_analyzer.update_config(
                api_key=gemini_api_key if gemini_api_key else self.main_window.ai_analyzer.gemini_api_key,
                api_base="",
                model=gemini_model
            )

        # 更新调度器
        scheduler = self.main_window.scheduler
        if self.auto_fetch_check.isChecked():
            interval = self.interval_spin.value()
            if not scheduler.is_running():
                scheduler.start()
            scheduler.add_global_fetch_job(self.main_window.fetch_all_active, interval)
            self.main_window.status_label.setText(f"● 自动监控中 ({interval}h)")
            self.main_window.status_label.setStyleSheet(f"color: {SUCCESS}; font-size: 12px; padding: 8px;")
        else:
            scheduler.remove_job("global_fetch")
            self.main_window.status_label.setText("● 就绪（手动模式）")
            self.main_window.status_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; padding: 8px;")

        QMessageBox.information(self, "保存成功", "设置已保存并生效！")
