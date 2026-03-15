"""
OpenAI兼容的API端点 - 仅支持Kiro
支持API key或JWT token认证
"""
import json
import logging
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_flexible import get_user_flexible
from app.api.deps import get_db_session, get_redis
from app.models.user import User
from app.services.kiro_service import KiroService, UpstreamAPIError
from app.services.usage_log_service import UsageLogService, SSEUsageTracker
from app.schemas.plugin_api import ChatCompletionRequest
from app.cache import RedisClient

router = APIRouter(prefix="/v1", tags=["OpenAI兼容API"])
logger = logging.getLogger(__name__)


def _sse_no_buffer_headers() -> Dict[str, str]:
    """SSE防缓冲头"""
    return {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


def get_kiro_service(
    db: AsyncSession = Depends(get_db_session),
    redis: RedisClient = Depends(get_redis)
) -> KiroService:
    return KiroService(db, redis)


@router.get(
    "/models",
    summary="获取可用的AI模型列表",
    description="获取可用的AI模型列表（OpenAI兼容）- 仅支持Kiro"
)
async def list_models(
    request: Request,
    current_user: User = Depends(get_user_flexible),
    kiro_service: KiroService = Depends(get_kiro_service),
):
    """
    获取可用的AI模型列表
    - 使用API key或JWT token认证
    - 返回Kiro可用模型
    """
    try:
        result = await kiro_service.get_models(current_user.id)
        return result
    except UpstreamAPIError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.extracted_message, "type": "api_error"}
        )
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "type": "internal_error"}
        )


@router.post(
    "/chat/completions",
    summary="聊天补全",
    description="OpenAI兼容的聊天补全API - 仅支持Kiro"
)
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
    current_user: User = Depends(get_user_flexible),
    kiro_service: KiroService = Depends(get_kiro_service),
    db: AsyncSession = Depends(get_db_session),
    redis: RedisClient = Depends(get_redis),
):
    """
    聊天补全API
    - 支持流式和非流式响应
    - 仅支持Kiro配置
    """
    usage_service = UsageLogService(db)
    
    # 检查beta权限
    if current_user.beta != 1 and getattr(current_user, "trust_level", 0) < 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kiro功能需要beta权限"
        )
    
    try:
        if body.stream:
            # 流式响应
            async def stream_generator():
                tracker = SSEUsageTracker()
                try:
                    async for chunk in kiro_service.chat_completions_stream(
                        user_id=current_user.id,
                        request_data=body.model_dump()
                    ):
                        tracker.feed(chunk)
                        chunk_json = json.dumps(chunk, ensure_ascii=False, separators=(",", ":"))
                        yield f"data: {chunk_json}\n\n"
                    
                    yield "data: [DONE]\n\n"
                    
                    # 记录使用日志
                    usage = tracker.get_usage()
                    if usage:
                        await usage_service.create_usage_log(
                            user_id=current_user.id,
                            config_type="kiro",
                            model=body.model,
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0),
                            total_tokens=usage.get("total_tokens", 0),
                            request_body=body.model_dump(),
                            response_body=None,
                            request_headers=dict(request.headers),
                        )
                except UpstreamAPIError as e:
                    error_data = {
                        "error": {
                            "message": str(e.extracted_message),
                            "type": "upstream_error",
                            "code": e.status_code
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                except Exception as e:
                    logger.error(f"Kiro stream failed: {str(e)}", exc_info=True)
                    error_data = {
                        "error": {
                            "message": str(e),
                            "type": "internal_error",
                            "code": 500
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers=_sse_no_buffer_headers()
            )
        else:
            # 非流式响应
            openai_stream = kiro_service.chat_completions_stream(
                user_id=current_user.id,
                request_data=body.model_dump()
            )
            
            # 收集流式响应
            chunks = []
            async for chunk in openai_stream:
                chunks.append(chunk)
            
            # 合并为完整响应
            if not chunks:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="未收到响应"
                )
            
            result = chunks[0]
            for chunk in chunks[1:]:
                if "choices" in chunk and chunk["choices"]:
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        if "choices" not in result:
                            result["choices"] = [{"message": {"content": ""}}]
                        result["choices"][0]["message"]["content"] = result["choices"][0]["message"].get("content", "") + delta["content"]
            
            # 记录使用日志
            usage = result.get("usage", {})
            await usage_service.create_usage_log(
                user_id=current_user.id,
                config_type="kiro",
                model=body.model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                request_body=body.model_dump(),
                response_body=result,
                request_headers=dict(request.headers),
            )
            
            return result
            
    except UpstreamAPIError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.extracted_message, "type": "api_error"}
        )
    except Exception as e:
        logger.error(f"Chat completions failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "type": "internal_error"}
        )


@router.get(
    "/cache/stats",
    summary="获取缓存统计",
    description="获取Redis缓存使用统计信息"
)
async def get_cache_stats(
    current_user: User = Depends(get_user_flexible),
    redis: RedisClient = Depends(get_redis),
):
    """
    获取缓存统计信息
    - 缓存命中率
    - 缓存键数量
    - 内存使用情况
    """
    try:
        info = await redis.info("stats")
        memory_info = await redis.info("memory")
        keyspace_info = await redis.info("keyspace")
        
        # 计算命中率
        hits = int(info.get("keyspace_hits", 0))
        misses = int(info.get("keyspace_misses", 0))
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        # 获取键数量
        total_keys = 0
        for db_key, db_info in keyspace_info.items():
            if db_key.startswith("db"):
                keys_str = db_info.split(",")[0].split("=")[1]
                total_keys += int(keys_str)
        
        return {
            "cache_enabled": True,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total,
            "hits": hits,
            "misses": misses,
            "total_keys": total_keys,
            "memory_used": memory_info.get("used_memory_human", "N/A"),
            "memory_peak": memory_info.get("used_memory_peak_human", "N/A"),
        }
    except Exception as e:
        logger.error(f"获取缓存统计失败: {str(e)}", exc_info=True)
        return {
            "cache_enabled": False,
            "error": str(e)
        }
