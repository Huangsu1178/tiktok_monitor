# Gemini API 配置指南

## 概述

TikTok Monitor 现在支持 **Gemini API** 和 **OpenAI API**，并**优先使用 Gemini**。

## 为什么选择 Gemini？

✅ **免费额度更高**：Gemini 提供更大的免费使用额度  
✅ **速度更快**：gemini-2.0-flash 模型响应速度优秀  
✅ **质量优秀**：Google 最新的 AI 模型，分析质量出色  
✅ **成本更低**：相比 OpenAI，Gemini 的性价比更高

## 获取 Gemini API Key

1. 访问 [Google AI Studio](https://aistudio.google.com/apikey)
2. 使用 Google 账号登录
3. 点击 "Create API Key"
4. 复制生成的 API Key

## 配置方法

### 方法一：直接编辑 .env 文件（推荐）

打开 `.env` 文件，添加以下配置：

```env
# Gemini 配置（推荐使用）
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash

# OpenAI 配置（备选）
OPENAI_API_KEY=your-openai-api-key-here  # 可选
```

### 方法二：通过设置界面

1. 启动 TikTok Monitor
2. 进入 **设置页面**
3. 在 **AI 分析配置** 部分：
   - 填写 **Gemini API Key**（推荐）
   - 选择 **Gemini 模型**（默认：gemini-2.0-flash）
   - （可选）填写 OpenAI 配置作为备选
4. 点击 **保存设置**

## 可用模型

| 模型 | 特点 | 推荐场景 |
|------|------|----------|
| `gemini-2.5-flash` | 最新模型，速度和成本最优 | 日常分析（推荐）|
| `gemini-2.5-pro` | 最新高质量模型 | 复杂分析任务 |
| `gemini-2.0-flash` | 速度快，成本低 | 日常分析（默认）|
| `gemini-2.0-pro` | 质量更高 | 复杂分析任务 |
| `gemini-1.5-pro` | 长上下文 | 需要理解长视频内容 |

## 配置优先级

系统会按以下顺序选择 AI 服务：

1. **Gemini API**（如果配置了 GEMINI_API_KEY）
2. **OpenAI API**（如果配置了 OPENAI_API_KEY）
3. **不可用**（如果都没配置）

## 安装依赖

如果还没有安装 Gemini SDK，运行：

```bash
pip install google-generativeai>=0.3.0
```

或重新安装所有依赖：

```bash
pip install -r requirements.txt
```

## 验证配置

启动应用后，查看控制台输出：

```
[Config] ✅ Gemini配置: api_key 已设置
[Config] ✅ Gemini配置: model = gemini-2.0-flash
[AI Client] ✅ Gemini 客户端已初始化: gemini-2.0-flash
```

如果看到以上输出，说明 Gemini 配置成功！

## 故障排除

### 问题：Gemini 初始化失败

**可能原因：**
- API Key 不正确
- 网络无法访问 Google API
- 未安装 `google-generativeai` 包

**解决方法：**
1. 检查 API Key 是否正确
2. 确认网络可以访问 `generativelanguage.googleapis.com`
3. 运行 `pip install google-generativeai`

### 问题：想切换回 OpenAI

**方法：**
1. 清空 `GEMINI_API_KEY`（留空）
2. 填写 `OPENAI_API_KEY`
3. 保存设置并重启应用

系统会自动使用 OpenAI 作为 AI 服务。

## 性能对比

| 特性 | Gemini 2.0 Flash | OpenAI GPT-4o |
|------|------------------|---------------|
| 响应速度 | ⚡ 非常快 | 快 |
| 分析质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 免费额度 | 15 RPM / 1M TPM | $5 信用额度 |
| 成本 | 免费额度内 $0 | $0.005/1K tokens |

## 技术支持

如有问题，请查看：
- 完整配置指南：`SETUP_GUIDE.md`
- 环境变量模板：`.env.example`
