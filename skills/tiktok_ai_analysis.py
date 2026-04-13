"""
TikTok Monitor - TikTok AI Analysis Skill
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import AI_CONFIG

from .ai_client import AIClientMixin
from .prompts import (
    BATCH_ANALYSIS_PROMPT,
    COMPETITOR_ANALYSIS_PROMPT,
    HOOK_ANALYSIS_PROMPT,
    HOOK_LIBRARY_TAGGING_PROMPT,
    TREND_PREDICTION_PROMPT,
)


class TikTokAIAnalysisSkill(AIClientMixin):
    """TikTok AI 分析技能。"""

    def __init__(self, api_key: str = "", api_base: str = "", model: str = ""):
        self._init_ai_client(api_key, api_base, model)

    def analyze_single_video(self, video: dict, username: str = "") -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return self._mock_single_analysis(video)

        prompt = HOOK_ANALYSIS_PROMPT.format(
            username=username or "未知",
            description=video.get("description", video.get("title", "无描述")),
            hashtags=video.get("hashtags", "无标签"),
            music_name=video.get("music_name", "未知"),
            published_at=video.get("published_at", "未知"),
            play_count=f"{video.get('play_count', 0):,}",
            like_count=f"{video.get('like_count', 0):,}",
            comment_count=f"{video.get('comment_count', 0):,}",
            share_count=f"{video.get('share_count', 0):,}",
            duration=video.get("duration", 0),
        )

        messages = [
            {"role": "system", "content": "你是专业的 TikTok 内容策略分析师，请用中文回答。"},
            {"role": "user", "content": prompt},
        ]
        response = self._call_api_with_retry(
            messages=messages,
            max_retries=AI_CONFIG["max_retries"],
            temperature=AI_CONFIG["temperature"],
            max_tokens=AI_CONFIG["max_tokens"],
        )
        if response is None:
            return self._mock_single_analysis(video)

        raw_response = self._extract_response_text(response)
        result = self._parse_json_response(raw_response)
        if not result:
            return self._mock_single_analysis(video)

        result["raw_response"] = raw_response
        return result

    def analyze_batch_videos(self, videos: list, username: str = "") -> Optional[Dict[str, Any]]:
        if not videos:
            return None
        if not self.is_available():
            return self._mock_batch_analysis(videos)

        videos_data = "\n".join(
            [
                (
                    f"{i}. 描述：{v.get('description', v.get('title', ''))[:80]} | "
                    f"播放：{v.get('play_count', 0):,} | 点赞：{v.get('like_count', 0):,} | "
                    f"标签：{v.get('hashtags', '')} | BGM：{v.get('music_name', '')}"
                )
                for i, v in enumerate(videos[:10], 1)
            ]
        )
        prompt = BATCH_ANALYSIS_PROMPT.format(count=len(videos[:10]), videos_data=videos_data)
        messages = [
            {"role": "system", "content": "你是专业的 TikTok 内容策略分析师，请用中文回答。"},
            {"role": "user", "content": prompt},
        ]
        response = self._call_api_with_retry(
            messages=messages,
            max_retries=AI_CONFIG["max_retries"],
            temperature=AI_CONFIG["temperature"],
            max_tokens=AI_CONFIG["max_tokens_batch"],
        )
        if response is None:
            return self._mock_batch_analysis(videos)

        raw_response = self._extract_response_text(response)
        result = self._parse_json_response(raw_response)
        if not result:
            return self._mock_batch_analysis(videos)

        result["raw_response"] = raw_response
        result["analyzed_videos_count"] = len(videos[:10])
        result["username"] = username
        return result

    def analyze_competitors(self, creators_data: list) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None

        creators_summary = []
        for creator in creators_data:
            username = creator.get("username", "未知")
            videos = creator.get("videos", [])
            top_videos = sorted(videos, key=lambda v: v.get("play_count", 0), reverse=True)[:5]
            creators_summary.append(f"博主：@{username}")
            for i, video in enumerate(top_videos, 1):
                creators_summary.append(
                    f"  {i}. 播放：{video.get('play_count', 0):,} | 描述：{video.get('description', '')[:60]}"
                )
            creators_summary.append("")

        prompt = COMPETITOR_ANALYSIS_PROMPT.format(
            num_creators=len(creators_data),
            creators_data="\n".join(creators_summary),
        )
        response = self._call_api_with_retry(
            messages=[
                {"role": "system", "content": "你是专业的 TikTok 竞品分析师，请用中文回答。"},
                {"role": "user", "content": prompt},
            ],
            max_retries=AI_CONFIG["max_retries"],
            temperature=AI_CONFIG["temperature"],
            max_tokens=AI_CONFIG["max_tokens_competitor"],
        )
        if response is None:
            return None
        return self._parse_json_response(self._extract_response_text(response))

    def predict_trend(self, draft_data: dict, historical_data: list) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None

        prompt = TREND_PREDICTION_PROMPT.format(
            draft_data=json.dumps(draft_data, ensure_ascii=False, indent=2),
            historical_data=json.dumps(historical_data[:5], ensure_ascii=False, indent=2),
        )
        response = self._call_api_with_retry(
            messages=[
                {"role": "system", "content": "你是专业的 TikTok 数据科学家，请用中文回答。"},
                {"role": "user", "content": prompt},
            ],
            max_retries=AI_CONFIG["max_retries"],
            temperature=AI_CONFIG["temperature"],
            max_tokens=AI_CONFIG["max_tokens_trend"],
        )
        if response is None:
            return None
        return self._parse_json_response(self._extract_response_text(response))

    def tag_hook_library_entry(self, hook_analysis: dict) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return self._mock_hook_tagging(hook_analysis)

        prompt = HOOK_LIBRARY_TAGGING_PROMPT.format(
            hook_analysis_data=json.dumps(hook_analysis, ensure_ascii=False, indent=2)
        )
        response = self._call_api_with_retry(
            messages=[
                {"role": "system", "content": "你是专业的信息架构师，请用中文回答。"},
                {"role": "user", "content": prompt},
            ],
            max_retries=AI_CONFIG["max_retries"],
            temperature=0.5,
            max_tokens=AI_CONFIG["max_tokens_hook_tag"],
        )
        if response is None:
            return self._mock_hook_tagging(hook_analysis)

        result = self._parse_json_response(self._extract_response_text(response))
        return result or self._mock_hook_tagging(hook_analysis)

    def calculate_engagement_metrics(self, video: dict) -> Dict[str, float]:
        play_count = video.get("play_count", 0) or 0
        like_count = video.get("like_count", 0) or 0
        comment_count = video.get("comment_count", 0) or 0
        share_count = video.get("share_count", 0) or 0

        like_rate = (like_count / play_count * 100) if play_count > 0 else 0
        comment_rate = (comment_count / play_count * 100) if play_count > 0 else 0
        share_rate = (share_count / play_count * 100) if play_count > 0 else 0
        engagement_rate = ((like_count + comment_count + share_count) / play_count * 100) if play_count > 0 else 0

        return {
            "like_rate": round(like_rate, 2),
            "comment_rate": round(comment_rate, 2),
            "share_rate": round(share_rate, 2),
            "engagement_rate": round(engagement_rate, 2),
            "total_engagement": like_count + comment_count + share_count,
        }

    def analyze_trends(self, videos: List[dict]) -> Dict[str, Any]:
        if not videos:
            return {}

        durations = [v.get("duration", 0) for v in videos if v.get("duration")]
        avg_duration = sum(durations) / len(durations) if durations else 0
        plays = [v.get("play_count", 0) for v in videos]
        avg_plays = sum(plays) / len(plays) if plays else 0
        top_video = max(videos, key=lambda v: v.get("play_count", 0))
        engagement_rates = [self.calculate_engagement_metrics(v)["engagement_rate"] for v in videos]
        avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0

        hashtag_freq: Dict[str, int] = {}
        for video in videos:
            for tag in (video.get("hashtags", "") or "").split():
                hashtag_freq[tag] = hashtag_freq.get(tag, 0) + 1

        bgm_freq: Dict[str, int] = {}
        for video in videos:
            bgm = video.get("music_name", "")
            if bgm:
                bgm_freq[bgm] = bgm_freq.get(bgm, 0) + 1

        top_hashtags = sorted(hashtag_freq.items(), key=lambda item: item[1], reverse=True)[:10]
        top_bgms = sorted(bgm_freq.items(), key=lambda item: item[1], reverse=True)[:5]

        return {
            "duration_analysis": {
                "avg_duration": round(avg_duration, 1),
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
            },
            "performance_analysis": {
                "avg_play_count": round(avg_plays, 0),
                "top_video_id": top_video.get("video_id", ""),
                "top_video_plays": top_video.get("play_count", 0),
            },
            "engagement_analysis": {
                "avg_engagement_rate": round(avg_engagement, 2),
            },
            "top_hashtags": [{"tag": tag, "count": count} for tag, count in top_hashtags],
            "top_bgms": [{"name": name, "count": count} for name, count in top_bgms],
            "total_videos_analyzed": len(videos),
        }

    def generate_hook_library_entry(self, video: dict, analysis: dict) -> Dict[str, Any]:
        metrics = self.calculate_engagement_metrics(video)
        return {
            "hook_type": analysis.get("hook_type", "未知"),
            "hook_description": analysis.get("hook_description", ""),
            "video_id": video.get("video_id", ""),
            "video_url": video.get("video_url", ""),
            "play_count": video.get("play_count", 0),
            "engagement_rate": metrics["engagement_rate"],
            "opening_script": analysis.get("opening_script", ""),
            "content_structure": analysis.get("content_structure", ""),
            "replication_suggestions": analysis.get("replication_suggestions", ""),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _mock_single_analysis(self, video: dict) -> Dict[str, Any]:
        play_count = video.get("play_count", 0)
        desc = (video.get("description") or video.get("title") or "").lower()

        hook_type = "信息价值型"
        if play_count > 1_000_000:
            hook_type = "病毒传播型"
        elif any(keyword in desc for keyword in ["how", "why", "secret", "tip", "trick", "如何", "秘密", "技巧"]):
            hook_type = "教程干货型"
        elif any(keyword in desc for keyword in ["funny", "lol", "haha", "搞笑", "哈哈"]):
            hook_type = "娱乐搞笑型"

        return {
            "hook_type": hook_type,
            "hook_description": f"该视频通过 {hook_type} 策略吸引观众，播放量达到 {play_count:,} 次。",
            "opening_script": "前 3 秒直接展示结果、冲突或核心利益点，快速抓住注意力。",
            "content_structure": "开头抛出钩子，中段展开过程，结尾给出总结与互动引导。",
            "bgm_strategy": f"搭配音乐《{video.get('music_name', '未知')}》，节奏与画面切换保持一致。",
            "visual_style": "更适合竖屏近景、字幕强化重点、封面与正文信息一致。",
            "copywriting_style": "标题倾向于短句、结果先行、带一点好奇心缺口。",
            "replication_suggestions": (
                "1. 在前 3 秒先给结果或反差。\n"
                "2. 保留 1 个核心卖点，不要信息过载。\n"
                "3. 用 3-5 个垂类标签配合热点音乐。"
            ),
            "raw_response": "[mock analysis]",
        }

    def _mock_batch_analysis(self, videos: list) -> Dict[str, Any]:
        return {
            "common_hooks": "这批视频普遍使用结果前置、痛点切入和反差展示来争取前 3 秒停留。",
            "top_patterns": "1. 先抛结论\n2. 再补过程\n3. 结尾追加互动问题或行动建议",
            "bgm_insights": "高表现内容更偏向节奏明确、辨识度高的 BGM，而不是复杂配乐。",
            "hashtag_strategy": "建议 1 个大流量标签 + 2 个垂类标签 + 1-2 个场景标签。",
            "content_recommendations": (
                "1. 开头直接亮结果。\n"
                "2. 时长控制在 15-30 秒。\n"
                "3. 关键句必须上字幕。\n"
                "4. 结尾引导评论或收藏。"
            ),
            "hook_formula": "痛点/结果前置 -> 过程拆解 -> 情绪强化 -> 行动召唤",
            "raw_response": "[mock batch analysis]",
            "analyzed_videos_count": len(videos[:10]),
        }

    def _mock_hook_tagging(self, hook_analysis: dict) -> Dict[str, Any]:
        return {
            "primary_category": hook_analysis.get("hook_type", "信息价值型"),
            "secondary_tags": ["前3秒钩子", "可复用"],
            "content_goal": "提升停留与点击",
            "audience_stage": "冷启动",
            "risk_level": "low",
        }
