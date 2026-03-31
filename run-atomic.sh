#!/bin/bash
# Atomic CLI 启动脚本 for AIGovern_Pro

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BUN_PATH="/Users/wclu/.bun/bin/bun"
ATOMIC_PATH="/Users/wclu/Atomic_Workspace"
PROJECT_PATH="$(pwd)"

echo -e "${GREEN}🚀 Atomic CLI Launcher for AIGovern_Pro${NC}"
echo "=================="

# 检查Bun
if [ ! -f "$BUN_PATH" ]; then
    echo -e "${RED}✗ Bun not found at $BUN_PATH${NC}"
    echo -e "${YELLOW}Please install Bun first:${NC}"
    echo "  curl -fsSL https://bun.sh/install | bash"
    exit 1
fi

echo -e "${GREEN}✓ Bun found${NC}"

# 检查Atomic_Workspace
if [ ! -d "$ATOMIC_PATH" ]; then
    echo -e "${RED}✗ Atomic workspace not found at $ATOMIC_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Atomic workspace found${NC}"

# 检查Claude Code
if ! command -v claude &> /dev/null; then
    echo -e "${RED}✗ Claude Code CLI not found${NC}"
    echo -e "${YELLOW}Please install Claude Code:${NC}"
    echo "  https://code.claude.com/docs/en/quickstart"
    exit 1
fi

echo -e "${GREEN}✓ Claude Code CLI found${NC}"

# 选择agent
echo ""
echo -e "${YELLOW}Select agent:${NC}"
echo "  1) claude (recommended)"
echo "  2) opencode"
echo "  3) copilot"
read -p "Enter choice [1-3] (default: 1): " agent_choice

case $agent_choice in
    2) AGENT="opencode" ;;
    3) AGENT="copilot" ;;
    *) AGENT="claude" ;;
esac

echo ""
echo -e "${YELLOW}Select mode:${NC}"
echo "  1) Chat mode (interactive)"
echo "  2) Init mode (generate CLAUDE.md)"
echo "  3) Research mode (analyze codebase)"
read -p "Enter choice [1-3] (default: 1): " mode_choice

echo ""
echo -e "${GREEN}Starting Atomic with $AGENT agent...${NC}"
echo ""

case $mode_choice in
    2)
        # Init mode
        echo -e "${YELLOW}📝 Initializing project...${NC}"
        $BUN_PATH run "$ATOMIC_PATH/src/cli.ts" init -a $AGENT -y
        ;;
    3)
        # Research mode
        read -p "Enter research topic: " research_topic
        echo -e "${YELLOW}🔍 Starting research...${NC}"
        $BUN_PATH run "$ATOMIC_PATH/src/cli.ts" chat -a $AGENT "/research-codebase \"$research_topic\""
        ;;
    *)
        # Chat mode (default)
        $BUN_PATH run "$ATOMIC_PATH/src/cli.ts" chat -a $AGENT
        ;;
esac

echo ""
echo -e "${GREEN}✓ Done${NC}"
