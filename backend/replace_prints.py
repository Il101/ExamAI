#!/usr/bin/env python3
"""Replace print statements with proper logging in quiz_generator.py"""

import re

# Read the file
with open("app/agent/quiz_generator.py", "r") as f:
    content = f.read()

# Define replacements
replacements = [
    # Info level logs
    (r'print\(f"\[QuizGenerator\] Generating \{num_cards\} flashcards\.\.\."\)',
     'logger.info("Generating flashcards", extra={"component": "quiz_generator", "num_cards": num_cards})'),
    
    (r'print\(f"\[QuizGenerator\] Generating \{num_questions\} MCQ questions\.\.\."\)',
     'logger.info("Generating MCQ questions", extra={"component": "quiz_generator", "num_questions": num_questions})'),
    
    (r'print\(f"\[QuizGenerator\] Recreating cache for exam \{exam_id\}\.\.\."\)',
     'logger.info("Recreating cache for exam", extra={"component": "quiz_generator", "exam_id": str(exam_id)})'),
    
    (r'print\(f"\[QuizGenerator\] Successfully recreated cache: \{new_cache_name\}"\)',
     'logger.info("Successfully recreated cache", extra={"component": "quiz_generator", "cache_name": new_cache_name})'),
    
    (r'print\(f"\[QuizGenerator\] Generated \{len\(flashcards\)\} flashcards"\)',
     'logger.info("Generated flashcards", extra={"component": "quiz_generator", "count": len(flashcards)})'),
    
    (r'print\(f"\[QuizGenerator\] Generated \{len\(questions\)\} MCQ questions"\)',
     'logger.info("Generated MCQ questions", extra={"component": "quiz_generator", "count": len(questions)})'),
    
    # Warning level logs
    (r'print\(f"\[QuizGenerator\] Cache expired, attempting to recreate\.\.\."\)',
     'logger.warning("Cache expired, attempting to recreate", extra={"component": "quiz_generator"})'),
    
    (r'print\(f"\[QuizGenerator\] Falling back to full content"\)',
     'logger.warning("Falling back to full content", extra={"component": "quiz_generator"})'),
    
    (r'print\(f"\[QuizGenerator\] No exam_id, falling back to full content"\)',
     'logger.warning("No exam_id provided, falling back to full content", extra={"component": "quiz_generator"})'),
    
    # Error level logs
    (r'print\(f"\[QuizGenerator\] Failed to recreate cache: \{recreate_error\}"\)',
     'logger.error("Failed to recreate cache", extra={"component": "quiz_generator", "error": str(recreate_error)})'),
    
    (r'print\(f"\[QuizGenerator\] Error parsing flashcards: \{e\}"\)',
     'logger.error("Error parsing flashcards", extra={"component": "quiz_generator", "error": str(e)})'),
    
    (r'print\(f"\[QuizGenerator\] Error parsing MCQ questions: \{e\}"\)',
     'logger.error("Error parsing MCQ questions", extra={"component": "quiz_generator", "error": str(e)})'),
    
    # Debug level logs
    (r'print\(f"\[QuizGenerator\] Raw text \(first 500 chars\): \{json_text\[:500\]\}"\)',
     'logger.debug("Raw text preview", extra={"component": "quiz_generator", "preview": json_text[:500]})'),
]

# Apply replacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Write back
with open("app/agent/quiz_generator.py", "w") as f:
    f.write(content)

print("✅ Replaced all print statements with logging")
