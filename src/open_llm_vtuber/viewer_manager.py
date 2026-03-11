import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger

class ViewerManager:
    """
    Manages persistent viewer data using SQLite.
    Includes tracking of visits, donations, notes, and tags.
    """

    def __init__(self, db_path: str = "viewers.db"):
        self.db_path = db_path
        self._session_seen = set() # Track who visited in current session
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database and create the viewers table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS viewers (
                        nickname TEXT PRIMARY KEY,
                        total_donation INTEGER DEFAULT 0,
                        visit_count INTEGER DEFAULT 0,
                        first_seen TEXT,
                        last_seen TEXT,
                        notes TEXT DEFAULT '[]',
                        tags TEXT DEFAULT '[]'
                    )
                """)
                conn.commit()
            logger.info(f"Viewer database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize viewer database: {e}")

    def update_viewer(self, nickname: str, donation_increment: int = 0):
        """Update or create a viewer record. Visit count only increases once per session."""
        now = datetime.now().isoformat()
        should_increment_visit = nickname not in self._session_seen
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Check if viewer exists
                cursor.execute("SELECT visit_count, total_donation FROM viewers WHERE nickname = ?", (nickname,))
                row = cursor.fetchone()

                if row:
                    visit_count, total_donation = row
                    new_visit_count = visit_count + 1 if should_increment_visit else visit_count
                    cursor.execute("""
                        UPDATE viewers 
                        SET visit_count = ?, total_donation = ?, last_seen = ?
                        WHERE nickname = ?
                    """, (new_visit_count, total_donation + donation_increment, now, nickname))
                else:
                    cursor.execute("""
                        INSERT INTO viewers (nickname, total_donation, visit_count, first_seen, last_seen)
                        VALUES (?, ?, ?, ?, ?)
                    """, (nickname, donation_increment, 1, now, now))
                conn.commit()
            
            if should_increment_visit:
                self._session_seen.add(nickname)
                logger.debug(f"Incremented visit count for: {nickname}")
        except Exception as e:
            logger.error(f"Error updating viewer {nickname}: {e}")

    def add_note(self, nickname: str, note: str):
        """Add a note to a viewer's record. Deduplicates against very recent notes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT notes FROM viewers WHERE nickname = ?", (nickname,))
                row = cursor.fetchone()
                if row:
                    notes = json.loads(row[0])
                    # Check for duplication in last 2 notes
                    recent_notes = [n['text'] for n in notes[-2:]]
                    if note in recent_notes:
                        logger.debug(f"Skipping duplicate note for {nickname}")
                        return

                    notes.append({"text": note, "timestamp": datetime.now().isoformat()})
                    cursor.execute("UPDATE viewers SET notes = ? WHERE nickname = ?", (json.dumps(notes, ensure_ascii=False), nickname))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error adding note for {nickname}: {e}")

    def add_tag(self, nickname: str, tag: str):
        """Add a tag to a viewer's record. Case-insensitive deduplication."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT tags FROM viewers WHERE nickname = ?", (nickname,))
                row = cursor.fetchone()
                if row:
                    tags = json.loads(row[0])
                    tag_lower = tag.lower()
                    if tag_lower not in [t.lower() for t in tags]:
                        tags.append(tag)
                        cursor.execute("UPDATE viewers SET tags = ? WHERE nickname = ?", (json.dumps(tags, ensure_ascii=False), nickname))
                        conn.commit()
                        logger.info(f"Tag '{tag}' added to {nickname}")
        except Exception as e:
            logger.error(f"Error adding tag for {nickname}: {e}")

    def get_viewer(self, nickname: str) -> Optional[Dict[str, Any]]:
        """Get the full raw viewer data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM viewers WHERE nickname = ?", (nickname,))
                row = cursor.fetchone()
                if row:
                    data = dict(row)
                    data['notes'] = json.loads(data['notes'])
                    data['tags'] = json.loads(data['tags'])
                    return data
        except Exception as e:
            logger.error(f"Error getting viewer {nickname}: {e}")
        return None

    def get_viewer_context(self, nickname: str, mode: str = 'short', recent_logs: List[Dict[str, Any]] = None) -> str:
        """
        Generate a string context for the LLM based on viewer data and research logs.
        """
        viewer = self.get_viewer(nickname)
        if not viewer:
            return f"[viewer_context] nickname: {nickname} (First interaction) [/viewer_context]"

        if mode == 'short':
            return (f"[viewer_context] "
                    f"nickname: {nickname}, "
                    f"visit_count: {viewer['visit_count']}, "
                    f"total_donation: {viewer['total_donation']} "
                    f"[/viewer_context]")
        else:
            notes_str = "\n".join([f"- {n['text']}" for n in viewer['notes'][-3:]]) # last 3 notes
            tags_str = ", ".join(viewer['tags'])
            
            research_str = ""
            if recent_logs:
                research_str = "\n[recent_research_logs]\n" + "\n".join([f"- {log['observation']}" for log in recent_logs]) + "\n[/recent_research_logs]"

            return (f"[viewer_research_memory]\n"
                    f"nickname: {nickname}\n"
                    f"visit_count: {viewer['visit_count']}\n"
                    f"total_donation: {viewer['total_donation']}\n"
                    f"known_traits: {tags_str if tags_str else 'N/A'}\n"
                    f"recent_notes:\n{notes_str if notes_str else '- N/A'}"
                    f"{research_str}\n"
                    f"[/viewer_research_memory]")
