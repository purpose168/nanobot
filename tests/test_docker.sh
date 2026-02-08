#!/usr/bin/env bash
# 设置脚本执行选项：
# -e: 遇到错误立即退出
# -u: 遇到未定义变量立即退出
# -o pipefail: 管道命令中任何一个失败立即退出
set -euo pipefail
# 切换到项目根目录
cd "$(dirname "$0")/.." || exit 1

IMAGE_NAME="nanobot-test"

echo "=== 构建 Docker 镜像 ==="
docker build -t "$IMAGE_NAME" .

echo ""
echo "=== 运行 'nanobot onboard' ==="
docker run --name nanobot-test-run "$IMAGE_NAME" onboard

echo ""
echo "=== 运行 'nanobot status' ==="
STATUS_OUTPUT=$(docker commit nanobot-test-run nanobot-test-onboarded > /dev/null && \
    docker run --rm nanobot-test-onboarded status 2>&1) || true

echo "$STATUS_OUTPUT"

echo ""
echo "=== 验证输出 ==="
PASS=true

# 检查函数：验证输出中是否包含指定文本
check() {
    if echo "$STATUS_OUTPUT" | grep -q "$1"; then
        echo "  通过: 找到 '$1'"
    else
        echo "  失败: 缺少 '$1'"
        PASS=false
    fi
}

# 验证输出中包含关键信息
check "nanobot 状态"
check "配置:"
check "工作区:"
check "模型:"
check "OpenRouter API:"
check "Anthropic API:"
check "OpenAI API:"

echo ""
if $PASS; then
    echo "=== 所有检查通过 ==="
else
    echo "=== 部分检查失败 ==="
    exit 1
fi

# 清理操作
echo ""
echo "=== 清理 ==="
docker rm -f nanobot-test-run 2>/dev/null || true
docker rmi -f nanobot-test-onboarded 2>/dev/null || true
docker rmi -f "$IMAGE_NAME" 2>/dev/null || true
echo "完成。"
