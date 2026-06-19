"""
LinkedIn Easy Apply automation.

Logs in once and saves session cookies so subsequent runs don't need credentials.
Handles multi-step Easy Apply modals including:
  - Contact info pre-fill
  - Resume upload
  - Screening questions (yes/no, dropdown, text)
  - Voluntary disclosures (EEO)
  - Review & submit
"""

import os
import json
import time
from pathlib import Path
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from src.models import Job
from src.apply.base_applier import BaseApplier
from src.apply.answers import get_answer, CANDIDATE

COOKIES_FILE = Path(".linkedin_cookies.json")
LOGIN_URL = "https://www.linkedin.com/login"
JOBS_URL = "https://www.linkedin.com/jobs/view/{job_id}"


class LinkedInApplier(BaseApplier):

    def login(self, email: str, password: str) -> bool:
        """Log in and save session cookies for reuse."""
        if COOKIES_FILE.exists():
            cookies = json.loads(COOKIES_FILE.read_text())
            self._context.add_cookies(cookies)
            self.page.goto("https://www.linkedin.com/feed/")
            time.sleep(2)
            if "feed" in self.page.url:
                print("  [linkedin] logged in via saved cookies")
                return True

        self.page.goto(LOGIN_URL)
        self.page.fill("#username", email)
        self.page.fill("#password", password)
        self.page.click('[data-litms-control-urn="login-submit"]')
        time.sleep(3)

        if "checkpoint" in self.page.url or "challenge" in self.page.url:
            print("  [linkedin] 2FA or CAPTCHA required — solve it manually, then press Enter")
            input()

        if "feed" in self.page.url or "jobs" in self.page.url:
            cookies = self._context.cookies()
            COOKIES_FILE.write_text(json.dumps(cookies))
            print("  [linkedin] logged in and cookies saved")
            return True

        print("  [linkedin] login failed")
        return False

    def easy_apply(self, job: Job, resume_path: str, cover_letter: str = "",
                   master_resume: str = "") -> str:
        """
        Apply to a LinkedIn job via Easy Apply.
        Returns: 'applied' | 'skipped' | 'error'
        """
        job_url = job.url
        if not job_url:
            return "skipped"

        print(f"  [linkedin] Opening: {job.title} @ {job.company}")
        self.page.goto(job_url, wait_until="domcontentloaded")
        time.sleep(2)

        # Check if Easy Apply button exists
        easy_apply_btn = self.page.locator(
            'button:has-text("Easy Apply"), .jobs-apply-button'
        ).first
        if not easy_apply_btn.is_visible(timeout=5000):
            print("  [linkedin] No Easy Apply button — skipping")
            return "skipped"

        easy_apply_btn.click()
        time.sleep(1)
        self.screenshot(f"li_start_{job.company}")

        max_steps = 10
        for step in range(max_steps):
            time.sleep(1)

            # Check if we're done (submitted)
            if self.page.locator('h2:has-text("application was sent")').count() > 0:
                self.screenshot(f"li_done_{job.company}")
                print(f"  [linkedin] ✓ Applied to {job.title} @ {job.company}")
                return "applied"

            # Handle resume upload
            resume_section = self.page.locator('label:has-text("Resume"), input[type="file"]')
            if resume_section.count() > 0 and Path(resume_path).exists():
                try:
                    file_input = self.page.locator('input[type="file"]').first
                    file_input.set_input_files(resume_path)
                    time.sleep(1)
                except Exception:
                    pass

            # Fill in visible text/select fields
            self._fill_form_fields(job, cover_letter, master_resume)

            # Advance: click Next / Review / Submit
            if not self._advance_modal():
                self.screenshot(f"li_stuck_{job.company}_step{step}")
                print(f"  [linkedin] stuck on step {step} — manual review needed")
                return "error"

        return "error"

    def _fill_form_fields(self, job: Job, cover_letter: str, resume_text: str):
        """Fill all visible form fields on the current modal step."""
        # Text inputs
        inputs = self.page.locator(
            'input[type="text"], input[type="tel"], input[type="number"], textarea'
        ).all()
        for inp in inputs:
            try:
                if not inp.is_visible() or not inp.is_editable():
                    continue
                current_val = inp.input_value()
                if current_val and current_val.strip():
                    continue  # already filled

                # Find associated label
                label_text = self._get_label_for(inp)
                if not label_text:
                    continue

                # Cover letter field
                if "cover letter" in label_text.lower():
                    inp.fill(cover_letter[:2000] if cover_letter else "")
                    continue

                answer = get_answer(label_text, f"{job.title} at {job.company}", resume_text)
                if answer:
                    inp.triple_click()
                    inp.type(answer, delay=30)
                    time.sleep(0.2)
            except Exception:
                pass

        # Dropdowns / selects
        selects = self.page.locator("select").all()
        for sel in selects:
            try:
                if not sel.is_visible():
                    continue
                label_text = self._get_label_for(sel)
                answer = get_answer(label_text or "", f"{job.title} at {job.company}", resume_text)
                if answer:
                    options = sel.locator("option").all()
                    for opt in options:
                        opt_text = opt.text_content() or ""
                        if answer.lower() in opt_text.lower() and opt_text.strip() not in ("", "Select an option"):
                            sel.select_option(label=opt_text)
                            break
            except Exception:
                pass

        # Radio buttons (yes/no)
        radio_groups = self.page.locator('fieldset').all()
        for group in radio_groups:
            try:
                if not group.is_visible():
                    continue
                legend = group.locator("legend").first.text_content() or ""
                answer = get_answer(legend, f"{job.title} at {job.company}", resume_text)
                if answer:
                    # Try clicking the radio matching the answer
                    radios = group.locator('input[type="radio"]').all()
                    for radio in radios:
                        lbl = self._get_label_for(radio)
                        if lbl and answer.lower() in lbl.lower():
                            radio.check()
                            break
            except Exception:
                pass

    def _get_label_for(self, element) -> str:
        """Get the label text associated with a form element."""
        try:
            element_id = element.get_attribute("id")
            if element_id:
                label = self.page.locator(f'label[for="{element_id}"]').first
                if label.count() > 0:
                    return label.text_content() or ""
            # Walk up to find label
            return element.evaluate(
                """el => {
                    const label = el.closest('label') ||
                                  el.closest('.fb-form-element')?.querySelector('label') ||
                                  el.closest('.jobs-easy-apply-form-element')?.querySelector('label');
                    return label ? label.innerText : '';
                }"""
            )
        except Exception:
            return ""

    def _advance_modal(self) -> bool:
        """Click Next, Review, or Submit. Returns False if none found."""
        for btn_text in ["Submit application", "Review your application", "Review", "Next"]:
            btn = self.page.locator(f'button:has-text("{btn_text}")').last
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                time.sleep(1.5)
                return True

        # Try generic primary button
        primary = self.page.locator('button[aria-label*="Submit"], button.artdeco-button--primary').last
        if primary.count() > 0 and primary.is_visible():
            primary.click()
            time.sleep(1.5)
            return True

        return False
