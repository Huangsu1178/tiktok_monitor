"""
TikTok Monitor - TikTok AI Analysis Skill
"""

import json
import os
import sys
import time
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
        timestamp = datetime.now().strftime("%H:%M:%S")
        start_time = time.time()
        video_id = video.get('video_id', 'unknown')
        print(f"[AI Analysis] [{timestamp}] 开始分析视频: {video_id}")
        print(f"[AI Analysis] 开始分析单个视频: {video_id}")
        if not self.is_available():
            print("[AI Analysis] ⚠️ AI服务不可用，使用模拟分析")
            return self._mock_single_analysis(video)

        print(f"[AI Analysis] 准备分析提示词...")
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
        
        api_timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[AI Analysis] [{api_timestamp}] 发送API请求...")
        print(f"[AI Analysis] 调用AI API进行分析...")
        response = self._call_api_with_retry(
            messages=messages,
            max_retries=AI_CONFIG["max_retries"],
            temperature=AI_CONFIG["temperature"],
            max_tokens=AI_CONFIG["max_tokens"],
        )
        
        if response is None:
            print("[AI Analysis] ❌ AI API调用失败，使用模拟分析")
            return self._mock_single_analysis(video)

        print(f"[AI Analysis] 收到AI响应，正在解析...")
        raw_response = self._extract_response_text(response)
        result = self._parse_json_response(raw_response)
        if not result:
            print("[AI Analysis] ⚠️ JSON解析失败，使用模拟分析")
            return self._mock_single_analysis(video)

        result["raw_response"] = raw_response
        end_timestamp = datetime.now().strftime("%H:%M:%S")
        elapsed = time.time() - start_time
        print(f"[AI Analysis] [{end_timestamp}] 分析完成 | 总耗时: {elapsed:.1f}s")
        print(f"[AI Analysis] ✅ 单个视频分析完成")
        return result

    def analyze_batch_videos(self, videos: list, username: str = "") -> Optional[Dict[str, Any]]:
        timestamp = datetime.now().strftime("%H:%M:%S")
        start_time = time.time()
        print(f"[AI Analysis] [{timestamp}] 批量分析 | 视频数: {len(videos)} | 开始处理...")
        print(f"[AI Analysis] 开始批量分析 {len(videos)} 个视频")
        if not videos:
            print("[AI Analysis] ⚠️ 视频列表为空")
            return None
        if not self.is_available():
            print("[AI Analysis] ⚠️ AI服务不可用，使用模拟批量分析")
            return self._mock_batch_analysis(videos)

        print(f"[AI Analysis] 准备批量分析数据...")
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
        
        api_timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[AI Analysis] [{api_timestamp}] 发送API请求...")
        print(f"[AI Analysis] 调用AI API进行批量分析...")
        response = self._call_api_with_retry(
            messages=messages,
            max_retries=AI_CONFIG["max_retries"],
            temperature=AI_CONFIG["temperature"],
            max_tokens=AI_CONFIG["max_tokens_batch"],
        )
        
        if response is None:
            print("[AI Analysis] ❌ AI API批量调用失败，使用模拟分析")
            return self._mock_batch_analysis(videos)

        print(f"[AI Analysis] 收到AI批量响应，正在解析...")
        raw_response = self._extract_response_text(response)
        result = self._parse_json_response(raw_response)
        if not result:
            print("[AI Analysis] ⚠️ 批量分析JSON解析失败，使用模拟分析")
            return self._mock_batch_analysis(videos)

        result["raw_response"] = raw_response
        result["analyzed_videos_count"] = len(videos[:10])
        result["username"] = username
        end_timestamp = datetime.now().strftime("%H:%M:%S")
        elapsed = time.time() - start_time
        print(f"[AI Analysis] [{end_timestamp}] 批量分析完成 | 总耗时: {elapsed:.1f}s")
        print(f"[AI Analysis] ✅ 批量分析完成，分析了 {len(videos[:10])} 个视频")
        return result

    def analyze_competitors(self, creators_data: list) -> Optional[Dict[str, Any]]:
        timestamp = datetime.now().strftime("%H:%M:%S")
        start_time = time.time()
        print(f"[AI Analysis] [{timestamp}] 开始竞品分析 | 博主数: {len(creators_data)}")
        print(f"[AI Analysis] 开始竞品分析，共 {len(creators_data)} 个博主")
        if not self.is_available():
            print("[AI Analysis] ⚠️ AI服务不可用，无法进行竞品分析")
            return None

        print(f"[AI Analysis] 准备竞品分析数据...")
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
        
        api_timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[AI Analysis] [{api_timestamp}] 发送API请求...")
        print(f"[AI Analysis] 调用AI API进行竞品分析...")
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
            print("[AI Analysis] ❌ AI API竞品分析调用失败")
            return None
        
        print(f"[AI Analysis] 收到竞品分析响应，正在解析...")
        result = self._parse_json_response(self._extract_response_text(response))
        end_timestamp = datetime.now().strftime("%H:%M:%S")
        elapsed = time.time() - start_time
        print(f"[AI Analysis] [{end_timestamp}] 竞品分析完成 | 总耗时: {elapsed:.1f}s")
        print(f"[AI Analysis] ✅ 竞品分析完成")
        return result

    def predict_trend(self, draft_data: dict, historical_data: list) -> Optional[Dict[str, Any]]:
        timestamp = datetime.now().strftime("%H:%M:%S")
        start_time = time.time()
        print(f"[AI Analysis] [{timestamp}] 开始趋势预测分析")
        print(f"[AI Analysis] 开始趋势预测分析")
        if not self.is_available():
            print("[AI Analysis] ⚠️ AI服务不可用，无法进行趋势预测")
            return None

        print(f"[AI Analysis] 准备趋势预测数据...")
        prompt = TREND_PREDICTION_PROMPT.format(
            draft_data=json.dumps(draft_data, ensure_ascii=False, indent=2),
            historical_data=json.dumps(historical_data[:5], ensure_ascii=False, indent=2),
        )
        
        api_timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[AI Analysis] [{api_timestamp}] 发送API请求...")
        print(f"[AI Analysis] 调用AI API进行趋势预测...")
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
            print("[AI Analysis] ❌ AI API趋势预测调用失败")
            return None
        
        print(f"[AI Analysis] 收到趋势预测响应，正在解析...")
        result = self._parse_json_response(self._extract_response_text(response))
        end_timestamp = datetime.now().strftime("%H:%M:%S")
        elapsed = time.time() - start_time
        print(f"[AI Analysis] [{end_timestamp}] 趋势预测完成 | 总耗时: {elapsed:.1f}s")
        print(f"[AI Analysis] ✅ 趋势预测完成")
        return result

    def tag_hook_library_entry(self, hook_analysis: dict) -> Optional[Dict[str, Any]]:
        timestamp = datetime.now().strftime("%H:%M:%S")
        start_time = time.time()
        print(f"[AI Analysis] [{timestamp}] 开始钩子库条目标签化")
        print(f"[AI Analysis] 开始钩子库条目标签化")
        if not self.is_available():
            print("[AI Analysis] ⚠️ AI服务不可用，使用模拟标签化")
            return self._mock_hook_tagging(hook_analysis)

        print(f"[AI Analysis] 准备标签化数据...")
        prompt = HOOK_LIBRARY_TAGGING_PROMPT.format(
            hook_analysis_data=json.dumps(hook_analysis, ensure_ascii=False, indent=2)
        )
        
        api_timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[AI Analysis] [{api_timestamp}] 发送API请求...")
        print(f"[AI Analysis] 调用AI API进行标签化...")
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
            print("[AI Analysis] ❌ AI API标签化调用失败，使用模拟标签化")
            return self._mock_hook_tagging(hook_analysis)

        print(f"[AI Analysis] 收到标签化响应，正在解析...")
        result = self._parse_json_response(self._extract_response_text(response))
        if not result:
            print("[AI Analysis] ⚠️ 标签化JSON解析失败，使用模拟标签化")
            return self._mock_hook_tagging(hook_analysis)
        
        end_timestamp = datetime.now().strftime("%H:%M:%S")
        elapsed = time.time() - start_time
        print(f"[AI Analysis] [{end_timestamp}] 钩子库条目标签化完成 | 总耗时: {elapsed:.1f}s")
        print(f"[AI Analysis] ✅ 钩子库条目标签化完成")
        return result

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
            "start_framework": {
                "stop": "视频开头通过直接抛出痛点或反常识观点，在第一秒截停用户滑动",
                "tension": "暗示有解决方案但不立即揭晓，用疑问句或悬念画面制造期待感",
                "authority": "通过专业身份背书或展示实际成果，快速建立信任",
                "reveal": "分步骤交付核心价值，配合紧凑的视觉切换保持注意力",
                "transfer": "在情绪高点给出明确的行动号召，引导点赞、评论或关注"
            },
            "performance_benchmark": {
                "engagement_rate": "计算中...",
                "benchmark_8pct": "待评估",
                "verdict": "需要实际互动数据进行评估",
                "improvement_tips": "建议优化开场钩子以提升3秒完播率，增加互动引导以提升评论和分享率"
            },
            "script_template": "S (钩子): [抛出一个关于该领域的反常识观点或强烈痛点]\nT (悬念): [暗示你掌握了解决方法，但先卖个关子制造期待]\nA (信任): [一句话交代你的专业背景或亲身经历]\nR (交付): [分3步给出具体的解决方案，配合清晰的视觉展示]\nT (引导): [给出明确的下一步行动指令，如点赞、收藏或在评论区留言]",
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
            "common_start_patterns": {
                "stop": "多数视频采用痛点前置或数字冲击型钩子截停用户",
                "tension": "常用疑问句或'你一定不知道'句式制造悬念",
                "authority": "通过展示成果数据或专业身份快速建立信任",
                "reveal": "倾向于使用3步法或清单式交付核心价值",
                "transfer": "结尾常用'点赞收藏'或'评论区告诉我'引导互动"
            },
            "script_template": "S (钩子): [结合该博主最常用的钩子类型，抛出目标受众的核心痛点]\nT (悬念): [用该博主惯用的悬念手法，暗示即将揭晓答案]\nA (信任): [模仿该博主的信任建立方式]\nR (交付): [按照该博主的内容节奏，分步交付价值]\nT (引导): [使用该博主最有效的CTA话术引导互动]",
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
