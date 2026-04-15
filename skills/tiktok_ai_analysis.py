"""
TikTok Monitor - TikTok AI Analysis Skill
"""

import json
import time
from datetime import datetime
from statistics import median
from typing import Any, Dict, List, Optional

from config import AI_CONFIG

from .ai_client import AIClientMixin
from .prompts import (
    AB_COMPARISON_PROMPT,
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

    def analyze_ab_comparison(self, group_a_videos: list, group_b_videos: list,
                              group_a_label: str = "A组",
                              group_b_label: str = "B组") -> dict:
        """AB对比分析：分析两组视频的表现差异、原因和优化建议"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        start_time = time.time()
        print(f"[AI Analysis] [{timestamp}] AB对比分析 | A组: {len(group_a_videos)}个 | B组: {len(group_b_videos)}个")
        print(f"[AI Analysis] 开始AB对比分析: {group_a_label} vs {group_b_label}")

        if not self.is_available():
            print("[AI Analysis] ⚠️ AI服务不可用，使用模拟AB对比分析")
            return self._mock_ab_comparison(group_a_videos, group_b_videos, group_a_label, group_b_label)

        print("[AI Analysis] 准备AB对比分析数据...")
        group_a_snapshot = self._build_ab_group_snapshot(group_a_videos)
        group_b_snapshot = self._build_ab_group_snapshot(group_b_videos)
        group_a_data = self._build_ab_group_input(group_a_videos, group_a_label, group_a_snapshot)
        group_b_data = self._build_ab_group_input(group_b_videos, group_b_label, group_b_snapshot)

        prompt = AB_COMPARISON_PROMPT.format(
            group_a_label=group_a_label,
            group_b_label=group_b_label,
            group_a_data=group_a_data,
            group_b_data=group_b_data,
        )

        messages = [
            {"role": "system", "content": "你是专业的TikTok内容诊断分析师，请用中文回答。"},
            {"role": "user", "content": prompt},
        ]

        api_timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[AI Analysis] [{api_timestamp}] 发送API请求...")
        print(f"[AI Analysis] 调用AI API进行AB对比分析...")
        response = self._call_api_with_retry(
            messages=messages,
            max_retries=AI_CONFIG["max_retries"],
            temperature=0.7,
            max_tokens=AI_CONFIG["max_tokens_ab_comparison"],
        )

        if response is None:
            print("[AI Analysis] ❌ AI API AB对比分析调用失败，使用模拟分析")
            return self._mock_ab_comparison(group_a_videos, group_b_videos, group_a_label, group_b_label)

        print(f"[AI Analysis] 收到AB对比分析响应，正在解析...")
        raw_response = self._extract_response_text(response)
        result = self._parse_json_response(raw_response)
        if not result:
            print("[AI Analysis] ⚠️ AB对比分析JSON解析失败，使用模拟分析")
            return self._mock_ab_comparison(group_a_videos, group_b_videos, group_a_label, group_b_label)

        result = self._normalize_ab_comparison_result(
            result,
            group_a_videos,
            group_b_videos,
            group_a_label,
            group_b_label,
        )
        result["raw_response"] = raw_response
        end_timestamp = datetime.now().strftime("%H:%M:%S")
        elapsed = time.time() - start_time
        print(f"[AI Analysis] [{end_timestamp}] AB对比分析完成 | 总耗时: {elapsed:.1f}s")
        print(f"[AI Analysis] ✅ AB对比分析完成")
        return result

    def _build_ab_group_snapshot(self, videos: list) -> Dict[str, Any]:
        play_counts = [int(v.get("play_count", 0) or 0) for v in videos]
        engagement_rates = [
            float(self.calculate_engagement_metrics(v).get("engagement_rate", 0) or 0)
            for v in videos
        ]

        avg_play_count = sum(play_counts) / len(play_counts) if play_counts else 0
        median_play_count = median(play_counts) if play_counts else 0
        max_play_count = max(play_counts) if play_counts else 0
        avg_engagement_rate = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0

        return {
            "sample_count": len(videos),
            "avg_play_count": avg_play_count,
            "median_play_count": median_play_count,
            "max_play_count": max_play_count,
            "avg_engagement_rate": avg_engagement_rate,
        }

    def _build_ab_group_input(self, videos: list, label: str, snapshot: Dict[str, Any]) -> str:
        summary_lines = [
            f"- 组别: {label}",
            f"- 样本数: {snapshot['sample_count']}",
            f"- 平均播放量: {snapshot['avg_play_count']:.0f}",
            f"- 中位播放量: {snapshot['median_play_count']:.0f}",
            f"- 最高播放量: {snapshot['max_play_count']:.0f}",
            f"- 平均互动率: {snapshot['avg_engagement_rate']:.2f}%",
            "- 样本视频:",
        ]

        sample_lines = []
        for idx, video in enumerate(videos[:10], 1):
            description = video.get("description", video.get("title", ""))[:80] or "无描述"
            hashtags = video.get("hashtags", "") or "无标签"
            music_name = video.get("music_name", "") or "未知"
            sample_lines.append(
                f"{idx}. 描述：{description} | 播放：{int(video.get('play_count', 0) or 0):,} | "
                f"点赞：{int(video.get('like_count', 0) or 0):,} | 标签：{hashtags} | BGM：{music_name}"
            )

        if not sample_lines:
            sample_lines.append("1. 暂无样本视频")

        return "\n".join(summary_lines + sample_lines)

    def _normalize_ab_comparison_result(
        self,
        result: dict,
        group_a_videos: list,
        group_b_videos: list,
        group_a_label: str,
        group_b_label: str,
    ) -> dict:
        normalized = dict(result or {})
        group_a_snapshot = self._build_ab_group_snapshot(group_a_videos)
        group_b_snapshot = self._build_ab_group_snapshot(group_b_videos)

        if "dimension_comparison" in normalized and "dimension_comparisons" not in normalized:
            normalized["dimension_comparisons"] = normalized["dimension_comparison"]
        if "start_framework_comparison" in normalized and "start_comparison" not in normalized:
            normalized["start_comparison"] = normalized["start_framework_comparison"]
        if "actionable_script" in normalized and "script_template" not in normalized:
            normalized["script_template"] = normalized["actionable_script"]

        group_a_summary = dict(normalized.get("group_a_summary") or {})
        group_b_summary = dict(normalized.get("group_b_summary") or {})
        group_a_summary.setdefault("sample_count", group_a_snapshot["sample_count"])
        group_b_summary.setdefault("sample_count", group_b_snapshot["sample_count"])
        group_a_summary.setdefault("avg_play_count", f"{group_a_snapshot['avg_play_count']:.0f}")
        group_b_summary.setdefault("avg_play_count", f"{group_b_snapshot['avg_play_count']:.0f}")
        group_a_summary.setdefault("avg_engagement_rate", f"{group_a_snapshot['avg_engagement_rate']:.2f}%")
        group_b_summary.setdefault("avg_engagement_rate", f"{group_b_snapshot['avg_engagement_rate']:.2f}%")
        group_a_summary.setdefault("strengths", [])
        group_b_summary.setdefault("strengths", [])
        group_a_summary.setdefault("weaknesses", [])
        group_b_summary.setdefault("weaknesses", [])
        normalized["group_a_summary"] = group_a_summary
        normalized["group_b_summary"] = group_b_summary

        winner = normalized.get("winner", "")
        if winner not in {"A", "B"}:
            if group_a_snapshot["avg_play_count"] > group_b_snapshot["avg_play_count"]:
                winner = "A"
            elif group_b_snapshot["avg_play_count"] > group_a_snapshot["avg_play_count"]:
                winner = "B"
            else:
                winner = ""
        normalized["winner"] = winner

        gap_summary = dict(normalized.get("performance_gap_summary") or {})
        if not gap_summary:
            gap_summary = self._build_default_gap_summary(
                winner,
                normalized.get("dimension_comparisons", []),
                group_a_snapshot,
                group_b_snapshot,
                group_a_label,
                group_b_label,
            )
        normalized["performance_gap_summary"] = gap_summary

        if not normalized.get("winner_reason"):
            normalized["winner_reason"] = gap_summary.get("core_gap", "")

        normalized["diagnosis_summary"] = self._build_default_diagnosis_summary(
            normalized.get("diagnosis_summary", {}),
            gap_summary,
            normalized.get("root_causes", []),
            normalized.get("optimization_suggestions", []),
        )

        normalized["group_a_overview"] = self._normalize_ab_overview(
            normalized.get("group_a_overview"),
            group_a_summary,
            group_a_snapshot,
        )
        normalized["group_b_overview"] = self._normalize_ab_overview(
            normalized.get("group_b_overview"),
            group_b_summary,
            group_b_snapshot,
        )
        normalized["key_differences"] = self._normalize_key_differences(
            normalized.get("key_differences", []),
            normalized.get("dimension_comparisons", []),
        )
        normalized["root_causes"] = self._normalize_root_causes(normalized.get("root_causes", []))
        normalized["optimization_suggestions"] = self._normalize_optimization_suggestions(
            normalized.get("optimization_suggestions", [])
        )

        return normalized

    def _build_default_gap_summary(
        self,
        winner: str,
        dimension_comparisons: list,
        group_a_snapshot: Dict[str, Any],
        group_b_snapshot: Dict[str, Any],
        group_a_label: str,
        group_b_label: str,
    ) -> dict:
        if winner == "A":
            leading_group = "A"
            leading_label = group_a_label
            trailing_label = group_b_label
            lead_plays = group_a_snapshot["avg_play_count"]
            trail_plays = group_b_snapshot["avg_play_count"]
        elif winner == "B":
            leading_group = "B"
            leading_label = group_b_label
            trailing_label = group_a_label
            lead_plays = group_b_snapshot["avg_play_count"]
            trail_plays = group_a_snapshot["avg_play_count"]
        else:
            leading_group = "平衡"
            leading_label = group_a_label
            trailing_label = group_b_label
            lead_plays = group_a_snapshot["avg_play_count"]
            trail_plays = group_b_snapshot["avg_play_count"]

        major_dimensions = []
        for item in dimension_comparisons or []:
            verdict = item.get("verdict", "")
            if winner == "A" and verdict == "A优":
                major_dimensions.append(item.get("dimension", ""))
            elif winner == "B" and verdict == "B优":
                major_dimensions.append(item.get("dimension", ""))

        if winner and trail_plays > 0:
            play_ratio = lead_plays / trail_plays
            core_gap = (
                f"{leading_label} 当前整体流量更强，平均播放量约为 {trailing_label} 的 {play_ratio:.1f} 倍，"
                f"差距主要集中在 {('、'.join(major_dimensions[:2]) or '开场吸引与内容结构')}。"
            )
        elif winner:
            core_gap = f"{leading_label} 当前整体流量更强，差距主要集中在 {('、'.join(major_dimensions[:2]) or '开场吸引与内容结构')}。"
        else:
            core_gap = "两组整体流量接近，但优势分布在不同维度，建议按具体指标拆开看。"

        if winner == "A":
            recommended_direction = f"优先拆解并迁移 {group_a_label} 中被验证过的高效做法，同时保留 {group_b_label} 的差异化优势。"
        elif winner == "B":
            recommended_direction = f"优先拆解并迁移 {group_b_label} 中被验证过的高效做法，同时保留 {group_a_label} 的差异化优势。"
        else:
            recommended_direction = "不要强行照搬整组内容，而是按维度提炼更能提升流量的做法。"

        return {
            "leading_group": leading_group,
            "core_gap": core_gap,
            "metric_focus": "平均播放量、完播率相关信号、互动转化",
            "recommended_direction": recommended_direction,
        }

    def _build_default_diagnosis_summary(
        self,
        diagnosis_summary: dict,
        gap_summary: dict,
        root_causes: list,
        optimization_suggestions: list,
    ) -> dict:
        diagnosis = dict(diagnosis_summary or {})

        if not diagnosis.get("what"):
            diagnosis["what"] = gap_summary.get("core_gap", "两组在核心内容策略上存在可解释的表现差异。")

        if not diagnosis.get("why"):
            first_cause = ""
            for item in root_causes or []:
                if isinstance(item, dict):
                    first_cause = item.get("reason") or item.get("mechanism") or item.get("title") or ""
                elif item:
                    first_cause = str(item)
                if first_cause:
                    break
            diagnosis["why"] = first_cause or "差异主要来自开场吸引、内容节奏和互动设计对分发与停留的共同作用。"

        if not diagnosis.get("how"):
            first_action = ""
            for item in optimization_suggestions or []:
                if isinstance(item, dict):
                    first_action = item.get("suggestion") or ""
                elif item:
                    first_action = str(item)
                if first_action:
                    break
            diagnosis["how"] = first_action or gap_summary.get("recommended_direction", "优先迁移高表现组中最稳定有效的内容动作。")

        return diagnosis

    def _normalize_ab_overview(self, overview: Optional[dict], summary: dict, snapshot: Dict[str, Any]) -> dict:
        normalized = dict(overview or {})
        normalized.setdefault("sample_count", summary.get("sample_count", snapshot["sample_count"]))
        normalized.setdefault("avg_plays", summary.get("avg_play_count", f"{snapshot['avg_play_count']:.0f}"))
        normalized.setdefault("avg_engagement_rate", summary.get("avg_engagement_rate", f"{snapshot['avg_engagement_rate']:.2f}%"))
        normalized.setdefault("median_plays", f"{snapshot['median_play_count']:.0f}")
        normalized.setdefault("top_play_count", f"{snapshot['max_play_count']:.0f}")
        normalized.setdefault("hook_type", summary.get("dominant_hook_type", ""))
        normalized.setdefault("content_pattern", summary.get("content_pattern", ""))
        normalized.setdefault("strengths", summary.get("strengths", []))
        normalized.setdefault("weaknesses", summary.get("weaknesses", []))
        return normalized

    def _normalize_key_differences(self, key_differences: list, dimension_comparisons: list) -> list:
        normalized = []
        for item in key_differences or []:
            if isinstance(item, dict):
                normalized.append({
                    "dimension": item.get("dimension", ""),
                    "difference": item.get("difference", "") or item.get("summary", ""),
                    "impact": item.get("impact", ""),
                })
            elif item:
                normalized.append({
                    "dimension": "关键差异",
                    "difference": str(item),
                    "impact": "",
                })

        if normalized:
            return normalized

        for item in (dimension_comparisons or [])[:4]:
            normalized.append({
                "dimension": item.get("dimension", ""),
                "difference": item.get("gap_analysis", ""),
                "impact": f"当前判定：{item.get('verdict', '待判断')}",
            })
        return normalized

    def _normalize_root_causes(self, root_causes: list) -> list:
        normalized = []
        for idx, item in enumerate(root_causes or [], 1):
            if isinstance(item, dict):
                normalized.append({
                    "title": item.get("title", f"原因 {idx}"),
                    "reason": item.get("reason", item.get("title", "")),
                    "mechanism": item.get("mechanism", item.get("impact", "")),
                })
            elif item:
                normalized.append({
                    "title": f"原因 {idx}",
                    "reason": str(item),
                    "mechanism": "",
                })
        return normalized

    def _normalize_optimization_suggestions(self, suggestions: list) -> list:
        normalized = []
        for item in suggestions or []:
            if isinstance(item, dict):
                normalized.append({
                    "priority": item.get("priority", "中"),
                    "target_group": item.get("target_group", "两组"),
                    "suggestion": item.get("suggestion", ""),
                    "why_this_matters": item.get("why_this_matters", ""),
                    "expected_impact": item.get("expected_impact", ""),
                    "how_to_execute": item.get("how_to_execute", ""),
                })
            elif item:
                normalized.append({
                    "priority": "中",
                    "target_group": "两组",
                    "suggestion": str(item),
                    "why_this_matters": "",
                    "expected_impact": "",
                    "how_to_execute": "",
                })
        return normalized

    def _mock_ab_comparison(self, group_a_videos, group_b_videos, group_a_label, group_b_label):
        """API不可用时的模拟AB对比分析"""
        a_snapshot = self._build_ab_group_snapshot(group_a_videos)
        b_snapshot = self._build_ab_group_snapshot(group_b_videos)

        if a_snapshot["avg_play_count"] > b_snapshot["avg_play_count"]:
            winner = "A"
            winner_label = group_a_label
            chasing_group = "B组"
        elif b_snapshot["avg_play_count"] > a_snapshot["avg_play_count"]:
            winner = "B"
            winner_label = group_b_label
            chasing_group = "A组"
        else:
            winner = ""
            winner_label = "两组"
            chasing_group = "两组"

        diagnosis_what = (
            f"{winner_label}在整体流量上更占优，差距主要出现在开场截停、内容结构和互动设计。"
            if winner
            else "两组整体流量接近，但高低表现的差异主要体现在开场截停、内容结构和互动设计的取舍上。"
        )
        performance_core_gap = (
            f"{winner_label}当前更容易拿到分发，说明其内容设计更符合平台对停留、完播和互动的综合判断。"
            if winner
            else "两组不是简单的胜负关系，而是分别在不同流量指标上有强弱，适合按维度迁移做法。"
        )

        base_result = {
            "diagnosis_summary": {
                "what": diagnosis_what,
                "why": "更高流量的一组通常在更短时间内完成价值预告，并且更早把用户带入互动或结果预期。",
                "how": "先迁移高表现组最稳定的开场与结构动作，再做文案和互动层面的微调。",
            },
            "performance_gap_summary": {
                "leading_group": winner or "平衡",
                "core_gap": performance_core_gap,
                "metric_focus": "重点看平均播放量、前3秒截停、完播率和评论触发能力。",
                "recommended_direction": "不要把AB对比当成单条视频胜负，而是把高表现组当成策略样本库来拆动作。",
            },
            "group_a_summary": {
                "sample_count": a_snapshot["sample_count"],
                "avg_play_count": f"{a_snapshot['avg_play_count']:.0f}",
                "avg_engagement_rate": f"{a_snapshot['avg_engagement_rate']:.2f}%",
                "dominant_hook_type": "信息价值型",
                "content_pattern": "结果前置型内容结构，快速给出利益点或答案预告。",
                "strengths": [
                    "开场更直接，用户更快知道这条视频值不值得停留。",
                    "信息交付节奏更紧凑，减少了前段铺垫浪费。",
                    "CTA更明确，容易把观看转成点赞或评论。",
                ],
                "weaknesses": [
                    "情绪张力不足时，可能显得过于直给。",
                    "视觉记忆点如果不够，会让内容辨识度偏弱。",
                ],
            },
            "group_b_summary": {
                "sample_count": b_snapshot["sample_count"],
                "avg_play_count": f"{b_snapshot['avg_play_count']:.0f}",
                "avg_engagement_rate": f"{b_snapshot['avg_engagement_rate']:.2f}%",
                "dominant_hook_type": "情感共鸣型",
                "content_pattern": "故事递进型内容结构，更强调情绪铺垫和关系建立。",
                "strengths": [
                    "情绪连接更自然，容易让用户愿意继续看下去。",
                    "画面和调性更统一，品牌感更强。",
                    "评论互动更有参与感，适合沉淀深层用户反馈。",
                ],
                "weaknesses": [
                    "进入主题偏慢时，会损失前3秒截停能力。",
                    "价值点后置过深时，容易影响推荐扩散。",
                ],
            },
            "key_differences": [
                {
                    "dimension": "开场截停",
                    "difference": "高表现组更早把结果、利益点或冲突抛出来，低表现组进入主题更慢。",
                    "impact": "直接影响3秒停留和首轮分发。",
                },
                {
                    "dimension": "内容结构",
                    "difference": "高表现组更快进入价值交付，低表现组铺垫更长。",
                    "impact": "会拉开完播率和中段流失率。",
                },
                {
                    "dimension": "互动设计",
                    "difference": "高表现组会在情绪或价值节点主动引导互动，低表现组更多依赖自然发生。",
                    "impact": "影响评论量、二次分发和粉丝沉淀。",
                },
            ],
            "winner": winner,
            "winner_reason": f"{winner_label}的内容更容易在短时间内完成截停、价值预告和互动触发，所以整体流量更高。" if winner else "两组在不同维度各有优势，建议拆维度迁移而不是简单判胜负。",
            "dimension_comparison": [
                {
                    "dimension": "钩子策略",
                    "group_a_performance": "更偏结果前置和直接利益表达。",
                    "group_b_performance": "更偏悬念或情绪引入。",
                    "gap_analysis": "高流量并不只来自更强刺激，而是来自更快让用户知道“为什么要继续看”。",
                    "verdict": "A优" if winner == "A" else ("B优" if winner == "B" else "持平"),
                },
                {
                    "dimension": "内容结构",
                    "group_a_performance": "段落更短，价值交付更靠前。",
                    "group_b_performance": "铺垫更多，情绪递进更明显。",
                    "gap_analysis": "如果目标是拿更高播放，通常更短的铺垫会更有利于进入下一层分发。",
                    "verdict": "A优" if winner == "A" else ("B优" if winner == "B" else "持平"),
                },
                {
                    "dimension": "视觉风格",
                    "group_a_performance": "信息传达效率更高。",
                    "group_b_performance": "整体质感和记忆点更强。",
                    "gap_analysis": "一个偏效率，一个偏辨识度，适合结合使用。",
                    "verdict": "持平",
                },
                {
                    "dimension": "文案策略",
                    "group_a_performance": "标题更结果导向，适合抢点击。",
                    "group_b_performance": "标题更情绪导向，适合建立共鸣。",
                    "gap_analysis": "高点击不一定等于高完播，关键在标题承诺与内容兑现是否匹配。",
                    "verdict": "持平",
                },
                {
                    "dimension": "BGM策略",
                    "group_a_performance": "更强调节奏感和推进效率。",
                    "group_b_performance": "更强调氛围和情绪放大。",
                    "gap_analysis": "BGM本身不是决定性因素，但会放大结构与情绪的差异。",
                    "verdict": "持平",
                },
                {
                    "dimension": "互动引导",
                    "group_a_performance": "在价值点后主动引导互动。",
                    "group_b_performance": "更多依赖共鸣带来的自然互动。",
                    "gap_analysis": "主动设计互动节点，更容易放大评论和二次传播。",
                    "verdict": "A优" if winner == "A" else ("B优" if winner == "B" else "持平"),
                },
            ],
            "root_causes": [
                {
                    "title": "开场价值预告速度不同",
                    "reason": "高表现组更早告诉用户这条内容能带来什么，低表现组前段信息密度不足。",
                    "mechanism": "这会直接影响前3秒停留、继续观看意愿和推荐系统的首轮判断。",
                },
                {
                    "title": "价值交付位置不同",
                    "reason": "高表现组把核心信息放在更靠前的位置，低表现组存在铺垫过长的问题。",
                    "mechanism": "价值交付越晚，用户越容易中途滑走，进而拖低完播率。",
                },
                {
                    "title": "互动触发设计不同",
                    "reason": "高表现组更会在用户最容易产生反应的节点推动评论、点赞或收藏。",
                    "mechanism": "更高的互动密度会放大后续分发，帮助视频获得更长尾的流量。",
                },
            ],
            "optimization_suggestions": [
                {
                    "priority": "高",
                    "target_group": chasing_group,
                    "suggestion": "把第一句改成结果前置、痛点前置或冲突前置，让用户在3秒内知道这条内容的核心价值。",
                    "why_this_matters": "这是拉高截停率和首轮分发最直接的动作。",
                    "expected_impact": "有机会显著提升播放量和前段停留表现。",
                    "how_to_execute": "每条脚本先写一句“用户为什么要停下来看”的表达，再补叙事和背景。",
                },
                {
                    "priority": "高",
                    "target_group": chasing_group,
                    "suggestion": "把核心信息或答案前移，减少铺垫段落的长度。",
                    "why_this_matters": "更早交付价值，能降低中段流失。",
                    "expected_impact": "有助于提升完播率和整体推荐层级。",
                    "how_to_execute": "把原本第2段或第3段的价值点，压缩后挪到开头15秒内。",
                },
                {
                    "priority": "中",
                    "target_group": "两组",
                    "suggestion": "保留高表现组的结构效率，同时借用另一组更强的情绪连接方式。",
                    "why_this_matters": "效率和共鸣并不冲突，结合后更容易兼顾播放和互动。",
                    "expected_impact": "提升整体内容稳定性，减少只靠单一套路吃流量的波动。",
                    "how_to_execute": "开场用结果抓停留，中段补一个真实场景或情绪句，结尾再做互动引导。",
                },
                {
                    "priority": "中",
                    "target_group": "两组",
                    "suggestion": "为不同选题建立开场模板库，而不是每条视频都从零开始写。",
                    "why_this_matters": "固定高表现动作，能提高稳定复现率。",
                    "expected_impact": "减少脚本波动，提高团队复用效率。",
                    "how_to_execute": "按“痛点型、结果型、反常识型、故事型”各沉淀3套开场。",
                },
                {
                    "priority": "低",
                    "target_group": "两组",
                    "suggestion": "把BGM和字幕节奏作为放大器使用，而不是把它当成核心解法。",
                    "why_this_matters": "真正决定流量的通常是前3秒价值预告和结构设计。",
                    "expected_impact": "避免把精力花在边际收益更低的细节上。",
                    "how_to_execute": "先锁定脚本结构，再根据节奏选择BGM和字幕切换点。",
                },
            ],
            "start_framework_comparison": {
                "stop": {
                    "group_a": "更快展示利益点或结论。",
                    "group_b": "更偏情绪带入或悬念引入。",
                    "verdict": "A优" if winner == "A" else ("B优" if winner == "B" else "持平"),
                },
                "tension": {
                    "group_a": "依靠结果兑现推动观看。",
                    "group_b": "依靠情绪递进和故事张力推动观看。",
                    "verdict": "持平",
                },
                "authority": {
                    "group_a": "偏专业信息背书。",
                    "group_b": "偏真实经历和共鸣背书。",
                    "verdict": "持平",
                },
                "reveal": {
                    "group_a": "价值交付更靠前。",
                    "group_b": "价值交付更依赖情绪铺垫。",
                    "verdict": "A优" if winner == "A" else ("B优" if winner == "B" else "持平"),
                },
                "transfer": {
                    "group_a": "行动指令更明确。",
                    "group_b": "互动更自然但不够可控。",
                    "verdict": "A优" if winner == "A" else ("B优" if winner == "B" else "持平"),
                },
            },
            "actionable_script": "S (钩子): [先用结果、痛点或反常识句子截停用户，让人立刻知道看下去的价值]\\nT (悬念): [补一句为什么多数人会做错或忽略这一点，制造继续看的理由]\\nA (信任): [用一句真实经历、数据结果或身份背书建立可信度]\\nR (交付): [在前半段快速给出核心方法，再用一个具体场景解释怎么落地]\\nT (引导): [在价值交付后立刻引导点赞、收藏或评论，并告诉用户互动后能得到什么]",
        }

        normalized = self._normalize_ab_comparison_result(
            base_result,
            group_a_videos,
            group_b_videos,
            group_a_label,
            group_b_label,
        )
        normalized["raw_response"] = "[mock ab comparison analysis]"
        return normalized
