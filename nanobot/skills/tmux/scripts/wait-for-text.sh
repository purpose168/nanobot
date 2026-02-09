#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
用法：wait-for-text.sh -t target -p pattern [选项]

轮询 tmux 窗格中的文本，找到后退出。

选项：
  -t, --target    tmux 目标（session:window.pane），必需
  -p, --pattern   要查找的正则表达式模式，必需
  -F, --fixed     将模式视为固定字符串（grep -F）
  -T, --timeout   等待秒数（整数，默认：15）
  -i, --interval  轮询间隔（秒，默认：0.5）
  -l, --lines     要检查的历史行数（整数，默认：1000）
  -h, --help      显示此帮助
USAGE
}

target=""
pattern=""
grep_flag="-E"  # 默认使用扩展正则表达式
 timeout=15  # 默认超时时间为 15 秒
interval=0.5  # 默认轮询间隔为 0.5 秒
lines=1000  # 默认检查 1000 行历史

while [[ $# -gt 0 ]]; do  # 当参数数量大于 0 时循环处理参数
  case "$1" in
    -t|--target)   target="${2-}"; shift 2 ;;  # 设置目标并移动两个参数
    -p|--pattern)  pattern="${2-}"; shift 2 ;;  # 设置模式并移动两个参数
    -F|--fixed)    grep_flag="-F"; shift ;;  # 使用固定字符串模式并移动一个参数
    -T|--timeout)  timeout="${2-}"; shift 2 ;;  # 设置超时时间并移动两个参数
    -i|--interval) interval="${2-}"; shift 2 ;;  # 设置轮询间隔并移动两个参数
    -l|--lines)    lines="${2-}"; shift 2 ;;  # 设置检查行数并移动两个参数
    -h|--help)     usage; exit 0 ;;  # 显示帮助信息并退出
    *) echo "未知选项：$1" >&2; usage; exit 1 ;;  # 未知选项，显示错误并退出
  esac
done

if [[ -z "$target" || -z "$pattern" ]]; then
  echo "目标和模式是必需的" >&2  # 错误：缺少必需参数
  usage
  exit 1
fi

if ! [[ "$timeout" =~ ^[0-9]+$ ]]; then
  echo "超时必须是整数秒数" >&2  # 错误：超时不是整数
  exit 1
fi

if ! [[ "$lines" =~ ^[0-9]+$ ]]; then
  echo "行数必须是整数" >&2  # 错误：行数不是整数
  exit 1
fi

if ! command -v tmux >/dev/null 2>&1; then
  echo "在 PATH 中未找到 tmux" >&2  # 错误：tmux 命令不存在
  exit 1
fi

# 结束时间（以纪元秒为单位，对于轮询来说足够了）
start_epoch=$(date +%s)  # 获取当前时间的纪元秒
 deadline=$((start_epoch + timeout))  # 计算截止时间

while true; do  # 无限循环，直到找到模式或超时
  # -J 连接换行的行，-S 使用负索引读取最后 N 行
  pane_text="$(tmux capture-pane -p -J -t "$target" -S "-${lines}" 2>/dev/null || true)"  # 捕获窗格内容

  if printf '%s\n' "$pane_text" | grep $grep_flag -- "$pattern" >/dev/null 2>&1; then  # 检查模式是否匹配
    exit 0  # 找到模式，退出成功
  fi

  now=$(date +%s)  # 获取当前时间
  if (( now >= deadline )); then  # 检查是否超时
    echo "在 ${timeout}s 后超时，等待模式：$pattern" >&2  # 错误：超时
    echo "来自 $target 的最后 ${lines} 行：" >&2  # 输出最后几行内容
    printf '%s\n' "$pane_text" >&2
    exit 1  # 超时，退出失败
  fi

  sleep "$interval"  # 等待指定的轮询间隔

done
