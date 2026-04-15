"""
Shared helpers for AI report export and history metadata.
"""

import os
import re
from datetime import datetime

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from data.database import get_setting


REPORT_TYPE_META = {
    "single": {"label": "单视频", "accent": "#ff7b65"},
    "batch": {"label": "批量规律", "accent": "#6ec8b5"},
    "ab_comparison": {"label": "AB 对比", "accent": "#92a2f7"},
}


def report_type_label(report_type: str) -> str:
    return REPORT_TYPE_META.get(report_type, {}).get("label", report_type or "未知类型")


def report_type_accent(report_type: str) -> str:
    return REPORT_TYPE_META.get(report_type, {}).get("accent", "#7caef5")


def sanitize_filename(name: str) -> str:
    filename = re.sub(r"[\\/:*?\"<>|]+", "_", str(name or "").strip())
    filename = re.sub(r"\s+", " ", filename).strip(" .")
    return filename or "AI_分析报告"


def get_report_export_dir() -> str:
    base_dir = get_setting("download_path", os.path.expanduser("~/Downloads/TikTok_Monitor"))
    export_dir = os.path.join(base_dir, "reports")
    os.makedirs(export_dir, exist_ok=True)
    return export_dir


def save_report_markdown(parent, title: str, markdown: str) -> str:
    default_dir = get_report_export_dir()
    default_name = sanitize_filename(title) + ".md"
    default_path = os.path.join(default_dir, default_name)
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        "保存报告",
        default_path,
        "Markdown Files (*.md);;Text Files (*.txt)",
    )
    if not file_path:
        return ""

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(markdown or "")
    except OSError as exc:
        QMessageBox.critical(parent, "保存失败", f"报告保存失败：{exc}")
        return ""

    QMessageBox.information(parent, "保存成功", f"报告已保存到：\n{file_path}")
    return file_path


def build_single_report_title(subject: str) -> str:
    return f"{subject} 单视频分析报告".strip()


def build_batch_report_title(subject: str, count: int) -> str:
    count_text = f"（{count} 条视频）" if count else ""
    return f"{subject} 批量规律分析报告{count_text}".strip()


def build_ab_report_title(group_a_label: str, group_b_label: str) -> str:
    return f"{group_a_label} vs {group_b_label} AB 对比报告"


def build_single_report_summary(video: dict, analysis: dict) -> str:
    hook_type = analysis.get("hook_type", "").strip()
    desc = (video.get("description") or video.get("title") or "").strip().replace("\n", " ")
    desc = desc[:48] + ("..." if len(desc) > 48 else "")
    if hook_type and desc:
        return f"{hook_type} | {desc}"
    return hook_type or desc or "单视频分析报告"


def build_batch_report_summary(analysis: dict) -> str:
    key_findings = list(analysis.get("key_findings") or [])
    if key_findings:
        first = key_findings[0] or {}
        summary = str(first.get("title") or first.get("insight") or "").strip().replace("\n", " ")
        summary = summary[:72] + ("..." if len(summary) > 72 else "")
        if summary:
            return summary
    formula = (analysis.get("hook_formula") or "").strip().replace("\n", " ")
    formula = formula[:72] + ("..." if len(formula) > 72 else "")
    return formula or "批量内容规律总结"


def build_ab_report_summary(result: dict, group_a_label: str, group_b_label: str) -> str:
    winner = result.get("winner", "")
    winner_text = "两组各有优势"
    if winner == "A":
        winner_text = f"整体更强：{group_a_label}"
    elif winner == "B":
        winner_text = f"整体更强：{group_b_label}"

    diagnosis = (result.get("diagnosis_summary", {}) or {}).get("what", "")
    diagnosis = diagnosis.strip().replace("\n", " ")
    diagnosis = diagnosis[:56] + ("..." if len(diagnosis) > 56 else "")
    return f"{winner_text} | {diagnosis or 'AB 差异诊断报告'}"


def _append_metadata(lines: list[str], rows: list[tuple[str, str]]):
    for label, value in rows:
        if value:
            lines.append(f"- {label}: {value}")
    if rows:
        lines.append("")


def _append_text_section(lines: list[str], title: str, content: str, level: int = 2):
    text = str(content or "").strip()
    if not text:
        return
    lines.append(f"{'#' * level} {title}")
    lines.append("")
    lines.append(text)
    lines.append("")


def _append_dict_section(lines: list[str], title: str, content: dict, level: int = 2):
    content = dict(content or {})
    if not content:
        return
    lines.append(f"{'#' * level} {title}")
    lines.append("")
    for key, value in content.items():
        value_text = str(value or "").strip()
        if not value_text:
            continue
        lines.append(f"- {key}: {value_text}")
    lines.append("")


def _append_list_section(lines: list[str], title: str, items, level: int = 2):
    items = list(items or [])
    if not items:
        return
    lines.append(f"{'#' * level} {title}")
    lines.append("")
    for item in items:
        if isinstance(item, dict):
            name = str(
                item.get("dimension")
                or item.get("title")
                or item.get("label")
                or item.get("pattern")
                or item.get("action")
                or item.get("video_label")
                or ""
            ).strip()
            body_parts = []
            for key, value in item.items():
                if key in {"dimension", "title", "label", "pattern", "action", "video_label"}:
                    continue
                value_text = str(value or "").strip()
                if value_text:
                    body_parts.append(f"{key}: {value_text}")
            if name and body_parts:
                lines.append(f"- {name} | {'；'.join(body_parts)}")
            elif name:
                lines.append(f"- {name}")
            elif body_parts:
                lines.append(f"- {'；'.join(body_parts)}")
        else:
            item_text = str(item or "").strip()
            if item_text:
                lines.append(f"- {item_text}")
    lines.append("")


def build_single_report_markdown(title: str, subject: str, video: dict, analysis: dict) -> str:
    lines = [f"# {title}", ""]
    _append_metadata(
        lines,
        [
            ("报告类型", report_type_label("single")),
            ("对象", subject),
            ("生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("发布时间", str(video.get("published_at") or "")),
            ("视频时长", f"{video.get('duration', 0) or 0}s"),
            ("播放量", str(video.get("play_count", 0) or 0)),
            ("点赞数", str(video.get("like_count", 0) or 0)),
            ("评论数", str(video.get("comment_count", 0) or 0)),
            ("分享数", str(video.get("share_count", 0) or 0)),
        ],
    )
    _append_text_section(lines, "视频描述", video.get("description") or video.get("title") or "")
    _append_text_section(lines, "核心钩子类型", analysis.get("hook_type", ""))
    _append_text_section(lines, "钩子说明", analysis.get("hook_description", ""))
    _append_text_section(lines, "开场脚本", analysis.get("opening_script", ""))
    _append_text_section(lines, "内容结构", analysis.get("content_structure", ""))
    _append_text_section(lines, "BGM 策略", analysis.get("bgm_strategy", ""))
    _append_text_section(lines, "视觉风格", analysis.get("visual_style", ""))
    _append_text_section(lines, "文案风格", analysis.get("copywriting_style", ""))
    _append_text_section(lines, "复用建议", analysis.get("replication_suggestions", ""))
    _append_dict_section(lines, "S.T.A.R.T 开场框架", analysis.get("start_framework", {}))
    _append_dict_section(lines, "表现基准", analysis.get("performance_benchmark", {}))
    _append_text_section(lines, "脚本模板", analysis.get("script_template", ""))
    return "\n".join(lines).strip() + "\n"


def build_batch_report_markdown(title: str, subject: str, analysis: dict) -> str:
    lines = [f"# {title}", ""]
    _append_metadata(
        lines,
        [
            ("报告类型", report_type_label("batch")),
            ("对象", subject),
            ("生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("分析视频数", str(analysis.get("analyzed_videos_count", 0) or 0)),
        ],
    )
    _append_list_section(lines, "关键结论", analysis.get("key_findings", []))
    _append_list_section(lines, "共性优秀点", analysis.get("common_winning_patterns", []))
    _append_list_section(lines, "单条视频特色优秀点", analysis.get("unique_video_highlights", []))
    _append_list_section(lines, "优先执行动作", analysis.get("priority_actions", []))
    _append_text_section(lines, "爆款内容公式", analysis.get("hook_formula", ""))
    _append_dict_section(lines, "共同开场模式", analysis.get("common_start_patterns", {}))
    _append_text_section(lines, "共同钩子策略", analysis.get("common_hooks", ""))
    _append_text_section(lines, "高频内容模式", analysis.get("top_patterns", ""))
    _append_text_section(lines, "BGM 洞察", analysis.get("bgm_insights", ""))
    _append_text_section(lines, "标签策略", analysis.get("hashtag_strategy", ""))
    _append_text_section(lines, "优化建议", analysis.get("content_recommendations", ""))
    _append_text_section(lines, "脚本模板", analysis.get("script_template", ""))
    return "\n".join(lines).strip() + "\n"


def build_ab_report_markdown(title: str, result: dict, group_a_label: str, group_b_label: str) -> str:
    winner = result.get("winner", "")
    winner_text = ""
    if winner == "A":
        winner_text = group_a_label
    elif winner == "B":
        winner_text = group_b_label

    lines = [f"# {title}", ""]
    _append_metadata(
        lines,
        [
            ("报告类型", report_type_label("ab_comparison")),
            ("对比对象", f"{group_a_label} vs {group_b_label}"),
            ("生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("当前优势组", winner_text or "两组各有优势"),
        ],
    )
    _append_dict_section(lines, "诊断总结", result.get("diagnosis_summary", {}))
    _append_dict_section(lines, "表现差距概览", result.get("performance_gap_summary", {}))
    _append_text_section(lines, "整体对比概览", result.get("overview", ""))
    _append_list_section(lines, "关键差异", result.get("key_differences", []))
    _append_list_section(lines, "维度对比", result.get("dimension_comparisons", []))
    _append_list_section(lines, "根因诊断", result.get("root_causes", []))
    _append_list_section(lines, "优化建议", result.get("optimization_suggestions", []))
    _append_dict_section(lines, "开场框架对比", result.get("start_comparison", {}))
    _append_text_section(lines, "脚本模板", result.get("script_template", ""))
    return "\n".join(lines).strip() + "\n"
