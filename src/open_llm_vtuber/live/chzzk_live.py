import asyncio
import json
import random
from typing import List, Dict, Any, Optional, Callable
from loguru import logger
import websockets

from .live_interface import LivePlatformInterface
from .chzzk.official import OfficialChzzkProvider
from .chzzk.unofficial import UnofficialChzzkProvider
from .chzzk.base import ChzzkMessage
from .donation_engine import DonationEngine

class ChzzkLivePlatform(LivePlatformInterface):
    """
    Implementation of LivePlatformInterface for Chzzk platform.
    """

    def __init__(self, channel_id: str, use_official: bool = True, access_token: str = None):
        self.channel_id = channel_id
        self.use_official = use_official
        self.access_token = access_token
        
        if use_official:
            self.provider = OfficialChzzkProvider(channel_id, access_token)
        else:
            self.provider = UnofficialChzzkProvider(channel_id)
            
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = False
        self._running = False
        self._message_handlers: List[Callable[[Dict[str, Any]], None]] = []
        
        # Bridge Rules state
        self._user_cooldowns: Dict[str, float] = {}
        self._cooldown_seconds = 5.0 # Minimum time between messages from the same user
        self._blacklisted_users: List[str] = [] # Optional: list of user_ids to ignore

        # NULL_AI Engines
        self.donation_engine = DonationEngine()

    @property
    def is_connected(self) -> bool:
        return self._connected and self._websocket is not None

    async def connect(self, proxy_url: str) -> bool:
        try:
            self._websocket = await websockets.connect(proxy_url)
            self._connected = True
            logger.info(f"Connected to proxy at {proxy_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to proxy: {e}")
            return False

    async def disconnect(self) -> None:
        self._running = False
        if hasattr(self.provider, 'disconnect'):
            await self.provider.disconnect()
        if self._websocket:
            await self._websocket.close()
        self._connected = False

    async def register_message_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        self._message_handlers.append(handler)

    async def _on_chzzk_message(self, message: ChzzkMessage):
        """Handle message from Chzzk and forward to VTuber via proxy."""
        
        # 1. User Blacklist Filter
        if message.user_id in self._blacklisted_users:
            logger.debug(f"Ignoring blacklisted user: {message.nickname} ({message.user_id})")
            return

        # 2. Duplicate/Spam Filter (Cooldown per user)
        current_time = asyncio.get_event_loop().time()
        last_time = self._user_cooldowns.get(message.user_id, 0)
        if current_time - last_time < self._cooldown_seconds:
            logger.debug(f"User {message.nickname} is on cooldown. Skipping.")
            return
        
        self._user_cooldowns[message.user_id] = current_time

        # 3. Content Filter (Basic)
        if not message.content.strip():
            return
            
        # 4. Format with Donation Engine or Basic Metadata
        if message.event_type == "donation":
            formatted_text = self.donation_engine.format_donation_event(
                message.nickname, 
                message.amount, 
                message.content
            )
        else:
            event_tag = f"[event:{message.event_type}]"
            name_tag = f"[nickname:{message.nickname}]"
            formatted_text = f"{event_tag}{name_tag} {message.content}"
        
        if self.is_connected:
            try:
                msg_payload = {"type": "text-input", "text": formatted_text}
                await self._websocket.send(json.dumps(msg_payload))
                logger.info(f"Forwarded Chzzk message: {formatted_text}")
            except Exception as e:
                logger.error(f"Error forwarding to proxy: {e}")
                self._connected = False

    async def run(self) -> None:
        proxy_url = "ws://localhost:12393/proxy-ws"
        self._running = True
        
        if not await self.connect(proxy_url):
            logger.error("Failed to connect to proxy")
            return
            
        try:
            # Start listening to Chzzk messages
            await self.provider.listen(self._on_chzzk_message)
        except Exception as e:
            logger.error(f"Error in Chzzk run loop: {e}")
        finally:
            await self.disconnect()
