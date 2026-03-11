import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from open_llm_vtuber.live.donation_engine import DonationEngine

class TestDonationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DonationEngine()

    def test_get_level_info(self):
        # Critical
        info = self.engine.get_level_info(60000)
        self.assertEqual(info["name"], "Critical Research Mode")
        
        # Special
        info = self.engine.get_level_info(12000)
        self.assertEqual(info["name"], "Special Experiment")
        
        # Priority
        info = self.engine.get_level_info(5500)
        self.assertEqual(info["name"], "Priority Analysis")
        
        # Support
        info = self.engine.get_level_info(1500)
        self.assertEqual(info["name"], "Research Support")
        
        # Minor
        info = self.engine.get_level_info(500)
        self.assertEqual(info["name"], "Minor Contribution")

    def test_format_donation_event(self):
        formatted = self.engine.format_donation_event("홍길동", 10000, "화이팅!")
        self.assertIn("[level:Special Experiment]", formatted)
        self.assertIn("[state:Special_Experiment]", formatted)
        self.assertIn("[nickname:홍길동]", formatted)
        self.assertIn("화이팅!", formatted)

if __name__ == "__main__":
    unittest.main()
