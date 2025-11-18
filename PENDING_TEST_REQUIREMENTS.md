# Pending Test Requirements

The following tests or test categories are currently skipped or pending due to missing environment variables (API keys).

## Missing Keys
- `GEMINI_API_KEY`: Required for integration tests involving the LLM provider.
- `DATABASE_URL`: Required for integration tests involving the real database (though Docker is available, some tests might expect a specific env var).

## Skipped Tests
1. **Integration Tests for LLM**: Any test that calls `GoogleGeminiProvider` directly without mocking.
2. **E2E Tests**: Full flow tests that generate content using the AI agent.

## Action Items
When keys become available:
1. Add keys to `.env` file.
2. Run the full test suite including integration tests.
3. Verify that the Agent's Plan-and-Execute flow works with the real API.
