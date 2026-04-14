# 🎬 Short Video Monitor - TikTok/抖音双平台监控与分析工具

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 一款本地运行的桌面应用程序，用于追踪TikTok/抖音博主视频表现，AI分析流量钩子，辅助内容创作决策。

## ✨ 核心功能

- 📊 **博主管理**：添加、删除、配置需要监控的博主账号
- ⏰ **定时抓取**：自动抓取博主最新视频数据（可配置间隔）
- 📈 **数据采集**：获取播放量、点赞数、评论数、分享数等关键指标
- 🎥 **无水印下载**：支持视频下载，用于深度内容分析
- 🤖 **AI流量钩子分析**：调用大模型识别开场设计、BGM策略、文案风格等钩子元素
- 📋 **批量规律总结**：对Top视频进行批量分析，提炼爆款内容公式
- 🎯 **双平台支持**：同时支持 TikTok 和 抖音 平台监控

## 🚀 快速开始

### 环境要求

- Python 3.11+
- 操作系统：Windows 10/11、macOS 12+、Ubuntu 20.04+

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd tiktok_monitor

# 2. 安装Python依赖
pip install -r requirements.txt

# 3. 安装Playwright浏览器内核
python -m playwright install chromium

# 4. 配置API密钥（必需）
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API Key

# 5. 运行程序
python main.py
```

> 📖 **详细配置指南**：查阅 [SETUP_GUIDE.md](SETUP_GUIDE.md) 获取完整配置说明

## ⚙️ 配置说明

### 必需配置

**⚠️ 首次使用必须配置 API Key！**

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件
# OPENAI_API_KEY=your-actual-api-key-here
```

### 可选配置

| 配置项 | 说明 | 是否必须 |
|--------|------|----------|
| `OPENAI_API_KEY` | OpenAI API密钥，用于AI分析功能 | ✅ 必需 |
| `OPENAI_API_BASE` | API地址（留空使用官方API） | 可选 |
| `HTTP_PROXY` / `HTTPS_PROXY` | 代理服务器，提高访问稳定性 | 建议配置 |
| `LOG_LEVEL` | 日志级别（DEBUG/INFO/WARNING/ERROR） | 可选 |

### 应用内设置

启动应用后，进入「设置」页面可配置：

- 🔄 抓取间隔：定时抓取的时间间隔
- 🌐 代理服务器：提高TikTok访问稳定性
- 📁 下载路径：视频下载保存目录
- 🎨 主题设置：自定义界面外观

## 📚 详细文档

- [🔧 配置指南](SETUP_GUIDE.md) - 详细的配置说明和常见问题
- [📋 配置管理](CONFIG_GUIDE.md) - 配置文件结构和最佳实践
- [🔄 配置变更](CONFIG_CHANGES.md) - 配置初始化和版本控制说明

## 🏗️ 技术架构

```
tiktok_monitor/
├── main.py                 # 主程序入口（PyQt6应用）
├── config.py               # 统一配置管理
├── requirements.txt        # Python依赖清单
├── .env.example            # 环境变量配置模板
│
├── db/                     # 数据库目录
│   └── tiktok_monitor.db   # SQLite数据库文件（自动生成）
│
├── core/                   # 核心功能模块
│   ├── scraper.py          # 数据抓取（yt-dlp + Playwright）
│   ├── ai_analyzer.py      # AI流量钩子分析
│   ├── scheduler.py        # 定时任务调度
│   └── platforms.py        # 多平台支持
│
├── data/                   # 数据管理
│   └── database.py         # SQLite数据库操作
│
├── skills/                 # AI技能模块
│   ├── tiktok_ai_analysis.py   # TikTok AI分析
│   ├── hook_research.py        # 钩子研究
│   ├── format_research.py      # 格式研究
│   ├── content_pipeline.py     # 内容流水线
│   └── skill_registry.py       # 技能注册表
│
└── ui/                     # 用户界面
    ├── main_window.py          # 主窗口
    ├── dashboard_page.py       # 仪表盘
    ├── influencer_page.py      # 博主管理
    ├── data_view_page.py       # 数据视图
    ├── ai_report_page.py       # AI分析报告
    └── settings_page.py        # 设置页面
```

## 🔍 数据抓取策略

本工具采用双模式数据抓取策略：

1. **yt-dlp模式（默认）**：通过yt-dlp获取结构化数据，速度快、数据完整
2. **Playwright模式（备选）**：浏览器自动化模拟用户访问，拦截网络请求获取数据

## 🛡️ 配置优先级

系统按以下优先级加载配置（高优先级覆盖低优先级）：

1. `.env` 文件（如果存在）
2. `config_local.py` 文件（如果存在）
3. 系统环境变量
4. `config.py` 中的默认值

## ⚠️ 注意事项

- 本工具仅用于个人学习和内容创作研究，请遵守各平台使用条款
- 建议配置代理以提高数据抓取的稳定性
- AI分析功能需要有效的OpenAI API Key
- `.env` 和 `config_local.py` 包含敏感信息，已添加到 `.gitignore`，请勿提交到版本控制系统

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [OpenAI](https://openai.com/) - 提供AI分析能力
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 视频下载工具
- [Playwright](https://playwright.dev/) - 浏览器自动化
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - 桌面应用框架

---

<div align="center">
  <sub>Built with ❤️ by Manus AI</sub>
</div>
