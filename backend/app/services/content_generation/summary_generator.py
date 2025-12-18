from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from app.integrations.llm.base import LLMProvider
from app.prompts import load_prompt
from app.utils.content_cleaner import clean_ai_content


@dataclass(frozen=True)
class TopicGist:
    title: str
    content: str


class ExamSummaryGenerator:
    """Generates a short TL;DR summary for an exam for frontend display."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    @staticmethod
    def _extract_gist(content: str, max_chars: int = 2000) -> str:  # Increased from 1000 to provide more context
        if not content:
            return ""
        text = clean_ai_content(content, content_type="executor")
        text = " ".join(text.split())
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."

    def _format_topic_gists(self, topics: Iterable[TopicGist]) -> str:
        lines: list[str] = []
        for topic in topics:
            gist = self._extract_gist(topic.content)
            if gist:
                lines.append(f"- {topic.title}: {gist}")
            else:
                lines.append(f"- {topic.title}: (no content)")
        return "\n".join(lines)

    @staticmethod
    def _normalize_bullets(markdown: str, max_lines: int = 25) -> str:
        """Extract and normalize bullet points from markdown text."""
        if not markdown:
            return ""

        lines = []
        for raw_line in markdown.splitlines():
            line = raw_line.rstrip()
            # Skip empty lines and code fence markers
            if line.strip() and not line.strip().startswith("```"):
                lines.append(line.strip())

        bullets: list[str] = []
        for line in lines:
            if line.startswith("- "):
                bullets.append(line)
            elif line.startswith("* "):
                bullets.append("- " + line[2:].strip())

        # If no bullets found, convert all lines to bullets
        if not bullets:
            bullets = ["- " + line.lstrip("-*").strip() for line in lines if line.strip()]

        return "\n".join(bullets[:max_lines]).strip()

    async def generate_tldr(
        self,
        *,
        subject: str,
        exam_type: str,
        level: str,
        topics: Iterable[TopicGist],
        total_count: int,
        ready_count: int,
        output_language: Optional[str] = None,
        cache_name: Optional[str] = None,
    ) -> tuple[str, dict[str, Any]]:
        prompt = load_prompt(
            "summary/exam_tldr.txt",
            subject=subject,
            exam_type=exam_type,
            level=level,
            total_count=total_count,
            ready_count=ready_count,
            output_language=output_language or "ru",
            topic_gists=self._format_topic_gists(topics),
        )

        # Try with normal token limit first
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.2,
            max_tokens=2000,  # Increased from 700 to allow longer summaries
            system_prompt=(
                "You write short, accurate study TL;DRs. "
                "Never reveal hidden reasoning or meta text."
            ),
            cache_name=cache_name,
        )

        total_tokens_in = response.tokens_input
        total_tokens_out = response.tokens_output
        total_cost = response.cost_usd

        # Check if response was truncated
        finish_reason = (response.finish_reason or "").lower()
        if finish_reason in {"max_tokens", "length", "max_output_tokens"}:
            print(
                f"[SummaryGenerator] ⚠️ Summary truncated (finish_reason={finish_reason}). "
                f"Retrying with higher token limit..."
            )
            
            # Retry with doubled token limit
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=4000,  # Double the limit
                system_prompt=(
                    "You write short, accurate study TL;DRs. "
                    "Never reveal hidden reasoning or meta text."
                ),
                cache_name=cache_name,
            )
            
            # Check again
            finish_reason = (response.finish_reason or "").lower()
            if finish_reason in {"max_tokens", "length", "max_output_tokens"}:
                # Still truncated - return fallback
                print(
                    f"[SummaryGenerator] ❌ Summary still truncated after retry. "
                    f"Using fallback message."
                )
                usage = {
                    "tokens_input": total_tokens_in,
                    "tokens_output": total_tokens_out,
                    "cost_usd": total_cost,
                }
                return f"- Сгенерировано {ready_count}/{total_count} тем по предмету: {subject}", usage
            
            # Update totals if retry was used
            total_tokens_in += response.tokens_input
            total_tokens_out += response.tokens_output
            total_cost += response.cost_usd

        usage = {
            "tokens_input": total_tokens_in,
            "tokens_output": total_tokens_out,
            "cost_usd": total_cost,
        }

        cleaned = clean_ai_content(response.content, content_type="general")
        return self._normalize_bullets(cleaned), usage
