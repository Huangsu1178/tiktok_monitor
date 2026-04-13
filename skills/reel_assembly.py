"""
TikTok Monitor - Reel Assembly Skill
参考 ReelClaw 的 FFmpeg 组装理念，提供智能视频组装指导

功能：
1. 生成详细的视频组装脚本和步骤
2. 提供文字覆盖 Green Zone 指导
3. BGM 选择和节奏匹配建议
4. 平台规范检查清单
5. FFmpeg 命令生成（可选）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class ReelAssemblySkill:
    """视频组装指导技能 - 生成详细的视频制作指导"""

    def __init__(self):
        """初始化组装指导技能（无需 API）"""
        self.platform_specs = {
            "tiktok": {
                "resolution": "1080x1920",
                "aspect_ratio": "9:16",
                "max_duration": 180,
                "recommended_duration": 15,
                "font": "TikTok Sans / Montserrat",
                "safe_zones": {
                    "top_margin": 200,  # px from top
                    "bottom_margin": 300,  # px from bottom
                    "left_margin": 50,
                    "right_margin": 50,
                },
                "text_guidelines": "避免被 UI 元素遮挡（点赞、评论、分享按钮）",
            },
            "instagram": {
                "resolution": "1080x1920",
                "aspect_ratio": "9:16",
                "max_duration": 90,
                "recommended_duration": 15,
                "font": "Instagram Sans / Helvetica",
                "safe_zones": {
                    "top_margin": 250,
                    "bottom_margin": 350,
                    "left_margin": 50,
                    "right_margin": 50,
                },
                "text_guidelines": "避免被账号名和互动按钮遮挡",
            }
        }

    def generate_assembly_guide(
        self,
        concept: Dict[str, Any],
        platform: str = "tiktok"
    ) -> Dict[str, Any]:
        """
        为视频概念生成详细的组装指导
        
        Args:
            concept: 视频概念字典（来自 Pipeline）
            platform: 目标平台
            
        Returns:
            详细的组装指导
        """
        print(f"[Assembly] 生成组装指导 - 平台: {platform}")
        
        hook = concept.get("hook", {})
        fmt = concept.get("format", {})
        target_duration = concept.get("estimated_duration", 15)
        
        # 生成时间线脚本
        timeline = self._generate_timeline(hook, fmt, target_duration)
        
        # 生成文字覆盖指导
        text_overlay = self._generate_text_overlay_guide(hook, platform)
        
        # 生成 BGM 建议
        bgm_guide = self._generate_bgm_guide(concept)
        
        # 生成视觉风格指导
        visual_guide = self._generate_visual_guide(concept)
        
        # 生成平台规范检查
        platform_check = self._generate_platform_checklist(platform)
        
        # 生成 FFmpeg 命令模板（可选）
        ffmpeg_template = self._generate_ffmpeg_template(timeline, platform)
        
        assembly_guide = {
            "concept_id": concept.get("concept_id", "unknown"),
            "platform": platform,
            "target_duration": target_duration,
            "timeline": timeline,
            "text_overlay_guide": text_overlay,
            "bgm_guide": bgm_guide,
            "visual_guide": visual_guide,
            "platform_checklist": platform_check,
            "ffmpeg_template": ffmpeg_template,
            "production_notes": self._generate_production_notes(concept),
            "quality_checklist": self._generate_quality_checklist(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        return assembly_guide

    def _generate_timeline(
        self,
        hook: dict,
        format_info: dict,
        duration: int
    ) -> Dict[str, Any]:
        """生成视频时间线脚本"""
        # 根据 ReelClaw 规则：15秒 max
        actual_duration = min(duration, 15)
        
        # 三段式结构
        opening_duration = 3  # 0-3秒
        middle_duration = actual_duration - 6  # 3到倒数3秒
        ending_duration = 3  # 最后3秒
        
        structure = format_info.get("structure", {})
        
        return {
            "total_duration": actual_duration,
            "segments": [
                {
                    "name": "Opening Hook",
                    "time_range": f"0-{opening_duration}s",
                    "duration": opening_duration,
                    "purpose": "阻止滑动，触发好奇",
                    "action": structure.get("opening", hook.get("hook_text", "强力开场")),
                    "text_overlay": hook.get("hook_text", ""),
                    "visual_priority": "highest",
                    "key_metric": "3秒留存率",
                },
                {
                    "name": "Core Content",
                    "time_range": f"{opening_duration}-{opening_duration + middle_duration}s",
                    "duration": middle_duration,
                    "purpose": "传递核心价值",
                    "action": structure.get("middle", "展示核心内容/教程步骤"),
                    "text_overlay": "关键点标注",
                    "visual_priority": "high",
                    "key_metric": "完播率",
                },
                {
                    "name": "Call to Action",
                    "time_range": f"{opening_duration + middle_duration}-{actual_duration}s",
                    "duration": ending_duration,
                    "purpose": "引导互动",
                    "action": structure.get("ending", "关注+点赞+评论引导"),
                    "text_overlay": "Follow for more / Save this",
                    "visual_priority": "medium",
                    "key_metric": "互动率",
                }
            ],
            "pacing_tips": [
                "前3秒必须展示最有吸引力的内容",
                "中间部分保持快节奏，每2-3秒切换一次画面",
                "最后3秒明确号召行动",
                "整体节奏：快-中-快",
            ],
        }

    def _generate_text_overlay_guide(
        self,
        hook: dict,
        platform: str
    ) -> Dict[str, Any]:
        """生成文字覆盖指导"""
        specs = self.platform_specs.get(platform, self.platform_specs["tiktok"])
        safe_zones = specs["safe_zones"]
        
        return {
            "font": specs["font"],
            "font_size": {
                "headline": "48-56px",
                "body": "32-40px",
                "caption": "24-28px",
            },
            "colors": {
                "primary_text": "#FFFFFF",
                "accent_text": "#FFD700",  # 金色高亮
                "background": "rgba(0, 0, 0, 0.6)",  # 半透明黑底
            },
            "green_zone_positioning": {
                "safe_area": {
                    "top": f"{safe_zones['top_margin']}px from top",
                    "bottom": f"{safe_zones['bottom_margin']}px from bottom",
                    "left": f"{safe_zones['left_margin']}px from left",
                    "right": f"{safe_zones['right_margin']}px from right",
                },
                "headline_position": "中上部，避开顶部UI",
                "body_position": "中部，避开左右按钮",
                "cta_position": "中下部，避开底部UI",
            },
            "text_rules": [
                "每行不超过8个单词",
                "使用大写增加视觉冲击",
                "关键数字/词汇使用高亮色",
                "添加半透明背景提升可读性",
                "避免文字被平台UI遮挡",
                "保持文字在画面中心区域",
            ],
            "hook_text_display": {
                "text": hook.get("hook_text", ""),
                "display_duration": "3s",
                "position": "中心偏上",
                "style": "大号加粗，带阴影",
                "animation": "快速淡入",
            },
        }

    def _generate_bgm_guide(self, concept: dict) -> Dict[str, Any]:
        """生成 BGM 指导"""
        hook_type = concept.get("hook", {}).get("hook_type", "")
        format_type = concept.get("format", {}).get("format_type", "")
        
        # 根据内容类型推荐 BGM 风格
        bgm_style = self._match_bgm_style(hook_type, format_type)
        
        return {
            "music_style": bgm_style["style"],
            "tempo": bgm_style["tempo"],
            "mood": bgm_style["mood"],
            "volume_levels": {
                "bgm_volume": "15-25%",  # 背景音乐音量
                "voiceover_volume": "80-100%",  # 人声音量
                "sound_effects": "30-50%",  # 音效音量
            },
            "timing_tips": [
                "在转折点切换音乐节奏",
                "高潮部分配合音乐节拍",
                "避免音乐盖过人声",
                "使用热门音乐增加曝光",
            ],
            "music_sources": [
                "TikTok 热门音乐库",
                "Trending Sounds on TikTok",
                "版权免费音乐库",
            ],
            "sync_points": [
                "0-3s: 强节拍开场",
                "3-12s: 稳定节奏配合内容",
                "12-15s: 音乐高潮配合 CTA",
            ],
        }

    def _generate_visual_guide(self, concept: dict) -> Dict[str, Any]:
        """生成视觉风格指导"""
        return {
            "resolution": "1080x1920 (9:16)",
            "frame_rate": "30fps 或 60fps",
            "color_grading": {
                "style": "鲜艳、高对比度",
                "saturation": "+10-20%",
                "contrast": "+5-10%",
                "brightness": "保持明亮",
            },
            "transitions": [
                "硬切（最常用）",
                "缩放转场",
                "滑动转场",
                "避免过度使用特效",
            ],
            "visual_elements": {
                "b_roll": "产品/场景特写",
                "screen_recordings": "应用演示/操作过程",
                "reaction_clips": "UGC 反应镜头（如有）",
                "text_overlays": "关键信息标注",
            },
            "composition_rules": [
                "主体居中或三分法",
                "保持画面稳定（使用三脚架）",
                "光线充足，避免逆光",
                "背景简洁不杂乱",
            ],
        }

    def _generate_platform_checklist(self, platform: str) -> Dict[str, Any]:
        """生成平台规范检查清单"""
        specs = self.platform_specs.get(platform, self.platform_specs["tiktok"])
        
        return {
            "platform": platform,
            "technical_specs": {
                "resolution": specs["resolution"],
                "aspect_ratio": specs["aspect_ratio"],
                "max_duration": f"{specs['max_duration']}s",
                "recommended_duration": f"{specs['recommended_duration']}s",
                "file_format": "MP4 (H.264)",
                "max_file_size": "287.6 MB (TikTok)",
            },
            "content_guidelines": [
                "✓ 文字在 Green Zone 内",
                "✓ 时长不超过15秒（推荐）",
                "✓ 使用热门 BGM",
                "✓ 包含明确的 CTA",
                "✓ 描述包含3-5个精准标签",
                "✓ 封面图清晰有吸引力",
            ],
            "avoid": [
                "✗ 文字被 UI 遮挡",
                "✗ 视频过长导致完播率低",
                "✗ 使用版权音乐",
                "✗ 模糊或低质量画面",
                "✗ 过度水印或品牌标识",
                "✗ 违规内容或敏感话题",
            ],
        }

    def _generate_ffmpeg_template(
        self,
        timeline: dict,
        platform: str
    ) -> str:
        """生成 FFmpeg 命令模板"""
        specs = self.platform_specs.get(platform, self.platform_specs["tiktok"])
        
        return f"""# FFmpeg 视频组装模板
# 参考: ReelClaw FFmpeg Assembly Engine

# 1. 合并多个片段
ffmpeg -i opening.mp4 -i middle.mp4 -i ending.mp4 \\
-filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0[outv]" \\
-map "[outv]" -map 1:a \\
-c:v libx264 -crf 23 -preset fast \\
-c:a aac -b:a 128k \\
output_merged.mp4

# 2. 添加文字覆盖
ffmpeg -i output_merged.mp4 \\
-vf "drawtext=text='{timeline['segments'][0]['text_overlay']}':\\
fontsize=48:fontcolor=white:\\
x=(w-text_w)/2:y=200:\\
box=1:boxcolor=black@0.6:boxborderw=10" \\
-c:v libx264 -crf 23 \\
-c:a copy \\
output_with_text.mp4

# 3. 添加 BGM 并调整音量
ffmpeg -i output_with_text.mp4 -i bgm.mp3 \\
-filter_complex "[0:a]volume=1.0[a0];[1:a]volume=0.2[a1];[a0][a1]amix=inputs=2:duration=first" \\
-c:v copy \\
-c:a aac -b:a 128k \\
final_output.mp4

# 4. 调整分辨率和格式（{specs['resolution']}）
ffmpeg -i final_output.mp4 \\
-vf "scale={specs['resolution']},setsar=1" \\
-c:v libx264 -crf 23 -preset fast \\
-c:a aac -b:a 128k \\
-r 30 \\
final_{platform}.mp4

# 5. 完整一键命令（合并所有步骤）
ffmpeg \\
-i opening.mp4 -i middle.mp4 -i ending.mp4 -i bgm.mp3 \\
-filter_complex "
  [0:v][1:v][2:v]concat=n=3:v=1:a=0[v];
  [v]scale={specs['resolution']},setsar=1,
  drawtext=text='HOOK TEXT':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=200:box=1:boxcolor=black@0.6:boxborderw=10[outv];
  [3:a]volume=0.2[a3];
  [1:a]volume=1.0[a1];
  [a1][a3]amix=inputs=2:duration=first[outa]
" \\
-map "[outv]" -map "[outa]" \\
-c:v libx264 -crf 23 -preset fast \\
-c:a aac -b:a 128k \\
-r 30 \\
final_{platform}.mp4
"""

    def _generate_production_notes(self, concept: dict) -> List[str]:
        """生成制作注意事项"""
        notes = [
            "📌 关键原则：15秒内传达核心价值",
            "🎯 前3秒决定生死 - 必须强力开场",
            "⚡ 快节奏剪辑 - 每2-3秒切换画面",
            "🎵 使用当前热门 BGM 增加曝光",
            "📝 文字简洁 - 每行不超过8个单词",
            "✅ 发布前检查 Green Zone 规范",
        ]
        
        hook_type = concept.get("hook", {}).get("hook_type", "")
        if hook_type:
            notes.append(f"💡 本视频使用 {hook_type} 钩子，确保开场匹配")
        
        return notes

    def _generate_quality_checklist(self) -> List[str]:
        """生成质量检查清单"""
        return [
            "□ 视频时长 ≤ 15秒",
            "□ 分辨率 1080x1920 (9:16)",
            "□ 前3秒有强力钩子",
            "□ 文字在 Green Zone 内",
            "□ 文字清晰可读（大小、颜色、对比度）",
            "□ BGM 音量适中（不盖过人声）",
            "□ 画面稳定、光线充足",
            "□ 剪辑节奏快速流畅",
            "□ 结尾有明确的 CTA",
            "□ 描述包含3-5个精准标签",
            "□ 封面图有吸引力",
            "□ 无版权风险内容",
        ]

    def _match_bgm_style(self, hook_type: str, format_type: str) -> Dict[str, str]:
        """匹配 BGM 风格"""
        # 根据钩子类型和格式类型推荐 BGM
        if any(kw in hook_type.lower() for kw in ["悬念", "反常识"]):
            return {
                "style": "悬疑/紧张",
                "tempo": "中等（90-110 BPM）",
                "mood": "紧张、期待",
            }
        elif any(kw in hook_type.lower() for kw in ["教程", "数字"]):
            return {
                "style": "轻快/活力",
                "tempo": "快速（120-140 BPM）",
                "mood": "积极、向上",
            }
        elif any(kw in hook_type.lower() for kw in ["故事", "情感"]):
            return {
                "style": "温暖/感性",
                "tempo": "慢速（70-90 BPM）",
                "mood": "温暖、共鸣",
            }
        else:
            return {
                "style": "流行/热门",
                "tempo": "中快速（110-130 BPM）",
                "mood": "活力、吸引",
            }
