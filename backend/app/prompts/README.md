# AI Prompts Directory

This directory contains all AI prompts used throughout the ExamAI application. Prompts are organized by component and stored as separate text files for easier maintenance and version control.

## Directory Structure

```
prompts/
├── __init__.py          # Exports PromptLoader utilities
├── loader.py            # PromptLoader implementation
├── planner/            # Course planning prompts
│   └── course_plan.txt
├── executor/           # Content generation prompts
│   └── topic_content.txt
├── quiz/              # Quiz and flashcard prompts
│   ├── flashcards.txt
│   └── mcq_questions.txt
├── tutor/             # AI tutor prompts
│   └── chat_system.txt
├── finalizer/         # Content finalization prompts
│   └── polish_content.txt
└── analyze/           # Content analysis prompts
    └── extract_outline.txt
```

## Usage

### Loading Prompts

Use the `load_prompt()` function to load prompts with template variable substitution:

```python
from app.prompts import load_prompt

# Simple usage
prompt = load_prompt('planner/course_plan.txt', content_context="...")

# With multiple variables
prompt = load_prompt(
    'executor/topic_content.txt',
    level='University',
    exam_type='Final Exam',
    title='Introduction to Python',
    description='Basic concepts',
    estimated_paragraphs=5,
    previous_context='',
    content_section='...'
)
```

### Template Variables

Prompts support Python string formatting with named placeholders using `{variable_name}` syntax.

Example prompt file:
```
Create {num_cards} flashcards from the following content:

{content}

Focus on key concepts.
```

Usage:
```python
prompt = load_prompt('quiz/flashcards.txt', num_cards=10, content='...')
```

### Caching

The `PromptLoader` automatically caches loaded prompts to improve performance. Caching can be disabled by setting the environment variable:

```bash
export PROMPT_CACHE_ENABLED=false
```

To reload a specific prompt during development:
```python
from app.prompts import get_prompt_loader

loader = get_prompt_loader()
loader.reload('planner/course_plan.txt')  # Reload specific prompt
loader.reload()  # Clear entire cache
```

## Prompt Components

### Planner Prompts
- **course_plan.txt**: Generates structured learning plan with blocks and topics

### Executor Prompts
- **topic_content.txt**: Generates detailed study notes for individual topics

### Quiz Prompts
- **flashcards.txt**: Creates flashcards from content
- **mcq_questions.txt**: Generates multiple-choice questions

### Tutor Prompts
- **chat_system.txt**: AI tutor conversation system prompt

### Finalizer Prompts
- **polish_content.txt**: Polishes and formats complete study notes

### Analyze Prompts
- **extract_outline.txt**: Analyzes uploaded files for topic structure

## Best Practices

1. **Keep prompts focused**: Each file should serve a single, clear purpose
2. **Use descriptive variables**: Make template variable names self-documenting
3. **Document requirements**: Include clear instructions within prompts
4. **Version control**: Track changes to prompts like code
5. **Test changes**: Always verify prompt changes don't break functionality

## Modifying Prompts

When modifying prompts:

1. Edit the `.txt` file directly
2. Keep variable names consistent with existing code
3. Test with representative inputs
4. Document significant changes in version control

Note: In development, changes to prompt files are automatically picked up if caching is disabled or after calling `reload()`.
