# TikTok Monitor - 博主监控与流量分析工具

## 功能概述

TikTok Monitor 是一款本地运行的桌面应用程序，用于追踪指定TikTok博主账号的视频表现，分析流量钩子，辅助内容创作决策。

### 核心功能

- **博主管理**：添加、删除、配置需要监控的TikTok博主账号
- **定时抓取**：每1小时（可配置）自动抓取指定博主最新视频数据
- **数据采集**：获取视频播放量、点赞数、评论数、分享数等关键指标
- **无水印下载**：支持无水印视频下载，用于深度内容分析
- **AI流量钩子分析**：调用大模型对高表现视频进行分析，识别开场设计、BGM策略、文案风格等钩子元素
- **批量规律总结**：对博主Top10视频进行批量分析，提炼爆款内容公式

## 安装与运行

### 环境要求

- Python 3.11+
- 操作系统：Windows 10/11、macOS 12+、Ubuntu 20.04+

### 安装步骤

```bash
# 1. 克隆或下载项目
cd tiktok_monitor

# 2. 安装Python依赖
pip install -r requirements.txt

# 3. 安装Playwright浏览器内核
python -m playwright install chromium

# 4. 运行程序
python main.py
```

### 配置说明

首次运行后，进入「设置」页面配置：

| 配置项 | 说明 | 是否必须 |
|--------|------|----------|
| OpenAI API Key | 用于AI流量钩子分析功能 | 可选（不配置则使用模拟分析） |
| 抓取间隔 | 定时抓取的时间间隔，默认1小时 | 可选 |
| 代理服务器 | 提高TikTok访问稳定性 | 建议配置 |
| 下载路径 | 视频下载保存目录 | 可选 |

## 技术架构

```
tiktok_monitor/
├── main.py              # 主程序入口
├── requirements.txt     # 依赖清单
├── core/
│   ├── scraper.py       # TikTok数据抓取模块（Playwright + API）
│   ├── ai_analyzer.py   # AI流量钩子分析模块
│   └── scheduler.py     # 定时任务调度模块
├── data/
│   └── database.py      # SQLite数据库管理
└── ui/
    ├── main_window.py   # 主窗口
    ├── dashboard_page.py    # 仪表盘页面
    ├── influencer_page.py   # 博主管理页面
    ├── data_view_page.py    # 数据视图页面
    ├── ai_report_page.py    # AI分析报告页面
    └── settings_page.py     # 设置页面
```

## 数据抓取说明

本工具采用双模式数据抓取策略：

1. **API模式（优先）**：通过内置数据接口获取结构化数据，速度快、数据完整
2. **Playwright模式（备选）**：通过浏览器自动化模拟用户访问，拦截网络请求获取数据

## 注意事项

- 本工具仅用于个人学习和内容创作研究，请遵守TikTok使用条款
- 建议配置代理以提高数据抓取的稳定性
- AI分析功能需要有效的OpenAI API Key，不配置时将使用基于规则的模拟分析

---
*版本：v1.0.0 MVP | 作者：Manus AI*
