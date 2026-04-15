"""
Shared visual theme for the desktop UI.
"""

APP_FONT_FAMILY = '"Microsoft YaHei", "Segoe UI", sans-serif'

BG_APP = "#0d1522"
BG_PANEL = "#121c2b"
BG_PANEL_ALT = "#172233"
BG_SIDEBAR = "#0f1826"
BG_SURFACE = "#1a2638"
BG_SURFACE_HOVER = "#22324a"
BG_MUTED = "#24364f"

TEXT_PRIMARY = "#edf3ff"
TEXT_SECONDARY = "#aab9cf"
TEXT_MUTED = "#7f8ea7"

BORDER = "#263a56"
BORDER_STRONG = "#365071"

ACCENT = "#ff7a59"
ACCENT_HOVER = "#ff8b6d"
ACCENT_SOFT = "#fff1ec"

SUCCESS = "#52c58b"
WARNING = "#f2b265"
DANGER = "#f47f8b"
DANGER_HOVER = "#f6959e"
INFO = "#63a4ff"
VIOLET = "#7c8cff"
TEAL = "#52c7b8"


def global_stylesheet() -> str:
    return f"""
    QMainWindow {{
        background-color: {BG_APP};
    }}
    QWidget#main_content {{
        background-color: {BG_APP};
    }}
    QScrollBar:vertical {{
        background: {BG_PANEL};
        width: 10px;
        margin: 4px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {BG_MUTED};
        min-height: 36px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {BORDER_STRONG};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """


def page_background_style() -> str:
    return f"background-color: {BG_APP}; color: {TEXT_PRIMARY};"


def section_title_style(size: int = 16) -> str:
    return f"color: {TEXT_PRIMARY}; font-size: {size}px; font-weight: 700;"


def page_title_style() -> str:
    return section_title_style(24)


def body_text_style() -> str:
    return f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.6;"


def subtle_text_style() -> str:
    return f"color: {TEXT_MUTED}; font-size: 12px; line-height: 1.6;"


def sidebar_style() -> str:
    return f"""
    QWidget#sidebar {{
        background-color: {BG_SIDEBAR};
        border-right: 1px solid {BORDER};
    }}
    """


def nav_button_style() -> str:
    return f"""
    QPushButton {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: 1px solid transparent;
        border-radius: 12px;
        padding: 12px 16px;
        text-align: left;
        font-size: 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {BG_SURFACE};
        color: {TEXT_PRIMARY};
        border-color: {BORDER};
    }}
    QPushButton:checked {{
        background-color: {ACCENT_SOFT};
        color: {ACCENT};
        border-color: #ffd4c7;
    }}
    """


def primary_button_style() -> str:
    return f"""
    QPushButton {{
        background-color: {ACCENT};
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 18px;
        font-size: 13px;
        font-weight: 700;
    }}
    QPushButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
    """


def secondary_button_style() -> str:
    return f"""
    QPushButton {{
        background-color: {BG_SURFACE};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 9px 16px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {BG_SURFACE_HOVER};
        border-color: {BORDER_STRONG};
    }}
    """


def table_button_style() -> str:
    """表格内使用的小按钮样式"""
    return f"""
    QPushButton {{
        background-color: {BG_SURFACE};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {BG_SURFACE_HOVER};
        border-color: {BORDER_STRONG};
    }}
    """


def table_danger_button_style() -> str:
    """表格内使用的危险操作按钮样式"""
    return f"""
    QPushButton {{
        background-color: transparent;
        color: {DANGER};
        border: 1px solid {DANGER};
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: rgba(244, 127, 139, 0.12);
    }}
    """


def accent_button_style() -> str:
    return f"""
    QPushButton {{
        background-color: {VIOLET};
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 16px;
        font-size: 13px;
        font-weight: 700;
    }}
    QPushButton:hover {{
        background-color: #92a0ff;
    }}
    """


def success_button_style() -> str:
    return f"""
    QPushButton {{
        background-color: {TEAL};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 11px;
        font-weight: 700;
    }}
    QPushButton:hover {{
        background-color: #63d6c8;
    }}
    """


def danger_button_style() -> str:
    return f"""
    QPushButton {{
        background-color: transparent;
        color: {DANGER};
        border: 1px solid {DANGER};
        border-radius: 8px;
        padding: 7px 12px;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: rgba(244, 127, 139, 0.12);
    }}
    """


def table_style(alternate: bool = True) -> str:
    alternate_rule = f"QTableWidget {{ alternate-background-color: {BG_PANEL_ALT}; }}" if alternate else ""
    return f"""
    QTableWidget {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER};
        border-radius: 14px;
        color: {TEXT_PRIMARY};
        gridline-color: {BORDER};
        font-size: 13px;
    }}
    QTableWidget::item {{
        padding: 6px 8px;
        border-bottom: 1px solid {BORDER};
    }}
    QTableWidget::item:selected {{
        background-color: {BG_SURFACE};
    }}
    QHeaderView::section {{
        background-color: {BG_SURFACE};
        color: {TEXT_SECONDARY};
        padding: 8px 10px;
        border: none;
        border-bottom: 1px solid {BORDER};
        font-size: 12px;
        font-weight: 700;
    }}
    {alternate_rule}
    """


def card_style(left_accent: str | None = None) -> str:
    accent_rule = f"border-left: 4px solid {left_accent};" if left_accent else ""
    return f"""
    QFrame {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER};
        border-radius: 16px;
        {accent_rule}
    }}
    """


def input_style(min_width: int = 220) -> str:
    return f"""
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {BG_SURFACE};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 9px 12px;
        font-size: 13px;
        min-width: {min_width}px;
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border-color: {ACCENT};
    }}
    """


def group_style() -> str:
    return f"""
    QGroupBox {{
        color: {TEXT_PRIMARY};
        font-size: 14px;
        font-weight: 700;
        border: 1px solid {BORDER};
        border-radius: 16px;
        margin-top: 14px;
        padding-top: 12px;
        background-color: {BG_PANEL};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
        color: {TEXT_SECONDARY};
    }}
    """


def selector_style() -> str:
    return f"""
    QToolButton {{
        background-color: {BG_SURFACE};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 9px 12px;
        font-size: 13px;
        min-width: 240px;
        text-align: left;
    }}
    QToolButton::menu-indicator {{
        subcontrol-origin: padding;
        subcontrol-position: right center;
        right: 10px;
    }}
    QMenu {{
        background-color: {BG_PANEL};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 8px;
    }}
    QMenu::item {{
        padding: 8px 28px 8px 12px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background-color: {BG_SURFACE};
    }}
    """
