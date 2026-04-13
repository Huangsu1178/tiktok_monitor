"""
TikTok Monitor - AI Analyzer Module
基于大模型的TikTok视频流量钩子分析模块（已迁移至skills模块）

此模块保留作为向后兼容，新功能请使用 skills.TikTokAIAnalysisSkill
"""
import warnings
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 导入新的skill模块
from skills.tiktok_ai_analysis import TikTokAIAnalysisSkill
from config import DEFAULT_AI_MODEL

# 导出所有公共接口
__all__ = ['AIAnalyzer']


class AIAnalyzer(TikTokAIAnalysisSkill):
    """AI分析器 - 继承自TikTokAIAnalysisSkill，保持向后兼容"""
    
    def __init__(self, api_key: str = "", api_base: str = "", model: str = DEFAULT_AI_MODEL):
        warnings.warn(
            "AIAnalyzer 已迁移至 skills.TikTokAIAnalysisSkill，请更新导入路径",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(api_key, api_base, model)
    
    # 保留旧方法名以保持向后兼容
    def analyze_video(self, video: dict, username: str = ""):
        """向后兼容：调用新的analyze_single_video方法"""
        return self.analyze_single_video(video, username)
    
    def analyze_batch(self, videos: list, username: str = ""):
        """向后兼容：调用新的analyze_batch_videos方法"""
        return self.analyze_batch_videos(videos, username)


