#!/bin/bash
# AIGovern Pro 快速启动脚本

echo "🚀 AIGovern Pro 启动向导"
echo "======================================"

# 1. 启动后端
echo ""
echo "1️⃣  启动后端服务..."
cd /Users/wclu/AIGovern_Pro/backend
source venv/bin/activate
set -a && source .env && set +a
python3 run.py &
BACKEND_PID=$!
sleep 3
echo "✅ 后端启动成功 (PID: $BACKEND_PID)"

# 2. 验证后端
echo ""
echo "2️⃣  验证后端连接..."
curl -s http://localhost:8000/health | python3 -m json.tool | head -5
echo "✅ 后端验证成功"

# 3. 启动前端
echo ""
echo "3️⃣  启动前端应用..."
cd /Users/wclu/AIGovern_Pro/frontend
npm run dev &
FRONTEND_PID=$!
sleep 5
echo "✅ 前端启动成功 (PID: $FRONTEND_PID)"

# 4. 显示访问信息
echo ""
echo "======================================"
echo "🎉 系统启动完成！"
echo "======================================"
echo ""
echo "📊 访问信息："
echo "  🌐 前端应用：http://localhost:3000"
echo "  📚 后端 API：http://localhost:8000"
echo "  📖 Swagger文档：http://localhost:8000/docs"
echo ""
echo "🧪 测试命令："
echo "  cd /Users/wclu/AIGovern_Pro/backend"
echo "  source venv/bin/activate"
echo "  python3 test_rag_e2e.py"
echo ""
echo "📌 进程信息："
echo "  后端 PID: $BACKEND_PID"
echo "  前端 PID: $FRONTEND_PID"
echo ""
echo "❌ 停止服务："
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
