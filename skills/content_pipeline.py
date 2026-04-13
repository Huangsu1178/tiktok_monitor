"""
TikTok Monitor - Content Production Pipeline
参考 ReelClaw 的全流程自动化理念，提供从研究到发布的内容生产流水线

Pipeline 流程：
1. Hook Research - 研究并发现已验证的文本钩子
2. Format Research - 发现病毒式格式创意
3. Video Analysis - 深度分析视频流量钩子
4. Assembly Guide - 智能组装指导（脚本+结构+BGM）
5. Performance Tracking - 追踪表现并复制赢家
6. Batch Optimization - 批量优化建议
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# 导入统一配置
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DEFAULT_AI_MODEL

from .tiktok_ai_analysis import TikTokAIAnalysisSkill
from .hook_research import HookResearchSkill
from .format_research import FormatResearchSkill
from .reel_assembly import ReelAssemblySkill
from .performance_tracker import PerformanceTrackerSkill


class TikTokContentPipeline:
    """
    TikTok 内容生产流水线编排器
    
    参考 ReelClaw 的设计理念，将多个 AI Skill 组合成完整的内容生产工作流
    """

    def __init__(self, api_key: str = "", api_base: str = "", model: str = DEFAULT_AI_MODEL):
        """
        初始化内容生产流水线
        
        Args:
            api_key: OpenAI API密钥
            api_base: API基础URL
            model: 模型名称
        """
        # 初始化所有子 Skills
        self.ai_analysis = TikTokAIAnalysisSkill(api_key, api_base, model)
        self.hook_research = HookResearchSkill(api_key, api_base, model)
        self.format_research = FormatResearchSkill(api_key, api_base, model)
        self.reel_assembly = ReelAssemblySkill()
        self.performance_tracker = PerformanceTrackerSkill()
        
        self.pipeline_history = []

    def is_available(self) -> bool:
        """检查流水线是否可用"""
        return self.ai_analysis.is_available()

    def update_config(self, api_key: str, api_base: str = "", model: str = ""):
        """更新所有 Skills 的 API 配置"""
        self.ai_analysis.update_config(api_key, api_base, model)
        self.hook_research.update_config(api_key, api_base, model)
        self.format_research.update_config(api_key, api_base, model)

    # ==================== 核心 Pipeline 方法 ====================

    def full_content_pipeline(
        self,
        niche: str,
        target_audience: str = "",
        product_type: str = "",
        video_count: int = 5
    ) -> Dict[str, Any]:
        """
        完整内容生产流水线（参考 ReelClaw 全流程）
        
        Args:
            niche: 内容细分领域（如：fitness, tech, beauty）
            target_audience: 目标受众描述
            product_type: 产品类型（如：app, course, physical product）
            video_count: 生成视频创意数量
            
        Returns:
            完整的内容生产方案
        """
        print(f"[Pipeline] 启动完整内容生产流水线 - 领域: {niche}")
        
        pipeline_result = {
            "niche": niche,
            "target_audience": target_audience,
            "product_type": product_type,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # Step 1: 钩子研究
        print("[Pipeline] Step 1/5: 研究已验证的钩子...")
        hook_research = self.hook_research.research_hooks(niche, video_count * 3)
        pipeline_result["hook_research"] = hook_research
        
        # Step 2: 格式研究
        print("[Pipeline] Step 2/5: 研究病毒式格式...")
        format_research = self.format_research.research_formats(niche)
        pipeline_result["format_research"] = format_research
        
        # Step 3: 生成视频创意（组合钩子+格式）
        print("[Pipeline] Step 3/5: 生成视频创意...")
        video_concepts = self._generate_video_concepts(
            hook_research,
            format_research,
            video_count,
            target_audience,
            product_type
        )
        pipeline_result["video_concepts"] = video_concepts
        
        # Step 4: 为每个创意生成组装指导
        print("[Pipeline] Step 4/5: 生成组装指导...")
        assembly_guides = []
        for concept in video_concepts:
            guide = self.reel_assembly.generate_assembly_guide(concept)
            assembly_guides.append(guide)
        pipeline_result["assembly_guides"] = assembly_guides
        
        # Step 5: 生成执行计划
        print("[Pipeline] Step 5/5: 生成执行计划...")
        execution_plan = self._generate_execution_plan(
            video_concepts,
            assembly_guides,
            niche
        )
        pipeline_result["execution_plan"] = execution_plan
        
        # 记录历史
        self.pipeline_history.append(pipeline_result)
        
        print(f"[Pipeline] 流水线完成！生成 {video_count} 个视频创意")
        return pipeline_result

    def analyze_and_optimize(
        self,
        videos: List[dict],
        username: str = ""
    ) -> Dict[str, Any]:
        """
        分析现有视频并生成优化建议
        
        Args:
            videos: 视频数据列表
            username: 博主用户名
            
        Returns:
            分析和优化结果
        """
        print(f"[Pipeline] 分析 {len(videos)} 个视频...")
        
        # 批量分析
        batch_analysis = self.ai_analysis.analyze_batch_videos(videos, username)
        
        # 趋势分析
        trends = self.ai_analysis.analyze_trends(videos)
        
        # 性能追踪
        performance = self.performance_tracker.track_performance(videos)
        
        # 识别赢家
        winners = self.performance_tracker.identify_winners(videos, top_n=3)
        
        # 生成优化建议
        optimization = self._generate_optimization_suggestions(
            batch_analysis,
            trends,
            performance,
            winners
        )
        
        return {
            "batch_analysis": batch_analysis,
            "trends": trends,
            "performance": performance,
            "winners": winners,
            "optimization": optimization,
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def replicate_winners(
        self,
        winner_videos: List[dict],
        niche: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        复制赢家视频模式（参考 ReelClaw 的 "double down on winners"）
        
        Args:
            winner_videos: 表现优异的视频列表
            niche: 内容领域
            count: 生成新创意数量
            
        Returns:
            新的视频创意列表
        """
        print(f"[Pipeline] 基于 {len(winner_videos)} 个赢家视频生成 {count} 个新创意...")
        
        # 分析赢家模式
        winner_patterns = self.performance_tracker.analyze_winner_patterns(winner_videos)
        
        # 研究相关钩子
        hook_research = self.hook_research.research_hooks(niche, count * 2)
        
        # 生成新创意
        new_concepts = []
        for i in range(count):
            # 组合赢家元素 + 新钩子
            concept = self._create_replica_concept(
                winner_patterns,
                hook_research,
                i
            )
            new_concepts.append(concept)
        
        return new_concepts

    # ==================== 内部辅助方法 ====================

    def _generate_video_concepts(
        self,
        hook_research: dict,
        format_research: dict,
        count: int,
        target_audience: str,
        product_type: str
    ) -> List[Dict[str, Any]]:
        """生成视频创意"""
        hooks = hook_research.get("hooks", [])[:count * 2]
        formats = format_research.get("formats", [])[:count]
        
        concepts = []
        for i in range(count):
            hook = hooks[i % len(hooks)] if hooks else {}
            fmt = formats[i % len(formats)] if formats else {}
            
            concept = {
                "concept_id": f"concept_{i+1}",
                "hook": hook,
                "format": fmt,
                "target_audience": target_audience,
                "product_type": product_type,
                "estimated_duration": 15,  # ReelClaw 规则：15秒 max
                "priority": "high" if i < 3 else "medium",
            }
            concepts.append(concept)
        
        return concepts

    def _generate_execution_plan(
        self,
        concepts: List[dict],
        guides: List[dict],
        niche: str
    ) -> Dict[str, Any]:
        """生成执行计划"""
        return {
            "total_videos": len(concepts),
            "estimated_production_time": f"{len(concepts) * 2}小时",
            "posting_schedule": self._suggest_posting_schedule(len(concepts)),
            "production_checklist": [
                "✓ 准备素材（产品演示/使用场景）",
                "✓ 录制或购买 UGC 反应钩子",
                "✓ 选择热门 BGM",
                "✓ 按组装指导剪辑视频",
                "✓ 添加文字覆盖（注意 Green Zone）",
                "✓ 检查平台安全区域",
                "✓ 撰写描述和标签",
                "✓ 按计划发布",
            ],
            "key_metrics_to_track": [
                "播放量（前24小时）",
                "完播率",
                "互动率（点赞+评论+分享）/播放量",
                "分享率",
                "粉丝增长",
            ],
        }

    def _suggest_posting_schedule(self, video_count: int) -> List[Dict[str, str]]:
        """建议发布时间表"""
        # 建议间隔 10-15 分钟发布（参考 ReelClaw）
        schedule = []
        base_hour = 18  # 晚上6点开始
        base_minute = 0
        
        for i in range(video_count):
            hour = base_hour + (base_minute + i * 10) // 60
            minute = (base_minute + i * 10) % 60
            schedule.append({
                "video": f"Video #{i+1}",
                "time": f"{hour:02d}:{minute:02d}",
                "platform": "TikTok + Instagram",
            })
        
        return schedule

    def _generate_optimization_suggestions(
        self,
        batch_analysis: dict,
        trends: dict,
        performance: dict,
        winners: list
    ) -> Dict[str, Any]:
        """生成优化建议"""
        suggestions = []
        
        # 基于批量分析的建议
        if batch_analysis and "content_recommendations" in batch_analysis:
            suggestions.append({
                "type": "content_strategy",
                "source": "batch_analysis",
                "recommendations": batch_analysis["content_recommendations"],
            })
        
        # 基于趋势的建议
        if trends:
            suggestions.append({
                "type": "trend_optimization",
                "source": "trend_analysis",
                "recommendations": {
                    "top_hashtags": trends.get("top_hashtags", []),
                    "top_bgms": trends.get("top_bgms", []),
                    "optimal_duration": trends.get("duration_analysis", {}).get("avg_duration", 15),
                },
            })
        
        # 基于赢家的建议
        if winners:
            suggestions.append({
                "type": "winner_replication",
                "source": "performance_tracking",
                "winners_count": len(winners),
                "recommendation": "复制这些赢家视频的模式和元素",
            })
        
        return {
            "suggestions": suggestions,
            "priority_actions": [
                "立即复制 top 3 赢家视频的模式",
                "使用分析出的高频标签组合",
                "采用平均时长最优的视频长度",
                "在目标受众活跃时段发布",
            ],
        }

    def _create_replica_concept(
        self,
        winner_patterns: dict,
        hook_research: dict,
        index: int
    ) -> Dict[str, Any]:
        """创建复制赢家的新概念"""
        hooks = hook_research.get("hooks", [])
        hook = hooks[index % len(hooks)] if hooks else {}
        
        return {
            "concept_id": f"replica_{index+1}",
            "based_on_winners": True,
            "winner_patterns": winner_patterns,
            "new_hook": hook,
            "replication_strategy": {
                "keep": winner_patterns.get("common_elements", []),
                "change": ["hook_text", "visual_style", "bgm"],
                "test": ["posting_time", "caption_style"],
            },
            "estimated_duration": 15,
            "priority": "high",
        }
