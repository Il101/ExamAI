"""E2E test with real Physics PDF file"""

from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import httpx
import pytest
from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.dependencies import get_current_user
from app.domain.user import User
from app.main import app
from app.repositories.user_repository import UserRepository
from app.tasks.exam_tasks import _generate_exam_content_async

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
class TestPhysicsPDF:

    async def test_physics_pdf_exam_generation(self):
        """
        Test exam generation from real Physics PDF file.
        This demonstrates the full workflow with actual study material.
        """
        # Read PDF file
        pdf_path = Path(
            "/Users/iliazarikov/Documents/Python Projects/ExamAI/VO Physik ges 2022.pdf"
        )

        if not pdf_path.exists():
            pytest.skip(f"PDF file not found: {pdf_path}")

        # Extract text from PDF
        print(f"\n[E2E-Physics] Reading PDF: {pdf_path.name}")

        try:
            import PyPDF2

            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)

                # Read first 10 pages for faster testing
                pages_to_read = min(10, total_pages)
                text_content = ""

                for i in range(pages_to_read):
                    page = pdf_reader.pages[i]
                    text_content += page.extract_text() + "\n"

                print(
                    f"[E2E-Physics] Extracted {len(text_content)} chars from {pages_to_read}/{total_pages} pages"
                )

        except ImportError:
            pytest.skip("PyPDF2 not installed. Install with: pip install PyPDF2")
        except Exception as e:
            pytest.fail(f"Failed to read PDF: {str(e)}")

        if len(text_content) < 200:
            pytest.fail(f"Not enough content extracted: {len(text_content)} chars")

        # Setup: Create mock user
        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            unique_id = str(uuid4())[:8]
            email = f"physics_test_{unique_id}@example.com"
            user_id = uuid4()

            async with AsyncSessionLocal() as session:
                repo = UserRepository(session)
                user = User(
                    id=user_id,
                    email=email,
                    full_name="Physics Test User",
                    is_verified=True,
                )
                await repo.create(user)
                await session.commit()
                print(f"[E2E-Physics] Created user: {user.id}")

            # Override auth
            async def mock_get_current_user():
                return user

            app.dependency_overrides[get_current_user] = mock_get_current_user

            try:
                headers = {"Authorization": "Bearer mock_token"}

                # Create exam with PDF content
                print(
                    f"[E2E-Physics] Creating exam with {len(text_content)} chars of content"
                )

                exam_data = {
                    "title": f"Physics Exam - {pdf_path.stem}",
                    "subject": "Physics",
                    "exam_type": "written",
                    "level": "bachelor",
                    "original_content": text_content[
                        :10000
                    ],  # Limit to 10k chars for speed
                }

                create_response = await client.post(
                    "/api/v1/exams/", json=exam_data, headers=headers
                )

                if create_response.status_code not in [200, 201]:
                    pytest.fail(f"Exam creation failed: {create_response.text}")

                exam = create_response.json()
                exam_id = exam["id"]
                print(f"[E2E-Physics] Exam created: {exam_id}")
                print(f"[E2E-Physics] Status: {exam['status']}")

                # Trigger generation
                gen_response = await client.post(
                    f"/api/v1/exams/{exam_id}/generate", headers=headers
                )

                if gen_response.status_code not in [200, 202]:
                    pytest.fail(f"Generation trigger failed: {gen_response.text}")

                # Execute generation task
                print("[E2E-Physics] Starting content generation...")
                print("[E2E-Physics] This will take ~2-3 minutes with Gemini 2.0...")

                mock_task = Mock()
                mock_task.update_state = Mock()

                from uuid import UUID

                await _generate_exam_content_async(
                    exam_id=UUID(exam_id), user_id=user_id, task=mock_task
                )

                print("[E2E-Physics] Generation completed!")

                # Verify results
                get_response = await client.get(
                    f"/api/v1/exams/{exam_id}", headers=headers
                )
                final_exam = get_response.json()

                print(f"\n[E2E-Physics] RESULTS:")
                print(f"  Status: {final_exam['status']}")
                print(f"  Topics generated: {len(final_exam['topics'])}")
                print(
                    f"  Token usage: {final_exam['token_count_input']} → {final_exam['token_count_output']}"
                )

                # Assertions
                assert final_exam["status"] == "ready"
                assert len(final_exam["topics"]) > 0
                assert final_exam["ai_summary"] is not None

                # Show generated topics
                print(f"\n[E2E-Physics] Generated Topics:")
                for i, topic in enumerate(final_exam["topics"], 1):
                    print(
                        f"  {i}. {topic['topic_name']} (difficulty: {topic['difficulty_level']}/5)"
                    )

                # Show preview of first topic
                if final_exam["topics"]:
                    first_topic = final_exam["topics"][0]
                    preview = (
                        first_topic["content"][:300]
                        if first_topic["content"]
                        else "No content"
                    )
                    print(f"\n[E2E-Physics] First Topic Preview:")
                    print(f"  {preview}...")

                print("\n[E2E-Physics] ✅ Test PASSED!")

            finally:
                app.dependency_overrides.clear()
