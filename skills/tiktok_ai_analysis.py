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

        print(f"[AI Analysis] 准备AB对比分析数据...")
        # 准备A组视频摘要
        group_a_data = "\n".join(
            [
                (
                    f"{i}. 描述：{v.get('description', v.get('title', ''))[:80]} | "
                    f"播放：{v.get('play_count', 0):,} | 点赞：{v.get('like_count', 0):,} | "
                    f"标签：{v.get('hashtags', '')} | BGM：{v.get('music_name', '')}"
                )
                for i, v in enumerate(group_a_videos[:10], 1)
            ]
        )

        # 准备B组视频摘要
        group_b_data = "\n".join(
            [
                (
                    f"{i}. 描述：{v.get('description', v.get('title', ''))[:80]} | "
                    f"播放：{v.get('play_count', 0):,} | 点赞：{v.get('like_count', 0):,} | "
                    f"标签：{v.get('hashtags', '')} | BGM：{v.get('music_name', '')}"
                )
                for i, v in enumerate(group_b_videos[:10], 1)
            ]
        )

        # 构建prompt
        prompt = AB_COMPARISON_PROMPT.format(
            group_a_label=group_a_label,
            group_b_label=group_b_label,
            group_a_data=group_a_data,
            group_b_data=group_b_data,
        )

        messages = [
            {"role": "system", "content": "你是专业的TikTok内容AB测试分析师，请用中文回答。"},
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

        # 兼容字段映射，确保 UI 能正确读取
        if "group_a_summary" in result and "group_a_overview" not in result:
            result["group_a_overview"] = {
                "avg_plays": result["group_a_summary"].get("avg_play_count", 0),
                "avg_engagement_rate": result["group_a_summary"].get("avg_engagement_rate", 0),
                "hook_type": result["group_a_summary"].get("dominant_hook_type", ""),
                "content_pattern": result["group_a_summary"].get("content_pattern", ""),
                "strengths": result["group_a_summary"].get("strengths", []),
            }
        if "group_b_summary" in result and "group_b_overview" not in result:
            result["group_b_overview"] = {
                "avg_plays": result["group_b_summary"].get("avg_play_count", 0),
                "avg_engagement_rate": result["group_b_summary"].get("avg_engagement_rate", 0),
                "hook_type": result["group_b_summary"].get("dominant_hook_type", ""),
                "content_pattern": result["group_b_summary"].get("content_pattern", ""),
                "strengths": result["group_b_summary"].get("strengths", []),
            }
        if "dimension_comparison" in result and "dimension_comparisons" not in result:
            result["dimension_comparisons"] = result["dimension_comparison"]
        if "start_framework_comparison" in result and "start_comparison" not in result:
            result["start_comparison"] = result["start_framework_comparison"]
        if "actionable_script" in result and "script_template" not in result:
            result["script_template"] = result["actionable_script"]

        result["raw_response"] = raw_response
        end_timestamp = datetime.now().strftime("%H:%M:%S")
        elapsed = time.time() - start_time
        print(f"[AI Analysis] [{end_timestamp}] AB对比分析完成 | 总耗时: {elapsed:.1f}s")
        print(f"[AI Analysis] ✅ AB对比分析完成")
        return result

    def _mock_ab_comparison(self, group_a_videos, group_b_videos, group_a_label, group_b_label):
        """API不可用时的模拟AB对比分析"""
        # 计算A组统计数据
        a_plays = [v.get("play_count", 0) for v in group_a_videos]
        a_avg_plays = sum(a_plays) / len(a_plays) if a_plays else 0
        a_engagement_rates = [self.calculate_engagement_metrics(v)["engagement_rate"] for v in group_a_videos]
        a_avg_engagement = sum(a_engagement_rates) / len(a_engagement_rates) if a_engagement_rates else 0

        # 计算B组统计数据
        b_plays = [v.get("play_count", 0) for v in group_b_videos]
        b_avg_plays = sum(b_plays) / len(b_plays) if b_plays else 0
        b_engagement_rates = [self.calculate_engagement_metrics(v)["engagement_rate"] for v in group_b_videos]
        b_avg_engagement = sum(b_engagement_rates) / len(b_engagement_rates) if b_engagement_rates else 0

        # 判定胜出方
        winner = "A" if a_avg_plays >= b_avg_plays else "B"
        winner_label = group_a_label if winner == "A" else group_b_label
        winner_reason = f"{winner_label}的平均播放量更高，整体内容策略更有效"

        return {
            "group_a_summary": {
                "avg_play_count": f"{int(a_avg_plays):,}",
                "avg_engagement_rate": f"{a_avg_engagement:.2f}%",
                "dominant_hook_type": "信息价值型",
                "content_pattern": "结果前置型内容结构，快速抓住用户注意力",
                "strengths": [
                    "开场钩子设计较为直接，能快速吸引目标受众",
                    "内容节奏紧凑，信息密度适中",
                    "BGM选择贴合内容主题，增强观看体验"
                ]
            },
            "group_b_summary": {
                "avg_play_count": f"{int(b_avg_plays):,}",
                "avg_engagement_rate": f"{b_avg_engagement:.2f}%",
                "dominant_hook_type": "情感共鸣型",
                "content_pattern": "故事叙述型内容结构，注重情感连接",
                "strengths": [
                    "情感共鸣点把握较好，用户停留时间较长",
                    "视觉呈现风格统一，品牌识别度高",
                    "互动引导设计自然，评论转化率较高"
                ]
            },
            "winner": winner,
            "winner_reason": winner_reason,
            "dimension_comparison": [
                {
                    "dimension": "钩子策略",
                    "group_a_performance": "采用结果前置型钩子，开场直接展示核心内容",
                    "group_b_performance": "采用悬念型钩子，通过提问或冲突吸引注意",
                    "gap_analysis": "A组开场更直接，B组更有悬念感，各有优势",
                    "verdict": "持平"
                },
                {
                    "dimension": "内容结构",
                    "group_a_performance": "信息密度高，节奏紧凑，适合快速消费",
                    "group_b_performance": "叙事节奏舒缓，注重情感铺垫和递进",
                    "gap_analysis": "A组适合碎片化阅读，B组适合深度观看",
                    "verdict": "A优" if a_avg_plays >= b_avg_plays else "B优"
                },
                {
                    "dimension": "视觉风格",
                    "group_a_performance": "画面简洁明了，重点突出，剪辑节奏快",
                    "group_b_performance": "画面质感较好，色调统一，视觉记忆点强",
                    "gap_analysis": "A组信息传达效率高，B组品牌调性更突出",
                    "verdict": "持平"
                },
                {
                    "dimension": "文案策略",
                    "group_a_performance": "标题直接明了，使用数字和结果导向词汇",
                    "group_b_performance": "标题富有情感，善于使用疑问句和共鸣词",
                    "gap_analysis": "A组点击转化率高，B组用户情感连接更深",
                    "verdict": "持平"
                },
                {
                    "dimension": "BGM策略",
                    "group_a_performance": "选择节奏明快的流行音乐，与内容节奏匹配",
                    "group_b_performance": "选择情感氛围音乐，强化内容情绪表达",
                    "gap_analysis": "两组BGM策略差异明显，适应不同内容风格",
                    "verdict": "持平"
                },
                {
                    "dimension": "互动引导",
                    "group_a_performance": "CTA设计直接，明确引导点赞和关注",
                    "group_b_performance": "通过情感共鸣自然引导用户评论互动",
                    "gap_analysis": "A组转化路径清晰，B组用户参与感更强",
                    "verdict": "B优"
                }
            ],
            "root_causes": [
                "内容定位差异导致受众群体不同，影响整体播放量表现",
                "开场策略的差异直接影响3秒完播率和推荐算法分发",
                "互动引导方式不同导致用户参与深度和转化效果存在差异"
            ],
            "optimization_suggestions": [
                {
                    "priority": "高",
                    "suggestion": "融合A组的结果前置开场和B组的情感共鸣设计，打造既有冲击力又有温度的开场",
                    "expected_impact": "提升3秒完播率和用户情感连接，预计播放量提升20-30%"
                },
                {
                    "priority": "高",
                    "suggestion": "优化内容节奏，在信息密度和情感铺垫之间找到平衡点",
                    "expected_impact": "提升完播率和用户满意度，增强内容传播力"
                },
                {
                    "priority": "中",
                    "suggestion": "统一视觉风格的同时保留内容多样性，建立品牌识别度",
                    "expected_impact": "增强用户记忆点，提高粉丝粘性和复访率"
                },
                {
                    "priority": "中",
                    "suggestion": "文案采用A/B测试策略，针对不同内容类型使用不同的标题风格",
                    "expected_impact": "提升整体点击率，找到最优文案策略"
                },
                {
                    "priority": "低",
                    "suggestion": "建立BGM素材库，根据内容情绪标签匹配合适的背景音乐",
                    "expected_impact": "提升内容制作效率，保证BGM与内容的契合度"
                }
            ],
            "start_framework_comparison": {
                "stop": {
                    "group_a": "直接抛出结果或核心观点，快速截停用户滑动",
                    "group_b": "通过情感共鸣点或悬念问题吸引用户停留",
                    "verdict": "持平"
                },
                "tension": {
                    "group_a": "用信息密度和节奏感维持用户注意力",
                    "group_b": "通过情感递进和故事发展制造期待感",
                    "verdict": "B优"
                },
                "authority": {
                    "group_a": "通过专业知识和数据展示建立信任",
                    "group_b": "通过真实经历和情感真诚获得认同",
                    "verdict": "持平"
                },
                "reveal": {
                    "group_a": "分步骤清晰交付核心价值，逻辑性强",
                    "group_b": "通过故事高潮自然呈现价值，感染力强",
                    "verdict": "持平"
                },
                "transfer": {
                    "group_a": "明确给出行动指令，转化路径清晰",
                    "group_b": "情感高点自然引导互动，用户参与感强",
                    "verdict": "B优"
                }
            },
            "actionable_script": "S (钩子): [结合A组的结果前置优势，直接展示核心利益点或反常识观点，同时融入B组的情感共鸣元素，让用户感到'这与我有关']\\nT (悬念): [采用B组的悬念制造技巧，暗示即将揭晓的答案或解决方案，但先铺垫情感背景或痛点场景]\\nA (信任): [融合A组的专业背书和B组的真实经历，一句话交代你的专业资质和亲身实践]\\nR (交付): [按照A组的清晰逻辑分3步交付价值，同时借鉴B组的情感表达方式，让信息传递更有温度]\\nT (引导): [结合A组的明确CTA和B组的情感引导，在情绪高点给出行动号召，如'如果你也有这样的困扰，双击屏幕让我知道'或'评论区分享你的经历']",
            "raw_response": "[mock ab comparison analysis]",
            # UI 期望的字段映射
            "group_a_overview": {
                "avg_plays": f"{int(a_avg_plays):,}",
                "avg_engagement_rate": f"{a_avg_engagement:.2f}%",
                "hook_type": "信息价值型",
                "content_pattern": "结果前置型内容结构，快速抓住用户注意力",
                "strengths": [
                    "开场钩子设计较为直接，能快速吸引目标受众",
                    "内容节奏紧凑，信息密度适中",
                    "BGM选择贴合内容主题，增强观看体验"
                ]
            },
            "group_b_overview": {
                "avg_plays": f"{int(b_avg_plays):,}",
                "avg_engagement_rate": f"{b_avg_engagement:.2f}%",
                "hook_type": "情感共鸣型",
                "content_pattern": "故事叙述型内容结构，注重情感连接",
                "strengths": [
                    "情感共鸣点把握较好，用户停留时间较长",
                    "视觉呈现风格统一，品牌识别度高",
                    "互动引导设计自然，评论转化率较高"
                ]
            },
            "dimension_comparisons": [
                {
                    "dimension": "钩子策略",
                    "group_a_performance": "采用结果前置型钩子，开场直接展示核心内容",
                    "group_b_performance": "采用悬念型钩子，通过提问或冲突吸引注意",
                    "gap_analysis": "A组开场更直接，B组更有悬念感，各有优势",
                    "verdict": "持平"
                },
                {
                    "dimension": "内容结构",
                    "group_a_performance": "信息密度高，节奏紧凑，适合快速消费",
                    "group_b_performance": "叙事节奏舒缓，注重情感铺垫和递进",
                    "gap_analysis": "A组适合碎片化阅读，B组适合深度观看",
                    "verdict": "A优" if a_avg_plays >= b_avg_plays else "B优"
                },
                {
                    "dimension": "视觉风格",
                    "group_a_performance": "画面简洁明了，重点突出，剪辑节奏快",
                    "group_b_performance": "画面质感较好，色调统一，视觉记忆点强",
                    "gap_analysis": "A组信息传达效率高，B组品牌调性更突出",
                    "verdict": "持平"
                },
                {
                    "dimension": "文案策略",
                    "group_a_performance": "标题直接明了，使用数字和结果导向词汇",
                    "group_b_performance": "标题富有情感，善于使用疑问句和共鸣词",
                    "gap_analysis": "A组点击转化率高，B组用户情感连接更深",
                    "verdict": "持平"
                },
                {
                    "dimension": "BGM策略",
                    "group_a_performance": "选择节奏明快的流行音乐，与内容节奏匹配",
                    "group_b_performance": "选择情感氛围音乐，强化内容情绪表达",
                    "gap_analysis": "两组BGM策略差异明显，适应不同内容风格",
                    "verdict": "持平"
                },
                {
                    "dimension": "互动引导",
                    "group_a_performance": "CTA设计直接，明确引导点赞和关注",
                    "group_b_performance": "通过情感共鸣自然引导用户评论互动",
                    "gap_analysis": "A组转化路径清晰，B组用户参与感更强",
                    "verdict": "B优"
                }
            ],
            "start_comparison": {
                "stop": {
                    "group_a": "直接抛出结果或核心观点，快速截停用户滑动",
                    "group_b": "通过情感共鸣点或悬念问题吸引用户停留",
                    "verdict": "持平"
                },
                "tension": {
                    "group_a": "用信息密度和节奏感维持用户注意力",
                    "group_b": "通过情感递进和故事发展制造期待感",
                    "verdict": "B优"
                },
                "authority": {
                    "group_a": "通过专业知识和数据展示建立信任",
                    "group_b": "通过真实经历和情感真诚获得认同",
                    "verdict": "持平"
                },
                "reveal": {
                    "group_a": "分步骤清晰交付核心价值，逻辑性强",
                    "group_b": "通过故事高潮自然呈现价值，感染力强",
                    "verdict": "持平"
                },
                "transfer": {
                    "group_a": "明确给出行动指令，转化路径清晰",
                    "group_b": "情感高点自然引导互动，用户参与感强",
                    "verdict": "B优"
                }
            },
            "script_template": "S (钩子): [结合A组的结果前置优势，直接展示核心利益点或反常识观点，同时融入B组的情感共鸣元素，让用户感到'这与我有关']\\nT (悬念): [采用B组的悬念制造技巧，暗示即将揭晓的答案或解决方案，但先铺垫情感背景或痛点场景]\\nA (信任): [融合A组的专业背书和B组的真实经历，一句话交代你的专业资质和亲身实践]\\nR (交付): [按照A组的清晰逻辑分3步交付价值，同时借鉴B组的情感表达方式，让信息传递更有温度]\\nT (引导): [结合A组的明确CTA和B组的情感引导，在情绪高点给出行动号召，如'如果你也有这样的困扰，双击屏幕让我知道'或'评论区分享你的经历']",
        }
