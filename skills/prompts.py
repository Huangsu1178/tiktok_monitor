"""
TikTok Monitor - AI分析Prompt模板库
集中管理所有AI分析场景的提示词模板
"""

# 单视频流量钩子深度分析Prompt
HOOK_ANALYSIS_PROMPT = """你是一位专业的TikTok内容策略分析师，擅长分析高流量视频的成功要素。

请对以下TikTok视频的数据进行深度分析，重点识别其"流量钩子"（Hook）元素。

## 视频基本信息
- 博主：@{username}
- 视频描述：{description}
- 使用标签：{hashtags}
- 背景音乐：{music_name}
- 发布时间：{published_at}

## 视频表现数据
- 播放量：{play_count}
- 点赞数：{like_count}
- 评论数：{comment_count}
- 分享数：{share_count}
- 时长：{duration}秒

## 分析要求

请从以下维度进行结构化分析，并以JSON格式返回结果：

1. **hook_type**（钩子类型）：识别主要的流量钩子类型，如"悬念型"、"痛点型"、"挑战型"、"情感共鸣型"、"信息价值型"、"娱乐型"等
2. **hook_description**（钩子描述）：详细描述该视频的核心吸引力和钩子机制（100字以内）
3. **opening_script**（开场设计）：推断视频前3秒可能的开场方式和吸引观众的策略
4. **content_structure**（内容结构）：分析视频的内容节奏和结构安排（开头-中间-结尾）
5. **bgm_strategy**（BGM策略）：分析背景音乐的选择策略及其对情绪和完播率的影响
6. **visual_style**（视觉风格）：根据标签和描述推断视频的视觉呈现风格
7. **copywriting_style**（文案风格）：分析标题/描述的文案策略（如疑问句、数字、对比等）
8. **replication_suggestions**（可复用建议）：提供3条具体的内容创作建议，帮助复制该视频的成功要素
9. **start_framework**（S.T.A.R.T框架拆解）：按S.T.A.R.T五阶段分析该视频的内容策略
   - S (Stop)：该视频如何在第一秒截停用户滑动（钩子策略描述）
   - T (Tension)：如何制造悬念和期待感
   - A (Authority)：如何建立信任和专业度
   - R (Reveal)：如何交付核心价值（分步骤描述）
   - T (Transfer)：如何引导用户行动（CTA策略）
10. **performance_benchmark**（爆款达标线对比）：基于视频的互动数据，与行业爆款达标线进行对比评估
    - 计算互动率 = (点赞数+评论数+分享数) / 播放量 × 100%
    - 对比8%爆款达标线
    - 给出综合评价和优化建议
11. **script_template**（仿写脚本模板）：基于该视频的钩子类型和成功策略，输出一份可填空的S.T.A.R.T仿写脚本模板

请严格按照以下JSON格式返回，不要包含任何额外文字：
```json
{{
  "hook_type": "...",
  "hook_description": "...",
  "opening_script": "...",
  "content_structure": "...",
  "bgm_strategy": "...",
  "visual_style": "...",
  "copywriting_style": "...",
  "replication_suggestions": "1. ...\\n2. ...\\n3. ...",
  "start_framework": {{
    "stop": "...",
    "tension": "...",
    "authority": "...",
    "reveal": "...",
    "transfer": "..."
  }},
  "performance_benchmark": {{
    "engagement_rate": "...",
    "benchmark_8pct": true/false,
    "verdict": "...",
    "improvement_tips": "..."
  }},
  "script_template": "S (钩子): [...]\\nT (悬念): [...]\\nA (信任): [...]\\nR (交付): [...]\\nT (引导): [...]"
}}
```
"""

# 批量视频规律总结与爆款公式提炼Prompt
BATCH_ANALYSIS_PROMPT = """你是一位专业的TikTok内容策略分析师。

请对以下{count}个高播放量TikTok视频进行批量分析，总结其共同的流量钩子规律和内容策略。

## 视频数据列表
{videos_data}

## 分析要求

请以JSON格式返回以下分析结果：

1. **common_hooks**（共同钩子）：这些视频共同使用的流量钩子类型和策略
2. **top_patterns**（高频模式）：出现频率最高的内容模式（如开场方式、文案结构等）
3. **bgm_insights**（BGM洞察）：背景音乐选择的规律和趋势
4. **hashtag_strategy**（标签策略）：标签使用的规律和建议
5. **content_recommendations**（内容建议）：基于以上分析，给出5条具体的内容创作优化建议
6. **hook_formula**（钩子公式）：总结出一个可复用的"爆款公式"
7. **common_start_patterns**（S.T.A.R.T共同模式）：总结该博主视频在S.T.A.R.T各阶段的共同策略模式
   - S (Stop)：共同的钩子截停策略
   - T (Tension)：共同的悬念制造方式
   - A (Authority)：共同的信任建立手法
   - R (Reveal)：共同的价值交付模式
   - T (Transfer)：共同的行动引导策略
8. **script_template**（通用仿写模板）：基于爆款公式生成一份通用的S.T.A.R.T创作模板

请严格按照以下JSON格式返回：
```json
{{
  "common_hooks": "...",
  "top_patterns": "...",
  "bgm_insights": "...",
  "hashtag_strategy": "...",
  "content_recommendations": "1. ...\\n2. ...\\n3. ...\\n4. ...\\n5. ...",
  "hook_formula": "...",
  "common_start_patterns": {{
    "stop": "...",
    "tension": "...",
    "authority": "...",
    "reveal": "...",
    "transfer": "..."
  }},
  "script_template": "S (钩子): [...]\\nT (悬念): [...]\\nA (信任): [...]\\nR (交付): [...]\\nT (引导): [...]"
}}
```
"""

# 竞品对比分析Prompt（扩展场景）
COMPETITOR_ANALYSIS_PROMPT = """你是一位专业的TikTok内容策略分析师，擅长竞品分析和内容定位研究。

请对以下{num_creators}位TikTok博主的内容策略进行横向对比分析：

## 博主数据
{creators_data}

## 分析要求

请以JSON格式返回以下对比分析结果：

1. **positioning_differences**（定位差异）：各博主的内容定位和差异化特征
2. **hook_comparison**（钩子对比）：各博主偏好的流量钩子类型及效果对比
3. **performance_analysis**（表现分析）：播放量、互动率的横向对比
4. **content_gap**（内容空白）：发现的市场机会和未被充分覆盖的内容方向
5. **competitive_advantages**（竞争优势）：各博主的核心竞争力分析
6. **opportunity_recommendations**（机会建议）：基于对比分析，给出5条差异化创作建议

请严格按照以下JSON格式返回：
```json
{{
  "positioning_differences": "...",
  "hook_comparison": "...",
  "performance_analysis": "...",
  "content_gap": "...",
  "competitive_advantages": "...",
  "opportunity_recommendations": "1. ...\\n2. ...\\n3. ...\\n4. ...\\n5. ..."
}}
```
"""

# 趋势预测分析Prompt（扩展场景）
TREND_PREDICTION_PROMPT = """你是一位专业的TikTok内容策略分析师和数据科学家。

请基于以下视频草稿信息和历史爆款数据，预测该视频的爆款概率并提供优化建议。

## 视频草稿信息
{draft_data}

## 历史爆款参考
{historical_data}

## 分析要求

请以JSON格式返回以下预测分析结果：

1. **viral_probability**（爆款概率）：预估该视频达到100万播放的概率（0-100%）
2. **strength_analysis**（优势分析）：该视频草稿的核心优势
3. **weakness_analysis**（劣势分析）：可能导致表现不佳的风险点
4. **optimization_suggestions**（优化建议）：5条具体的优化建议，提升爆款概率
5. **best_posting_time**（最佳发布时间）：基于目标受众活跃度的发布时间建议
6. **expected_engagement**（预期互动）：预估的播放量、点赞数、评论数范围

请严格按照以下JSON格式返回：
```json
{{
  "viral_probability": 0.0,
  "strength_analysis": "...",
  "weakness_analysis": "...",
  "optimization_suggestions": "1. ...\\n2. ...\\n3. ...\\n4. ...\\n5. ...",
  "best_posting_time": "...",
  "expected_engagement": {{
    "play_count_range": "...",
    "like_count_range": "...",
    "comment_count_range": "..."
  }}
}}
```
"""

# 钩子库分类与标签生成Prompt（扩展场景）
HOOK_LIBRARY_TAGGING_PROMPT = """你是一位专业的TikTok内容策略分析师和信息架构师。

请对以下流量钩子分析结果进行分类和标签化处理，便于后续检索和应用。

## 钩子分析数据
{hook_analysis_data}

## 分析要求

请以JSON格式返回以下分类结果：

1. **primary_category**（主分类）：钩子的主要类型分类（如：悬念型、教程型、娱乐型等）
2. **secondary_tags**（次级标签）：3-5个细粒度标签（如：前3秒高潮、情感共鸣、数字冲击等）
3. **industry_tags**（行业标签）：适用的行业或领域标签
4. **difficulty_level**（难度等级）：复制该钩子的难度（简单/中等/困难）
5. **applicable_scenarios**（适用场景）：适合使用此类钩子的内容场景
6. **search_keywords**（检索关键词）：5-8个用于快速检索的关键词

请严格按照以下JSON格式返回：
```json
{{
  "primary_category": "...",
  "secondary_tags": ["...", "...", "..."],
  "industry_tags": ["...", "..."],
  "difficulty_level": "...",
  "applicable_scenarios": ["...", "..."],
  "search_keywords": ["...", "...", "...", "...", "..."]
}}
```
"""

# AB对比分析Prompt（对比两组视频数据）
AB_COMPARISON_PROMPT = """你是一位专业的TikTok内容AB测试分析师，擅长通过数据对比分析找出内容策略的优劣差异。

请对以下两组TikTok视频数据进行深度对比分析。

## A组数据（{group_a_label}）
{group_a_data}

## B组数据（{group_b_label}）
{group_b_data}

## 分析要求

请从以下维度进行结构化对比分析，并以严格JSON格式返回结果：

1. **group_a_summary**（A组摘要）：统计A组视频的平均播放量、平均互动率、主要钩子类型、内容模式总结、核心优势列表（3条）
2. **group_b_summary**（B组摘要）：同上结构统计B组数据
3. **winner**（胜出方）：判定整体表现更优的组别（"A"或"B"）
4. **winner_reason**（胜出原因）：一句话总结胜出方的核心优势
5. **dimension_comparison**（维度对比）：从以下6个维度进行横向对比分析
   - 钩子策略（开场吸引力、钩子类型分布）
   - 内容结构（叙事节奏、信息密度、价值交付方式）
   - 视觉风格（画面呈现、剪辑节奏、视觉记忆点）
   - 文案策略（标题技巧、描述写法、CTA设计）
   - BGM策略（音乐选择、节奏匹配、情绪调动）
   - 互动引导（评论引导、分享触发、粉丝转化）
   每个维度需包含：A组表现、B组表现、差距分析、优劣判定（"A优"/"B优"/"持平"）
6. **root_causes**（根本原因）：分析导致两组表现差异的3条深层原因
7. **optimization_suggestions**（优化建议）：提供5条具体的优化建议，每条包含优先级（高/中/低）、建议内容、预期效果
8. **start_framework_comparison**（S.T.A.R.T框架对比）：按S.T.A.R.T五阶段对比两组的内容策略差异
   - S (Stop)：截停能力对比
   - T (Tension)：悬念制造对比
   - A (Authority)：信任建立对比
   - R (Reveal)：价值交付对比
   - T (Transfer)：行动引导对比
   每个阶段需包含：A组表现、B组表现、优劣判定
9. **actionable_script**（可执行脚本）：基于对比结论，输出一份优化版的S.T.A.R.T仿写脚本，融合两组优势

## 输出格式

请严格按照以下JSON格式返回，不要包含任何额外文字：
```json
{{
  "group_a_summary": {{
    "avg_play_count": "数值",
    "avg_engagement_rate": "百分比字符串",
    "dominant_hook_type": "主要钩子类型",
    "content_pattern": "内容模式总结",
    "strengths": ["优势1", "优势2", "优势3"]
  }},
  "group_b_summary": {{
    "avg_play_count": "数值",
    "avg_engagement_rate": "百分比字符串",
    "dominant_hook_type": "主要钩子类型",
    "content_pattern": "内容模式总结",
    "strengths": ["优势1", "优势2", "优势3"]
  }},
  "winner": "A或B",
  "winner_reason": "一句话总结胜出原因",
  "dimension_comparison": [
    {{
      "dimension": "维度名称（如钩子策略、内容结构、视觉风格、文案策略、BGM策略、互动引导）",
      "group_a_performance": "A组在该维度的表现",
      "group_b_performance": "B组在该维度的表现",
      "gap_analysis": "差距分析",
      "verdict": "A优/B优/持平"
    }}
  ],
  "root_causes": ["原因1", "原因2", "原因3"],
  "optimization_suggestions": [
    {{
      "priority": "高/中/低",
      "suggestion": "优化建议",
      "expected_impact": "预期效果"
    }}
  ],
  "start_framework_comparison": {{
    "stop": {{"group_a": "A组表现", "group_b": "B组表现", "verdict": "判定"}},
    "tension": {{"group_a": "...", "group_b": "...", "verdict": "..."}},
    "authority": {{"group_a": "...", "group_b": "...", "verdict": "..."}},
    "reveal": {{"group_a": "...", "group_b": "...", "verdict": "..."}},
    "transfer": {{"group_a": "...", "group_b": "...", "verdict": "..."}}
  }},
  "actionable_script": "基于对比结论的优化版S.T.A.R.T仿写脚本"
}}
```
"""
