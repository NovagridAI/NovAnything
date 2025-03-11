import os
import sys


# 获取当前脚本的绝对路径
current_script_path = os.path.abspath(__file__)

# 获取当前脚本的父目录的路径，即`qanything_server`目录
current_dir = os.path.dirname(current_script_path)

# 获取`qanything_server`目录的父目录，即`qanything_kernel`
parent_dir = os.path.dirname(current_dir)

# 获取根目录：`qanything_kernel`的父目录
root_dir = os.path.dirname(parent_dir)

# 将项目根目录添加到sys.path
sys.path.append(root_dir)

from qanything_kernel.qanything_server.routes import register_routes
from qanything_kernel.core.local_doc_qa import LocalDocQA
from sanic.worker.manager import WorkerManager
from sanic import Sanic
from sanic_ext import Extend
import time
import argparse
import webbrowser
from sanic.exceptions import SanicException, NotFound

WorkerManager.THRESHOLD = 6000

# 接收外部参数mode
parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default='0.0.0.0', help='host')
parser.add_argument('--port', type=int, default=8777, help='port')
parser.add_argument('--workers', type=int, default=4, help='workers')
# 检查是否是local或online，不是则报错
args = parser.parse_args()

start_time = time.time()
app = Sanic("QAnything")
app.config.CORS_ORIGINS = "*"
Extend(app)
# 设置请求体最大为 128MB
app.config.REQUEST_MAX_SIZE = 128 * 1024 * 1024

# 将 /qanything 路径映射到 ./dist/qanything 文件夹，并指定路由名称
app.static('/qanything/', 'qanything_kernel/qanything_server/dist/qanything/', name='qanything', index="index.html")

# 添加错误处理器
@app.exception(NotFound)
async def handle_404(request, exception):
    print(f"404错误: {request.method} {request.path}", flush=True)
    return app.json({"error": "资源不存在", "status": 404}, status=404)

@app.exception(SanicException)
async def handle_exception(request, exception):
    print(f"服务器异常: {request.method} {request.path} - {str(exception)}", flush=True)
    return app.json({"error": str(exception), "status": exception.status_code}, status=exception.status_code)

@app.before_server_start
async def init_local_doc_qa(app, loop):
    start = time.time()
    local_doc_qa = LocalDocQA(args.port)
    local_doc_qa.init_cfg(args)
    end = time.time()
    print(f'init local_doc_qa cost {end - start}s', flush=True)
    app.ctx.local_doc_qa = local_doc_qa
    
@app.after_server_start
async def notify_server_started(app, loop):
    print(f"Server Start Cost {time.time() - start_time} seconds", flush=True)

@app.after_server_start
async def start_server_and_open_browser(app, loop):
    try:
        print(f"Opening browser at http://{args.host}:{args.port}/qanything/")
        webbrowser.open(f"http://{args.host}:{args.port}/qanything/")
    except Exception as e:
        # 记录或处理任何异常
        print(f"Failed to open browser: {e}")

# 注册所有路由
print("开始注册路由", flush=True)
register_routes(app)
print(f"路由注册完成，共注册 {len(app.router.routes)} 个路由", flush=True)

if __name__ == "__main__":
    print(f"准备启动服务器，监听地址: {args.host}:{args.port}，工作进程数: {args.workers}", flush=True)
    app.run(host='0.0.0.0', port=args.port, workers=args.workers, access_log=False)