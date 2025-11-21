from playwright.sync_api import sync_playwright
import time

def verify_frontend():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Set local storage
        context.add_init_script("""
            localStorage.setItem('access_token', 'fake_token');
            localStorage.setItem('refresh_token', 'fake_refresh');
        """)

        page = context.new_page()

        # Mock API responses

        # CORRECT ENDPOINT: /auth/me
        page.route("**/api/v1/auth/me", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"id": "123", "email": "test@example.com", "full_name": "Test User", "role": "user", "is_verified": true}'
        ))

        # Also mock /users/me just in case
        page.route("**/api/v1/users/me", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"id": "123", "email": "test@example.com", "full_name": "Test User", "role": "user", "is_verified": true}'
        ))

        page.route("**/api/v1/exams", lambda route: route.fulfill(status=200, body='[]', content_type="application/json"))
        page.route("**/api/v1/analytics/stats", lambda route: route.fulfill(status=200, body='{"total_cards_learned": 100, "total_minutes_studied": 500, "current_streak": 5, "daily_progress": [], "retention_curve": [], "activity_heatmap": []}', content_type="application/json"))
        page.route("**/api/v1/subscriptions/plans", lambda route: route.fulfill(status=200, body='[]', content_type="application/json"))
        page.route("**/api/v1/subscriptions/current", lambda route: route.fulfill(status=200, body='{"plan_type": "free", "status": "active"}', content_type="application/json"))

        try:
            # Navigate to Settings
            print("Navigating to Settings...")
            page.goto("http://localhost:3000/settings")

            # Wait for h1
            page.wait_for_selector("h1:has-text('Settings')")
            page.screenshot(path="/home/jules/verification/settings.png")
            print("Settings screenshot captured.")

            # Navigate to Analytics
            print("Navigating to Analytics...")
            page.goto("http://localhost:3000/analytics")
            page.wait_for_selector("h1:has-text('Analytics')")

            # Tabs
            print("Clicking Retention tab...")
            retention_tab = page.get_by_role("tab", name="Retention")
            retention_tab.click()
            page.wait_for_selector(".recharts-responsive-container", timeout=5000)
            time.sleep(1)
            page.screenshot(path="/home/jules/verification/analytics_retention.png")

            print("Clicking Activity tab...")
            activity_tab = page.get_by_role("tab", name="Activity")
            activity_tab.click()
            time.sleep(1)
            page.screenshot(path="/home/jules/verification/analytics_activity.png")

            print("Verification Successful!")

        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/error_state.png")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    verify_frontend()
