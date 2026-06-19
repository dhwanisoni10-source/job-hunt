"""
Base class for all platform-specific appliers.
Handles browser setup, screenshots, and shared utilities.
"""

import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from src.models import Job
from src.apply.answers import get_answer, CANDIDATE


class BaseApplier:
    SCREENSHOT_DIR = Path("screenshots")

    def __init__(self, headless: bool = False, slow_mo: int = 150):
        self.headless = headless
        self.slow_mo = slow_mo
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self.page: Page | None = None
        self.SCREENSHOT_DIR.mkdir(exist_ok=True)

    def __enter__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        self._context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        self.page = self._context.new_page()
        return self

    def __exit__(self, *_):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def screenshot(self, name: str):
        path = self.SCREENSHOT_DIR / f"{name}_{int(time.time())}.png"
        self.page.screenshot(path=str(path))
        return str(path)

    def fill_field(self, selector: str, value: str, clear_first: bool = True):
        el = self.page.locator(selector).first
        if clear_first:
            el.triple_click()
        el.type(value, delay=40)

    def select_option_containing(self, selector: str, text: str):
        """Select a <select> option whose label contains `text`."""
        el = self.page.locator(selector).first
        options = el.locator("option").all()
        for opt in options:
            if text.lower() in (opt.text_content() or "").lower():
                el.select_option(label=opt.text_content())
                return True
        return False

    def answer_question(self, label_text: str, input_selector: str,
                        job_context: str = "", resume: str = "") -> str:
        answer = get_answer(label_text, job_context, resume)
        if answer and input_selector:
            try:
                self.fill_field(input_selector, answer)
            except Exception:
                pass
        return answer

    def upload_resume(self, file_input_selector: str, resume_path: str):
        if not Path(resume_path).exists():
            print(f"  [warn] resume file not found: {resume_path}")
            return
        self.page.locator(file_input_selector).set_input_files(resume_path)

    def wait_and_click(self, selector: str, timeout: int = 10000):
        self.page.wait_for_selector(selector, timeout=timeout)
        self.page.click(selector)

    def safe_click(self, selector: str) -> bool:
        try:
            self.page.locator(selector).first.click(timeout=5000)
            return True
        except Exception:
            return False
