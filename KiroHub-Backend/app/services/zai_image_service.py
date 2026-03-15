from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ZaiImageService:
    """ZAI Image 服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
