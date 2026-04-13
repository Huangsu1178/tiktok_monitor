"""
TikTok Monitor - Hook Research Skill
参考 ReelClaw 的钩子研究能力，发现和分析高转化文本钩子

功能：
1. 基于领域研究已验证的文本钩子
2. 分析高表现视频的钩子模式
3. 生成可复用的钩子模板
4. 钩子效果预测和评分
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

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class HookResearchSkill(AIClientMixin):
    """钩子研究技能 - 发现和分析高转化文本钩子"""

    def __init__(self, api_key: str = "", api_base: str = "", model: str = DEFAULT_AI_MODEL):
        self._init_ai_client(api_key, api_base, model)

    def is_available(self) -> bool:
        return OPENAI_AVAILABLE and bool(self.api_key) and self._client is not None

    def update_config(self, api_key: str, api_base: str = "", model: str = ""):
        self.api_key = api_key
        if api_base:
            self.api_base = api_base
        if model:
            self.model = model
            
        if OPENAI_AVAILABLE and api_key:
            client_kwargs = {"api_key": api_key}
            if self.api_base:
                client_kwargs["base_url"] = self.api_base
            self._client = OpenAI(**client_kwargs)

    def research_hooks(
        self,
        niche: str,
        count: int = 20,
        emotion_type: str = ""
    ) -> Dict[str, Any]:
        """
        研究特定领域的已验证钩子
        
        Args:
            niche: 内容领域（如：fitness, tech, beauty, finance）
            count: 返回钩子数量
            emotion_type: 情感类型（shocked, crying, laughing, frustrated, inspired）
            
        Returns:
            钩子研究结果
        """
        print(f"[Hook Research] 研究领域: {niche}, 情感: {emotion_type or 'all'}")
        
        if not self.is_available():
            return self._mock_hook_research(niche, count, emotion_type)

        prompt = f"""你是一位专业的 TikTok 钩子研究专家。

请为以下领域研究 {count} 个已验证的高转化文本钩子（text hooks）。

## 研究领域
- 领域（Niche）：{niche}
- 情感类型：{emotion_type or "全部类型"}
- 目标：创建能在前3秒阻止滑动的钩子

## 钩子类型要求

请包含以下类型的钩子：
1. **问题型** - 提出观众痛点问题
2. **数字冲击型** - 使用具体数字制造冲击
3. **反常识型** - 违反直觉的陈述
4. **故事型** - 用故事开头吸引
5. **挑战型** - 发起挑战或测试
6. **秘密型** - 揭示"秘密"或"内幕"
7. **对比型** - 前后对比或你我对比
8. **紧急型** - 制造紧迫感

## 返回格式

请以 JSON 格式返回：
```json
{{
  "niche": "{niche}",
  "emotion_type": "{emotion_type or 'all'}",
  "hooks": [
    {{
      "hook_text": "钩子文本内容",
      "hook_type": "钩子类型",
      "emotion": "触发的情感",
      "pattern": "使用的模式",
      "why_it_works": "为什么有效（简短解释）",
      "use_case": "适用场景",
      "effectiveness_score": 85,
      "example_structure": "示例结构"
    }}
  ],
  "top_patterns": ["最常见的高效模式"],
  "research_insights": "研究洞察总结"
}}
```

返回 {count} 个高质量钩子，确保每个都是实际可用的。"""

        try:
            response = self._call_api_with_retry(
                messages=[
                    {"role": "system", "content": "你是 TikTok 钩子研究专家，擅长发现和分析高转化钩子。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=3000,
            )
            
            if response is None:
                return self._mock_hook_research(niche, count, emotion_type)
            
            raw_response = self._extract_response_text(response)
            result = self._parse_json(raw_response)
            
            if result:
                result["researched_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return result
                
        except Exception as e:
            print(f"[Hook Research] 研究失败: {e}")
        
        return self._mock_hook_research(niche, count, emotion_type)

    def analyze_hook_effectiveness(
        self,
        hook_text: str,
        niche: str,
        target_audience: str = ""
    ) -> Dict[str, Any]:
        """
        分析单个钩子的有效性
        
        Args:
            hook_text: 钩子文本
            niche: 领域
            target_audience: 目标受众
            
        Returns:
            分析结果
        """
        if not self.is_available():
            return self._mock_hook_analysis(hook_text, niche)

        prompt = f"""分析以下 TikTok 钩子的有效性。

## 钩子文本
"{hook_text}"

## 背景信息
- 领域：{niche}
- 目标受众：{target_audience or "通用"}

## 分析维度

请从以下维度分析：
1. **scroll_stop_score** - 阻止滑动评分（0-100）
2. **curiosity_gap** - 好奇心缺口（强/中/弱）
3. **emotional_trigger** - 触发的情感
4. **clarity** - 清晰度（是否容易理解）
5. **specificity** - 具体性（是否具体而非模糊）
6. **urgency** - 紧迫感
7. **relatability** - 共鸣度
8. **predicted_performance** - 预期表现（高/中/低）

## 返回格式

```json
{{
  "hook_text": "{hook_text}",
  "scroll_stop_score": 85,
  "curiosity_gap": "强",
  "emotional_trigger": "好奇心+惊讶",
  "clarity": "高",
  "specificity": "高",
  "urgency": "中",
  "relatability": "高",
  "predicted_performance": "高",
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["劣势1"],
  "optimization_suggestions": ["优化建议1", "优化建议2"],
  "best_use_case": "最佳使用场景"
}}
```"""

        try:
            response = self._call_api_with_retry(
                messages=[
                    {"role": "system", "content": "你是 TikTok 内容分析专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1500,
            )
            
            if response is None:
                return self._mock_hook_analysis(hook_text, niche)
            
            raw_response = self._extract_response_text(response)
            return self._parse_json(raw_response) or self._mock_hook_analysis(hook_text, niche)
                
        except Exception as e:
            print(f"[Hook Research] 分析失败: {e}")
            return self._mock_hook_analysis(hook_text, niche)

    def generate_hook_variations(
        self,
        base_hook: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        基于基础钩子生成变体
        
        Args:
            base_hook: 基础钩子文本
            count: 变体数量
            
        Returns:
            钩子变体列表
        """
        if not self.is_available():
            return [{"variation": base_hook, "type": "original"}]

        prompt = f"""基于以下 TikTok 钩子，生成 {count} 个变体。

## 基础钩子
"{base_hook}"

## 要求

生成不同风格的变体：
- 保持核心信息不变
- 尝试不同的情感触发
- 使用不同的句式结构
- 调整具体性和紧迫感

## 返回格式

```json
{{
  "base_hook": "{base_hook}",
  "variations": [
    {{
      "hook_text": "变体文本",
      "variation_type": "变体类型（如：更具体、更紧急、更情感化等）",
      "expected_difference": "预期差异"
    }}
  ]
}}
```"""

        try:
            response = self._call_api_with_retry(
                messages=[
                    {"role": "system", "content": "你是创意文案专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=2000,
            )
            
            if response is None:
                return []
            
            raw_response = self._extract_response_text(response)
            result = self._parse_json(raw_response)
            
            return result.get("variations", []) if result else []
                
        except Exception as e:
            print(f"[Hook Research] 生成变体失败: {e}")
            return []

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

    def _mock_hook_research(self, niche: str, count: int, emotion_type: str) -> Dict[str, Any]:
        """模拟钩子研究结果"""
        hooks = [
            {
                "hook_text": f"我试了100个{nichename}方法，只有这个有效",
                "hook_type": "数字冲击型",
                "emotion": "好奇心",
                "pattern": "大量尝试 + 唯一有效",
                "why_it_works": "具体数字制造可信度，暗示有独特发现",
                "use_case": "教程、经验分享",
                "effectiveness_score": 88,
                "example_structure": "我试了[数字]个[领域]方法，只有这个有效"
            },
            {
                "hook_text": f"别再这样{nichename}了！90%的人都错了",
                "hook_type": "反常识型",
                "emotion": "惊讶+自我怀疑",
                "pattern": "否定常见做法 + 高比例错误",
                "why_it_works": "挑战观众现有认知，触发好奇心",
                "use_case": "纠错、教育内容",
                "effectiveness_score": 85,
                "example_structure": "别再[常见做法]了！[高比例]人都错了"
            },
            {
                "hook_text": f"30天从0到100K，我做了这3件事",
                "hook_type": "故事型+数字型",
                "emotion": "向往+好奇",
                "pattern": "时间框架 + 成果 + 具体行动数",
                "why_it_works": "明确的时间线和可复制的步骤",
                "use_case": "成果展示、案例研究",
                "effectiveness_score": 90,
                "example_structure": "[时间]从[起点]到[成果]，我做了这[数字]件事"
            },
        ]
        
        return {
            "niche": niche,
            "emotion_type": emotion_type or "all",
            "hooks": hooks[:count],
            "top_patterns": [
                "使用具体数字增加可信度",
                "制造好奇心缺口",
                "挑战常见认知",
                "展示明确成果",
            ],
            "research_insights": f"{niche}领域的高效钩子通常结合具体数字和反常识陈述",
            "researched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _mock_hook_analysis(self, hook_text: str, niche: str) -> Dict[str, Any]:
        """模拟钩子分析"""
        return {
            "hook_text": hook_text,
            "scroll_stop_score": 82,
            "curiosity_gap": "强",
            "emotional_trigger": "好奇心",
            "clarity": "高",
            "specificity": "中",
            "urgency": "中",
            "relatability": "高",
            "predicted_performance": "高",
            "strengths": ["触发好奇心", "简洁明了"],
            "weaknesses": ["可以更具体"],
            "optimization_suggestions": ["加入具体数字", "增强紧迫感"],
            "best_use_case": f"{niche}领域的教程或经验分享视频"
        }
