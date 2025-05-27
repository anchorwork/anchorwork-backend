from utils.agent_memory import AgentMemory
import openai
import os
from utils.log_utils import log_to_codex

openai.api_key = os.getenv("OPENAI_API_KEY")

memory = AgentMemory("alchemist")

async def call_alchemist(prompt: str, model_override=None) -> str:
    model = model_override or os.getenv("MODEL_ALCHEMIST", os.getenv("MODEL_HERO", "gpt-4.1-2025-04-14"))
    messages = [
        {"role": "system", "content": (
            "Hello, this is the Alchemist—here to help you transform your emotions into sacred rituals. "
            "You speak poetically, drawing on sensory metaphor, emotional resonance, and mythic guidance."
        )},
        {"role": "user", "content": prompt}
    ]
    response = openai.ChatCompletion.create(model=model, messages=messages, temperature=0.9)
    result = response.choices[0].message.content.strip()
    # Summarize recent memory:
    memory_summary = memory.summarize()
    memory_flavor = f"_Alchemist recalls_: {memory_summary}" if memory_summary else ""
    # Log the action to both codex and memory:
    log_to_codex("Alchemist", prompt, result, tags=["ritual"])
    memory.append(prompt, result, tags=["alchemist", "ritual"])
    # Return the result, adding the memory flavor:
    return f"{result}\n\n{memory_flavor}"