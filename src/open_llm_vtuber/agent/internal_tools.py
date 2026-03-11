from typing import List, Dict, Any

def get_internal_tool_definitions() -> List[Dict[str, Any]]:
    """
    Returns OpenAI-formatted tool definitions for NULL_AI internal research tools.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "save_research_log",
                "description": "Save a structured research log about a viewer's behavior or patterns.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "viewer": {"type": "string", "description": "The nickname of the viewer being observed."},
                        "observation": {"type": "string", "description": "The specific behavior or pattern observed."},
                        "category": {"type": "string", "description": "Category of study (e.g., behavior_pattern, linguistic_habit).", "default": "behavior_pattern"},
                        "confidence": {"type": "string", "enum": ["low", "medium", "high"], "description": "Confidence level of this observation.", "default": "medium"}
                    },
                    "required": ["viewer", "observation"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_viewer_note",
                "description": "Add a persistent note/fact about a specific viewer to their profile.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nickname": {"type": "string", "description": "The nickname of the viewer."},
                        "note": {"type": "string", "description": "The note or fact to remember (e.g., 'owns a cat', 'is a developer')."}
                    },
                    "required": ["nickname", "note"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_viewer_tag",
                "description": "Assign a specific tag or trait to a viewer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nickname": {"type": "string", "description": "The nickname of the viewer."},
                        "tag": {"type": "string", "description": "The tag name (e.g., 'Regular', 'Technical', 'Friendly')."}
                    },
                    "required": ["nickname", "tag"]
                }
            }
        }
    ]
