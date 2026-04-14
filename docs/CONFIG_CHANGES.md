# 配置初始化说明

## 分支目的

`chore-config` 分支用于为 GitHub 项目创建完整的初始配置模板，方便其他开发者拉取项目后快速配置和运行。

## 变更内容

### 1. 新增文件

#### `db/.gitkeep`
- 确保 `db/` 目录在版本控制中被保留
- 数据库文件 `tiktok_monitor.db` 会被 `.gitignore` 排除
- 首次运行时会自动创建数据库文件

#### `.env.example`
- OpenAI API 配置模板
- 代理配置模板
- 日志级别配置
- 使用方式：复制为 `.env` 并填入实际配置

#### `SETUP_GUIDE.md`
- 详细的配置指南文档
- 包含三种配置方式说明
- 常见问题解答
- 安全提示

### 2. 修改文件

#### `config.py`
- 更新 `DB_CONFIG` 配置注释，说明默认使用 `db/` 子目录
- 修改 `get_db_path()` 函数，默认将数据库文件存放在 `db/` 目录
- 自动创建 `db/` 目录（如果不存在）

#### `data/database.py`
- 修改数据库路径获取方式，使用 `config.py` 中的 `get_db_path()` 函数
- 统一数据库路径管理，避免硬编码

#### `.gitignore`
- 修改 `*.env` 为 `!.env.example`
- 确保 `.env.example` 模板文件可以被提交到 Git
- 保持 `.env` 文件被忽略（不提交敏感信息）

#### `requirements.txt`
- 添加 `python-dotenv>=1.0.0` 依赖
- 支持 `.env` 文件自动加载

#### `README.md`
- 更新配置说明部分
- 添加配置步骤和示例
- 链接到详细配置指南

### 3. 已有文件（无需修改）

#### `config_local.example.py`
- 已存在的本地配置模板
- 包含 AI 配置和代理配置示例
- 已正确添加到 `.gitignore`

#### `config.py`
- 主配置文件
- 包含所有默认配置项
- 支持加载 `config_local.py` 覆盖配置

## 配置优先级

系统按以下优先级加载配置（高优先级覆盖低优先级）：

1. `.env` 文件（如果存在）
2. `config_local.py` 文件（如果存在）
3. 系统环境变量
4. `config.py` 中的默认值

## 合并到 main 分支

此分支应该合并到 `main` 分支，以便：

✅ 新开发者拉取项目时有配置模板参考  
✅ 提供清晰的配置文档和指南  
✅ 确保敏感配置文件不会被提交  
✅ 统一项目的配置管理方式  

## 使用流程

新开发者克隆项目后：

```bash
# 1. 克隆项目
git clone <repository-url>
cd tiktok_monitor

# 2. 复制配置模板
cp .env.example .env
# 或
cp config_local.example.py config_local.py

# 3. 编辑配置文件，填入 API Key
# 使用编辑器打开 .env 或 config_local.py

# 4. 安装依赖
pip install -r requirements.txt

# 5. 安装 Playwright
python -m playwright install chromium

# 6. 运行程序
python main.py
```

## 安全说明

⚠️ **以下文件已添加到 `.gitignore`，不会被提交：**
- `.env`
- `config_local.py`
- `.env.local`
- `*.db`
- `*.log`

✅ **以下文件会被提交到 Git：**
- `.env.example`（配置模板）
- `config_local.example.py`（配置模板）
- `SETUP_GUIDE.md`（配置指南）

## 测试建议

合并前建议测试：

1. 在没有配置文件的干净环境中测试
2. 验证配置模板是否可以正常复制和使用
3. 确认程序在没有配置时的错误提示是否友好
4. 测试不同配置方式的优先级是否正确
