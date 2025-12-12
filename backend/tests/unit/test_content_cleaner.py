"""
Unit tests for content_cleaner utility.
Tests tag stripping functionality for AI-generated content.
"""

import pytest
from app.utils.content_cleaner import (
    strip_thinking_tags,
    strip_analysis_tags,
    clean_ai_content
)


class TestStripThinkingTags:
    """Test <thinking> tag removal"""
    
    def test_removes_thinking_tags(self):
        """Should remove thinking blocks"""
        content = "<thinking>Planning the response...</thinking>### Topic\nContent here"
        result = strip_thinking_tags(content)
        assert "<thinking>" not in result
        assert "</thinking>" not in result
        assert "### Topic" in result
        assert "Content here" in result
    
    def test_removes_multiline_thinking(self):
        """Should remove multiline thinking blocks"""
        content = """<thinking>
Step 1: Identify concepts
Step 2: Design questions
</thinking>
### Actual Content"""
        result = strip_thinking_tags(content)
        assert "Step 1" not in result
        assert "### Actual Content" in result
    
    def test_case_insensitive(self):
        """Should handle different cases"""
        content = "<THINKING>Test</THINKING>Content"
        result = strip_thinking_tags(content)
        assert "THINKING" not in result
        assert "Content" in result
    
    def test_multiple_blocks(self):
        """Should remove multiple thinking blocks"""
        content = "<thinking>First</thinking>Content<thinking>Second</thinking>More"
        result = strip_thinking_tags(content)
        assert "First" not in result
        assert "Second" not in result
        assert "Content" in result
        assert "More" in result
    
    def test_empty_content(self):
        """Should handle empty content"""
        assert strip_thinking_tags("") == ""
        assert strip_thinking_tags(None) is None
    
    def test_no_tags(self):
        """Should return content unchanged if no tags"""
        content = "### Topic\nRegular content"
        result = strip_thinking_tags(content)
        assert result == content


class TestStripAnalysisTags:
    """Test <analysis> tag removal"""
    
    def test_removes_analysis_tags(self):
        """Should remove analysis blocks"""
        content = "<analysis>Mode: Socratic</analysis>Great question!"
        result = strip_analysis_tags(content)
        assert "<analysis>" not in result
        assert "Mode: Socratic" not in result
        assert "Great question!" in result
    
    def test_removes_multiline_analysis(self):
        """Should remove multiline analysis blocks"""
        content = """<analysis>
Intent: Curiosity
Mode: 1 (Socratic)
Grounding: Yes
</analysis>
Let me ask you this..."""
        result = strip_analysis_tags(content)
        assert "Intent" not in result
        assert "Let me ask you this" in result
    
    def test_case_insensitive(self):
        """Should handle different cases"""
        content = "<ANALYSIS>Test</ANALYSIS>Response"
        result = strip_analysis_tags(content)
        assert "ANALYSIS" not in result
        assert "Response" in result
    
    def test_empty_content(self):
        """Should handle empty content"""
        assert strip_analysis_tags("") == ""
        assert strip_analysis_tags(None) is None


class TestCleanAIContent:
    """Test general AI content cleaning"""
    
    def test_executor_type(self):
        """Should clean executor content (thinking tags)"""
        content = "<thinking>Plan</thinking>Content"
        result = clean_ai_content(content, "executor")
        assert "Plan" not in result
        assert "Content" in result
    
    def test_tutor_type(self):
        """Should clean tutor content (analysis tags)"""
        content = "<analysis>Mode: 1</analysis>Response"
        result = clean_ai_content(content, "tutor")
        assert "Mode: 1" not in result
        assert "Response" in result
    
    def test_general_type(self):
        """Should clean both tag types for general content"""
        content = "<thinking>Think</thinking>Content<analysis>Analyze</analysis>More"
        result = clean_ai_content(content, "general")
        assert "Think" not in result
        assert "Analyze" not in result
        assert "Content" in result
        assert "More" in result
    
    def test_mixed_tags(self):
        """Should handle mixed tag types"""
        content = """<thinking>Planning...</thinking>
### Topic
<analysis>Mode selection</analysis>
Content here"""
        result = clean_ai_content(content)
        assert "Planning" not in result
        assert "Mode selection" not in result
        assert "### Topic" in result
        assert "Content here" in result


class TestEdgeCases:
    """Test edge cases and malformed input"""
    
    def test_nested_tags(self):
        """Should handle nested tags (though shouldn't happen)"""
        content = "<thinking>Outer<thinking>Inner</thinking>Outer</thinking>Content"
        result = strip_thinking_tags(content)
        # Regex will match first opening to first closing
        assert "Content" in result
    
    def test_unclosed_tags(self):
        """Should handle unclosed tags gracefully"""
        content = "<thinking>Unclosed tag\n### Topic\nContent"
        result = strip_thinking_tags(content)
        assert "Unclosed tag" not in result
        assert "### Topic" in result
        assert "Content" in result
    
    def test_tags_in_code_blocks(self):
        """Should remove tags even if they look like code"""
        content = """<thinking>Plan</thinking>
```python
# This is code
x = 5
```"""
        result = strip_thinking_tags(content)
        assert "Plan" not in result
        assert "```python" in result
        assert "x = 5" in result
    
    def test_whitespace_preservation(self):
        """Should preserve important whitespace"""
        content = "<thinking>Remove</thinking>\n\n### Header\n\nParagraph"
        result = strip_thinking_tags(content)
        assert "### Header" in result
        assert "Paragraph" in result
        # Should be trimmed
        assert not result.startswith("\n")

    def test_plain_preamble_before_heading(self):
        """Should drop plain-text planning before first markdown heading."""
        content = (
            "thinking\nHere is my plan...\n"
            "- item 1\n- item 2\n"
            "### Заголовок\nТекст"
        )
        result = strip_thinking_tags(content)
        assert result.startswith("### Заголовок")
        assert "Here is my plan" not in result
        assert "- item 1" not in result
        assert "Текст" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
