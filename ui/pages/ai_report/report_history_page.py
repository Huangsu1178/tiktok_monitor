"""
AI report history page.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from data.database import get_ai_report, get_ai_reports
from ui.components.theme import (
    BG_APP,
    BG_PANEL,
    BG_SURFACE,
    BORDER,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    accent_button_style,
    secondary_button_style,
)
from ui.pages.ai_report.ai_report_widgets import EmptyState
from ui.pages.ai_report.report_utils import (
    report_type_accent,
    report_type_label,
    save_report_markdown,
)


PAGE_STYLE = f"""
QWidget {{
    background-color: {BG_APP};
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
"""


class ReportHistoryPage(QWidget):
    back_requested = pyqtSignal()
    open_report_requested = pyqtSignal(int)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(PAGE_STYLE)

        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        root.addWidget(self._build_top_bar())

        intro = QLabel("这里会保存单视频、批量规律和 AB 对比的历史报告，支持重新查看和导出 Markdown。")
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.75;")
        root.addWidget(intro)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(14)
        root.addWidget(self.list_container, 1)

        main_scroll.setWidget(container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_scroll)

        self.refresh()

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        back_btn = QPushButton("返回")
        back_btn.setStyleSheet(secondary_button_style())
        back_btn.clicked.connect(self.back_requested.emit)
        layout.addWidget(back_btn)

        title = QLabel("历史报告")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 22px; font-weight: 800;")
        layout.addWidget(title)

        layout.addStretch()

        refresh_btn = QPushButton("刷新列表")
        refresh_btn.setStyleSheet(accent_button_style())
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)

        return bar

    def _clear_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def refresh(self):
        self._clear_list()
        reports = get_ai_reports(limit=100)
        if not reports:
            self.list_layout.addWidget(EmptyState("暂无历史报告", "完成一次 AI 分析后，报告会自动保存到这里。"))
            self.list_layout.addStretch()
            return

        for report in reports:
            self.list_layout.addWidget(self._build_report_card(report))
        self.list_layout.addStretch()

    def _build_report_card(self, report: dict) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
            """
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        type_badge = QLabel(report_type_label(report.get("report_type", "")))
        accent = report_type_accent(report.get("report_type", ""))
        type_badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {accent}22;
                color: {accent};
                border: 1px solid {accent}55;
                border-radius: 10px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: 700;
            }}
            """
        )
        top_row.addWidget(type_badge, 0, Qt.AlignmentFlag.AlignLeft)

        created_at = QLabel(report.get("created_at", ""))
        created_at.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        top_row.addWidget(created_at)
        top_row.addStretch()
        layout.addLayout(top_row)

        title = QLabel(report.get("title", "AI 分析报告"))
        title.setWordWrap(True)
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 17px; font-weight: 700;")
        layout.addWidget(title)

        subject = report.get("subject_label", "")
        if subject:
            subject_label = QLabel(subject)
            subject_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
            layout.addWidget(subject_label)

        summary = QLabel(report.get("summary", "") or "暂无摘要")
        summary.setWordWrap(True)
        summary.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.75;")
        layout.addWidget(summary)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        open_btn = QPushButton("查看报告")
        open_btn.setStyleSheet(accent_button_style())
        open_btn.clicked.connect(lambda: self.open_report_requested.emit(int(report["id"])))
        button_row.addWidget(open_btn)

        export_btn = QPushButton("导出 Markdown")
        export_btn.setStyleSheet(secondary_button_style())
        export_btn.clicked.connect(lambda: self._export_report(int(report["id"])))
        button_row.addWidget(export_btn)

        button_row.addStretch()
        layout.addLayout(button_row)
        return frame

    def _export_report(self, report_id: int):
        report = get_ai_report(report_id)
        if not report:
            return
        save_report_markdown(self, report.get("title", "AI 分析报告"), report.get("export_markdown", ""))
