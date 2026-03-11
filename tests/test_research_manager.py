import unittest
import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from open_llm_vtuber.research_manager import ResearchManager

class TestResearchManager(unittest.TestCase):
    def setUp(self):
        self.log_path = "test_research_logs.json"
        self.manager = ResearchManager(self.log_path)

    def tearDown(self):
        if os.path.exists(self.log_path):
            os.remove(self.log_path)

    def test_save_and_get_logs(self):
        self.manager.save_log("홍길동", "새벽에 고양이 얘기를 즐겨함", category="hobby")
        self.manager.save_log("홍길동", "반복적인 질문을 하는 경향이 있음", category="pattern")
        self.manager.save_log("임꺽정", "주로 낮 시간에 활동함")
        
        # Test generic retrieval
        logs = self.manager.get_recent_logs(limit=2)
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[-1]["viewer"], "임꺽정")
        
        # Test filtered retrieval
        hong_logs = self.manager.get_recent_logs(viewer="홍길동")
        self.assertEqual(len(hong_logs), 2)
        self.assertIn("hobby", [log["category"] for log in hong_logs])

    def test_log_structure(self):
        self.manager.save_log("test_user", "test observation")
        with open(self.log_path, "r", encoding="utf-8") as f:
            logs = json.load(f)
        
        log = logs[0]
        self.assertIn("timestamp", log)
        self.assertEqual(log["viewer"], "test_user")
        self.assertEqual(log["observation"], "test observation")

if __name__ == "__main__":
    unittest.main()
