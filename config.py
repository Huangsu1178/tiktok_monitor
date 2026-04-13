"""
TikTok Monitor - 统一配置管理
所有默认配置项集中管理，避免硬编码
"""
import os
from typing import Dict, Any


# ==================== AI 模型配置 ====================
AI_CONFIG = {
    # 默认使用的模型名称
    "default_model": "gpt-5-chat-latest",
    
    # API 配置
    "api_base": "",  # 留空则使用 OpenAI 官方 API
    "api_key": "",   # 留空则从环境变量读取
    
    # 请求参数
    "temperature": 0.7,
    "max_tokens": 1500,
    "max_tokens_batch": 2000,  # 批量分析使用更大的 token 限制
    "max_tokens_competitor": 2000,
    "max_tokens_trend": 1500,
    "max_tokens_hook_tag": 1000,
    
    # 超时设置（秒）
    "timeout_connect": 30.0,
    "timeout_read": 300.0,  # 5分钟
    "timeout_write": 30.0,
    "timeout_pool": 30.0,
    
    # 重试配置
    "max_retries": 3,
    "retry_backoff_base": 2,  # 指数退避基数：2s, 4s, 8s
}


# ==================== 数据库配置 ====================
DB_CONFIG = {
    "db_filename": "tiktok_monitor.db",
    "db_path": "",  # 留空则使用程序同目录
}


# ==================== 抓取配置 ====================
SCRAPER_CONFIG = {
    # 默认抓取策略
    "default_strategy": "yt-dlp",  # yt-dlp 或 playwright
    
    # 抓取限制
    "max_videos_per_fetch": 20,
    "max_retries": 3,
    "retry_delay": 5,  # 秒
    
    # yt-dlp 配置
    "ytdlp_format": "bestvideo[height<=1080]+bestaudio/best",
    "ytdlp_timeout": 30,
    
    # 代理配置
    "proxy_url": "",
    "headless": True,
}


# ==================== 调度器配置 ====================
SCHEDULER_CONFIG = {
    # 默认启用状态
    "auto_fetch_enabled": False,
    
    # 抓取间隔（小时）
    "fetch_interval_hours": 1.0,
    
    # 最小/最大间隔
    "min_interval_hours": 0.5,
    "max_interval_hours": 24.0,
}


# ==================== UI 配置 ====================
UI_CONFIG = {
    # 窗口尺寸
    "window_min_width": 1200,
    "window_min_height": 750,
    "window_default_width": 1400,
    "window_default_height": 850,
    
    # 侧边栏
    "sidebar_width": 220,
    "sidebar_bg_color": "#1a1a2e",
    "sidebar_border_color": "#16213e",
    
    # 主题色
    "theme_primary": "#e53e3e",  # 红色主题
    "theme_bg": "#0f0f1a",
    "theme_text": "#e2e8f0",
    "theme_text_muted": "#a0aec0",
    "theme_success": "#68d391",
    "theme_warning": "#f6ad55",
    "theme_error": "#fc8181",
    
    # 字体
    "font_family": "Microsoft YaHei, Arial",
    "font_size_small": 11,
    "font_size_normal": 14,
    "font_size_large": 16,
    "font_size_title": 24,
}


# ==================== 业务规则配置 ====================
BUSINESS_CONFIG = {
    # 视频分析
    "min_play_count_for_analysis": 1000,  # 最小播放量才进行AI分析
    "top_videos_for_batch": 10,  # 批量分析取前N个视频
    
    # 互动率计算
    "engagement_rate_threshold": 5.0,  # 互动率阈值（%）
    "viral_play_count": 1_000_000,  # 爆款播放量阈值
    
    # 钩子类型
    "hook_types": [
        "悬念型",
        "痛点型",
        "挑战型",
        "情感共鸣型",
        "信息价值型",
        "娱乐型",
        "教程干货型",
        "病毒传播型",
        "CP嗑糖型",
        "短时重复刷型",
    ],
    
    # 标签建议
    "hashtag_strategy": {
        "max_count": 5,
        "formula": "1个超大流量标签 + 2个垂直领域标签 + 1-2个话题标签",
    },
    
    # 视频时长建议
    "video_duration": {
        "optimal_min": 15,
        "optimal_max": 30,
        "max_recommended": 60,
    },
}


# ==================== 日志配置 ====================
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "file": "tiktok_monitor.log",
    "max_bytes": 10 * 1024 * 1024,  # 10MB
    "backup_count": 3,
}


# ==================== 配置管理函数 ====================

def get_config(section: str, key: str, default: Any = None) -> Any:
    """
    获取配置值
    
    Args:
        section: 配置节（如 'AI_CONFIG'）
        key: 配置键
        default: 默认值
        
    Returns:
        配置值
    """
    config_sections = {
        "AI_CONFIG": AI_CONFIG,
        "DB_CONFIG": DB_CONFIG,
        "SCRAPER_CONFIG": SCRAPER_CONFIG,
        "SCHEDULER_CONFIG": SCHEDULER_CONFIG,
        "UI_CONFIG": UI_CONFIG,
        "BUSINESS_CONFIG": BUSINESS_CONFIG,
        "LOGGING_CONFIG": LOGGING_CONFIG,
    }
    
    if section not in config_sections:
        return default
    
    return config_sections[section].get(key, default)


def get_ai_config(key: str, default: Any = None) -> Any:
    """获取 AI 配置（快捷方法）"""
    return AI_CONFIG.get(key, default)


def get_db_path() -> str:
    """获取数据库完整路径"""
    if DB_CONFIG["db_path"]:
        return DB_CONFIG["db_path"]
    
    # 使用程序同目录
    import sys
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, DB_CONFIG["db_filename"])


def update_config(section: str, key: str, value: Any) -> bool:
    """
    更新配置值（运行时）
    
    Args:
        section: 配置节
        key: 配置键
        value: 新值
        
    Returns:
        是否成功
    """
    config_sections = {
        "AI_CONFIG": AI_CONFIG,
        "DB_CONFIG": DB_CONFIG,
        "SCRAPER_CONFIG": SCRAPER_CONFIG,
        "SCHEDULER_CONFIG": SCHEDULER_CONFIG,
        "UI_CONFIG": UI_CONFIG,
        "BUSINESS_CONFIG": BUSINESS_CONFIG,
        "LOGGING_CONFIG": LOGGING_CONFIG,
    }
    
    if section not in config_sections:
        return False
    
    if key not in config_sections[section]:
        return False
    
    config_sections[section][key] = value
    return True


# ==================== 便捷常量（向后兼容）====================

# AI 默认模型（供其他模块导入使用）
DEFAULT_AI_MODEL = AI_CONFIG["default_model"]
DEFAULT_AI_TEMPERATURE = AI_CONFIG["temperature"]
DEFAULT_AI_MAX_TOKENS = AI_CONFIG["max_tokens"]

# 抓取默认配置
DEFAULT_MAX_VIDEOS = SCRAPER_CONFIG["max_videos_per_fetch"]
DEFAULT_FETCH_INTERVAL = SCHEDULER_CONFIG["fetch_interval_hours"]
