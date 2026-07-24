from app.browser.runner import BrowserTestRunner


runner = BrowserTestRunner(
    headless=False,
)

result = runner.run_smoke_test(
    url="https://example.com"
)

print("\nTest result:")

for key, value in result.items():
    print(f"{key}: {value}")