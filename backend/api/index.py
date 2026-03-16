"""
Vercel Serverless Function 入口文件
用于适配 Vercel 的 Python Serverless Functions
"""
import sys
import os

# 将 backend 目录添加到 Python 路径
backend_path = os.path.join(os.path.dirname(__file__), '..')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# 导入 FastAPI 应用
from app.main import app

# 尝试导入 Mangum 适配器（用于 AWS Lambda/Vercel）
try:
    from mangum import Mangum
    # 创建 Lambda 处理器
    handler = Mangum(app, lifespan="off")
except ImportError:
    # 如果没有安装 mangum，使用简单的 WSGI 包装
    from fastapi.middleware.wsgi import WSGIMiddleware
    
    def handler(event, context):
        """简化的 Lambda 处理器"""
        from fastapi import Request
        from fastapi.responses import JSONResponse
        
        # 提取请求信息
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        headers = event.get('headers', {})
        body = event.get('body', '')
        
        # 这里简化处理，实际应该构建 ASGI 请求
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': '{"message": "AIGovern Pro API", "path": "' + path + '"}'
        }

# Vercel 入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
