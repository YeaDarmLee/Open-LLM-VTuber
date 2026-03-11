import chzzkpy
from .base import ChzzkProvider, ChzzkMessage
from loguru import logger
from typing import Optional, Callable, Awaitable

class OfficialChzzkMessage:
    def __init__(self, message: chzzkpy.ChatMessage):
        self.content = message.content
        self.nickname = message.profile.nickname if message.profile else "Unknown"
        self.user_id = message.profile.user_hash if message.profile else "Unknown"
        self.event_type = "chat"
        self.amount = None

class OfficialChzzkProvider:
    def __init__(self, channel_id: str, access_token: Optional[str] = None):
        self.channel_id = channel_id
        self.client = chzzkpy.Client(access_token=access_token)
        self._callback: Optional[Callable[[ChzzkMessage], Awaitable[None]]] = None

    async def connect(self) -> bool:
        logger.info(f"Connecting to Chzzk Official API for channel: {self.channel_id}")
        return True

    async def listen(self, callback: Callable[[ChzzkMessage], Awaitable[None]]) -> None:
        self._callback = callback

        @self.client.event
        async def on_chat(message: chzzkpy.ChatMessage):
            if self._callback:
                await self._callback(OfficialChzzkMessage(message))

        @self.client.event
        async def on_donation(message: chzzkpy.DonationMessage):
            if self._callback:
                msg = OfficialChzzkMessage(message)
                msg.event_type = "donation"
                msg.amount = message.extras.pay_amount
                await self._callback(msg)

        await self.client.start(self.channel_id)

    async def disconnect(self) -> None:
        await self.client.close()
