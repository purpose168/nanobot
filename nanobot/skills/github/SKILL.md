---
name: github
description: "使用 `gh` 命令行工具与 GitHub 交互。使用 `gh issue`、`gh pr`、`gh run` 和 `gh api` 处理问题（Issues）、拉取请求（PRs）、CI 运行和高级查询。"
metadata: {"nanobot":{"emoji":"🐙","requires":{"bins":["gh"]},"install":[{"id":"brew","kind":"brew","formula":"gh","bins":["gh"],"label":"Install GitHub CLI (brew)"},{"id":"apt","kind":"apt","package":"gh","bins":["gh"],"label":"Install GitHub CLI (apt)"}]}}
---

# GitHub 技能（Skill）

使用 `gh` 命令行工具与 GitHub 交互。当不在 git 目录中时，始终指定 `--repo owner/repo`，或直接使用 URL。

## 拉取请求（Pull Requests）

检查 PR 的 CI 状态：
```bash
gh pr checks 55 --repo owner/repo  # 检查指定仓库中编号为 55 的 PR 的 CI 检查状态
```

列出最近的工作流运行：
```bash
gh run list --repo owner/repo --limit 10  # 列出指定仓库中最近 10 次工作流运行记录
```

查看运行记录并查看哪些步骤失败：
```bash
gh run view <run-id> --repo owner/repo  # 查看指定仓库中特定运行 ID 的详细信息，包括失败的步骤
```

仅查看失败步骤的日志：
```bash
gh run view <run-id> --repo owner/repo --log-failed  # 查看指定仓库中特定运行 ID 的失败步骤日志
```

## API 高级查询

`gh api` 命令对于访问其他子命令无法提供的数据非常有用。

获取包含特定字段的 PR：
```bash
gh api repos/owner/repo/pulls/55 --jq '.title, .state, .user.login'  # 使用 GitHub API 获取编号为 55 的 PR，并提取标题、状态和用户登录名
```

## JSON 输出

大多数命令支持 `--json` 用于结构化输出。您可以使用 `--jq` 进行过滤：

```bash
gh issue list --repo owner/repo --json number,title --jq '.[] | "\(.number): \(.title)"'  # 列出指定仓库中的所有问题，以 JSON 格式返回编号和标题，并使用 jq 过滤输出为"编号: 标题"的格式
```
