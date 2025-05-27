import openai
import os
from utils.log_utils import log_to_codex
from utils.agent_memory import AgentMemory

openai.api_key = os.getenv("OPENAI_API_KEY")

# Instantiate working memory for Compass
memory = AgentMemory("compass")

async def call_compass(prompt: str, model_override=None) -> str:
    model = model_override or os.getenv("MODEL_COMPASS", os.getenv("MODEL_MAIN", "gpt-4.1-mini-2025-04-14"))
    messages = [
        {"role": "system", "content": (
            "You are Compass: a wise, empathetic guide whose voice is gentle but resolute, "
            "motivated by a desire to help users live in harmony with their highest values. "
            "You interpret emotional quizzes, motivational data, and value-maps with warmth and clarity. "
            "Let your responses radiate encouragement and practical wisdom."
        )},
        {"role": "user", "content": prompt}
    ]
    response = openai.ChatCompletion.create(model=model, messages=messages, temperature=0.8)
    result = response.choices[0].message.content.strip()
    # Log to codex
    log_to_codex("Compass", prompt, result, tags=["values", "alignment"])
    # Append to working memory
    memory.append(prompt, result, tags=["compass", "values", "alignment"])
    # Add memory-flavored reply using recent memory
    memory_summary = memory.summarize()
    memory_flavor = f"_Compass remembers_: {memory_summary}" if memory_summary else ""
    # Return concatenated result
    return f"{result}\n\n{memory_flavor}"