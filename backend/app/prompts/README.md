# AI Prompts Directory

This directory contains all AI prompts used throughout the ExamAI application. 

**NEW:** All prompts have been redesigned based on **scientific pedagogical principles** including Cognitive Load Theory (CLT), Generative Learning Theory, and the Testing Effect. See [PRINCIPLES.md](./PRINCIPLES.md) for the complete scientific framework.

Prompts are organized by component and stored as separate text files for easier maintenance and version control.

---

## 📚 Scientific Foundation

Our prompts are grounded in research-backed learning principles:

- **Cognitive Load Theory** (Sweller) — Chunking, signaling, minimizing extraneous load
- **Generative Learning** (Mayer) — Active recall, summarizing, self-explanation
- **Testing Effect** (Roediger) — Retrieval practice strengthens memory
- **Advance Organizers** (Ausubel) — Pre-structure activates prior knowledge
- **Socratic Method** — Guide to discovery, don't give answers

All prompts include explicit instructions implementing these principles.

---

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
- **course_plan.txt**: Generates structured learning plan with blocks, topics, and **Learning Outcomes** (Advance Organizers)
  - **NEW:** Bloom's Taxonomy progression (basic → advanced)
  - **NEW:** Learning outcomes activate prior knowledge

### Executor Prompts
- **topic_content.txt**: Generates detailed study notes for individual topics
  - **NEW:** Chain-of-Thought planning before generation
  - **NEW:** 🎯 Key Concepts section (Advance Organizers)
  - **NEW:** ❓ Self-check questions (Testing Effect)
  - **NEW:** 📝 Generative summaries (must rephrase, not copy)
  - **Scientific principles:** All 5 major pedagogical strategies

### Quiz Prompts
- **flashcards.txt**: Creates flashcards optimized for spaced repetition
  - **NEW:** Orphan Knowledge Prevention (connect facts to concepts)
  - **NEW:** Difficulty distribution (40% easy, 40% medium, 20% hard)
  - **NEW:** Open-ended questions requiring explanation
  
- **mcq_questions.txt**: Generates multiple-choice questions with learning focus
  - **NEW:** Elaborative explanations (why correct + why distractors wrong)
  - **NEW:** Misconception-based distractors
  - **NEW:** Bloom's Taxonomy levels (recall, application, analysis)

### Tutor Prompts
- **chat_system.txt**: AI tutor conversation system with adaptive teaching
  - **NEW:** 4-Mode Switch (Socratic / Direct / Practice / Tool-Assisted)
  - **NEW:** Intent detection (deep learning vs. quick answer)
  - **NEW:** Metacognitive scaffolding
  - **Scientific basis:** Socratic Method + Zone of Proximal Development

### Finalizer Prompts
- **polish_content.txt**: Polishes and formats complete study notes
  - **NEW:** Generative Summarizing (MUST rephrase, not copy)
  - **NEW:** Cornell Method glossary (key terms)
  - **NEW:** Comprehensive self-check questions (10-15)

### Analyze Prompts
- **extract_outline.txt**: Analyzes uploaded files for topic structure
  - **NEW:** Bloom's Taxonomy progression enforcement
  - **Scientific basis:** Advance Organizers

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
