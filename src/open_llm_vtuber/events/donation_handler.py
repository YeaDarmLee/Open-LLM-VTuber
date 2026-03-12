from typing import Dict, Optional, Callable
from fastapi import WebSocket
from loguru import logger
import numpy as np
import asyncio

from ..service_context import ServiceContext
from ..chat_group import ChatGroupManager
from ..conversations.single_conversation import process_single_conversation
from ..conversations.group_conversation import process_group_conversation
from ..conversations.conversation_utils import EMOJI_LIST
from prompts import prompt_loader

import time

def get_donation_level(amount: int) -> str:
    """Determine the level of donation based on amount."""
    if amount < 1000:
        return "small"
    elif amount < 5000:
        return "medium"
    elif amount < 20000:
        return "big"
    else:
        return "huge"

# Cooldown tracker
donation_cooldowns: Dict[str, float] = {}

async def handle_donation_event(
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
    """Handle a donation event."""
    viewer_name = data.get("viewer_name", "Unknown")
    amount = data.get("amount", 0)
    currency = data.get("currency", "")
    message = data.get("message", "")

    # Check cooldown
    current_time = time.time()
    last_donation_time = donation_cooldowns.get(viewer_name, 0)
    is_in_cooldown = (current_time - last_donation_time) < 5.0
    donation_cooldowns[viewer_name] = current_time

    # Evaluate donation level based on cooldown and amount
    level = "cooldown" if is_in_cooldown else get_donation_level(amount)

    # Manage empty messages gracefully
    message_text = f"Message: {message}" if message else "Message: (None)"

    # Load prompt
    prompt_name = "donation_prompt"
    prompt_file = context.system_config.tool_prompts.get(prompt_name)

    if prompt_file:
        try:
            # We assume prompt_loader has a format util, or we just format it here
            prompt_template = prompt_loader.load_util(prompt_file)
            user_input = prompt_template.format(
                viewer_name=viewer_name,
                amount=amount,
                currency=currency,
                message=message_text,
                level=level
            )
        except Exception as e:
            logger.error(f"Error formatting donation prompt: {e}")
            user_input = f"[DONATION EVENT] {viewer_name} sent {amount} {currency}! {message_text}"
    else:
        logger.warning("Donation prompt not configured, using default")
        user_input = f"[DONATION EVENT] {viewer_name} sent {amount} {currency}! {message_text}"

    session_emoji = np.random.choice(EMOJI_LIST)

    # Metadata to ensure this doesn't pollute the long-term character memory
    metadata = {
        "is_donation": True,
        "skip_history": True, # Don't save to the main conversation history
    }

    group = chat_group_manager.get_client_group(client_uid)
    if group and len(group.members) > 1:
        # Group conversation
        task_key = group.group_id
        logger.info(f"Starting group reaction for donation in {task_key}")
        
        current_conversation_tasks[task_key] = asyncio.create_task(
            process_group_conversation(
                client_contexts=client_contexts,
                client_connections=client_connections,
                broadcast_func=broadcast_to_group,
                group_members=group.members,
                initiator_client_uid=client_uid,
                user_input=user_input,
                images=None,
                session_emoji=session_emoji,
                metadata=metadata,
            )
        )
    else:
        # Individual conversation
        logger.info(f"Starting individual reaction for donation by {viewer_name}")
        current_conversation_tasks[client_uid] = asyncio.create_task(
            process_single_conversation(
                context=context,
                websocket_send=websocket.send_text,
                client_uid=client_uid,
                user_input=user_input,
                images=None,
                session_emoji=session_emoji,
                metadata=metadata,
            )
        )
