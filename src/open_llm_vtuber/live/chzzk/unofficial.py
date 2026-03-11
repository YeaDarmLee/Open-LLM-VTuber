from chzzkpy.unofficial import UnofficialClient
from .base import ChzzkProvider, ChzzkMessage
from loguru import logger
from typing import Optional, Callable, Awaitable

class UnofficialChzzkMessage:
    def __init__(self, message):
        self.content = message.content
        self.nickname = message.profile.nickname if message.profile else "Unknown"
        self.user_id = message.profile.user_hash if message.profile else "Unknown"
        self.event_type = "chat"
        self.amount = None

class UnofficialChzzkProvider:
    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        self.client = UnofficialClient()
        self._callback: Optional[Callable[[ChzzkMessage], Awaitable[None]]] = None

    async def connect(self) -> bool:
        logger.info(f"Connecting to Chzzk Unofficial API for channel: {self.channel_id}")
        return True

    async def listen(self, callback: Callable[[ChzzkMessage], Awaitable[None]]) -> None:
        self._callback = callback
        
        # Note: Unofficial implementation details may vary by chzzkpy version.
        # This assumes a similar event-based interface or basic polling/websocket.
        chat = await self.client.chat(self.channel_id)
        
        @chat.event
        async def on_chat(message):
            if self._callback:
                await self._callback(UnofficialChzzkMessage(message))

        await chat.run()

    async def disconnect(self) -> None:
        await self.client.close()
