import asyncio
from typing import Dict, Any, Optional, Protocol, List
from loguru import logger

class ChzzkMessage(Protocol):
    content: str
    nickname: str
    user_id: str
    event_type: str # 'chat', 'donation', etc.
    amount: Optional[int] = None

class ChzzkProvider(Protocol):
    async def connect(self) -> bool:
        ...

    async def listen(self, callback) -> None:
        """callback: Callable[[ChzzkMessage], Awaitable[None]]"""
        ...

    async def disconnect(self) -> None:
        ...
