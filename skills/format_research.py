"""
TikTok Monitor - Format Research Skill
参考 ReelClaw 的格式研究能力，发现病毒式视频格式创意

功能：
1. 分析特定领域的热门视频格式
2. 识别当前流行的内容模板
3. 发现跨领域可复用的格式模式
4. 格式效果追踪和趋势预测
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# 导入统一配置
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DEFAULT_AI_MODEL, AI_CONFIG
from skills.ai_client import AIClientMixin


class FormatResearchSkill(AIClientMixin):
    """格式研究技能 - 发现和分析病毒式视频格式"""

    def __init__(self, api_key: str = "", api_base: str = "", model: str = DEFAULT_AI_MODEL):
        self._init_ai_client(api_key, api_base, model)

    def research_formats(
        self,
        niche: str,
        count: int = 15,
        platform: str = "tiktok"
    ) -> Dict[str, Any]:
        """
        研究特定领域的病毒式视频格式
        
        Args:
            niche: 内容领域
            count: 返回格式数量
            platform: 平台（tiktok, instagram, both）
            
        Returns:
            格式研究结果
        """
        print(f"[Format Research] 开始研究格式 - 领域: {niche}, 平台: {platform}, 数量: {count}")
        
        if not self.is_available():
            print("[Format Research] ⚠️ AI服务不可用，使用模拟研究结果")
            return self._mock_format_research(niche, count, platform)

        print(f"[Format Research] 准备格式研究提示词...")
        prompt = f"""你是一位专业的 TikTok/Instagram 内容格式研究专家。

请为以下领域研究 {count} 个当前流行的病毒式视频格式（viral formats）。

## 研究领域
- 领域（Niche）：{niche}
- 平台：{platform}
- 时间：当前 trending（2024年最新）

## 格式类型要求

请包含以下类型的格式：
1. **Before/After** - 前后对比
2. **Day in the Life** - 日常生活记录
3. **Tutorial/How-to** - 教程步骤
4. **List/Countdown** - 列表/倒数
5. **Storytime** - 故事讲述
6. **Reaction** - 反应视频
7. **Myth Busting** - 破除谣言
8. **Challenge** - 挑战类
9. **POV** - 视角类
10. **Green Screen** - 绿幕解说

## 返回格式

请以 JSON 格式返回：
```json
{{
  "niche": "{niche}",
  "platform": "{platform}",
  "formats": [
    {{
      "format_name": "格式名称",
      "format_type": "格式类型",
      "description": "格式描述",
      "structure": {{
        "opening": "开头（0-3秒）怎么做",
        "middle": "中间（3-12秒）怎么做",
        "ending": "结尾（12-15秒）怎么做"
      }},
      "why_viral": "为什么病毒传播",
      "best_use_cases": ["适用场景1", "适用场景2"],
      "text_overlay_style": "文字覆盖风格",
      "visual_style": "视觉风格",
      "avg_duration": 15,
      "difficulty": "简单/中等/困难",
      "viral_potential": 85,
      "examples": ["示例描述1", "示例描述2"]
    }}
  ],
  "trending_now": ["当前最火的3个格式"],
  "format_insights": "格式趋势洞察"
}}
```

返回 {count} 个高质量格式，确保都是当前实际流行的。"""

        try:
            print(f"[Format Research] 调用AI API进行格式研究...")
            response = self._call_api_with_retry(
                messages=[
                    {"role": "system", "content": "你是 TikTok/Instagram 格式研究专家，了解最新的内容趋势。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=3500,
            )
            
            if response is None:
                print("[Format Research] ❌ AI API调用失败，使用模拟结果")
                return self._mock_format_research(niche, count, platform)
            
            print(f"[Format Research] 收到AI响应，正在解析...")
            raw_response = self._extract_response_text(response)
            result = self._parse_json(raw_response)
            
            if result:
                result["researched_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[Format Research] ✅ 格式研究完成，找到 {len(result.get('formats', []))} 个格式")
                return result
            else:
                print("[Format Research] ⚠️ JSON解析失败，使用模拟结果")
                
        except Exception as e:
            print(f"[Format Research] ❌ 研究失败: {e}")
        
        return self._mock_format_research(niche, count, platform)

    def analyze_format_performance(
        self,
        format_name: str,
        niche: str,
        video_examples: List[dict] = []
    ) -> Dict[str, Any]:
        """
        分析特定格式的表现
        
        Args:
            format_name: 格式名称
            niche: 领域
            video_examples: 使用该格式的视频示例
            
        Returns:
            格式表现分析
        """
        print(f"[Format Research] 开始分析格式表现: {format_name} (领域: {niche})")
        if not self.is_available():
            print("[Format Research] ⚠️ AI服务不可用，使用模拟分析")
            return self._mock_format_analysis(format_name, niche)

        print(f"[Format Research] 准备格式分析提示词...")
        examples_text = ""
        if video_examples:
            examples_text = "\n## 视频示例\n"
            for i, v in enumerate(video_examples[:5], 1):
                examples_text += f"{i}. 播放: {v.get('play_count', 0):,} | {v.get('description', '')[:50]}\n"

        prompt = f"""分析以下视频格式在 {niche} 领域的表现。

## 格式信息
- 格式名称：{format_name}
- 领域：{niche}
{examples_text}

## 分析维度

请分析：
1. **effectiveness_score** - 有效性评分（0-100）
2. **saturation_level** - 饱和度（低/中/高/过饱和）
3. **longevity** - 持久性（短期爆/长期稳定）
4. **engagement_rate** - 预期互动率范围
5. **best_practices** - 最佳实践
6. **common_mistakes** - 常见错误
7. **optimization_tips** - 优化建议
8. **future_trend** - 未来趋势预测

## 返回格式

```json
{{
  "format_name": "{format_name}",
  "niche": "{niche}",
  "effectiveness_score": 85,
  "saturation_level": "中",
  "longevity": "长期稳定",
  "engagement_rate": "5-12%",
  "best_practices": ["最佳实践1", "最佳实践2"],
  "common_mistakes": ["常见错误1", "常见错误2"],
  "optimization_tips": ["优化建议1", "优化建议2"],
  "future_trend": "趋势预测",
  "recommended_for_beginners": true,
  "production_complexity": "简单/中等/复杂"
}}
```"""

        try:
            print(f"[Format Research] 调用AI API进行格式分析...")
            response = self._call_api_with_retry(
                messages=[
                    {"role": "system", "content": "你是 TikTok 内容策略分析师。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=2000,
            )
            
            if response is None:
                print("[Format Research] ❌ AI API调用失败，使用模拟分析")
                return self._mock_format_analysis(format_name, niche)
            
            print(f"[Format Research] 收到AI响应，正在解析...")
            raw_response = self._extract_response_text(response)
            result = self._parse_json(raw_response)
            if not result:
                print("[Format Research] ⚠️ JSON解析失败，使用模拟分析")
                return self._mock_format_analysis(format_name, niche)
            
            print(f"[Format Research] ✅ 格式表现分析完成")
            return result
                
        except Exception as e:
            print(f"[Format Research] ❌ 分析失败: {e}")
            return self._mock_format_analysis(format_name, niche)

    def cross_niche_format_transfer(
        self,
        source_niche: str,
        target_niche: str,
        format_name: str
    ) -> Dict[str, Any]:
        """
        跨领域格式迁移分析
        
        Args:
            source_niche: 源领域
            target_niche: 目标领域
            format_name: 格式名称
            
        Returns:
            迁移方案
        """
        print(f"[Format Research] 开始跨领域格式迁移: {format_name} ({source_niche} -> {target_niche})")
        if not self.is_available():
            print("[Format Research] ⚠️ AI服务不可用，返回基础迁移方案")
            return {
                "source_niche": source_niche,
                "target_niche": target_niche,
                "format": format_name,
                "transferable": True,
                "adaptation_tips": ["根据目标领域调整内容"]
            }

        print(f"[Format Research] 准备格式迁移分析提示词...")
        prompt = f"""分析如何将 {source_niche} 领域的 "{format_name}" 格式迁移到 {target_niche} 领域。

## 迁移分析

请分析：
1. **transferable** - 是否可迁移（true/false）
2. **adaptation_required** - 需要的调整程度（低/中/高）
3. **key_changes** - 关键改变点
4. **what_keeps_same** - 保持不变的元素
5. **what_changes** - 需要改变的元素
6. **expected_performance** - 预期表现
7. **risks** - 潜在风险
8. **step_by_step_guide** - 迁移步骤指南

## 返回格式

```json
{{
  "source_niche": "{source_niche}",
  "target_niche": "{target_niche}",
  "format": "{format_name}",
  "transferable": true,
  "adaptation_required": "中",
  "key_changes": ["关键改变1", "关键改变2"],
  "what_keeps_same": ["保持不变1", "保持不变2"],
  "what_changes": ["需要改变1", "需要改变2"],
  "expected_performance": "高/中/低",
  "risks": ["风险1", "风险2"],
  "step_by_step_guide": ["步骤1", "步骤2", "步骤3"],
  "success_probability": 75
}}
```"""

        try:
            print(f"[Format Research] 调用AI API进行迁移分析...")
            response = self._call_api_with_retry(
                messages=[
                    {"role": "system", "content": "你是内容策略和跨领域迁移专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            
            if response is None:
                print("[Format Research] ❌ AI API调用失败，返回基础迁移方案")
                return {
                    "source_niche": source_niche,
                    "target_niche": target_niche,
                    "format": format_name,
                    "transferable": True,
                    "adaptation_required": "中"
                }
            
            print(f"[Format Research] 收到AI响应，正在解析...")
            raw_response = self._extract_response_text(response)
            result = self._parse_json(raw_response)
            if not result:
                print("[Format Research] ⚠️ JSON解析失败，返回基础迁移方案")
                return {
                    "source_niche": source_niche,
                    "target_niche": target_niche,
                    "format": format_name,
                    "transferable": True,
                    "adaptation_required": "中"
                }
            
            print(f"[Format Research] ✅ 跨领域格式迁移分析完成")
            return result
                
        except Exception as e:
            print(f"[Format Research] ❌ 迁移分析失败: {e}")
            return {
                "source_niche": source_niche,
                "target_niche": target_niche,
                "format": format_name,
                "transferable": True,
                "adaptation_required": "中"
            }

    def _parse_json(self, raw: str) -> Optional[dict]:
        """解析 JSON 响应"""
        try:
            return json.loads(raw)
        except:
            pass
        
        import re
        match = re.search(r"```(?:json)?\s*(\{{.*?\}})\s*```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        
        match = re.search(r"\{{.*\}}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        
        return None

    def _mock_format_research(self, niche: str, count: int, platform: str) -> Dict[str, Any]:
        """模拟格式研究结果"""
        formats = [
            {
                "format_name": "Before/After Transformation",
                "format_type": "Before/After",
                "description": "展示使用前后的对比效果",
                "structure": {
                    "opening": "展示问题/现状（0-3秒）",
                    "middle": "快速转换过程（3-12秒）",
                    "ending": "展示结果+号召（12-15秒）"
                },
                "why_viral": "强烈的视觉冲击和满足感",
                "best_use_cases": ["产品演示", "技能展示", "改造类"],
                "text_overlay_style": "大字标注 Before/After",
                "visual_style": "分屏或快速切换",
                "avg_duration": 15,
                "difficulty": "简单",
                "viral_potential": 90,
                "examples": ["30天健身变化", "房间改造前后"]
            },
            {
                "format_name": "3 Tips You Need to Know",
                "format_type": "List/Countdown",
                "description": "快速列出3个实用技巧",
                "structure": {
                    "opening": "钩子：你可能不知道...（0-3秒）",
                    "middle": "Tip 1, 2, 3 快速展示（3-12秒）",
                    "ending": "保存到以后用（12-15秒）"
                },
                "why_viral": "高信息密度+实用价值",
                "best_use_cases": ["教育内容", "行业知识", "生活技巧"],
                "text_overlay_style": "编号列表，关键词高亮",
                "visual_style": "快速剪辑+文字覆盖",
                "avg_duration": 15,
                "difficulty": "简单",
                "viral_potential": 85,
                "examples": ["3个摄影技巧", "3个省钱方法"]
            },
            {
                "format_name": "Day in My Life as a...",
                "format_type": "Day in the Life",
                "description": "记录某一身份的日常",
                "structure": {
                    "opening": "我是[身份]，这是我的一天（0-3秒）",
                    "middle": "快速展示日常活动（3-12秒）",
                    "ending": "总结或感悟（12-15秒）"
                },
                "why_viral": "满足好奇心+共鸣感",
                "best_use_cases": ["职业展示", "生活方式", "幕后花絮"],
                "text_overlay_style": "时间戳+活动描述",
                "visual_style": "Vlog风格，快速剪辑",
                "avg_duration": 15,
                "difficulty": "中等",
                "viral_potential": 80,
                "examples": ["程序员的一天", "创业者日常"]
            },
        ]
        
        return {
            "niche": niche,
            "platform": platform,
            "formats": formats[:count],
            "trending_now": [
                "Before/After Transformation",
                "3 Tips You Need to Know",
                "POV Scenarios",
            ],
            "format_insights": f"{niche}领域当前最火的格式是对比类和教程类",
            "researched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _mock_format_analysis(self, format_name: str, niche: str) -> Dict[str, Any]:
        """模拟格式分析"""
        return {
            "format_name": format_name,
            "niche": niche,
            "effectiveness_score": 82,
            "saturation_level": "中",
            "longevity": "长期稳定",
            "engagement_rate": "5-12%",
            "best_practices": ["保持快节奏", "使用清晰文字", "加入情感元素"],
            "common_mistakes": ["节奏太慢", "信息过载", "缺乏钩子"],
            "optimization_tips": ["前3秒必须抓人", "使用热门BGM", "控制时长15秒内"],
            "future_trend": "将继续流行，但需要更多创新元素",
            "recommended_for_beginners": True,
            "production_complexity": "简单"
        }
