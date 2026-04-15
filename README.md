# Short Video Monitor

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![SQLite](https://img.shields.io/badge/database-SQLite-0f766e.svg)](https://www.sqlite.org/)

本项目是一个本地运行的桌面应用，用于监控 TikTok / 抖音账号、抓取视频数据，并结合 Gemini 模型生成结构化 AI 分析报告，帮助做选题、拆解爆款和内容复盘。

## 核心能力

- 双平台账号监控：统一管理 TikTok 和抖音账号
- 视频数据抓取：采集播放、点赞、评论、分享、发布时间等字段
- 自动调度：支持按间隔定时抓取，也支持手动立即抓取
- 无水印下载：支持下载视频到本地做进一步分析
- AI 报告中心：支持单视频分析、批量规律分析、AB 对比分析、历史报告回看
- 本地数据存储：使用 SQLite 保存账号、视频、抓取日志和 AI 报告
- 设置页可视化配置：支持在界面中修改 Gemini、代理、下载路径、抓取间隔等设置

## 当前技术栈

- Python 3.11+
- PyQt6
- Playwright
- yt-dlp
- APScheduler
- google-generativeai
- SQLite

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. 配置环境变量

推荐先复制模板文件：

```powershell
Copy-Item .env.example .env
```

然后至少填写以下配置：

```env
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
```

说明：

- `GEMINI_API_KEY` 为 AI 分析必填项
- `GEMINI_MODEL` 可选，未显式设置时代码默认使用 `gemini-2.0-flash`
- 应用启动时如果发现缺少 `.env`，会尝试从 `.env.example` 自动生成

### 3. 启动应用

```bash
python main.py
```

## 环境变量说明

项目当前主要使用 Gemini 配置，常用项如下：

| 变量名 | 说明 | 是否必填 |
| --- | --- | --- |
| `GEMINI_API_KEY` | Gemini API Key | 是 |
| `GEMINI_MODEL` | 使用的模型名，例如 `gemini-2.5-flash` | 否 |
| `MAX_VIDEOS_PER_FETCH` | 每次抓取的最大视频数 | 否 |
| `AUTO_FETCH_ENABLED` | 是否启用自动抓取，`0` 或 `1` | 否 |
| `FETCH_INTERVAL` | 自动抓取间隔，单位小时 | 否 |
| `DOWNLOAD_PATH` | 视频下载目录 | 否 |
| `PROXY_URL` | 抓取时使用的代理地址 | 否 |
| `LOG_LEVEL` | 日志级别，如 `INFO`、`DEBUG` | 否 |

示例：

```env
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
MAX_VIDEOS_PER_FETCH=20
AUTO_FETCH_ENABLED=0
FETCH_INTERVAL=1.0
DOWNLOAD_PATH=
PROXY_URL=
LOG_LEVEL=INFO
```

## 使用流程

### 1. 添加监控账号

- TikTok 支持输入用户名或主页链接
- 抖音建议输入主页链接或分享链接
- 账号添加后会保存到本地 SQLite 数据库

### 2. 抓取视频数据

- 可在账号管理页对单个账号立即抓取
- 也可一键抓取全部启用中的账号
- 启用自动抓取后，调度器会按设置的间隔执行任务

### 3. 生成 AI 报告

AI 报告中心目前包含四种模式：

- 单视频分析：拆解某条视频的钩子、结构、文案与复用建议
- 批量规律分析：总结多条视频的共性特征和内容规律
- AB 对比分析：比较两组视频的表现差异和优化方向
- 历史报告：查看已保存的结构化报告，并支持再次打开

## 页面概览

- 仪表盘：查看监控账号数、视频总量、今日新增、近期抓取记录和热门视频
- 账号管理：添加、删除、抓取 TikTok / 抖音账号
- 数据视图：查看某个账号下的已采集视频数据
- AI 分析报告：进入单视频、批量、AB 对比和历史报告模式
- 设置：配置 Gemini、代理、自动抓取、下载目录等

## 抓取策略

项目内置两类抓取方式：

- `yt-dlp`：默认用于 TikTok，速度快，能直接提取结构化视频信息
- `Playwright`：用于页面访问、回退抓取，以及抖音页面解析

如果配置了代理，会同时用于 Playwright 和 yt-dlp 抓取流程。

## 数据存储

数据库文件默认位于：

```text
db/tiktok_monitor.db
```

当前会存储以下内容：

- `influencers`：监控账号
- `videos`：视频数据
- `fetch_logs`：抓取记录
- `ai_analysis`：单条视频分析结果
- `ai_reports`：结构化 AI 报告
- `ab_comparison`：AB 对比结果
- `hook_library`：钩子素材库

## 项目结构

```text
tiktok_monitor/
├── main.py
├── config.py
├── requirements.txt
├── .env.example
├── core/
│   ├── scraper.py
│   ├── scheduler.py
│   ├── platforms.py
│   └── ai_analyzer.py
├── data/
│   └── database.py
├── db/
├── skills/
├── ui/
│   ├── components/
│   ├── dialogs/
│   └── pages/
└── docs/
```

## 相关文档

- [安装与配置指南](docs/SETUP_GUIDE.md)
- [Gemini 配置说明](docs/GEMINI_SETUP.md)
- [配置管理说明](docs/CONFIG_GUIDE.md)
- [配置变更记录](docs/CONFIG_CHANGES.md)
- [AB 对比迁移说明](AB_COMPARISON_MIGRATION.md)

## 注意事项

- 本项目为本地桌面工具，抓取稳定性会受到网络、代理和平台页面变更影响
- AI 分析功能依赖有效的 Gemini API Key
- `.env` 中包含敏感信息，请勿提交到版本库
- 使用 TikTok / 抖音数据时请遵守对应平台条款与当地法律法规

## 开发与调试

常用命令：

```bash
pip install -r requirements.txt
python -m playwright install chromium
python main.py
```

如果你在首次运行时遇到浏览器相关报错，通常重新执行一次 `python -m playwright install chromium` 即可。
