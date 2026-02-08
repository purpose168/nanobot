#!/bin/bash
# 统计核心智能体代码行数（排除 channels/、cli/、providers/ 适配器）
cd "$(dirname "$0")" || exit 1

echo "nanobot 核心智能体代码行数统计"
echo "==============================="
echo ""

for dir in agent agent/tools bus config cron heartbeat session utils; do
  count=$(find "nanobot/$dir" -maxdepth 1 -name "*.py" -exec cat {} + | wc -l)
  printf "  %-16s %5s 行\n" "$dir/" "$count"
done

root=$(cat nanobot/__init__.py nanobot/__main__.py | wc -l)
printf "  %-16s %5s 行\n" "(root)" "$root"

echo ""
total=$(find nanobot -name "*.py" ! -path "*/channels/*" ! -path "*/cli/*" ! -path "*/providers/*" | xargs cat | wc -l)
echo "  核心总计:     $total 行"
echo ""
echo "  (排除: channels/, cli/, providers/)"
