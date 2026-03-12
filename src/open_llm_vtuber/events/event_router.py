from typing import Dict, List, Optional, Callable
from fastapi import WebSocket
from loguru import logger
import numpy as np
import asyncio

from ..service_context import ServiceContext
from ..chat_group import ChatGroupManager
from .donation_handler import handle_donation_event
from .idle_handler import handle_idle_event

class EventRouter:
    """Routes incoming events to their respective handlers."""

    def __init__(self):
        """Initialize event router."""
        pass

    async def route_event(
        self,
        event_type: str,
        data: dict,
        client_uid: str,
        context: ServiceContext,
        websocket: WebSocket,
        client_contexts: Dict[str, ServiceContext],
        client_connections: Dict[str, WebSocket],
        chat_group_manager: ChatGroupManager,
        current_conversation_tasks: Dict[str, Optional[asyncio.Task]],
        broadcast_to_group: Callable,
    ) -> None:
        """
        Route an incoming event to the appropriate handler.
        """
        if event_type == "donation":
            await handle_donation_event(
                data=data,
                client_uid=client_uid,
                context=context,
                websocket=websocket,
                client_contexts=client_contexts,
                client_connections=client_connections,
                chat_group_manager=chat_group_manager,
                current_conversation_tasks=current_conversation_tasks,
                broadcast_to_group=broadcast_to_group,
            )
        elif event_type == "idle":
            await handle_idle_event(
                client_uid=client_uid,
                context=context,
                websocket=websocket,
                client_contexts=client_contexts,
                client_connections=client_connections,
                chat_group_manager=chat_group_manager,
                current_conversation_tasks=current_conversation_tasks,
                broadcast_to_group=broadcast_to_group,
            )
        else:
            logger.warning(f"EventRouter received unknown event type: {event_type}")

# Singleton instance for the router
event_router = EventRouter()
