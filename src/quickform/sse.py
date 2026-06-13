import json
import uuid
import queue
import threading
import logging

logger = logging.getLogger(__name__)

# 连接注册表: task_id -> list of (sse_id, Queue)
_channels: dict[int, list[tuple[str, queue.Queue]]] = {}
_lock = threading.Lock()


def subscribe(task_id: int) -> tuple[str, queue.Queue]:
    """注册一个 SSE 连接，返回 (sse_id, queue)"""
    sse_id = str(uuid.uuid4())
    q = queue.Queue()
    with _lock:
        _channels.setdefault(task_id, []).append((sse_id, q))
    logger.info(f"SSE 连接注册: sse_id={sse_id}, task_id={task_id}")
    return sse_id, q


def unregister(sse_id: str, task_id: int):
    """移除一个 SSE 连接"""
    with _lock:
        conns = _channels.get(task_id, [])
        _channels[task_id] = [(sid, q) for sid, q in conns if sid != sse_id]
        if not _channels[task_id]:
            del _channels[task_id]
    logger.info(f"SSE 连接移除: sse_id={sse_id}, task_id={task_id}")


def publish(task_id: int, data: dict):
    """向某个 task_id 的所有 SSE 连接推送数据"""
    with _lock:
        conns = _channels.get(task_id, [])
    if not conns:
        return
    payload = json.dumps(data, ensure_ascii=False)
    for _, q in conns:
        try:
            q.put_nowait(payload)
        except queue.Full:
            pass
    logger.info(f"SSE 推送: task_id={task_id}, 连接数={len(conns)}")
