"""
TikTok Monitor - 统一配置管理
所有默认配置项集中管理，避免硬编码
"""
import os
import shutil
from typing import Dict, Any


# ==================== 环境文件管理 ====================

def _ensure_env_file():
    """确保 .env 文件存在，不存在则从 .env.example 复制"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, '.env')
    env_example_path = os.path.join(base_dir, '.env.example')
    
    if not os.path.exists(env_path):
        if os.path.exists(env_example_path):
            shutil.copy2(env_example_path, env_path)
            print(f"[Config] ✅ 已从 .env.example 创建 .env 文件")
            return True
        else:
            print(f"[Config] ⚠️ 警告: .env 和 .env.example 均不存在")
            return False
    else:
        print(f"[Config] ✅ .env 文件已存在")
        return False


def _load_dotenv_file():
    """加载 .env 文件到环境变量，每次启动强制重载"""
    print("[Config] 🔍 开始加载配置文件...")
    
    try:
        from dotenv import load_dotenv
        
        # 确保 .env 文件存在
        _ensure_env_file()
        
        # 加载 .env 文件（强制覆盖已存在的环境变量）
        base_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(base_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            print(f"[Config] ✅ 成功加载 .env 文件: {env_path}")
            
            # 输出加载的关键配置（隐藏敏感信息）
            if os.environ.get('PROXY_URL') or os.environ.get('HTTP_PROXY'):
                proxy = os.environ.get('PROXY_URL') or os.environ.get('HTTP_PROXY')
                print(f"[Config] 📝 PROXY: {proxy}")
            
            return True
        else:
            print(f"[Config] ❌ 错误: .env 文件不存在于 {env_path}")
            return False
    except ImportError:
        print("[Config] ⚠️ python-dotenv 未安装，跳过 .env 加载")
        print("[Config] 💡 请运行: pip install python-dotenv")
        return False


def _sync_env_file(key: str, value: str):
    """同步更新 .env 文件中的配置项"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, '.env')
    
    if not os.path.exists(env_path):
        print(f"[Config] 🔄 .env 文件不存在，正在创建...")
        _ensure_env_file()
    
    # 读取现有内容
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    
    # 查找并更新或添加配置项
    key_found = False 
    new_lines = []
    for line in lines:
        stripped = line.strip()
        # 跳过空行和注释行，但保留它们
        if not stripped or stripped.startswith('#'):
            new_lines.append(line)
            continue
        
        # 检查是否是目标 key
        if '=' in stripped:
            current_key = stripped.split('=', 1)[0].strip()
            if current_key == key:
                # 保留注释（如果有）
                comment = ''
                if '#' in line:
                    comment = ' #' + line.split('#', 1)[1].rstrip('\n')
                new_lines.append(f"{key}={value}{comment}\n")
                key_found = True
                continue
        
        new_lines.append(line)
    
    # 如果 key 不存在，添加到文件末尾
    if not key_found:
        # 确保文件末尾有空行
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines.append('\n')
        new_lines.append(f"{key}={value}\n")
    
    # 写回文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    # 输出日志（隐藏敏感值）
    if 'KEY' in key or 'SECRET' in key or 'PASSWORD' in key:
        display_value = '***' if value else '(empty)'
    else:
        display_value = value if value else '(empty)'
    print(f"[Config] ✅ 已更新 .env: {key}={display_value}")


# 程序启动时立即加载 .env 文件
print("[Config] " + "="*50)
print("[Config] 🚀 TikTok Monitor 配置初始化")
print("[Config] " + "="*50)
_load_dotenv_file()


# ==================== AI 模型配置 ====================
AI_CONFIG = {
    # 默认使用的模型名称
    "default_model": "gemini-2.0-flash",
    
    # Gemini 配置
    "gemini_api_key": "",
    "gemini_model": "gemini-2.0-flash",
    
    # 请求参数
    "temperature": 0.7,
    "max_tokens": 8192,  # 单视频分析（适配 thinking model 需要更大配额）
    "max_tokens_batch": 16384,  # 批量分析需要更多输出空间（适配 thinking model）
    "max_tokens_ab_comparison": 16384,  # AB对比分析需要大量输出空间
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
    "db_path": "",  # 留空则使用 db/ 子目录
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
    
    # 使用 db/ 子目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(base_dir, "db")
    
    # 确保 db 目录存在
    os.makedirs(db_dir, exist_ok=True)
    
    return os.path.join(db_dir, DB_CONFIG["db_filename"])


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


# ==================== 从环境变量更新配置 ====================
# .env 文件已在模块顶部加载，这里从 os.environ 读取并更新配置
print("[Config] 🔄 开始应用配置到各模块...")

# Gemini 配置
if os.environ.get('GEMINI_API_KEY'):
    AI_CONFIG['gemini_api_key'] = os.environ['GEMINI_API_KEY']
    print(f"[Config] ✅ Gemini配置: api_key 已设置")
if os.environ.get('GEMINI_MODEL'):
    AI_CONFIG['gemini_model'] = os.environ['GEMINI_MODEL']
    print(f"[Config] ✅ Gemini配置: model = {os.environ['GEMINI_MODEL']}")

# 代理配置（仅从 .env 读取，不使用系统环境变量）
if os.environ.get('PROXY_URL'):
    SCRAPER_CONFIG['proxy_url'] = os.environ['PROXY_URL']
    print(f"[Config] ✅ 代理配置: proxy_url = {os.environ['PROXY_URL']}")
elif os.environ.get('HTTP_PROXY'):
    SCRAPER_CONFIG['proxy_url'] = os.environ['HTTP_PROXY']
    print(f"[Config] ✅ 代理配置: 使用 HTTP_PROXY = {os.environ['HTTP_PROXY']}")
else:
    print(f"[Config] ℹ️  代理配置: 未设置")

# 日志配置
if os.environ.get('LOG_LEVEL'):
    LOGGING_CONFIG['level'] = os.environ['LOG_LEVEL']
    print(f"[Config] ✅ 日志配置: level = {os.environ['LOG_LEVEL']}")

# 调度器配置
if os.environ.get('AUTO_FETCH_ENABLED'):
    enabled = os.environ['AUTO_FETCH_ENABLED'] == '1' or os.environ['AUTO_FETCH_ENABLED'].lower() == 'true'
    SCHEDULER_CONFIG['auto_fetch_enabled'] = enabled
    print(f"[Config] ✅ 调度器: auto_fetch = {enabled}")
if os.environ.get('FETCH_INTERVAL'):
    try:
        SCHEDULER_CONFIG['fetch_interval_hours'] = float(os.environ['FETCH_INTERVAL'])
        print(f"[Config] ✅ 调度器: interval = {os.environ['FETCH_INTERVAL']}h")
    except ValueError:
        print(f"[Config] ⚠️ 调度器: FETCH_INTERVAL 值无效: {os.environ['FETCH_INTERVAL']}")

# 抓取配置
if os.environ.get('MAX_VIDEOS_PER_FETCH'):
    try:
        SCRAPER_CONFIG['max_videos_per_fetch'] = int(os.environ['MAX_VIDEOS_PER_FETCH'])
        print(f"[Config] ✅ 抓取配置: max_videos = {os.environ['MAX_VIDEOS_PER_FETCH']}")
    except ValueError:
        print(f"[Config] ⚠️ 抓取配置: MAX_VIDEOS_PER_FETCH 值无效: {os.environ['MAX_VIDEOS_PER_FETCH']}")

# 下载路径
if os.environ.get('DOWNLOAD_PATH'):
    SCRAPER_CONFIG['download_path'] = os.environ['DOWNLOAD_PATH']
    print(f"[Config] ✅ 下载路径: {os.environ['DOWNLOAD_PATH']}")

print("[Config] " + "="*50)


# ==================== 配置同步函数 ====================

def sync_config_to_env(section: str, key: str, value: Any) -> bool:
    """
    将配置更改同步到 .env 文件
    
    Args:
        section: 配置节（如 'AI_CONFIG'）
        key: 配置键（代码中的键名）
        value: 配置值
        
    Returns:
        是否成功同步
    """
    # 配置项映射：代码中的键名 -> .env 中的键名
    config_mapping = {
        ('AI_CONFIG', 'gemini_api_key'): 'GEMINI_API_KEY',
        ('AI_CONFIG', 'gemini_model'): 'GEMINI_MODEL',
        ('SCRAPER_CONFIG', 'proxy_url'): 'PROXY_URL',
        ('SCRAPER_CONFIG', 'max_videos_per_fetch'): 'MAX_VIDEOS_PER_FETCH',
        ('SCRAPER_CONFIG', 'download_path'): 'DOWNLOAD_PATH',
        ('SCHEDULER_CONFIG', 'auto_fetch_enabled'): 'AUTO_FETCH_ENABLED',
        ('SCHEDULER_CONFIG', 'fetch_interval_hours'): 'FETCH_INTERVAL',
        ('LOGGING_CONFIG', 'level'): 'LOG_LEVEL',
    }
    
    env_key = config_mapping.get((section, key))
    if not env_key:
        print(f"[Config] ⚠️ 同步配置: 未找到映射 {section}.{key}")
        return False
    
    # 转换值为字符串
    if isinstance(value, bool):
        str_value = '1' if value else '0'
    else:
        str_value = str(value)
    
    # 同步到 .env 文件
    _sync_env_file(env_key, str_value)
    
    # 同步到 os.environ
    os.environ[env_key] = str_value
    
    # 输出日志（隐藏敏感值）
    if 'KEY' in env_key or 'SECRET' in env_key or 'PASSWORD' in env_key:
        display_value = '***' if str_value else '(empty)'
    else:
        display_value = str_value if str_value else '(empty)'
    print(f"[Config] 🔄 同步配置: {section}.{key} -> {env_key}={display_value}")
    
    return True


# ==================== 从 config_local.py 加载（向后兼容）====================
try:
    from config_local import AI_LOCAL_CONFIG, SCRAPER_LOCAL_CONFIG
    AI_CONFIG.update(AI_LOCAL_CONFIG)
    SCRAPER_CONFIG.update(SCRAPER_LOCAL_CONFIG)
    print("[Config] 已加载本地配置 (config_local.py)")
except ImportError:
    # config_local.py 不存在，使用默认配置
    pass
