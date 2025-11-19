import os
from pathlib import Path
from typing import Dict, Any
from jinja2 import Template
from app.core.config import settings


class PromptService:
    """
    Manages loading and rendering of prompts from external files.
    Prompts are stored in backend/app/prompts/*.txt
    """

    def __init__(self):
        # In Docker, the app is in /app, so prompts are in /app/app/prompts
        # But locally it might be different.
        # settings.PROMPTS_DIR is relative to where the app is run or absolute.
        # Let's assume it's relative to the backend root for now.
        self.prompts_dir = Path(settings.PROMPTS_DIR)

    def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Load a prompt file and render it with provided variables.

        Args:
            prompt_name: Name of the prompt file (without extension)
            **kwargs: Variables to pass to the template

        Returns:
            Rendered prompt string
        """
        # Ensure we look in the right place. If running from backend root:
        # app/prompts/name.txt
        file_path = self.prompts_dir / f"{prompt_name}.txt"

        # Fallback: try to find it relative to this file if the config path doesn't work
        if not file_path.exists():
            # backend/app/services/../prompts -> backend/app/prompts
            fallback_path = (
                Path(__file__).parent.parent / "prompts" / f"{prompt_name}.txt"
            )
            if fallback_path.exists():
                file_path = fallback_path

        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        template = Template(content)
        return template.render(**kwargs)
