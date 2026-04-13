"""
TikTok Monitor - Skills Package
AI技能模块包，用于组织和管理各种AI分析能力

参考 ReelClaw 的设计理念，提供完整的内容生产流水线：
1. Hook Research - 钩子研究
2. Format Research - 格式研究  
3. Video Analysis - 视频分析
4. Reel Assembly - 组装指导
5. Performance Tracking - 性能追踪
6. Content Pipeline - 完整流水线
"""

from .tiktok_ai_analysis import TikTokAIAnalysisSkill
from .hook_research import HookResearchSkill
from .format_research import FormatResearchSkill
from .reel_assembly import ReelAssemblySkill
from .performance_tracker import PerformanceTrackerSkill
from .content_pipeline import TikTokContentPipeline
from .skill_registry import SkillRegistry, SkillInfo, get_registry, initialize_skills
from .prompts import (
    HOOK_ANALYSIS_PROMPT,
    BATCH_ANALYSIS_PROMPT,
    COMPETITOR_ANALYSIS_PROMPT,
    TREND_PREDICTION_PROMPT,
    HOOK_LIBRARY_TAGGING_PROMPT
)

__all__ = [
    # Core Skills
    'TikTokAIAnalysisSkill',
    'HookResearchSkill',
    'FormatResearchSkill',
    'ReelAssemblySkill',
    'PerformanceTrackerSkill',
    
    # Pipeline
    'TikTokContentPipeline',
    
    # Registry
    'SkillRegistry',
    'SkillInfo',
    'get_registry',
    'initialize_skills',
    
    # Prompts
    'HOOK_ANALYSIS_PROMPT',
    'BATCH_ANALYSIS_PROMPT',
    'COMPETITOR_ANALYSIS_PROMPT',
    'TREND_PREDICTION_PROMPT',
    'HOOK_LIBRARY_TAGGING_PROMPT'
]
