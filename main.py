# BOSS问数后端入口：FastAPI 应用
import uuid

from fastapi import FastAPI, Request

from app.api.routers.query_router import query_router
from app.core.context import request_id_ctx_var
from app.core.lifespan import lifespan


# 创建FastAPI应用实例，并注册生命周期组件（启动时初始化各客户端，关闭时释放资源）
app = FastAPI(lifespan=lifespan)

# 绑定查询router
app.include_router(query_router)


# 添加中间件，为每个请求生成唯一的request_id，用于日志链路追踪
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # 调用路径函数之前进行业务处理
    request_id_ctx_var.set(uuid.uuid4())
    # 调用路径函数
    response = await call_next(request)
    # 调用路径函数之后进行业务处理
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
