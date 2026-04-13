# TikTok Monitor 配置管理说明

## 📋 概述

所有配置项已统一管理在 `config.py` 文件中，避免了硬编码问题。

## 🔧 配置文件位置

```
tiktok_monitor/
└── config.py  # 统一配置文件
```

## 📦 配置分类

### 1. AI 模型配置 (`AI_CONFIG`)

```python
AI_CONFIG = {
    "default_model": "gpt-5-chat-latest",  # 默认模型
    "api_base": "",                         # API地址（留空使用OpenAI官方）
    "api_key": "",                          # API密钥
    "temperature": 0.7,                     # 温度参数
    "max_tokens": 1500,                     # 最大token数
    # ... 更多参数
}
```

**修改默认模型**：只需修改 `default_model` 即可全局生效。

### 2. 数据库配置 (`DB_CONFIG`)

```python
DB_CONFIG = {
    "db_filename": "tiktok_monitor.db",
    "db_path": "",  # 留空使用程序同目录
}
```

### 3. 抓取配置 (`SCRAPER_CONFIG`)

```python
SCRAPER_CONFIG = {
    "default_strategy": "yt-dlp",
    "max_videos_per_fetch": 20,
    # ...
}
```

### 4. 调度器配置 (`SCHEDULER_CONFIG`)

```python
SCHEDULER_CONFIG = {
    "auto_fetch_enabled": False,
    "fetch_interval_hours": 1.0,
    # ...
}
```

### 5. UI 配置 (`UI_CONFIG`)

```python
UI_CONFIG = {
    "window_min_width": 1200,
    "theme_primary": "#e53e3e",
    # ...
}
```

### 6. 业务规则配置 (`BUSINESS_CONFIG`)

```python
BUSINESS_CONFIG = {
    "min_play_count_for_analysis": 1000,
    "top_videos_for_batch": 10,
    "hook_types": [...],
    # ...
}
```

## 🎯 使用方式

### 在代码中使用配置

```python
# 方法1: 导入便捷常量
from config import DEFAULT_AI_MODEL, DEFAULT_MAX_VIDEOS

# 方法2: 使用配置函数
from config import get_config, get_ai_config

model = get_ai_config("default_model")
max_videos = get_config("SCRAPER_CONFIG", "max_videos_per_fetch")

# 方法3: 直接导入配置字典
from config import AI_CONFIG

model = AI_CONFIG["default_model"]
```

### 修改默认配置

**方式1: 修改配置文件（推荐）**
```python
# config.py
AI_CONFIG = {
    "default_model": "gpt-4o-mini",  # 改这里即可
    ...
}
```

**方式2: 运行时修改**
```python
from config import update_config

update_config("AI_CONFIG", "default_model", "gpt-4o-mini")
```

**方式3: 通过设置页面（用户友好）**
- 打开程序 → 设置页面 → AI模型配置
- 修改后保存到数据库，下次启动自动加载

## 🔄 配置优先级

1. **用户设置**（数据库）> 2. **环境变量** > 3. **配置文件默认值**

示例：
```python
# 优先使用数据库中的设置
model = get_setting("openai_model", DEFAULT_AI_MODEL)

# 如果数据库没有，使用环境变量
api_key = os.environ.get("OPENAI_API_KEY", "")

# 最后使用配置文件默认值
temperature = AI_CONFIG["temperature"]
```

## ✅ 已更新的模块

以下模块已改为使用配置常量，不再硬编码：

- ✅ `skills/tiktok_ai_analysis.py`
- ✅ `skills/hook_research.py`
- ✅ `skills/format_research.py`
- ✅ `skills/content_pipeline.py`
- ✅ `skills/skill_registry.py`
- ✅ `core/ai_analyzer.py`
- ✅ `ui/main_window.py`
- ✅ `ui/settings_page.py`

## 💡 最佳实践

1. **新增配置项**：添加到 `config.py` 对应的配置字典中
2. **修改默认值**：只修改 `config.py`，不要在各处硬编码
3. **使用配置**：导入 `DEFAULT_AI_MODEL` 等便捷常量
4. **用户可配置**：通过设置页面保存到数据库

## 📝 示例：添加新配置

```python
# 1. 在 config.py 中添加
AI_CONFIG = {
    ...
    "new_feature_enabled": True,  # 新增配置
}

# 添加便捷常量
NEW_FEATURE_ENABLED = AI_CONFIG["new_feature_enabled"]

# 2. 在代码中使用
from config import NEW_FEATURE_ENABLED

if NEW_FEATURE_ENABLED:
    # 执行新功能
    pass
```

## 🎉 优势

1. **集中管理**：所有配置在一处，易于维护
2. **类型安全**：使用字典结构，IDE 有提示
3. **灵活扩展**：新增配置只需修改一处
4. **避免硬编码**：消除散布在各处的魔法值
5. **用户友好**：支持运行时修改和持久化
