from typing import Dict, Tuple
from loguru import logger

class DonationEngine:
    """
    Engine to handle donation logic and map increments to NULL_AI research levels.
    """
    
    # Define thresholds and their corresponding metadata
    LEVELS = {
        50000: {
            "name": "Critical Research Mode",
            "tag": "[state:Critical_Research]",
            "priority": "Max"
        },
        10000: {
            "name": "Special Experiment",
            "tag": "[state:Special_Experiment]",
            "priority": "High"
        },
        5000: {
            "name": "Priority Analysis",
            "tag": "[state:Priority_Analysis]",
            "priority": "Medium"
        },
        1000: {
            "name": "Research Support",
            "tag": "[state:Research_Support]",
            "priority": "Normal"
        }
    }

    def get_level_info(self, amount: int) -> Dict[str, str]:
        """
        Determine the research level based on the donation amount.
        Returns a dictionary with level name, system tags, and priority.
        """
        # Sort keys in descending order to find the highest matching threshold
        for threshold in sorted(self.LEVELS.keys(), reverse=True):
            if amount >= threshold:
                return self.LEVELS[threshold]
        
        # Default for small donations
        return {
            "name": "Minor Contribution",
            "tag": "[state:Normal]",
            "priority": "Low"
        }

    def format_donation_event(self, nickname: str, amount: int, content: str) -> str:
        """
        Create a formatted string for the LLM that includes research level information.
        """
        level_info = self.get_level_info(amount)
        
        event_tag = "[event:donation]"
        name_tag = f"[nickname:{nickname}]"
        amount_tag = f"[amount:{amount}]"
        level_tag = f"[level:{level_info['name']}]"
        system_tag = level_info['tag']
        
        formatted = f"{event_tag}{name_tag}{amount_tag}{level_tag}{system_tag} {content}"
        logger.debug(f"Formatted donation for {nickname}: {level_info['name']} ({amount})")
        return formatted
