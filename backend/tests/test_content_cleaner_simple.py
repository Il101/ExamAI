"""
Simple standalone test for content_cleaner (no app dependencies).
Run with: python3 backend/tests/test_content_cleaner_simple.py
"""

import re
import sys


def strip_thinking_tags(content: str) -> str:
    """Remove <thinking>...</thinking> blocks"""
    if not content:
        return content
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


def strip_analysis_tags(content: str) -> str:
    """Remove <analysis>...</analysis> blocks"""
    if not content:
        return content
    cleaned = re.sub(r'<analysis>.*?</analysis>', '', content, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


def test_strip_thinking():
    """Test thinking tag removal"""
    content = "<thinking>Planning...</thinking>### Topic\nContent"
    result = strip_thinking_tags(content)
    assert "<thinking>" not in result
    assert "### Topic" in result
    print("✅ test_strip_thinking passed")


def test_strip_analysis():
    """Test analysis tag removal"""
    content = "<analysis>Mode: Socratic</analysis>Great question!"
    result = strip_analysis_tags(content)
    assert "<analysis>" not in result
    assert "Great question!" in result
    print("✅ test_strip_analysis passed")


def test_multiline():
    """Test multiline tag removal"""
    content = """<thinking>
Step 1: Plan
Step 2: Execute
</thinking>
### Actual Content"""
    result = strip_thinking_tags(content)
    assert "Step 1" not in result
    assert "### Actual Content" in result
    print("✅ test_multiline passed")


def test_multiple_blocks():
    """Test multiple tag blocks"""
    content = "<thinking>First</thinking>Content<thinking>Second</thinking>More"
    result = strip_thinking_tags(content)
    assert "First" not in result
    assert "Second" not in result
    assert "Content" in result
    print("✅ test_multiple_blocks passed")


def test_case_insensitive():
    """Test case insensitivity"""
    content = "<THINKING>Test</THINKING>Content"
    result = strip_thinking_tags(content)
    assert "THINKING" not in result
    assert "Content" in result
    print("✅ test_case_insensitive passed")


def test_no_tags():
    """Test content without tags"""
    content = "### Topic\nRegular content"
    result = strip_thinking_tags(content)
    assert result == content
    print("✅ test_no_tags passed")


def test_both_tags():
    """Test removing both tag types"""
    content = "<thinking>Think</thinking>Content<analysis>Analyze</analysis>More"
    result = strip_thinking_tags(strip_analysis_tags(content))
    assert "Think" not in result
    assert "Analyze" not in result
    assert "Content" in result
    assert "More" in result
    print("✅ test_both_tags passed")


if __name__ == "__main__":
    try:
        test_strip_thinking()
        test_strip_analysis()
        test_multiline()
        test_multiple_blocks()
        test_case_insensitive()
        test_no_tags()
        test_both_tags()
        
        print("\n🎉 All tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
