import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger

class ResearchManager:
    """
    Manages structured research logs for NULL_AI.
    Records observations about human behavior (viewers) during broadcasts.
    """

    def __init__(self, log_path: str = "research_logs.json", highlight_path: str = "research_highlights.json"):
        self.log_path = log_path
        self.highlight_path = highlight_path
        self._ensure_log_file(self.log_path)
        self._ensure_log_file(self.highlight_path)

    def _ensure_log_file(self, path: str):
        """Ensure the log file exists and is a valid JSON list."""
        if not os.path.exists(path):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([], f)
                logger.info(f"Initialized research log file at {path}")
            except Exception as e:
                logger.error(f"Failed to initialize research log {path}: {e}")

    def save_log(self, viewer: str, observation: str, category: str = "behavior_pattern", confidence: str = "medium", source_event: str = "chat"):
        """
        Save a structured research log.
        Confidence: low (not saved), medium (saved to logs), high (saved to logs + highlights)
        """
        if confidence.lower() == "low":
            logger.debug(f"Skipping low confidence log for {viewer}")
            return

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "viewer": viewer,
            "category": category,
            "observation": observation,
            "confidence": confidence.lower(),
            "source_event": source_event
        }

        # Save to main logs
        self._append_to_json(self.log_path, log_entry)
        
        # Save to highlights if high confidence
        if confidence.lower() == "high":
            self._append_to_json(self.highlight_path, log_entry)
            logger.info(f"High confidence research HIGHLIGHT saved for {viewer}")

        logger.info(f"Research log saved for {viewer}: {observation[:30]}...")

    def _append_to_json(self, path: str, entry: dict):
        """Helper to append an entry to a JSON list file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                logs = json.load(f)
            logs.append(entry)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error appending to {path}: {e}")

    def get_recent_logs(self, viewer: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve recent research logs, optionally filtered by viewer.
        """
        try:
            if not os.path.exists(self.log_path):
                return []
                
            with open(self.log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
            
            if viewer:
                filtered_logs = [log for log in logs if log["viewer"] == viewer]
            else:
                filtered_logs = logs
            
            return filtered_logs[-limit:]
        except Exception as e:
            logger.error(f"Error reading research logs: {e}")
            return []

    def clear_logs(self):
        """Clear all research logs (mainly for testing)."""
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump([], f)
        except Exception as e:
            logger.error(f"Error clearing logs: {e}")
