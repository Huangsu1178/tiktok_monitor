"""
TikTok Monitor - Skill Registry
统一的 Skill 注册和管理系统

功能：
1. 集中管理所有 Skills
2. 提供 Skill 发现和查询
3. 统一配置管理
4. Skill 执行编排
"""

import os
import sys
from typing import Dict, Any, List, Optional, Type
from datetime import datetime

# 导入统一配置
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DEFAULT_AI_MODEL

from .tiktok_ai_analysis import TikTokAIAnalysisSkill
from .hook_research import HookResearchSkill
from .format_research import FormatResearchSkill
from .reel_assembly import ReelAssemblySkill
from .performance_tracker import PerformanceTrackerSkill
from .content_pipeline import TikTokContentPipeline


class SkillInfo:
    """Skill 信息描述"""
    
    def __init__(
        self,
        skill_id: str,
        name: str,
        description: str,
        category: str,
        requires_api: bool = False,
        tags: List[str] = None
    ):
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.category = category
        self.requires_api = requires_api
        self.tags = tags or []


class SkillRegistry:
    """
    Skill 注册表 - 管理和编排所有 Skills
    
    参考 ReelClaw 的技能系统设计：
    - 模块化：每个 skill 独立可测试
    - 可组合：skills 可以组合成 pipeline
    - 可发现：统一的注册和查询机制
    """
    
    def __init__(self):
        self.skills = {}
        self.skill_instances = {}
        self._register_builtin_skills()
    
    def _register_builtin_skills(self):
        """注册内置 Skills"""
        
        # 1. AI Analysis Skill
        self.register_skill(
            SkillInfo(
                skill_id="ai_analysis",
                name="AI 视频分析",
                description="深度分析 TikTok 视频的流量钩子（8维度分析），支持 AB 对比分析",
                category="analysis",
                requires_api=True,
                tags=["视频分析", "钩子识别", "AI", "ab_comparison"]
            ),
            TikTokAIAnalysisSkill
        )
        
        # 2. Hook Research Skill
        self.register_skill(
            SkillInfo(
                skill_id="hook_research",
                name="钩子研究",
                description="发现和验证高转化文本钩子（参考 ReelClaw）",
                category="research",
                requires_api=True,
                tags=["钩子", "研究", "文案"]
            ),
            HookResearchSkill
        )
        
        # 3. Format Research Skill
        self.register_skill(
            SkillInfo(
                skill_id="format_research",
                name="格式研究",
                description="发现病毒式视频格式创意（参考 ReelClaw）",
                category="research",
                requires_api=True,
                tags=["格式", "趋势", "创意"]
            ),
            FormatResearchSkill
        )
        
        # 4. Reel Assembly Skill
        self.register_skill(
            SkillInfo(
                skill_id="reel_assembly",
                name="视频组装指导",
                description="生成详细的视频制作指导（参考 ReelClaw FFmpeg 组装）",
                category="production",
                requires_api=False,
                tags=["组装", "制作", "FFmpeg"]
            ),
            ReelAssemblySkill
        )
        
        # 5. Performance Tracker Skill
        self.register_skill(
            SkillInfo(
                skill_id="performance_tracker",
                name="性能追踪",
                description="追踪表现、识别赢家、复制成功模式（参考 ReelClaw）",
                category="analytics",
                requires_api=False,
                tags=["性能", "追踪", "赢家复制"]
            ),
            PerformanceTrackerSkill
        )
        
        # 6. Content Pipeline (组合 Skill)
        self.register_skill(
            SkillInfo(
                skill_id="content_pipeline",
                name="内容生产流水线",
                description="完整的从研究到制作的内容生产流程（参考 ReelClaw 全流程）",
                category="pipeline",
                requires_api=True,
                tags=["流水线", "全流程", "自动化"]
            ),
            TikTokContentPipeline
        )
    
    def register_skill(
        self,
        skill_info: SkillInfo,
        skill_class: Type
    ):
        """
        注册 Skill
        
        Args:
            skill_info: Skill 信息
            skill_class: Skill 类
        """
        self.skills[skill_info.skill_id] = {
            "info": skill_info,
            "class": skill_class,
        }
        print(f"[Registry] 注册 Skill: {skill_info.name} ({skill_info.skill_id})")
    
    def get_skill_instance(
        self,
        skill_id: str,
        api_key: str = "",
        api_base: str = "",
        model: str = DEFAULT_AI_MODEL
    ) -> Any:
        """
        获取 Skill 实例
        
        Args:
            skill_id: Skill ID
            api_key: API 密钥
            api_base: API 基础 URL
            model: 模型名称
            
        Returns:
            Skill 实例
        """
        if skill_id in self.skill_instances:
            return self.skill_instances[skill_id]
        
        if skill_id not in self.skills:
            raise ValueError(f"Skill 未找到: {skill_id}")
        
        skill_class = self.skills[skill_id]["class"]
        
        # 实例化
        if self.skills[skill_id]["info"].requires_api:
            instance = skill_class(api_key, api_base, model)
        else:
            instance = skill_class()
        
        self.skill_instances[skill_id] = instance
        return instance
    
    def get_skill_info(self, skill_id: str) -> Optional[SkillInfo]:
        """获取 Skill 信息"""
        if skill_id in self.skills:
            return self.skills[skill_id]["info"]
        return None
    
    def list_skills(self, category: str = None) -> List[SkillInfo]:
        """
        列出所有 Skills
        
        Args:
            category: 按分类过滤
            
        Returns:
            Skill 信息列表
        """
        skills = [s["info"] for s in self.skills.values()]
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        return skills
    
    def search_skills(self, keyword: str) -> List[SkillInfo]:
        """
        搜索 Skills
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的 Skill 列表
        """
        results = []
        keyword_lower = keyword.lower()
        
        for skill in self.skills.values():
            info = skill["info"]
            if (keyword_lower in info.name.lower() or
                keyword_lower in info.description.lower() or
                any(keyword_lower in tag.lower() for tag in info.tags)):
                results.append(info)
        
        return results
    
    def update_all_configs(
        self,
        api_key: str,
        api_base: str = "",
        model: str = ""
    ):
        """
        更新所有需要 API 的 Skills 配置
        
        Args:
            api_key: API 密钥
            api_base: API 基础 URL
            model: 模型名称
        """
        for skill_id, instance in self.skill_instances.items():
            if hasattr(instance, 'update_config'):
                instance.update_config(api_key, api_base, model)
                print(f"[Registry] 更新 {skill_id} 配置")
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for skill in self.skills.values():
            categories.add(skill["info"].category)
        return sorted(list(categories))
    
    def export_skill_catalog(self) -> Dict[str, Any]:
        """
        导出 Skill 目录
        
        Returns:
            Skill 目录字典
        """
        catalog = {
            "total_skills": len(self.skills),
            "categories": self.get_categories(),
            "skills": [],
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        for skill in self.skills.values():
            info = skill["info"]
            catalog["skills"].append({
                "skill_id": info.skill_id,
                "name": info.name,
                "description": info.description,
                "category": info.category,
                "requires_api": info.requires_api,
                "tags": info.tags,
            })
        
        return catalog
    
    def create_pipeline(
        self,
        skill_ids: List[str],
        api_key: str = "",
        api_base: str = "",
        model: str = DEFAULT_AI_MODEL
    ) -> Dict[str, Any]:
        """
        创建 Skill 流水线
        
        Args:
            skill_ids: Skill ID 列表（按执行顺序）
            api_key: API 密钥
            api_base: API 基础 URL
            model: 模型名称
            
        Returns:
            流水线配置
        """
        pipeline = {
            "skills": [],
            "execution_order": skill_ids,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        for skill_id in skill_ids:
            if skill_id in self.skills:
                instance = self.get_skill_instance(
                    skill_id, api_key, api_base, model
                )
                pipeline["skills"].append({
                    "skill_id": skill_id,
                    "info": self.skills[skill_id]["info"],
                    "instance": instance,
                })
        
        return pipeline


# 全局 Skill 注册表实例
_registry = None


def get_registry() -> SkillRegistry:
    """获取全局 Skill 注册表"""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry


def initialize_skills(
    api_key: str = "",
    api_base: str = "",
    model: str = DEFAULT_AI_MODEL
) -> SkillRegistry:
    """
    初始化所有 Skills
    
    Args:
        api_key: API 密钥
        api_base: API 基础 URL
        model: 模型名称
        
    Returns:
        Skill 注册表实例
    """
    registry = get_registry()
    registry.update_all_configs(api_key, api_base, model)
    return registry
