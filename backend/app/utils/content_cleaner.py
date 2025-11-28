"""
Utility functions for cleaning AI-generated content.
Removes internal reasoning tags that should not be shown to users.
"""

import re


def strip_thinking_tags(content: str) -> str:
    """
    Remove <thinking>...</thinking> blocks from Executor output.
    
    Args:
        content: Raw AI-generated content
        
    Returns:
        Cleaned content without thinking tags
        
    Example:
        >>> text = "<thinking>Planning...</thinking>### Topic\\nContent"
        >>> strip_thinking_tags(text)
        '### Topic\\nContent'
    """
    if not content:
        return content
    
    # Remove thinking blocks (case-insensitive, multiline)
    cleaned = re.sub(
        r'<thinking>.*?</thinking>',
        '',
        content,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    return cleaned.strip()


def strip_analysis_tags(content: str) -> str:
    """
    Remove <analysis>...</analysis> blocks from Tutor output.
    
    Args:
        content: Raw AI-generated response
        
    Returns:
        Cleaned response without analysis tags
        
    Example:
        >>> text = "<analysis>Mode: Socratic</analysis>Great question!"
        >>> strip_analysis_tags(text)
        'Great question!'
    """
    if not content:
        return content
    
    # Remove analysis blocks (case-insensitive, multiline)
    cleaned = re.sub(
        r'<analysis>.*?</analysis>',
        '',
        content,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    return cleaned.strip()


def clean_ai_content(content: str, content_type: str = "general") -> str:
    """
    Clean AI-generated content by removing all internal reasoning tags.
    
    Args:
        content: Raw AI-generated content
        content_type: Type of content ("executor", "tutor", or "general")
        
    Returns:
        Cleaned content
    """
    if not content:
        return content
    
    # Apply appropriate cleaning based on content type
    if content_type == "executor":
        return strip_thinking_tags(content)
    elif content_type == "tutor":
        return strip_analysis_tags(content)
    else:
        # General: remove both types
        content = strip_thinking_tags(content)
        content = strip_analysis_tags(content)
        return content
