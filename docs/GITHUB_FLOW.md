# GitHub Flow for `tiktok_monitor`

本项目采用精简版 GitHub Flow。

## 1. 分支模型

- `main`
  - 唯一长期存在的稳定分支
  - 保持可发布、可运行
  - 所有功能、修复都通过 Pull Request 合并回 `main`

以下均为短生命周期分支，合并后删除：

- `feature/<name>`: 新功能开发
- `fix/<name>`: 常规缺陷修复
- `hotfix/<name>`: 线上紧急修复
- `refactor/<name>`: 重构但不改变行为
- `docs/<name>`: 文档调整
- `chore/<name>`: 工具、依赖、脚本、配置维护
- `test/<name>`: 测试补充或测试结构调整

## 2. 命名规范

分支名称建议使用小写中划线，避免空格和中文。

示例：

- `feature/ai-report-export`
- `fix/dashboard-empty-state`
- `hotfix/openai-timeout`
- `chore/update-playwright`

## 3. 日常流程

1. 保持 `main` 最新
2. 从 `main` 拉出短分支
3. 在短分支开发并提交
4. 推送到远端并发起 PR
5. 通过 review 后合并到 `main`
6. 删除远端和本地短分支

## 4. 推荐命令

### 直接创建功能分支

```powershell
git switch main
git pull origin main
git switch -c feature/ai-report-export
```

### 推荐方式：配合 worktree 创建独立目录

```powershell
pwsh ./scripts/new-github-flow-branch.ps1 -Type feature -Name ai-report-export
```

脚本会：

- 基于 `main` 创建分支
- 自动生成一个独立 worktree 目录
- 避免你在当前目录频繁切分支

### 合并后清理

```powershell
pwsh ./scripts/remove-github-flow-branch.ps1 -Branch feature/ai-report-export -DeleteBranch
```

## 5. 提交和 PR 约定

- 一个分支只做一件事
- 小步提交，提交信息说明“做了什么”
- PR 标题与分支目标保持一致
- 合并前至少确认：
  - 功能可运行
  - 关键路径无明显回归
  - 如有 UI 变化，附截图
  - 如有配置变化，更新文档

## 6. 合并策略

推荐在 GitHub 上使用 `Squash and merge`：

- 保持 `main` 历史简洁
- 一个 PR 对应一个合并提交
- 方便后续回滚和追踪

## 7. 不建议创建的长期分支

本项目不建议维护以下长期分支：

- `develop`
- `release`
- `test`

原因是 GitHub Flow 的核心就是：

- 只有一个长期稳定分支 `main`
- 其余分支快速创建、快速合并、快速删除

## 8. GitHub 仓库建议设置

在 GitHub 仓库设置中，建议对 `main` 开启以下保护：

- Require a pull request before merging
- Require approvals
- Dismiss stale approvals when new commits are pushed
- Require status checks to pass before merging
- Restrict force pushes
- Restrict deletions

如果当前阶段只有你一个人维护仓库，最少也建议开启：

- 必须通过 PR 合并
- 禁止直接 force push 到 `main`

## 9. 本项目建议

结合当前仓库结构，建议按模块拆分分支主题：

- `feature/ui-*`: UI 页面与交互
- `feature/core-*`: 抓取、调度、分析核心逻辑
- `feature/data-*`: 数据库和数据层
- `feature/skills-*`: AI/技能流水线能力
- `chore/config-*`: 配置、依赖、脚本维护

示例：

- `feature/ui-report-polish`
- `feature/core-scheduler-retry`
- `feature/data-index-tuning`
- `feature/skills-hook-analysis`

