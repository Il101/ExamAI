"""
Prompt loader utility for managing AI prompts stored in external files.
Supports template variables for dynamic content injection.
"""
from pathlib import Path
from typing import Dict, Optional
import os
import aiofiles


class PromptLoader:
    """
    Loads and manages AI prompts from text files.
    Supports template variable substitution.
    """
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt files. 
                        Defaults to app/prompts/
        """
        if prompts_dir is None:
            # Get the directory where this file is located
            current_file = Path(__file__)
            prompts_dir = current_file.parent
        
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, str] = {}
        self._cache_enabled = os.getenv("PROMPT_CACHE_ENABLED", "true").lower() == "true"
    def load(self, prompt_path: str, **variables) -> str:
        """
        Load a prompt from file and substitute variables.
        """
        # Load from cache or file
        if self._cache_enabled and prompt_path in self._cache:
            template = self._cache[prompt_path]
        else:
            template = self._load_from_file(prompt_path)
            if self._cache_enabled:
                self._cache[prompt_path] = template
        
        # Substitute variables if provided
        if variables:
            try:
                return template.format(**variables)
            except KeyError as e:
                raise ValueError(
                    f"Missing template variable {e} for prompt '{prompt_path}'. "
                    f"Available variables: {list(variables.keys())}"
                )
        
        return template

    async def aload(self, prompt_path: str, **variables) -> str:
        """
        Load a prompt from file and substitute variables (Asynchronous).
        """
        # Load from cache or file
        if self._cache_enabled and prompt_path in self._cache:
            template = self._cache[prompt_path]
        else:
            template = await self._aload_from_file(prompt_path)
            if self._cache_enabled:
                self._cache[prompt_path] = template
        
        # Substitute variables if provided
        if variables:
            try:
                return template.format(**variables)
            except KeyError as e:
                raise ValueError(
                    f"Missing template variable {e} for prompt '{prompt_path}'. "
                    f"Available variables: {list(variables.keys())}"
                )
        
        return template
    
    async def _aload_from_file(self, prompt_path: str) -> str:
        """Load prompt content from file asynchronously."""
        full_path = self.prompts_dir / prompt_path
        
        if not full_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {full_path}\n"
                f"Looking in: {self.prompts_dir}"
            )
        
        async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        return content.strip()

    def _load_from_file(self, prompt_path: str) -> str:
        """Load prompt content from file."""
        full_path = self.prompts_dir / prompt_path
        
        if not full_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {full_path}\n"
                f"Looking in: {self.prompts_dir}"
            )
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content.strip()
    
    def reload(self, prompt_path: Optional[str] = None):
        """
        Reload prompt(s) from disk, bypassing cache.
        
        Args:
            prompt_path: Specific prompt to reload, or None to clear entire cache
        """
        if prompt_path is None:
            self._cache.clear()
        elif prompt_path in self._cache:
            del self._cache[prompt_path]
    
    def get_available_prompts(self) -> list[str]:
        """
        List all available prompt files.
        
        Returns:
            List of relative paths to prompt files
        """
        prompts = []
        for file_path in self.prompts_dir.rglob("*.txt"):
            relative_path = file_path.relative_to(self.prompts_dir)
            prompts.append(str(relative_path))
        
        return sorted(prompts)


# Global instance for easy access
_default_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """
    Get the default global prompt loader instance.
    
    Returns:
        PromptLoader instance
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptLoader()
    return _default_loader


def load_prompt(prompt_path: str, **variables) -> str:
    """
    Convenience function to load a prompt using the default loader.
    """
    loader = get_prompt_loader()
    return loader.load(prompt_path, **variables)


async def aload_prompt(prompt_path: str, **variables) -> str:
    """
    Convenience function to load a prompt using the default loader (Asynchronous).
    """
    loader = get_prompt_loader()
    return await loader.aload(prompt_path, **variables)
