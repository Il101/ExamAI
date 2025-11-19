from pathlib import Path

import pytest

from app.core.config import settings
from app.services.prompt_service import PromptService


class TestPromptService:

    def test_get_prompt_success(self, tmp_path, monkeypatch):
        # Arrange
        # Create a dummy prompt file
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        prompt_file = prompt_dir / "test_prompt.txt"
        prompt_file.write_text("Hello {{ name }}!")

        # Patch settings
        monkeypatch.setattr(settings, "PROMPTS_DIR", str(prompt_dir))

        service = PromptService()

        # Act
        result = service.get_prompt("test_prompt", name="World")

        # Assert
        assert result == "Hello World!"

    def test_get_prompt_not_found(self, tmp_path, monkeypatch):
        # Arrange
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        monkeypatch.setattr(settings, "PROMPTS_DIR", str(prompt_dir))

        service = PromptService()

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            service.get_prompt("non_existent")

    def test_get_prompt_complex_template(self, tmp_path, monkeypatch):
        # Arrange
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        prompt_file = prompt_dir / "complex.txt"
        prompt_file.write_text("{% for item in items %}- {{ item }}\n{% endfor %}")

        monkeypatch.setattr(settings, "PROMPTS_DIR", str(prompt_dir))
        service = PromptService()

        # Act
        result = service.get_prompt("complex", items=["A", "B"])

        # Assert
        assert "- A" in result
        assert "- B" in result
