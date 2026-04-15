"""
TikTok Monitor - AI Report Home Page
AI报告模式选择主界面
"""

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

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
    """分析模式卡片"""
    
    clicked = pyqtSignal(str)
    
    def __init__(self, icon: str, title: str, description: str, mode: str, accent_color: str):
        super().__init__()
        self.mode = mode
        self.accent_color = accent_color
        
        self.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {BG_PANEL}, stop:1 {BG_SURFACE});
                border: 1px solid {BORDER};
                border-left: 4px solid {accent_color};
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
        
        # 图标
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 48px; color: {accent_color};")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: 700;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 描述
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.7;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # 按钮
        btn = QPushButton("进入分析")
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {accent_color};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER if accent_color == ACCENT else accent_color + 'dd'};
            }}
            """
        )
        btn.clicked.connect(lambda: self.clicked.emit(mode))
        layout.addWidget(btn)


class AIReportHomePage(QWidget):
    """AI报告模式选择主界面"""
    
    mode_selected = pyqtSignal(str)  # 信号：single, batch, ab_comparison
    
    def __init__(self):
        super().__init__()
        self._build_ui()
    
    def _build_ui(self):
        self.setStyleSheet(PAGE_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # 标题区
        header = self._build_header()
        layout.addWidget(header)
        
        # 模式卡片区
        cards_container = self._build_mode_cards()
        layout.addWidget(cards_container, 1)
    
    def _build_header(self) -> QWidget:
        """构建标题区"""
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
        
        # 主标题
        title = QLabel("AI 分析报告中心")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 32px; font-weight: 800;")
        layout.addWidget(title)
        
        # 副标题
        subtitle = QLabel("选择一种分析模式开始 AI 驱动的视频内容分析")
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 15px; line-height: 1.8;")
        layout.addWidget(subtitle)
        
        # 说明文字
        note = QLabel("支持单视频深度拆解、批量规律总结和 AB 对比分析，所有分析结果会自动保存到数据库")
        note.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(note)
        
        return header
    
    def _build_mode_cards(self) -> QWidget:
        """构建模式卡片区"""
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # 单视频分析卡片
        single_card = ModeCard(
            icon="🎯",
            title="单视频分析",
            description="深度拆解单条视频的开场钩子、内容结构、视觉风格和可复用策略，适合精细化学习爆款内容",
            mode="single",
            accent_color=ACCENT,
        )
        single_card.clicked.connect(self.mode_selected.emit)
        layout.addWidget(single_card, 0, 0)
        
        # 批量规律分析卡片
        batch_card = ModeCard(
            icon="📊",
            title="批量规律分析",
            description="分析博主多个视频的共性特征，总结爆款公式、高频内容模式和标签策略，发现创作规律",
            mode="batch",
            accent_color=TEAL,
        )
        batch_card.clicked.connect(self.mode_selected.emit)
        layout.addWidget(batch_card, 0, 1)
        
        # AB对比分析卡片
        ab_card = ModeCard(
            icon="⚖️",
            title="AB对比分析",
            description="对比两组视频的表现差异，找出胜出关键因素和根本原因，生成优化建议和仿写脚本",
            mode="ab_comparison",
            accent_color=VIOLET,
        )
        ab_card.clicked.connect(self.mode_selected.emit)
        layout.addWidget(ab_card, 0, 2)
        
        # 设置列等宽
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        
        return container
