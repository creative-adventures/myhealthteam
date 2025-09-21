from playwright.sync_api import sync_playwright

def take_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8502")
        page.wait_for_load_state('networkidle')
        page.screenshot(path="dashboard.png")
        browser.close()

if __name__ == "__main__":
    take_screenshot()