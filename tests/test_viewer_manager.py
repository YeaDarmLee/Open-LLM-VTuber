import os
import sys
import unittest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from open_llm_vtuber.viewer_manager import ViewerManager

class TestViewerManager(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_viewers.db"
        self.manager = ViewerManager(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_update_and_get_viewer(self):
        self.manager.update_viewer("test_user", 1000)
        viewer = self.manager.get_viewer("test_user")
        self.assertIsNotNone(viewer)
        self.assertEqual(viewer["nickname"], "test_user")
        self.assertEqual(viewer["total_donation"], 1000)
        self.assertEqual(viewer["visit_count"], 1)

        self.manager.update_viewer("test_user", 500)
        viewer = self.manager.get_viewer("test_user")
        self.assertEqual(viewer["total_donation"], 1500)
        self.assertEqual(viewer["visit_count"], 2)

    def test_add_note_and_tag(self):
        self.manager.update_viewer("test_user")
        self.manager.add_note("test_user", "개발자임")
        self.manager.add_tag("test_user", "고양이")
        
        viewer = self.manager.get_viewer("test_user")
        self.assertEqual(len(viewer["notes"]), 1)
        self.assertEqual(viewer["notes"][0]["text"], "개발자임")
        self.assertIn("고양이", viewer["tags"])

    def test_context_generation(self):
        self.manager.update_viewer("test_user", 5000)
        self.manager.add_tag("test_user", "단골")
        
        short_context = self.manager.get_viewer_context("test_user", mode="short")
        self.assertIn("total_donation: 5000", short_context)
        self.assertNotIn("단골", short_context)
        
        full_context = self.manager.get_viewer_context("test_user", mode="full")
        self.assertIn("known_traits: 단골", full_context)

if __name__ == "__main__":
    unittest.main()
