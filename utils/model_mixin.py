import re
from typing import Optional
from config.model_config import MODEL_REGISTRY, describe_model

class ModelSwitchingMixin:
    """
    Mixin class to add model switching capabilities.

    Attributes:
        model (str): The current model name in use.
        context (dict): A dictionary to hold context information, including model overrides.
    """

    def override_model(self, model_name: str) -> str:
        """
        Override the current model with the specified model name.

        Args:
            model_name (str): The name of the model to switch to.

        Returns:
            str: A message indicating success or failure of the model switch.
        """
        if model_name in MODEL_REGISTRY:
            self.model = model_name
            self.context["model_override"] = model_name
            return f"🔁 Model switched to: {model_name}"
        return f"❌ Unknown model: {model_name}"

    def recommend_model(self, based_on: str = "long") -> str:
        """
        Recommend a model based on a given criterion.

        Args:
            based_on (str, optional): The basis for recommendation. Defaults to "long".

        Returns:
            str: A message suggesting the recommended model.
        """
        preferred = {
            "long": "gpt-4.1-long" if "4.1" in self.model else "gpt-4o-long",
            "mini": "gpt-4.1-mini-2025-04-14" if "4.1" in self.model else "gpt-4o-mini-2024-07-18",
            "realtime": "gpt-4o-mini-realtime-preview-2024-12-17"
        }.get(based_on, self.model)
        return f"⚠️ Based on '{based_on}', I suggest using `{preferred}`."

    def handle_model_prompt(self, prompt: str) -> Optional[str]:
        """
        Handle a prompt that may contain commands to switch or describe models.

        Args:
            prompt (str): The input prompt string.

        Returns:
            Optional[str]: A response string if a command is recognized, otherwise None.
        """
        lowered = prompt.lower()
        if "switch to" in lowered:
            match = re.search(r"switch to ([\w\-\.]+)", prompt)
            if match:
                return self.override_model(match.group(1))
        if "use long" in lowered:
            return self.override_model("gpt-4.1-long" if "4.1" in self.model else "gpt-4o-long")
        if "use mini" in lowered:
            return self.override_model("gpt-4.1-mini-2025-04-14" if "4.1" in self.model else "gpt-4o-mini-2024-07-18")
        if "use realtime" in lowered:
            return self.override_model("gpt-4o-mini-realtime-preview-2024-12-17")
        if "describe model" in lowered:
            return describe_model(self.model)
        return None
