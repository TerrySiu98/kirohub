from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Iterator
from uuid import uuid4


@dataclass
class _OpenAIStreamState:
    """OpenAI 流式响应状态"""
    created: int
    function_index: int = 0
    model: str = "gpt-3.5-turbo"
    id: str = field(default_factory=lambda: f"chatcmpl-{uuid4().hex[:8]}")


def _openai_done_sse() -> str:
    """生成 SSE 完成消息"""
    return "data: [DONE]\n\n"


def _openai_error_sse(message: str, code: int = 500) -> str:
    """生成 SSE 错误消息"""
    error_obj = {
        "error": {
            "message": message,
            "type": "server_error",
            "code": code
        }
    }
    return f"data: {json.dumps(error_obj)}\n\n"


def _openai_request_to_gemini_cli_payload(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """将 OpenAI 请求转换为 Gemini CLI 格式"""
    return {
        "contents": [
            {
                "role": "user" if msg.get("role") == "user" else "model",
                "parts": [{"text": msg.get("content", "")}]
            }
            for msg in request_data.get("messages", [])
            if msg.get("role") in ("user", "assistant")
        ],
        "generationConfig": {
            "temperature": request_data.get("temperature", 1.0),
            "topP": request_data.get("top_p", 1.0),
            "maxOutputTokens": request_data.get("max_tokens", 2048),
        }
    }


def _gemini_cli_response_to_openai_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """将 Gemini CLI 响应转换为 OpenAI 格式"""
    content = ""
    if isinstance(response_data, dict):
        candidates = response_data.get("candidates", [])
        if candidates and isinstance(candidates[0], dict):
            content_obj = candidates[0].get("content", {})
            parts = content_obj.get("parts", [])
            if parts and isinstance(parts[0], dict):
                content = parts[0].get("text", "")

    return {
        "id": f"chatcmpl-{uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "gpt-3.5-turbo",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }


def _gemini_cli_event_to_openai_chunks(
    event_data: Dict[str, Any],
    state: _OpenAIStreamState
) -> Iterator[str]:
    """将 Gemini CLI 事件转换为 OpenAI 流式块"""
    content = ""
    if isinstance(event_data, dict):
        candidates = event_data.get("candidates", [])
        if candidates and isinstance(candidates[0], dict):
            content_obj = candidates[0].get("content", {})
            parts = content_obj.get("parts", [])
            if parts and isinstance(parts[0], dict):
                content = parts[0].get("text", "")

    if content:
        chunk = {
            "id": state.id,
            "object": "chat.completion.chunk",
            "created": state.created,
            "model": state.model,
            "choices": [{
                "index": 0,
                "delta": {"content": content},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(chunk)}\n\n"
