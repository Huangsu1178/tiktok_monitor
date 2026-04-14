# TikTok Monitor - 配置指南

本指南将帮助你快速配置 TikTok Monitor 项目。

## 📋 目录

- [快速开始](#快速开始)
- [配置方式](#配置方式)
  - [方式一：使用 .env 文件（推荐）](#方式一使用-env-文件推荐)
  - [方式二：使用 config_local.py 文件](#方式二使用-config_localpy-文件)
  - [方式三：使用环境变量](#方式三使用环境变量)
- [详细配置说明](#详细配置说明)
  - [OpenAI API 配置](#openai-api-配置)
  - [代理配置](#代理配置)
  - [其他配置](#其他配置)
- [常见问题](#常见问题)

---

## 快速开始

1. **复制配置模板**

   ```bash
   # 复制 .env 模板
   cp .env.example .env
   
   # 或复制 config_local 模板
   cp config_local.example.py config_local.py
   ```

2. **编辑配置文件**，填入你的 API Key

3. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

4. **运行程序**

   ```bash
   python main.py
   ```

---

## 配置方式

本项目**推荐使用 `.env` 文件**进行配置，简单直观。

### 推荐方式：使用 .env 文件

**优点**：
- ✅ 简单直观，所有配置集中管理
- ✅ 支持所有主要配置项
- ✅ 跨平台兼容性好
- ✅ 易于版本控制（模板文件）

**步骤**：

1. 复制模板文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件：
   ```env
   OPENAI_API_KEY=your-actual-api-key-here
   OPENAI_API_BASE=  # 留空使用官方 API
   ```

3. 保存后运行程序即可

### 可选方式：使用 config_local.py 文件

**适用场景**：
- 需要更多 Python 级别自定义配置
- 旧版本迁移（向后兼容）

> ⚠️ **注意**：新用户强烈建议使用 `.env` 文件，`config_local.py` 仅用于向后兼容。

---

## 详细配置说明

### OpenAI API 配置

#### 获取 API Key

1. 访问 [OpenAI Platform](https://platform.openai.com/api-keys)
2. 登录或注册账号
3. 点击 "Create new secret key"
4. 复制生成的 API Key

#### API Base 配置

- **官方 API**：留空或删除该行
- **第三方代理**：填入代理地址，例如：
  ```
  OPENAI_API_BASE=https://your-proxy.com/v1
  ```

#### 模型选择

默认使用 `gpt-5-chat-latest`，你可以在 `config_local.py` 中修改：

```python
AI_LOCAL_CONFIG = {
    "default_model": "gpt-4o",  # 或其他支持的模型
}
```

### 代理配置

如果你需要代理访问 TikTok，可以配置代理：

**方式一：在 config_local.py 中配置**
```python
SCRAPER_LOCAL_CONFIG = {
    "proxy_url": "http://127.0.0.1:7890",
}
```

**方式二：在 .env 中配置**
```env
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

### 其他配置

项目中还有其他可配置项，都在 [config.py](../config.py) 中：

- **数据库配置**：`DB_CONFIG`
  - 数据库文件默认存放在 `db/tiktok_monitor.db`
  - `db/` 目录会在首次运行时自动创建
  - 数据库文件已被 `.gitignore` 排除，不会被提交到 Git
- **抓取配置**：`SCRAPER_CONFIG`
- **调度器配置**：`SCHEDULER_CONFIG`
- **UI 配置**：`UI_CONFIG`
- **业务规则配置**：`BUSINESS_CONFIG`

一般情况下，使用默认值即可，无需修改。

---

## 常见问题

### Q1: 提示 "API Key 未配置" 怎么办？

确保你已经：
1. 复制了 `.env.example` 为 `.env`
2. 在 `.env` 文件中填入了有效的 API Key
3. 保存文件后重新启动程序

### Q2: 使用第三方代理如何配置？

在 `.env` 文件中添加：
```env
OPENAI_API_BASE=https://your-proxy.com/v1
```

### Q3: 配置文件应该放在哪里？

配置文件应该放在项目根目录，与 `main.py` 同级：

```
tiktok_monitor/
├── main.py
├── config.py
├── .env              ← 放在这里
└── ...
```

### Q4: 为什么我的配置没有生效？

检查以下几点：
1. 文件名是否正确（`.env`）
2. 文件是否在项目根目录
3. 是否正确保存了文件
4. 是否重新启动了程序
5. 查看控制台是否有 "[Config] 已加载 .env 配置文件" 的提示

### Q5: 可以同时使用 .env 和 config_local.py 吗？

可以，`.env` 文件的优先级更高。如果两者都存在：
- `.env` 中的配置会先加载
- `config_local.py` 中的配置会覆盖 `.env` 的同名配置

> 💡 **建议**：只使用一种配置方式，避免混淆。推荐使用 `.env`。

---

## 安全提示

⚠️ **重要**：
- 不要将 `.env` 或 `config_local.py` 文件提交到 Git
- 不要将 API Key 分享给他人
- 定期轮换你的 API Key
- 如果 API Key 泄露，立即在 OpenAI 平台撤销并重新生成

这些文件已经添加到 `.gitignore`，正常情况下不会被提交。

---

## 需要帮助？

如果遇到问题，请：
1. 检查控制台输出的错误信息
2. 查看本指南的常见问题部分
3. 查阅项目的 README.md
4. 提交 Issue 寻求帮助
