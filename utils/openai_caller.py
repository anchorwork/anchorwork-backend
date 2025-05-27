# utils/openai_caller.py

import os
import openai
from dotenv import load_dotenv
import logging
from typing import Optional

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def call_gpt(prompt: str, model: str = "gpt-4", system_instruction: str = "You are a helpful assistant.", temperature: float = 0.7) -> str:
    """
    Calls the OpenAI GPT model with the given prompt and returns the generated response.

    Args:
        prompt (str): The user input prompt to send to the model.
        model (str, optional): The GPT model to use. Defaults to "gpt-4".
        system_instruction (str, optional): The system message instruction to guide the assistant. Defaults to "You are a helpful assistant.".
        temperature (float, optional): Sampling temperature to use, between 0 and 2. Higher values mean more creative responses. Defaults to 0.7.

    Returns:
        str: The generated response from the GPT model or an error message if something goes wrong.
    """
    if not openai.api_key:
        return "❌ GPT Error: OpenAI API key is missing."

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"GPT call failed: {e}")
        return f"❌ GPT Error: {e}"
