from utils.log_utils import search_codex
from utils.agent_memory import AgentMemory

memory = AgentMemory("watcher")

async def summarize_logs(keyword: str) -> str:
    entries = search_codex(keyword)
    if not entries:
        return "No matching logs found."
    summary = f"Found {len(entries)} entries related to '{keyword}':\n"
    for e in entries[-5:]:  # show latest 5
        summary += f"- [{e['timestamp']}] {e['agent']}: {e['response'][:100]}...\n"
    memory_summary = memory.summarize()
    memory_flavor = f"_Watcher recalls_: {memory_summary}" if memory_summary else ""
    memory.append(f"summarize_logs({keyword})", summary, tags=["watch", "summary"])
    return f"{summary}\n{memory_flavor}"