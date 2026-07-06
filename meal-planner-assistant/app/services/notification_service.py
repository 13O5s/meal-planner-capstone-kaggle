from __future__ import annotations

import time
import uuid

from sqlalchemy import delete, func, select, update


def _serialise(row) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "type": row.type,
        "title": row.title,
        "message": row.message,
        "read": row.read,
        "created_at": row.created_at,
    }


class NotificationService:
    def __init__(self, session) -> None:
        self.session = session

    async def create(
        self,
        user_id: str,
        type_: str,
        title: str,
        message: str,
    ) -> dict:
        from app.database.models.notification import Notification

        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        notif = Notification(
            id=uuid.uuid4().hex[:8],
            user_id=user_id,
            type=type_,
            title=title,
            message=message,
            read=False,
            created_at=now,
        )
        self.session.add(notif)
        await self.session.commit()
        await self.session.refresh(notif)
        return _serialise(notif)

    async def get_for_user(self, user_id: str, limit: int = 20) -> list[dict]:
        from app.database.models.notification import Notification

        result = await self.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return [_serialise(row) for row in result.scalars().all()]

    async def mark_read(self, notification_id: str) -> bool:
        from app.database.models.notification import Notification

        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(read=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def mark_all_read(self, user_id: str) -> int:
        from app.database.models.notification import Notification

        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read == False)
            .values(read=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def unread_count(self, user_id: str) -> int:
        from app.database.models.notification import Notification

        result = await self.session.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.read == False)
        )
        return result.scalar() or 0

    async def delete_old(self, days: int = 30) -> int:
        import datetime as dt

        from app.database.models.notification import Notification

        cutoff = (
            dt.datetime.now(dt.UTC) - dt.timedelta(days=days)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        stmt = delete(Notification).where(Notification.created_at < cutoff)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
