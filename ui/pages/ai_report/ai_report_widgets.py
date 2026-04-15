"""
TikTok Monitor - AI report shared widgets.
"""

import re
from dataclasses import dataclass
from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.components.theme import BG_PANEL, BORDER, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, card_style


EMPTY_ANALYSIS_TEXT = "\u6682\u65e0\u5206\u6790\u5185\u5bb9"
CURRENT_SCOPE_TEXT = "\u5f53\u524d\u8303\u56f4"
SELECTED_PREFIX = "\u5df2\u9009"

COLON_CLASS = r"[:\uFF1A]"
SENTENCE_BREAK_CLASS = r"[\n:\uFF1A\.\!\?\u3002\uFF01\uFF1F]"
BULLET_CLASS = r"[-\u2022]"


@dataclass
class _StructuredItem:
    index: str = ""
    title: str = ""
    body: str = ""


@dataclass
class _ScriptStage:
    letter: str = ""
    title: str = ""
    body: str = ""


def _alpha_color(color: str, alpha: int) -> str:
    qcolor = QColor(color)
    return f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {alpha})"


def _normalize_report_text(text: str) -> str:
    normalized = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if "\\n" in normalized:
        normalized = normalized.replace("\\n", "\n")
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    normalized = re.sub(r"\n[ \t]+", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized


def _clean_inline_markup(text: str) -> str:
    cleaned = re.sub(r"[*_`]+", "", text or "")
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip(" \n\t")


def _split_title_and_body(text: str):
    patterns = [
        rf"^\[\s*(.+?)\s*{COLON_CLASS}\s*(.+?)\s*\]$",
        rf"^\*{{1,2}}\s*(.+?)\s*\*+\s*{COLON_CLASS}\s*(.+)$",
        rf"^([^{COLON_CLASS[1:-1]}\n]{{2,40}})\s*{COLON_CLASS}\s*(.+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, text.strip(), re.S)
        if not match:
            continue
        title = _clean_inline_markup(match.group(1))
        body = _clean_inline_markup(match.group(2))
        if title and body:
            return title, body
    return "", _clean_inline_markup(text)


def _extract_numbered_items(text: str):
    marker_re = re.compile(
        rf"(?:(?<=^)|(?<={SENTENCE_BREAK_CLASS}))\s*(?P<index>\d{{1,2}})\.\s*",
        re.S,
    )
    matches = [match for match in marker_re.finditer(text) if int(match.group("index")) <= 20]
    if not matches:
        return "", []

    intro = _clean_inline_markup(text[:matches[0].start()].strip(" \n\t:\uFF1A"))
    items: List[_StructuredItem] = []

    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if not chunk:
            continue
        title, body = _split_title_and_body(chunk)
        items.append(_StructuredItem(index=match.group("index"), title=title, body=body))

    return intro, items


def _looks_like_list_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False

    patterns = [
        r"^\d{1,2}\.\s+",
        rf"^{BULLET_CLASS}\s+",
        rf"^[A-Z]\s*\([^)]+\)\s*{COLON_CLASS}",
        rf"^\[[^\]\n]{{1,24}}{COLON_CLASS}",
        rf"^[^\s\[\]{COLON_CLASS[1:-1]}]{{1,12}}(?:/[^\s\[\]{COLON_CLASS[1:-1]}]{{1,12}})?\s*{COLON_CLASS}",
        rf"^\*{{1,2}}.+\*+\s*{COLON_CLASS}",
    ]
    return any(re.match(pattern, stripped) for pattern in patterns)


def _parse_line_item(line: str) -> _StructuredItem:
    stripped = line.strip()
    numbered = re.match(r"^(?P<index>\d{1,2})\.\s*(?P<body>.+)$", stripped, re.S)
    if numbered:
        title, body = _split_title_and_body(numbered.group("body"))
        return _StructuredItem(index=numbered.group("index"), title=title, body=body)

    stripped = re.sub(rf"^{BULLET_CLASS}\s*", "", stripped)
    title, body = _split_title_and_body(stripped)
    return _StructuredItem(title=title, body=body)


def parse_report_blocks(text: str):
    normalized = _normalize_report_text(text)
    if not normalized:
        return []

    blocks = []
    sections = [section.strip() for section in re.split(r"\n{2,}", normalized) if section.strip()]
    for section in sections:
        intro, numbered_items = _extract_numbered_items(section)
        if numbered_items:
            if intro:
                blocks.append(("paragraph", intro))
            for item in numbered_items:
                blocks.append(("item", item))
            continue

        lines = [line.strip() for line in section.split("\n") if line.strip()]
        list_like_count = sum(1 for line in lines if _looks_like_list_line(line))
        if len(lines) > 1 and list_like_count >= max(2, len(lines) - 1):
            for line in lines:
                if _looks_like_list_line(line):
                    blocks.append(("item", _parse_line_item(line)))
                else:
                    blocks.append(("paragraph", _clean_inline_markup(line)))
            continue

        blocks.append(("paragraph", _clean_inline_markup(section)))

    return blocks


def _normalize_script_stage_body(text: str) -> str:
    normalized = _normalize_report_text(text)
    if not normalized:
        return ""

    normalized = re.sub(
        r"\[\s*([^\[\]\n:：]{1,20})\s*[:：]\s*([^\[\]]+?)\s*\]",
        lambda match: f"{_clean_inline_markup(match.group(1))}: {_clean_inline_markup(match.group(2))}",
        normalized,
    )
    normalized = re.sub(
        r"(?<!\n)(?=(?:画面|文案/口播|文案|口播|字幕|旁白|镜头|动作|提示|重点)\s*[:：])",
        "\n",
        normalized,
    )
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def parse_script_template_stages(text: str):
    normalized = _normalize_report_text(text)
    if not normalized:
        return []

    header_re = re.compile(
        r"^\s*(?:#{1,6}\s*)?(?:>\s*)?(?:\d{1,2}\.\s*)?(?:[-*]\s*)?(?:\*{1,2}\s*)?"
        r"(?P<letter>[START])(?=\s|[\(\[（【\.\-、:：]|$)"
        r"(?:(?:\s*[\(\[（【]\s*(?P<title_paren>[^()\[\]（）【】:：\n]{1,24})\s*[\)\]）】])"
        r"|(?:\s*[\.\-、]\s*(?P<title_sep>[^:：\n]{1,24}))"
        r"|(?:\s+(?P<title_text>[^:：\n]{1,24})))?"
        r"\s*(?:\*{1,2})?\s*(?:[:：]\s*(?:\*{1,2})?\s*)?(?P<inline_body>.*)$",
        re.I,
    )

    stages: List[_ScriptStage] = []
    current_stage = None
    body_lines: List[str] = []

    def flush_current_stage():
        if current_stage is None:
            return
        body = _normalize_script_stage_body("\n".join(body_lines))
        stages.append(
            _ScriptStage(
                letter=current_stage["letter"],
                title=current_stage["title"],
                body=body,
            )
        )

    for raw_line in normalized.split("\n"):
        match = header_re.match(raw_line)
        if match:
            flush_current_stage()
            title = _clean_inline_markup(
                match.group("title_paren") or match.group("title_sep") or match.group("title_text")
            )
            inline_body = (match.group("inline_body") or "").strip()
            current_stage = {
                "letter": match.group("letter").upper(),
                "title": title,
            }
            body_lines = [inline_body] if inline_body else []
            continue

        if current_stage is not None:
            body_lines.append(raw_line)

    flush_current_stage()
    return [stage for stage in stages if stage.title or stage.body]


class StructuredContent(QWidget):
    def __init__(self, content: str, accent: str, empty_text: str = EMPTY_ANALYSIS_TEXT):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        blocks = parse_report_blocks(content)
        if not blocks:
            blocks = [("paragraph", empty_text)]

        for block_type, value in blocks:
            if block_type == "item":
                layout.addWidget(self._build_item(value, accent))
                continue

            label = QLabel(value)
            label.setWordWrap(True)
            label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; line-height: 1.8;")
            layout.addWidget(label)

    def _build_item(self, item: _StructuredItem, accent: str) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {_alpha_color(accent, 18)};
                border: 1px solid {_alpha_color(accent, 56)};
                border-radius: 12px;
            }}
            """
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        if item.index:
            badge = QLabel(item.index)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {_alpha_color(accent, 44)};
                    color: {accent};
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 800;
                    min-width: 24px;
                    max-width: 24px;
                    min-height: 24px;
                    max-height: 24px;
                }}
                """
            )
            layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        if item.title:
            title = QLabel(item.title)
            title.setWordWrap(True)
            title.setStyleSheet(f"color: {accent}; font-size: 13px; font-weight: 700;")
            text_layout.addWidget(title)

        body = QLabel(item.body or item.title or EMPTY_ANALYSIS_TEXT)
        body.setWordWrap(True)
        body.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; line-height: 1.75;")
        text_layout.addWidget(body)

        layout.addLayout(text_layout, 1)
        return frame


def build_structured_content(content: str, accent: str, empty_text: str = EMPTY_ANALYSIS_TEXT) -> QWidget:
    return StructuredContent(content=content, accent=accent, empty_text=empty_text)


class ScriptTemplateContent(QWidget):
    def __init__(self, content: str, accent: str, empty_text: str = EMPTY_ANALYSIS_TEXT):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        stages = parse_script_template_stages(content)
        if not stages:
            layout.addWidget(build_structured_content(content, accent, empty_text))
            return

        for stage in stages:
            layout.addWidget(self._build_stage(stage, accent, empty_text))

    def _build_stage(self, stage: _ScriptStage, accent: str, empty_text: str) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {_alpha_color(accent, 12)};
                border: 1px solid {_alpha_color(accent, 44)};
                border-radius: 14px;
            }}
            """
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(10)

        badge = QLabel(stage.letter or "?")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {_alpha_color(accent, 40)};
                color: {accent};
                border-radius: 14px;
                font-size: 12px;
                font-weight: 800;
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
            }}
            """
        )
        header.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)

        title = QLabel(stage.title or "阶段")
        title.setWordWrap(True)
        title.setStyleSheet(f"color: {accent}; font-size: 14px; font-weight: 700;")
        header.addWidget(title, 1)
        header.addStretch()

        layout.addLayout(header)
        layout.addWidget(build_structured_content(stage.body, accent, empty_text))
        return frame


def build_script_template_content(content: str, accent: str, empty_text: str = EMPTY_ANALYSIS_TEXT) -> QWidget:
    return ScriptTemplateContent(content=content, accent=accent, empty_text=empty_text)


class MetricChip(QFrame):
    def __init__(self, label: str, value: str, accent: str):
        super().__init__()
        self.setStyleSheet(card_style(accent))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        title = QLabel(label)
        title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(title)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {accent}; font-size: 18px; font-weight: 700;")
        layout.addWidget(value_label)


class AnalysisCard(QFrame):
    def __init__(self, title: str, content: str, accent: str):
        super().__init__()
        self.setStyleSheet(card_style(accent))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {accent}; font-size: 13px; font-weight: 700;")
        layout.addWidget(title_label)

        layout.addWidget(build_structured_content(content, accent, EMPTY_ANALYSIS_TEXT))


class EmptyState(QFrame):
    def __init__(self, title: str, desc: str):
        super().__init__()
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px dashed {BORDER};
                border-radius: 16px;
            }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 32, 24, 32)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 16px; font-weight: 700;")
        layout.addWidget(title_label)

        desc_label = QLabel(desc)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; line-height: 1.75;")
        layout.addWidget(desc_label)


class LoadingIndicator(QFrame):
    def __init__(self, title: str, desc: str):
        super().__init__()
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 32, 24, 32)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 18px; font-weight: 700;")
        layout.addWidget(title_label)

        desc_label = QLabel(desc)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; line-height: 1.75;")
        layout.addWidget(desc_label)


def format_number(value) -> str:
    value = value or 0
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def get_subject_label(username: str) -> str:
    if not username:
        return CURRENT_SCOPE_TEXT
    if username.startswith(SELECTED_PREFIX):
        return username
    return f"@{username}"
