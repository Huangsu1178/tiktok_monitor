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
from PyQt6.QtGui import QFont

from config import DEFAULT_AI_MODEL


INPUT_STYLE = """
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #2d3748;
    color: #e2e8f0;
    border: 1px solid #4a5568;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-width: 300px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #e53e3e;
}
"""

GROUP_STYLE = """
QGroupBox {
    color: #a0aec0;
    font-size: 14px;
    font-weight: 600;
    border: 1px solid #2d3748;
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 8px;
    background-color: #1a1a2e;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #a0aec0;
}
"""

SAVE_BTN_STYLE = """
QPushButton {
    background-color: #e53e3e;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #c53030; }
"""

LABEL_STYLE = "color: #e2e8f0; font-size: 13px;"
HINT_STYLE = "color: #718096; font-size: 12px;"


class SettingsPage(QWidget):
    """设置页面"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        self.setStyleSheet("background-color: #0f0f1a;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #0f0f1a; }")

        content = QWidget()
        content.setStyleSheet("background-color: #0f0f1a;")
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # 页面标题
        title = QLabel("⚙️ 系统设置")
        title.setStyleSheet("color: #e2e8f0; font-size: 22px; font-weight: bold;")
        main_layout.addWidget(title)

        # ---- AI配置 ----
        ai_group = QGroupBox("🤖 AI分析配置")
        ai_group.setStyleSheet(GROUP_STYLE)
        ai_form = QFormLayout(ai_group)
        ai_form.setContentsMargins(16, 20, 16, 16)
        ai_form.setSpacing(12)
        ai_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        self.api_key_input.setStyleSheet(INPUT_STYLE)

        api_key_row = QHBoxLayout()
        api_key_row.addWidget(self.api_key_input)
        show_key_btn = QPushButton("👁")
        show_key_btn.setFixedSize(36, 36)
        show_key_btn.setStyleSheet("QPushButton { background-color: #2d3748; color: #e2e8f0; border: none; border-radius: 6px; }")
        show_key_btn.clicked.connect(self._toggle_api_key_visibility)
        api_key_row.addWidget(show_key_btn)

        api_key_label = QLabel("OpenAI API Key")
        api_key_label.setStyleSheet(LABEL_STYLE)
        ai_form.addRow(api_key_label, api_key_row)

        api_hint = QLabel(f"用于AI流量钩子分析功能。支持OpenAI兼容接口，默认使用{DEFAULT_AI_MODEL}模型。")
        api_hint.setStyleSheet(HINT_STYLE)
        api_hint.setWordWrap(True)
        ai_form.addRow("", api_hint)

        # API Base URL
        self.api_base_input = QLineEdit()
        self.api_base_input.setPlaceholderText("例如: https://api.openai.com/v1 （留空使用默认值）")
        self.api_base_input.setStyleSheet(INPUT_STYLE)
        api_base_label = QLabel("API Base URL")
        api_base_label.setStyleSheet(LABEL_STYLE)
        ai_form.addRow(api_base_label, self.api_base_input)

        api_base_hint = QLabel("如果使用第三方API服务（如Azure、本地部署等），请填写对应的API地址。OpenAI官方接口可留空。")
        api_base_hint.setStyleSheet(HINT_STYLE)
        api_base_hint.setWordWrap(True)
        ai_form.addRow("", api_base_hint)

        # 模型名称
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText(DEFAULT_AI_MODEL)
        self.model_input.setStyleSheet(INPUT_STYLE + "QLineEdit { min-width: 200px; }")
        model_label = QLabel("模型名称")
        model_label.setStyleSheet(LABEL_STYLE)
        ai_form.addRow(model_label, self.model_input)

        model_hint = QLabel(f"默认使用{DEFAULT_AI_MODEL}。支持gpt-5-chat-latest等OpenAI兼容模型，或第三方模型名称。")
        model_hint.setStyleSheet(HINT_STYLE)
        model_hint.setWordWrap(True)
        ai_form.addRow("", model_hint)

        main_layout.addWidget(ai_group)

        # ---- 抓取配置 ----
        fetch_group = QGroupBox("🔄 数据抓取配置")
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
        dl_group = QGroupBox("📥 视频下载配置")
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
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: #e2e8f0;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #4a5568; }
        """)
        browse_btn.clicked.connect(self._browse_download_path)
        dl_path_row.addWidget(browse_btn)

        dl_path_label = QLabel("下载保存路径")
        dl_path_label.setStyleSheet(LABEL_STYLE)
        dl_form.addRow(dl_path_label, dl_path_row)

        main_layout.addWidget(dl_group)

        # ---- 网络配置 ----
        net_group = QGroupBox("🌐 网络配置")
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
        save_btn = QPushButton("💾 保存设置")
        save_btn.setStyleSheet(SAVE_BTN_STYLE)
        save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(save_btn)
        main_layout.addLayout(btn_row)

        main_layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _toggle_api_key_visibility(self):
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _browse_download_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择下载目录")
        if path:
            self.download_path_input.setText(path)

    def _load_settings(self):
        """从数据库加载设置"""
        from data.database import get_setting
        self.api_key_input.setText(get_setting("openai_api_key", ""))
        self.api_base_input.setText(get_setting("openai_api_base", ""))
        self.model_input.setText(get_setting("openai_model", DEFAULT_AI_MODEL))
        self.auto_fetch_check.setChecked(get_setting("auto_fetch_enabled", "0") == "1")
        self.interval_spin.setValue(float(get_setting("fetch_interval_hours", "1")))
        self.max_videos_spin.setValue(int(get_setting("max_videos_per_fetch", "20")))
        self.download_path_input.setText(
            get_setting("download_path", os.path.expanduser("~/Downloads/TikTok_Monitor"))
        )
        self.proxy_input.setText(get_setting("proxy_url", ""))

    def _save_settings(self):
        """保存设置到数据库"""
        from data.database import set_setting

        api_key = self.api_key_input.text().strip()
        api_base = self.api_base_input.text().strip()
        model = self.model_input.text().strip() or DEFAULT_AI_MODEL
        
        set_setting("openai_api_key", api_key)
        set_setting("openai_api_base", api_base)
        set_setting("openai_model", model)
        set_setting("auto_fetch_enabled", "1" if self.auto_fetch_check.isChecked() else "0")
        set_setting("fetch_interval_hours", str(self.interval_spin.value()))
        set_setting("max_videos_per_fetch", str(self.max_videos_spin.value()))
        set_setting("download_path", self.download_path_input.text().strip())
        set_setting("proxy_url", self.proxy_input.text().strip())

        # 更新AI分析器的API Key、API地址和模型（使用skill模块的update_config方法）
        if api_key or api_base or model:
            self.main_window.ai_analyzer.update_config(
                api_key=api_key if api_key else self.main_window.ai_analyzer.api_key,
                api_base=api_base,
                model=model
            )

        # 更新调度器
        scheduler = self.main_window.scheduler
        if self.auto_fetch_check.isChecked():
            interval = self.interval_spin.value()
            if not scheduler.is_running():
                scheduler.start()
            scheduler.add_global_fetch_job(self.main_window.fetch_all_active, interval)
            self.main_window.status_label.setText(f"● 自动监控中 ({interval}h)")
            self.main_window.status_label.setStyleSheet("color: #68d391; font-size: 12px; padding: 8px;")
        else:
            scheduler.remove_job("global_fetch")
            self.main_window.status_label.setText("● 就绪（手动模式）")
            self.main_window.status_label.setStyleSheet("color: #a0aec0; font-size: 12px; padding: 8px;")

        QMessageBox.information(self, "保存成功", "设置已保存并生效！")
