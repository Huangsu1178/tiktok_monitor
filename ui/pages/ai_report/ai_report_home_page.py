"""
AI report mode selection home page.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui.components.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_APP,
    BG_PANEL,
    BG_SURFACE,
    BG_SURFACE_HOVER,
    BORDER,
    BORDER_STRONG,
    TEAL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    VIOLET,
)


PAGE_STYLE = f"""
QWidget {{
    background-color: {BG_APP};
}}
"""


class ModeCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, icon: str, title: str, description: str, mode: str, accent_color: str):
        super().__init__()
        self.mode = mode
        self.accent_color = accent_color
        self._build_ui(icon, title, description)

    def _build_ui(self, icon: str, title: str, description: str):
        self.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {BG_PANEL}, stop:1 {BG_SURFACE});
                border: 1px solid {BORDER};
                border-left: 4px solid {self.accent_color};
                border-radius: 16px;
            }}
            QFrame:hover {{
                background: {BG_SURFACE_HOVER};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"font-size: 42px; color: {self.accent_color};")
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: 700;")
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.7;")
        layout.addWidget(desc_label)

        btn = QPushButton("进入")
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.accent_color};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER if self.accent_color == ACCENT else self.accent_color + 'dd'};
            }}
            """
        )
        btn.clicked.connect(lambda: self.clicked.emit(self.mode))
        layout.addWidget(btn)


class AIReportHomePage(QWidget):
    mode_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_mode_cards(), 1)

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {BG_PANEL}, stop:0.45 {BG_SURFACE}, stop:1 {BG_SURFACE_HOVER});
                border: 1px solid {BORDER_STRONG};
                border-radius: 24px;
            }}
            """
        )

        layout = QVBoxLayout(header)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        title = QLabel("AI 分析报告中心")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 32px; font-weight: 800;")
        layout.addWidget(title)

        subtitle = QLabel("选择一种分析模式，生成可下载、可回看的结构化报告。")
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 15px; line-height: 1.8;")
        layout.addWidget(subtitle)

        note = QLabel("单视频、批量规律、AB 对比的分析结果都会自动保存到历史报告。")
        note.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(note)

        return header

    def _build_mode_cards(self) -> QWidget:
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        cards = [
            ModeCard(
                icon="🎬",
                title="单视频分析",
                description="深度拆解一条视频的钩子、结构、文案和复用建议。",
                mode="single",
                accent_color=ACCENT,
            ),
            ModeCard(
                icon="📊",
                title="批量规律分析",
                description="总结多条视频的共性特征、爆款公式和优化方向。",
                mode="batch",
                accent_color=TEAL,
            ),
            ModeCard(
                icon="⚖️",
                title="AB 对比分析",
                description="比较两组视频的表现差异、根因和下一步动作。",
                mode="ab_comparison",
                accent_color=VIOLET,
            ),
            ModeCard(
                icon="🗂️",
                title="历史报告",
                description="查看已保存的报告，并重新打开或导出 Markdown。",
                mode="history",
                accent_color="#7caef5",
            ),
        ]

        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for card, (row, col) in zip(cards, positions):
            card.clicked.connect(self.mode_selected.emit)
            layout.addWidget(card, row, col)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        return container
