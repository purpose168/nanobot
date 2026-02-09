---
name: tmux
description: 通过发送按键和抓取窗格输出来远程控制 tmux 会话，用于交互式命令行界面（CLI）。
metadata: {"nanobot":{"emoji":"🧵","os":["darwin","linux"],"requires":{"bins":["tmux"]}}}
---

# tmux 技能（Skill）

仅在需要交互式 TTY 时使用 tmux。对于长时间运行、非交互式任务，优先使用 exec 后台模式。

## 快速开始（独立套接字，exec 工具）

```bash
SOCKET_DIR="${NANOBOT_TMUX_SOCKET_DIR:-${TMPDIR:-/tmp}/nanobot-tmux-sockets}"  # 设置套接字目录，优先使用环境变量 NANOBOT_TMUX_SOCKET_DIR，否则使用临时目录
mkdir -p "$SOCKET_DIR"  # 创建套接字目录
SOCKET="$SOCKET_DIR/nanobot.sock"  # 设置套接字文件路径
SESSION=nanobot-python  # 设置会话名称

tmux -S "$SOCKET" new -d -s "$SESSION" -n shell  # 使用指定套接字创建新的分离会话，会话名为 nanobot-python，窗口名为 shell
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- 'PYTHON_BASIC_REPL=1 python3 -q' Enter  # 向会话的第一个窗格发送启动 Python REPL 的命令，设置环境变量 PYTHON_BASIC_REPL=1 以使用基础 REPL
tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0 -S -200  # 捕获窗格的最近 200 行输出，-p 表示纯文本，-J 表示连接换行
```

启动会话后，始终打印监控命令：

```
监控命令：
  tmux -S "$SOCKET" attach -t "$SESSION"  # 附加到指定会话以实时查看
  tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0 -S -200  # 捕获指定窗格的最近 200 行输出
```

## 套接字约定

- 使用 `NANOBOT_TMUX_SOCKET_DIR` 环境变量。
- 默认套接字路径：`"$NANOBOT_TMUX_SOCKET_DIR/nanobot.sock"`。

## 定位窗格和命名

- 目标格式：`session:window.pane`（默认为 `:0.0`）。
- 保持名称简短；避免使用空格。
- 检查：`tmux -S "$SOCKET" list-sessions`（列出会话），`tmux -S "$SOCKET" list-panes -a`（列出所有窗格）。

## 查找会话

- 列出您的套接字上的会话：`{baseDir}/scripts/find-sessions.sh -S "$SOCKET"`。
- 扫描所有套接字：`{baseDir}/scripts/find-sessions.sh --all`（使用 `NANOBOT_TMUX_SOCKET_DIR`）。

## 安全发送输入

- 优先使用字面发送：`tmux -S "$SOCKET" send-keys -t target -l -- "$cmd"`（使用 -l 标志发送字面字符，避免 shell 解释）。
- 控制键：`tmux -S "$SOCKET" send-keys -t target C-c`（发送 Ctrl+C 中断信号）。

## 监视输出

- 捕获最近历史：`tmux -S "$SOCKET" capture-pane -p -J -t target -S -200`（捕获最近 200 行）。
- 等待提示符：`{baseDir}/scripts/wait-for-text.sh -t session:0.0 -p 'pattern'`（等待匹配指定模式的文本出现）。
- 附加是可以的；使用 `Ctrl+b d` 分离（先按 Ctrl+b，再按 d）。

## 生成进程

- 对于 Python REPL，设置 `PYTHON_BASIC_REPL=1`（非基础 REPL 会破坏 send-keys 流程）。

## Windows / WSL

- tmux 在 macOS/Linux 上受支持。在 Windows 上，使用 WSL 并在 WSL 内安装 tmux。
- 此技能限制为 `darwin`/`linux`，并且 PATH 上需要 `tmux`。

## 编排编码代理（Codex、Claude Code）

tmux 擅长并行运行多个编码代理：

```bash
SOCKET="${TMPDIR:-/tmp}/codex-army.sock"  # 设置套接字文件路径

# 创建多个会话
for i in 1 2 3 4 5; do
  tmux -S "$SOCKET" new-session -d -s "agent-$i"  # 为每个代理创建一个独立的分离会话
done

# 在不同的工作目录中启动代理
tmux -S "$SOCKET" send-keys -t agent-1 "cd /tmp/project1 && codex --yolo 'Fix bug X'" Enter  # 在 agent-1 会话中切换到 project1 目录并运行 codex 修复 bug X
tmux -S "$SOCKET" send-keys -t agent-2 "cd /tmp/project2 && codex --yolo 'Fix bug Y'" Enter  # 在 agent-2 会话中切换到 project2 目录并运行 codex 修复 bug Y

# 轮询完成情况（检查提示符是否返回）
for sess in agent-1 agent-2; do
  if tmux -S "$SOCKET" capture-pane -p -t "$sess" -S -3 | grep -q "❯"; then  # 检查最近 3 行是否包含提示符
    echo "$sess: DONE"  # 如果找到提示符，表示任务完成
  else
    echo "$sess: Running..."  # 否则表示任务仍在运行
  fi
done

# 从完成的会话获取完整输出
tmux -S "$SOCKET" capture-pane -p -t agent-1 -S -500  # 捕获 agent-1 会话的最近 500 行输出
```

**提示：**
- 使用单独的 git 工作树进行并行修复（避免分支冲突）
- 在新克隆中运行 codex 之前先运行 `pnpm install`
- 检查 shell 提示符（`❯` 或 `$`）以检测完成
- Codex 需要使用 `--yolo` 或 `--full-auto` 进行非交互式修复

## 清理

- 终止会话：`tmux -S "$SOCKET" kill-session -t "$SESSION"`。
- 终止套接字上的所有会话：`tmux -S "$SOCKET" list-sessions -F '#{session_name}' | xargs -r -n1 tmux -S "$SOCKET" kill-session -t`。
- 删除私有套接字上的所有内容：`tmux -S "$SOCKET" kill-server`。

## 辅助工具：wait-for-text.sh

`{baseDir}/scripts/wait-for-text.sh` 轮询窗格以查找正则表达式（或固定字符串），并带有超时。

```bash
{baseDir}/scripts/wait-for-text.sh -t session:0.0 -p 'pattern' [-F] [-T 20] [-i 0.5] [-l 2000]
```

- `-t`/`--target` 窗格目标（必需）
- `-p`/`--pattern` 要匹配的正则表达式（必需）；添加 `-F` 表示固定字符串
- `-T` 超时秒数（整数，默认 15）
- `-i` 轮询间隔秒数（默认 0.5）
- `-l` 要搜索的历史行数（整数，默认 1000）
