import time
import uuid

_NOTIFICATIONS: dict[str, list[dict]] = {}


def _ensure(user_id: str) -> None:
    if user_id not in _NOTIFICATIONS:
        _NOTIFICATIONS[user_id] = []


def create_in_memory(user_id: str, type_: str, title: str, message: str) -> dict:
    _ensure(user_id)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    notif = {
        "id": uuid.uuid4().hex[:8],
        "user_id": user_id,
        "type": type_,
        "title": title,
        "message": message,
        "read": False,
        "created_at": now,
    }
    _NOTIFICATIONS[user_id].insert(0, notif)
    return notif


def get_for_user_in_memory(user_id: str, limit: int = 20) -> list[dict]:
    _ensure(user_id)
    return _NOTIFICATIONS[user_id][:limit]


def mark_read_in_memory(notification_id: str) -> bool:
    for uid, notifs in _NOTIFICATIONS.items():
        for n in notifs:
            if n["id"] == notification_id:
                n["read"] = True
                return True
    return False


def mark_all_read_in_memory(user_id: str) -> int:
    _ensure(user_id)
    count = 0
    for n in _NOTIFICATIONS[user_id]:
        if not n["read"]:
            n["read"] = True
            count += 1
    return count


def unread_count_in_memory(user_id: str) -> int:
    _ensure(user_id)
    return sum(1 for n in _NOTIFICATIONS[user_id] if not n["read"])
