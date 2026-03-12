import random
import time
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

async def handle_idle_event(
    client_uid: str,
    context: ServiceContext,
    websocket: WebSocket,
    client_contexts: Dict[str, ServiceContext],
    client_connections: Dict[str, WebSocket],
    chat_group_manager: ChatGroupManager,
    current_conversation_tasks: Dict[str, Optional[asyncio.Task]],
    broadcast_to_group: Callable,
) -> None:
    """Handle an idle stream event by triggering a spontaneous conversation."""
    logger.info(f"Handling idle event for client {client_uid}")
    
    # Try to get prompts from the tool_prompts configuration
    tool_prompts = context.system_config.tool_prompts
    
    # Check for our 3 idle prompts
    prompts = []
    if "idle_question_prompt" in tool_prompts:
        prompts.append(tool_prompts["idle_question_prompt"])
    if "idle_observation_prompt" in tool_prompts:
        prompts.append(tool_prompts["idle_observation_prompt"])
    if "idle_tease_prompt" in tool_prompts:
        prompts.append(tool_prompts["idle_tease_prompt"])
    
    # Fallback to general idle prompt if not configured with specific ones
    if not prompts and "idle_prompt" in tool_prompts:
        prompts.append(tool_prompts["idle_prompt"])
        
    prompt_file_name = random.choice(prompts) if prompts else None
    
    if prompt_file_name:
        try:
            user_input = prompt_loader.load_util(prompt_file_name)
        except Exception as e:
            logger.error(f"Error loading idle prompt {prompt_file_name}: {e}")
            user_input = "[IDLE EVENT] The chat has been quiet. Say something interesting."
    else:
        logger.warning(
            "Idle prompt not configured in system_config.tool_prompts. "
            "Using default idle text."
        )
        user_input = "[IDLE EVENT] The chat has been quiet. Say something interesting."

    session_emoji = np.random.choice(EMOJI_LIST)

    # Metadata to ensure this doesn't pollute the long-term character memory
    # You can customize whether this skips history or not. For now we skip it.
    metadata = {
        "is_idle_talk": True,
        "skip_history": True, 
    }

    group = chat_group_manager.get_client_group(client_uid)
    if group and len(group.members) > 1:
        # Group conversation
        task_key = group.group_id
        logger.info(f"Starting group reaction for idle talk in {task_key}")
        
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
        logger.info(f"Starting individual reaction for idle talk for {client_uid}")
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
