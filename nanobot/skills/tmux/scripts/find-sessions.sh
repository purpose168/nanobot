#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
用法：find-sessions.sh [-L socket-name|-S socket-path|-A] [-q pattern]

列出套接字上的 tmux 会话（如果未提供，则使用默认 tmux 套接字）。

选项：
  -L, --socket       tmux 套接字名称（传递给 tmux -L）
  -S, --socket-path  tmux 套接字路径（传递给 tmux -S）
  -A, --all          扫描 NANOBOT_TMUX_SOCKET_DIR 下的所有套接字
  -q, --query        不区分大小写的子字符串，用于过滤会话名称
  -h, --help         显示此帮助
USAGE
}

socket_name=""
socket_path=""
query=""
scan_all=false
socket_dir="${NANOBOT_TMUX_SOCKET_DIR:-${TMPDIR:-/tmp}/nanobot-tmux-sockets"  # 设置套接字目录，优先使用环境变量，否则使用临时目录

while [[ $# -gt 0 ]]; do  # 当参数数量大于 0 时循环处理参数
  case "$1" in
    -L|--socket)      socket_name="${2-}"; shift 2 ;;  # 设置套接字名称并移动两个参数
    -S|--socket-path) socket_path="${2-}"; shift 2 ;;  # 设置套接字路径并移动两个参数
    -A|--all)         scan_all=true; shift ;;  # 设置扫描所有标志并移动一个参数
    -q|--query)       query="${2-}"; shift 2 ;;  # 设置查询字符串并移动两个参数
    -h|--help)        usage; exit 0 ;;  # 显示帮助信息并退出
    *) echo "未知选项：$1" >&2; usage; exit 1 ;;  # 未知选项，显示错误并退出
  esac
done

if [[ "$scan_all" == true && ( -n "$socket_name" || -n "$socket_path" ) ]]; then
  echo "不能同时使用 --all 与 -L 或 -S" >&2  # 错误：不能同时使用 --all 和指定套接字
  exit 1
fi

if [[ -n "$socket_name" && -n "$socket_path" ]]; then
  echo "使用 -L 或 -S，不要同时使用两者" >&2  # 错误：不能同时使用套接字名称和路径
  exit 1
fi

if ! command -v tmux >/dev/null 2>&1; then
  echo "在 PATH 中未找到 tmux" >&2  # 错误：tmux 命令不存在
  exit 1
fi

list_sessions() {
  local label="$1"; shift  # 获取标签并移除第一个参数
  local tmux_cmd=(tmux "$@")  # 构建 tmux 命令数组

  if ! sessions="$("${tmux_cmd[@]}" list-sessions -F '#{session_name}\t#{session_attached}\t#{session_created_string}' 2>/dev/null)"; then
    echo "在 $label 上未找到 tmux 服务器" >&2  # 错误：无法连接到 tmux 服务器
    return 1
  fi

  if [[ -n "$query" ]]; then  # 如果有查询字符串，则过滤会话
    sessions="$(printf '%s\n' "$sessions" | grep -i -- "$query" || true)"  # 不区分大小写过滤
  fi

  if [[ -z "$sessions" ]]; then
    echo "在 $label 上未找到会话"  # 提示：没有找到会话
    return 0
  fi

  echo "在 $label 上的会话："  # 输出会话列表标题
  printf '%s\n' "$sessions" | while IFS=$'\t' read -r name attached created; do  # 逐行读取会话信息
    attached_label=$([[ "$attached" == "1" ]] && echo "已附加" || echo "已分离")  # 判断会话附加状态
    printf '  - %s (%s, 启动于 %s)\n' "$name" "$attached_label" "$created"  # 输出会话详情
  done
}

if [[ "$scan_all" == true ]]; then  # 如果设置了扫描所有标志
  if [[ ! -d "$socket_dir" ]]; then
    echo "未找到套接字目录：$socket_dir" >&2  # 错误：套接字目录不存在
    exit 1
  fi

  shopt -s nullglob  # 启用 nullglob，使不匹配的模式展开为空
  sockets=("$socket_dir"/*)  # 获取套接字目录下的所有文件
  shopt -u nullglob  # 禁用 nullglob

  if [[ "${#sockets[@]}" -eq 0 ]]; then
    echo "在 $socket_dir 下未找到套接字" >&2  # 错误：没有找到套接字文件
    exit 1
  fi

  exit_code=0  # 初始化退出代码
  for sock in "${sockets[@]}"; do  # 遍历所有套接字
    if [[ ! -S "$sock" ]]; then  # 跳过非套接字文件
      continue
    fi
    list_sessions "套接字路径 '$sock'" -S "$sock" || exit_code=$?  # 列出每个套接字的会话
  done
  exit "$exit_code"  # 返回最终的退出代码
fi

tmux_cmd=(tmux)  # 初始化 tmux 命令数组
socket_label="默认套接字"  # 默认套接字标签

if [[ -n "$socket_name" ]]; then  # 如果指定了套接字名称
  tmux_cmd+=(-L "$socket_name")  # 添加 -L 参数
  socket_label="套接字名称 '$socket_name'"  # 更新标签
elif [[ -n "$socket_path" ]]; then  # 如果指定了套接字路径
  tmux_cmd+=(-S "$socket_path")  # 添加 -S 参数
  socket_label="套接字路径 '$socket_path'"  # 更新标签
fi

list_sessions "$socket_label" "${tmux_cmd[@]:1}"  # 调用会话列表函数
