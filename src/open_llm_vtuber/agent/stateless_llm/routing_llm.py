from typing import AsyncIterator, List, Dict, Any
from .stateless_llm_interface import StatelessLLMInterface
from loguru import logger

class RoutingLLM(StatelessLLMInterface):
    """
    A stateless LLM that routes requests to a primary or secondary LLM
    based on the content of the messages (e.g., event tags or keywords).
    """

    def __init__(
        self, primary_llm: StatelessLLMInterface, secondary_llm: StatelessLLMInterface
    ):
        self.primary_llm = primary_llm
        self.secondary_llm = secondary_llm

    def _extract_text(self, content: Any) -> str:
        """Helper to extract text from both string and multimodal list content."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return " ".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
        return ""

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        system: str = None,
        tools: List[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        # Determine routing
        last_message_content = ""
        if messages:
            last_message_content = self._extract_text(messages[-1].get("content", ""))

        # Determine routing behavior based on 'intent'
        text = last_message_content
        small_talk_keywords = ["안녕", "뭐해", "잘자", "오늘 어때", "심심해", "반가워"]
        memory_heavy_keywords = [
            # Memory/Identity/Context
            "기억", "기록", "로그", "패턴", "분석", "메모",
            "나는", "내", "저의", "나에 대해", "나 기억", "내 데이터",
            "연구", "관찰", "피실험체", "데이터", 
            # Tool-related
            "태그", "노트", "실험", "테스트"
        ]
        
        # Broadcast Safety: Sensitive/NSFW keywords that should be handled by Primary LLM
        safety_keywords = [
            "섹스", "자위", "정액", "성관계", "항문", "성기", "보지", "자지", 
            "죽고 싶", "자살", "살인", "범죄", "마약", "도박",
            "엄마", "미안" # Sensitive emotional context
        ]
        
        is_high_value = False
        is_safety_risk = False
        
        # Priority 1: Safety risks always go to Primary
        if any(kw in text for kw in safety_keywords):
            is_safety_risk = True
            logger.warning(f"Safety/Sensitive intent detected: '{text[:20]}...'. Routing to PRIMARY LLM for safer handling.")
            is_high_value = True
        
        # Priority 2: Donation always goes to Primary
        elif "[event:donation]" in text:
            is_high_value = True
            logger.info("Donation event detected. Routing to PRIMARY LLM.")
        
        # Priority 2: Memory/Logging/Tool-likely intent
        elif any(kw in text for kw in memory_heavy_keywords):
            is_high_value = True
            logger.info(f"High-Value intent detected: '{text[:20]}...'. Routing to PRIMARY LLM.")
        
        # Priority 3: Default to Secondary for greetings/small talk
        else:
            logger.info(f"General chat intent detected: '{text[:20]}...'. Routing to SECONDARY LLM.")

        if is_high_value:
            async for chunk in self.primary_llm.chat_completion(messages, system, tools):
                yield chunk
        else:
            async for chunk in self.secondary_llm.chat_completion(messages, system, tools):
                yield chunk
