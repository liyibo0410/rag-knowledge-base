from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from app.api.dependencies import get_query_service
from app.api.schemas.query_schema import QuerySchema
from app.services.query_service import QueryService

# 声明查询的路由
query_router = APIRouter()


# 定义POST接口/api/query
@query_router.post("/api/query")
async def query(query: QuerySchema, query_service: QueryService = Depends(get_query_service)):
    # 调用服务处理查询，返回SSE流式响应（text/event-stream为SSE协议标准媒体类型）
    return StreamingResponse(query_service.query(query.query), media_type="text/event-stream")
