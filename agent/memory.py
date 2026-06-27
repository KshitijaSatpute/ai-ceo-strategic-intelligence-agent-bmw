import sqlite3
import json
from pathlib import Path
from datetime import datetime


class AgentMemory:
    def __init__(self):
        self.db_path = Path(__file__).resolve().parents[1] / "data" / "ai_ceo.db"
        self.create_memory_table()

    def create_memory_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                question TEXT,
                query_type TEXT,
                priority TEXT,
                confidence TEXT,
                selected_tools TEXT,
                executed_tools TEXT,
                validation_status TEXT,
                final_briefing TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save_run(self, result):
        trace = result.get("agent_trace", {})
        validation = result.get("validation", {})

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO agent_memory (
                timestamp,
                question,
                query_type,
                priority,
                confidence,
                selected_tools,
                executed_tools,
                validation_status,
                final_briefing
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(timespec="seconds"),
            result.get("question", ""),
            trace.get("query_type", ""),
            result.get("priority", ""),
            result.get("confidence", ""),
            json.dumps(trace.get("selected_tools", [])),
            json.dumps(trace.get("executed_tools", [])),
            validation.get("status", ""),
            result.get("final_briefing", "")
        ))

        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return memory_id


if __name__ == "__main__":
    memory = AgentMemory()
    print("Agent memory table is ready.")