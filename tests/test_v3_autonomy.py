import asyncio
import json
import os
import sys
from unittest.mock import MagicMock, AsyncMock

# Add root and src to sys.path
root_dir = os.getcwd()
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "src"))

from open_llm_vtuber.agent.agents.basic_memory_agent import BasicMemoryAgent
from open_llm_vtuber.viewer_manager import ViewerManager
from open_llm_vtuber.research_manager import ResearchManager
from open_llm_vtuber.agent.input_types import BatchInput, TextData, TextSource

async def test_v3_flow():
    # Setup
    if os.path.exists("test_viewers.db"): os.remove("test_viewers.db")
    if os.path.exists("test_research.json"): os.remove("test_research.json")
    if os.path.exists("test_highlights.json"): os.remove("test_highlights.json")

    vm = ViewerManager(db_path="test_viewers.db")
    rm = ResearchManager(log_path="test_research.json", highlight_path="test_highlights.json")

    # Mock LLM
    mock_llm = MagicMock()
    
    # Mock Live2D
    mock_l2d = MagicMock()

    agent = BasicMemoryAgent(
        llm=mock_llm,
        system="Persona: NULL_AI",
        live2d_model=mock_l2d,
        use_mcpp=True
    )
    agent.viewer_manager = vm
    agent.research_manager = rm

    nickname = "TestUser"
    
    print("\n--- Test 1: Session-based Visit Count ---")
    agent._to_text_prompt(BatchInput(texts=[TextData(content=f"[nickname:{nickname}] Hello", source=TextSource.INPUT)]))
    agent._to_text_prompt(BatchInput(texts=[TextData(content=f"[nickname:{nickname}] Still here", source=TextSource.INPUT)]))
    
    viewer = vm.get_viewer(nickname)
    print(f"Visit count (should be 1): {viewer['visit_count']}")
    assert viewer['visit_count'] == 1

    print("\n--- Test 2: Internal Tool Registration ---")
    print(f"Formatted Tools (OpenAI): {len(agent._formatted_tools_openai)}")
    assert any(t['function']['name'] == "save_research_log" for t in agent._formatted_tools_openai)

    print("\n--- Test 3: Log Reinjection (Block Format) ---")
    rm.save_log(nickname, "User likes technical topics", confidence="high")
    
    # Request that triggers 'full' context
    prompt = agent._to_text_prompt(BatchInput(texts=[TextData(content=f"[nickname:{nickname}] 나 누구야? 내 패턴 어때?", source=TextSource.INPUT)]))
    print(f"Generated text prompt snippet:\n{prompt[:300]}...")
    assert "[viewer_research_memory]" in prompt
    assert "[recent_research_logs]" in prompt
    assert "User likes technical topics" in prompt

    print("\n--- Test 4: High Confidence Highlights ---")
    assert os.path.exists("test_highlights.json")
    with open("test_highlights.json", "r", encoding="utf-8") as f:
        highlights = json.load(f)
    print(f"Highlights count: {len(highlights)}")
    assert len(highlights) == 1

    # Cleanup
    if os.path.exists("test_viewers.db"): os.remove("test_viewers.db")
    if os.path.exists("test_research.json"): os.remove("test_research.json")
    if os.path.exists("test_highlights.json"): os.remove("test_highlights.json")
    print("\nV3 Tests Passed!")

if __name__ == "__main__":
    asyncio.run(test_v3_flow())
