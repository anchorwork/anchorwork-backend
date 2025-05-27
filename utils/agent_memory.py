import json
from datetime import datetime
from pathlib import Path

class AgentMemory:
    def __init__(self, agent_id, log_dir="memory", max_history=25):
        self.agent_id = agent_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_path = self.log_dir / f"{agent_id}_log.jsonl"
        self.max_history = max_history
        self.recent_history = self.load_recent()
        self.mood = "neutral"
        self.goals = []

    def append(self, prompt, response, mood=None, tags=None):
        entry = {
            "timestamp": str(datetime.utcnow()),
            "prompt": prompt,
            "response": response,
            "mood": mood or self.mood,
            "tags": tags or [],
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        self.recent_history.append(entry)
        self.recent_history = self.recent_history[-self.max_history:]

    def load_recent(self):
        if not self.log_path.exists():
            return []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-self.max_history :]
            return [json.loads(line) for line in lines]
        except Exception:
            return []

    def summarize(self):
        # Example: Summarize the last few interactions for creative context
        prompts = [e["prompt"] for e in self.recent_history]
        return f"In recent memory, First Matey was asked: {', '.join(prompts[-5:])}"

    def update_mood(self, new_mood):
        self.mood = new_mood

    def add_goal(self, goal):
        self.goals.append(goal)