import asyncio
from uuid import UUID, uuid4

import httpx
import pytest
from httpx import AsyncClient

from app.dependencies import get_current_user
from app.domain.user import User
from app.main import app
from app.repositories.user_repository import UserRepository

# Mark all tests in this module as e2e
pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
class TestEndToEndFlow:

    async def test_full_exam_generation_flow(self):
        """
        Test the full flow with MOCKED Auth to avoid email bounces.
        1. Create a user directly in DB (bypassing Supabase)
        2. Override get_current_user to return this user
        3. Create an exam (triggers REAL Gemini)
        4. Poll for status until 'ready'
        5. Verify content
        """
        # Setup: Create a real user in the local DB
        unique_id = str(uuid4())[:8]
        email = f"mock_e2e_{unique_id}@example.com"

        # We need a DB session to insert the user
        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            # We can't easily get the DB session from outside without a context manager or dependency
            # So we will use a trick: We will override the dependency to return our user
            # But the user needs to exist in the DB for foreign keys to work (Exam -> User)

            # Let's create a user using the repository directly
            # We need to manually create a session
            from unittest.mock import Mock

            from app.db.session import AsyncSessionLocal
            from app.tasks.exam_tasks import _generate_exam_content_async

            user_id = uuid4()
            async with AsyncSessionLocal() as session:
                repo = UserRepository(session)
                user = User(
                    id=user_id, email=email, full_name="E2E Mock User", is_verified=True
                )
                await repo.create(user)
                await session.commit()
                print(f"\n[E2E] Created mock user in DB: {user.id}")

            # Override the Auth dependency
            async def mock_get_current_user():
                return user

            app.dependency_overrides[get_current_user] = mock_get_current_user

            try:
                print("[E2E] 1. Auth Mocked. Skipping Login.")

                # Fake token header (ignored by mock but good practice)
                headers = {"Authorization": "Bearer mock_token"}

                print("[E2E] 2. Creating Exam (Real Gemini Call)")
                # 3. Create Exam
                exam_data = {
                    "title": f"E2E Python Exam {unique_id}",
                    "subject": "Computer Science",
                    "exam_type": "written",
                    "level": "bachelor",
                    "original_content": "Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation. Python is dynamically-typed and garbage-collected. It supports multiple programming paradigms, including structured (particularly procedural), object-oriented and functional programming. It is often described as a 'batteries included' language due to its comprehensive standard library. "
                    * 2,  # Ensure > 100 chars
                }

                create_response = await client.post(
                    "/api/v1/exams/", json=exam_data, headers=headers
                )
                if create_response.status_code not in [200, 201]:
                    pytest.fail(
                        f"Exam creation failed (Status {create_response.status_code}): {create_response.text}"
                    )

                exam = create_response.json()
                exam_id = exam["id"]
                print(f"[E2E] Exam created: {exam_id}. Status: {exam['status']}")

                # 3.5 Trigger Generation (API call)
                print(f"[E2E] Triggering generation for exam {exam_id}")
                gen_response = await client.post(
                    f"/api/v1/exams/{exam_id}/generate", headers=headers
                )
                if gen_response.status_code not in [200, 202]:
                    pytest.fail(f"Generation trigger failed: {gen_response.text}")

                # 3.6 Manually execute the async task logic (since no Celery worker)
                print("[E2E] Manually executing generation task...")
                mock_task = Mock()
                mock_task.update_state = Mock()

                await _generate_exam_content_async(
                    exam_id=UUID(exam_id), user_id=user_id, task=mock_task
                )
                print("[E2E] Manual generation task completed.")

                # 4. Poll for completion
                max_retries = 30
                for i in range(max_retries):
                    await asyncio.sleep(2)  # Wait 2 seconds

                    get_response = await client.get(
                        f"/api/v1/exams/{exam_id}", headers=headers
                    )
                    current_exam = get_response.json()
                    status = current_exam["status"]
                    print(f"[E2E] Polling {i+1}/{max_retries}: Status = {status}")

                    if status == "ready":
                        print("[E2E] Exam generation complete!")
                        break
                    if status == "failed":
                        pytest.fail("Exam generation failed on server side.")
                else:
                    pytest.fail("Exam generation timed out.")

                # 5. Verify Content
                final_exam = get_response.json()
                assert final_exam["status"] == "ready"
                assert len(final_exam["topics"]) > 0
                assert final_exam["ai_summary"] is not None
                print(
                    "[E2E] Verification successful. Topics generated:",
                    len(final_exam["topics"]),
                )

            finally:
                # Cleanup
                app.dependency_overrides = {}
