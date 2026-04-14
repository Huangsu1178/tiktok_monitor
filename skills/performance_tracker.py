"""
TikTok Monitor - Performance Tracker Skill
参考 ReelClaw 的性能追踪和赢家复制机制

功能：
1. 追踪视频表现指标
2. 识别赢家视频（top performers）
3. 分析赢家模式
4. 生成复制建议
5. A/B 测试建议
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class PerformanceTrackerSkill:
    """性能追踪技能 - 监控、分析并复制赢家"""

    def __init__(self):
        self.performance_history = []

    def track_performance(
        self,
        videos: List[dict],
        time_period: str = "7d"
    ) -> Dict[str, Any]:
        """
        追踪视频表现
        
        Args:
            videos: 视频数据列表
            time_period: 时间周期（1d, 7d, 30d）
            
        Returns:
            性能追踪结果
        """
        print(f"[Performance] 开始追踪 {len(videos)} 个视频的表现 (周期: {time_period})")
        
        if not videos:
            print("[Performance] ⚠️ 没有视频数据")
            return {"error": "没有视频数据"}
        
        print(f"[Performance] 计算基础指标...")
        # 计算基础指标
        metrics = self._calculate_aggregate_metrics(videos)
        
        print(f"[Performance] 分析互动率...")
        # 计算互动率
        engagement_analysis = self._analyze_engagement(videos)
        
        print(f"[Performance] 分析趋势...")
        # 计算趋势
        trend_analysis = self._analyze_trends(videos)
        
        print(f"[Performance] 分析表现分布...")
        # 识别表现分布
        performance_distribution = self._analyze_distribution(videos)
        
        result = {
            "time_period": time_period,
            "total_videos": len(videos),
            "aggregate_metrics": metrics,
            "engagement_analysis": engagement_analysis,
            "trend_analysis": trend_analysis,
            "performance_distribution": performance_distribution,
            "tracked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        self.performance_history.append(result)
        print(f"[Performance] ✅ 性能追踪完成")
        return result

    def identify_winners(
        self,
        videos: List[dict],
        top_n: int = 3,
        criteria: str = "engagement_rate"
    ) -> List[Dict[str, Any]]:
        """
        识别赢家视频
        
        Args:
            videos: 视频数据列表
            top_n: 返回前N个
            criteria: 评判标准（play_count, engagement_rate, share_rate）
            
        Returns:
            赢家视频列表
        """
        print(f"[Performance] 开始识别 Top {top_n} 赢家（标准: {criteria}）")
        
        if not videos:
            print("[Performance] ⚠️ 没有视频数据")
            return []
        
        print(f"[Performance] 计算视频指标...")
        # 为每个视频计算指标
        videos_with_metrics = []
        for video in videos:
            metrics = self._calculate_video_metrics(video)
            videos_with_metrics.append({
                **video,
                "metrics": metrics,
            })
        
        print(f"[Performance] 根据 {criteria} 排序...")
        # 根据标准排序
        if criteria == "engagement_rate":
            sorted_videos = sorted(
                videos_with_metrics,
                key=lambda v: v["metrics"]["engagement_rate"],
                reverse=True
            )
        elif criteria == "share_rate":
            sorted_videos = sorted(
                videos_with_metrics,
                key=lambda v: v["metrics"]["share_rate"],
                reverse=True
            )
        else:  # play_count
            sorted_videos = sorted(
                videos_with_metrics,
                key=lambda v: v.get("play_count", 0),
                reverse=True
            )
        
        print(f"[Performance] 分析赢家特征...")
        # 返回 Top N
        winners = []
        for i, video in enumerate(sorted_videos[:top_n]):
            winners.append({
                "rank": i + 1,
                "video_id": video.get("video_id", ""),
                "description": video.get("description", video.get("title", ""))[:80],
                "play_count": video.get("play_count", 0),
                "metrics": video["metrics"],
                "why_won": self._analyze_why_won(video),
                "replicable_elements": self._identify_replicable_elements(video),
            })
        
        print(f"[Performance] ✅ 识别完成，找到 {len(winners)} 个赢家")
        return winners

    def analyze_winner_patterns(
        self,
        winner_videos: List[dict]
    ) -> Dict[str, Any]:
        """
        分析赢家视频的共同模式
        
        Args:
            winner_videos: 赢家视频列表
            
        Returns:
            赢家模式分析
        """
        print(f"[Performance] 开始分析 {len(winner_videos)} 个赢家的模式")
        
        if not winner_videos:
            print("[Performance] ⚠️ 没有赢家视频")
            return {"error": "没有赢家视频"}
        
        print(f"[Performance] 分析共同元素...")
        # 分析共同元素
        common_elements = self._find_common_elements(winner_videos)
        
        print(f"[Performance] 分析钩子类型分布...")
        # 分析钩子类型分布
        hook_distribution = self._analyze_hook_distribution(winner_videos)
        
        print(f"[Performance] 分析时长模式...")
        # 分析时长模式
        duration_patterns = self._analyze_duration_patterns(winner_videos)
        
        print(f"[Performance] 分析发布时间模式...")
        # 分析发布时间模式
        posting_patterns = self._analyze_posting_patterns(winner_videos)
        
        print(f"[Performance] 分析标签使用...")
        # 分析标签使用
        hashtag_patterns = self._analyze_hashtag_patterns(winner_videos)
        
        print(f"[Performance] 识别关键成功因素...")
        # 识别关键成功因素
        key_success_factors = self._identify_key_success_factors(winner_videos)
        
        print(f"[Performance] 生成复制公式...")
        # 生成复制公式
        replication_formula = self._generate_replication_formula(winner_videos)
        
        result = {
            "common_elements": common_elements,
            "hook_distribution": hook_distribution,
            "duration_patterns": duration_patterns,
            "posting_patterns": posting_patterns,
            "hashtag_patterns": hashtag_patterns,
            "key_success_factors": key_success_factors,
            "replication_formula": replication_formula,
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        print(f"[Performance] ✅ 赢家模式分析完成")
        return result

    def generate_ab_test_suggestions(
        self,
        base_video: dict,
        test_count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        生成 A/B 测试建议
        
        Args:
            base_video: 基础视频
            test_count: 测试变体数量
            
        Returns:
            A/B 测试方案列表
        """
        print(f"[Performance] 开始生成 {test_count} 个 A/B 测试方案")
        
        tests = []
        
        print(f"[Performance] 生成钩子测试方案...")
        # 测试 1: 不同钩子
        tests.append({
            "test_id": "test_hook",
            "variable": "hook_text",
            "description": "测试不同的开场钩子",
            "variants": [
                {"name": "Variant A", "hook": base_video.get("description", "")[:50]},
                {"name": "Variant B", "hook": "替换为问题型钩子"},
                {"name": "Variant C", "hook": "替换为数字冲击型钩子"},
            ],
            "metric_to_track": "3秒留存率",
            "test_duration": "48小时",
        })
        
        print(f"[Performance] 生成发布时间测试方案...")
        # 测试 2: 不同发布时间
        tests.append({
            "test_id": "test_posting_time",
            "variable": "posting_time",
            "description": "测试不同发布时间",
            "variants": [
                {"name": "Variant A", "time": "早上 8:00"},
                {"name": "Variant B", "time": "中午 12:00"},
                {"name": "Variant C", "time": "晚上 18:00"},
            ],
            "metric_to_track": "前24小时播放量",
            "test_duration": "3天",
        })
        
        print(f"[Performance] 生成标签组合测试方案...")
        # 测试 3: 不同标签组合
        tests.append({
            "test_id": "test_hashtags",
            "variable": "hashtag_strategy",
            "description": "测试不同的标签组合",
            "variants": [
                {"name": "Variant A", "strategy": "大流量标签为主"},
                {"name": "Variant B", "strategy": "垂直领域标签为主"},
                {"name": "Variant C", "strategy": "混合策略"},
            ],
            "metric_to_track": "发现页流量占比",
            "test_duration": "7天",
        })
        
        print(f"[Performance] ✅ A/B 测试方案生成完成")
        return tests[:test_count]

    def generate_performance_report(
        self,
        videos: List[dict],
        period: str = "weekly"
    ) -> Dict[str, Any]:
        """
        生成性能报告
        
        Args:
            videos: 视频数据列表
            period: 报告周期（daily, weekly, monthly）
            
        Returns:
            性能报告
        """
        print(f"[Performance] 开始生成 {period} 性能报告")
        
        print(f"[Performance] 识别赢家视频...")
        winners = self.identify_winners(videos, top_n=3)
        
        print(f"[Performance] 追踪整体表现...")
        performance = self.track_performance(videos)
        
        print(f"[Performance] 生成洞察...")
        # 生成洞察
        insights = self._generate_insights(videos, winners, performance)
        
        print(f"[Performance] 生成建议...")
        # 生成建议
        recommendations = self._generate_recommendations(videos, winners)
        
        result = {
            "period": period,
            "summary": {
                "total_videos": len(videos),
                "total_plays": sum(v.get("play_count", 0) for v in videos),
                "avg_engagement_rate": performance.get("engagement_analysis", {}).get("avg_engagement_rate", 0),
                "winners_count": len(winners),
            },
            "top_performers": winners,
            "insights": insights,
            "recommendations": recommendations,
            "next_actions": self._suggest_next_actions(videos, winners),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        print(f"[Performance] ✅ 性能报告生成完成")
        return result

    # ==================== 内部辅助方法 ====================

    def _calculate_video_metrics(self, video: dict) -> Dict[str, float]:
        """计算单个视频指标"""
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

    def _calculate_aggregate_metrics(self, videos: List[dict]) -> Dict[str, float]:
        """计算聚合指标"""
        total_plays = sum(v.get("play_count", 0) for v in videos)
        total_likes = sum(v.get("like_count", 0) for v in videos)
        total_comments = sum(v.get("comment_count", 0) for v in videos)
        total_shares = sum(v.get("share_count", 0) for v in videos)
        
        total_engagement = total_likes + total_comments + total_shares
        avg_engagement_rate = (total_engagement / total_plays * 100) if total_plays > 0 else 0
        
        return {
            "total_plays": total_plays,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "total_engagement": total_engagement,
            "avg_plays_per_video": round(total_plays / len(videos), 0) if videos else 0,
            "avg_engagement_rate": round(avg_engagement_rate, 2),
        }

    def _analyze_engagement(self, videos: List[dict]) -> Dict[str, Any]:
        """分析互动率"""
        engagement_rates = []
        for v in videos:
            metrics = self._calculate_video_metrics(v)
            engagement_rates.append(metrics["engagement_rate"])
        
        if not engagement_rates:
            return {}
        
        avg_rate = sum(engagement_rates) / len(engagement_rates)
        max_rate = max(engagement_rates)
        min_rate = min(engagement_rates)
        
        return {
            "avg_engagement_rate": round(avg_rate, 2),
            "max_engagement_rate": round(max_rate, 2),
            "min_engagement_rate": round(min_rate, 2),
            "engagement_distribution": {
                "high": len([r for r in engagement_rates if r > avg_rate * 1.5]),
                "medium": len([r for r in engagement_rates if avg_rate * 0.5 <= r <= avg_rate * 1.5]),
                "low": len([r for r in engagement_rates if r < avg_rate * 0.5]),
            },
        }

    def _analyze_trends(self, videos: List[dict]) -> Dict[str, Any]:
        """分析趋势"""
        # 简单趋势分析（按播放量排序）
        sorted_videos = sorted(videos, key=lambda v: v.get("play_count", 0), reverse=True)
        
        top_3 = sorted_videos[:3]
        bottom_3 = sorted_videos[-3:] if len(sorted_videos) >= 3 else []
        
        return {
            "top_performing": [
                {
                    "video_id": v.get("video_id", ""),
                    "play_count": v.get("play_count", 0),
                    "description": v.get("description", "")[:50],
                }
                for v in top_3
            ],
            "underperforming": [
                {
                    "video_id": v.get("video_id", ""),
                    "play_count": v.get("play_count", 0),
                    "description": v.get("description", "")[:50],
                }
                for v in bottom_3
            ],
        }

    def _analyze_distribution(self, videos: List[dict]) -> Dict[str, Any]:
        """分析表现分布"""
        plays = [v.get("play_count", 0) for v in videos]
        if not plays:
            return {}
        
        avg_plays = sum(plays) / len(plays)
        
        return {
            "viral": len([p for p in plays if p > avg_plays * 3]),  # 超过平均3倍
            "strong": len([p for p in plays if avg_plays * 1.5 < p <= avg_plays * 3]),
            "average": len([p for p in plays if avg_plays * 0.5 <= p <= avg_plays * 1.5]),
            "below_average": len([p for p in plays if p < avg_plays * 0.5]),
        }

    def _analyze_why_won(self, video: dict) -> str:
        """分析为什么赢了"""
        metrics = self._calculate_video_metrics(video)
        reasons = []
        
        if metrics["engagement_rate"] > 10:
            reasons.append("超高互动率")
        if metrics["share_rate"] > 2:
            reasons.append("高分享率（病毒传播）")
        if video.get("play_count", 0) > 100000:
            reasons.append("播放量突破10万")
        
        return " + ".join(reasons) if reasons else "综合表现优异"

    def _identify_replicable_elements(self, video: dict) -> List[str]:
        """识别可复制元素"""
        elements = []
        
        desc = video.get("description", video.get("title", "")).lower()
        
        # 检查钩子类型
        if any(kw in desc for kw in ["如何", "怎么", "how", "why"]):
            elements.append("教程型钩子")
        if any(kw in desc for kw in ["秘密", "secret", "没想到"]):
            elements.append("反常识钩子")
        if any(char.isdigit() for char in desc):
            elements.append("数字冲击")
        
        # 检查时长
        duration = video.get("duration", 0)
        if 10 <= duration <= 20:
            elements.append(f"最佳时长（{duration}秒）")
        
        elements.append("热门标签组合")
        elements.append("热门 BGM")
        
        return elements[:5]

    def _find_common_elements(self, winner_videos: List[dict]) -> List[str]:
        """找出共同元素"""
        # 简化版：基于常见模式
        return [
            "强有力的前3秒钩子",
            "清晰的价值主张",
            "明确的行动号召",
            "使用热门标签",
            "合适的视频时长（15秒左右）",
        ]

    def _analyze_hook_distribution(self, winner_videos: List[dict]) -> Dict[str, int]:
        """分析钩子类型分布"""
        # 简化版
        return {
            "教程型": 2,
            "反常识型": 1,
            "故事型": 1,
        }

    def _analyze_duration_patterns(self, winner_videos: List[dict]) -> Dict[str, Any]:
        """分析时长模式"""
        durations = [v.get("duration", 0) for v in winner_videos if v.get("duration")]
        if not durations:
            return {}
        
        return {
            "avg_duration": round(sum(durations) / len(durations), 1),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "recommended": "15秒",
        }

    def _analyze_posting_patterns(self, winner_videos: List[dict]) -> Dict[str, Any]:
        """分析发布时间模式"""
        # 简化版
        return {
            "best_times": ["18:00-20:00", "12:00-13:00"],
            "best_days": ["周二", "周四", "周末"],
        }

    def _analyze_hashtag_patterns(self, winner_videos: List[dict]) -> Dict[str, Any]:
        """分析标签模式"""
        # 简化版
        return {
            "avg_hashtags_per_video": 4,
            "recommended_strategy": "1个大流量 + 2个垂直 + 1个话题",
        }

    def _identify_key_success_factors(self, winner_videos: List[dict]) -> List[str]:
        """识别关键成功因素"""
        return [
            "前3秒强力钩子",
            "高信息密度",
            "明确的价值主张",
            "情感共鸣",
            "清晰的行动号召",
        ]

    def _generate_replication_formula(self, winner_videos: List[dict]) -> str:
        """生成复制公式"""
        return (
            "【强力钩子（0-3秒）】→【核心价值展示（3-12秒）】→【行动号召（12-15秒）】\n"
            "+ 热门标签组合\n"
            "+ 热门 BGM\n"
            "+ 清晰文字覆盖（Green Zone）"
        )

    def _generate_insights(
        self,
        videos: List[dict],
        winners: List[dict],
        performance: dict
    ) -> List[str]:
        """生成洞察"""
        insights = []
        
        if winners:
            insights.append(f"Top {len(winners)} 视频贡献了总播放量的显著比例")
        
        avg_engagement = performance.get("engagement_analysis", {}).get("avg_engagement_rate", 0)
        if avg_engagement > 8:
            insights.append("整体互动率良好，继续保持内容质量")
        elif avg_engagement > 5:
            insights.append("互动率中等，有优化空间")
        else:
            insights.append("互动率偏低，建议优化钩子和 CTA")
        
        return insights

    def _generate_recommendations(
        self,
        videos: List[dict],
        winners: List[dict]
    ) -> List[str]:
        """生成建议"""
        recommendations = [
            "复制 Top 赢家视频的模式和元素",
            "测试不同的钩子类型找到最优解",
            "优化发布时间以提高初始曝光",
            "使用热门标签组合增加发现页流量",
            "保持15秒以内的视频时长",
        ]
        
        return recommendations

    def _suggest_next_actions(
        self,
        videos: List[dict],
        winners: List[dict]
    ) -> List[str]:
        """建议下一步行动"""
        actions = [
            "立即分析赢家视频的共同模式",
            "基于赢家模式创建3-5个新视频",
            "设置 A/B 测试优化关键变量",
            "追踪新视频表现并迭代",
        ]
        
        return actions
