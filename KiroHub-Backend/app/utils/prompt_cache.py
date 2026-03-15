"""
模拟 Anthropic Prompt Caching 功能
"""
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple


CACHE_TTL_SECONDS = 5 * 60  # 5分钟，和 Anthropic 一致


def estimate_tokens(text: str) -> int:
    """简单估算 token 数量（1 token ≈ 4 字符）"""
    return max(1, len(text) // 4)


def extract_cacheable_content(messages: List[Dict[str, Any]], system: Optional[Any] = None) -> Tuple[List[Dict], int]:
    """
    提取带有 cache_control 的内容

    Returns:
        (cacheable_items, estimated_tokens)
    """
    cacheable = []
    total_tokens = 0

    # 处理 system
    if system:
        if isinstance(system, str):
            # 简单字符串 system 不支持 cache_control
            pass
        elif isinstance(system, list):
            for item in system:
                if isinstance(item, dict) and item.get("cache_control"):
                    content = item.get("text", "") or item.get("content", "")
                    tokens = estimate_tokens(str(content))
                    cacheable.append({"type": "system", "content": content, "tokens": tokens})
                    total_tokens += tokens

    # 处理 messages
    for msg in messages:
        if not isinstance(msg, dict):
            continue

        content = msg.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("cache_control"):
                    text = block.get("text", "")
                    tokens = estimate_tokens(text)
                    cacheable.append({
                        "type": "message",
                        "role": msg.get("role"),
                        "content": text,
                        "tokens": tokens
                    })
                    total_tokens += tokens

    return cacheable, total_tokens


def compute_cache_key(cacheable_items: List[Dict]) -> str:
    """计算缓存 key"""
    if not cacheable_items:
        return ""

    # 使用内容的 JSON 序列化 + SHA256
    content_str = json.dumps(cacheable_items, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(content_str.encode()).hexdigest()


def strip_cache_control(data: Dict[str, Any]) -> Dict[str, Any]:
    """移除请求中的 cache_control（Kiro 不支持）"""
    result = data.copy()

    # 处理 system
    system = result.get("system")
    if isinstance(system, list):
        result["system"] = [
            {k: v for k, v in item.items() if k != "cache_control"}
            if isinstance(item, dict) else item
            for item in system
        ]

    # 处理 messages
    messages = result.get("messages", [])
    cleaned_messages = []
    for msg in messages:
        if not isinstance(msg, dict):
            cleaned_messages.append(msg)
            continue

        cleaned_msg = msg.copy()
        content = cleaned_msg.get("content")

        if isinstance(content, list):
            cleaned_content = []
            for block in content:
                if isinstance(block, dict):
                    cleaned_block = {k: v for k, v in block.items() if k != "cache_control"}
                    cleaned_content.append(cleaned_block)
                else:
                    cleaned_content.append(block)
            cleaned_msg["content"] = cleaned_content

        cleaned_messages.append(cleaned_msg)

    result["messages"] = cleaned_messages
    return result
