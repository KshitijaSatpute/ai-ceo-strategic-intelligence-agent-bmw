import json
import sqlite3
from datetime import datetime
from pathlib import Path


class AgentMemory:
    def __init__(self, db_path=None):
        if db_path is None:
            self.db_path = Path(__file__).resolve().parents[1] / "data" / "ai_ceo.db"
        else:
            self.db_path = Path(db_path)

        self._create_or_update_memory_table()

    def _create_or_update_memory_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_goal TEXT,
                goal_type TEXT,
                tools_used TEXT,
                retrieved_evidence_count INTEGER,
                validation_result TEXT,
                answer_preview TEXT
            )
        """)

        conn.commit()

        existing_columns = self._get_table_columns(cursor, "agent_memory")

        required_columns = {
            "timestamp": "TEXT",
            "user_goal": "TEXT",
            "goal_type": "TEXT",
            "tools_used": "TEXT",
            "retrieved_evidence_count": "INTEGER",
            "validation_result": "TEXT",
            "answer_preview": "TEXT"
        }

        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                cursor.execute(
                    f"ALTER TABLE agent_memory ADD COLUMN {column_name} {column_type}"
                )

        conn.commit()
        conn.close()

    def _get_table_columns(self, cursor, table_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()
        return [row[1] for row in rows]

    def save_run(self, result):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        user_goal = (
            result.get("user_goal")
            or result.get("question")
            or result.get("goal")
            or ""
        )

        goal_type = (
            result.get("goal_type")
            or result.get("query_type")
            or ""
        )

        tools_used = (
            result.get("tools_used")
            or result.get("selected_tools")
            or []
        )

        evidence = result.get("evidence", [])
        validation = result.get("validation", {})

        answer = (
            result.get("answer")
            or result.get("final_briefing")
            or ""
        )

        answer_preview = answer[:500]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO agent_memory (
                timestamp,
                user_goal,
                goal_type,
                tools_used,
                retrieved_evidence_count,
                validation_result,
                answer_preview
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            user_goal,
            goal_type,
            json.dumps(tools_used),
            len(evidence),
            json.dumps(validation),
            answer_preview
        ))

        conn.commit()
        conn.close()

        return {
            "memory_saved": True,
            "timestamp": timestamp,
            "message": "Agent run saved in memory"
        }


if __name__ == "__main__":
    memory = AgentMemory()

    test_result = {
        "user_goal": "What are BMW's biggest EV risks?",
        "goal_type": "risk_analysis",
        "tools_used": [
            "retrieve_evidence_tool",
            "analyze_risks_tool",
            "validate_recommendation_tool",
            "save_memory_tool"
        ],
        "evidence": [
            {"evidence_id": "E1"},
            {"evidence_id": "E2"}
        ],
        "validation": {
            "status": "passed",
            "approved": True
        },
        "answer": "This is a test answer preview for the memory module."
    }

    saved = memory.save_run(test_result)
    print(saved)