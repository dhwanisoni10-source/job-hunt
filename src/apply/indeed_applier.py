"""
Indeed Apply automation.

Handles Indeed's "Apply Now" flow including:
  - Contact info
  - Resume upload (from file or paste)
  - Screening questions
  - Employer questions
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

COOKIES_FILE = Path(".indeed_cookies.json")
INDEED_LOGIN = "https://secure.indeed.com/account/login"


class IndeedApplier(BaseApplier):

    def login(self, email: str, password: str) -> bool:
        if COOKIES_FILE.exists():
            cookies = json.loads(COOKIES_FILE.read_text())
            self._context.add_cookies(cookies)
            self.page.goto("https://www.indeed.com")
            time.sleep(2)
            if self.page.locator('a[href*="account"]').count() > 0:
                print("  [indeed] logged in via saved cookies")
                return True

        self.page.goto(INDEED_LOGIN)
        time.sleep(1)

        # Email step
        email_input = self.page.locator('input[type="email"], input[name="__email"]').first
        email_input.fill(email)
        self.page.locator('button[type="submit"]').first.click()
        time.sleep(2)

        # Password step
        pw_input = self.page.locator('input[type="password"]').first
        if pw_input.is_visible(timeout=5000):
            pw_input.fill(password)
            self.page.locator('button[type="submit"]').first.click()
            time.sleep(3)

        if "captcha" in self.page.url.lower() or "challenge" in self.page.url.lower():
            print("  [indeed] CAPTCHA detected — solve it manually, then press Enter")
            input()

        cookies = self._context.cookies()
        COOKIES_FILE.write_text(json.dumps(cookies))
        print("  [indeed] logged in and cookies saved")
        return True

    def apply(self, job: Job, resume_path: str, cover_letter: str = "",
              master_resume: str = "") -> str:
        """
        Apply to an Indeed job.
        Returns: 'applied' | 'skipped' | 'error'
        """
        if not job.url:
            return "skipped"

        print(f"  [indeed] Opening: {job.title} @ {job.company}")
        self.page.goto(job.url, wait_until="domcontentloaded")
        time.sleep(2)

        # Look for Apply Now button
        apply_btn = self.page.locator(
            'button:has-text("Apply now"), a:has-text("Apply now"), #indeedApplyButton'
        ).first
        if not apply_btn.is_visible(timeout=5000):
            print("  [indeed] No Apply button found — skipping")
            return "skipped"

        apply_btn.click()
        time.sleep(2)

        # Indeed sometimes opens a new tab for apply
        pages = self._context.pages
        if len(pages) > 1:
            self.page = pages[-1]
            time.sleep(2)

        self.screenshot(f"indeed_start_{job.company}")

        max_steps = 12
        for step in range(max_steps):
            time.sleep(1.5)

            # Check success
            success_indicators = [
                'h1:has-text("application was sent")',
                'h1:has-text("You applied")',
                ':has-text("application submitted")',
            ]
            for indicator in success_indicators:
                if self.page.locator(indicator).count() > 0:
                    self.screenshot(f"indeed_done_{job.company}")
                    print(f"  [indeed] ✓ Applied to {job.title} @ {job.company}")
                    return "applied"

            # Upload resume if prompted
            file_input = self.page.locator('input[type="file"]').first
            if file_input.count() > 0 and Path(resume_path).exists():
                try:
                    file_input.set_input_files(resume_path)
                    time.sleep(1)
                except Exception:
                    pass

            # Fill visible fields
            self._fill_form_fields(job, cover_letter, master_resume)

            # Try to advance
            if not self._advance():
                self.screenshot(f"indeed_stuck_{job.company}_step{step}")
                print(f"  [indeed] stuck at step {step}")
                return "error"

        return "error"

    def _fill_form_fields(self, job: Job, cover_letter: str, resume_text: str):
        ctx = f"{job.title} at {job.company}"

        # Text inputs and textareas
        for inp in self.page.locator('input[type="text"], input[type="tel"], input[type="number"], textarea').all():
            try:
                if not inp.is_visible() or not inp.is_editable():
                    continue
                val = inp.input_value()
                if val and val.strip():
                    continue
                label = self._label_for(inp)
                if not label:
                    continue
                if "cover" in label.lower():
                    inp.fill(cover_letter[:3000] if cover_letter else "")
                    continue
                answer = get_answer(label, ctx, resume_text)
                if answer:
                    inp.triple_click()
                    inp.type(answer, delay=30)
            except Exception:
                pass

        # Selects
        for sel in self.page.locator("select").all():
            try:
                if not sel.is_visible():
                    continue
                label = self._label_for(sel)
                answer = get_answer(label or "", ctx, resume_text)
                if not answer:
                    continue
                options = sel.locator("option").all()
                for opt in options:
                    t = opt.text_content() or ""
                    if answer.lower() in t.lower() and t.strip() not in ("", "-- Select --", "Select"):
                        sel.select_option(label=t)
                        break
            except Exception:
                pass

        # Radio groups
        for fieldset in self.page.locator("fieldset").all():
            try:
                if not fieldset.is_visible():
                    continue
                legend = fieldset.locator("legend").first.text_content() or ""
                answer = get_answer(legend, ctx, resume_text)
                if not answer:
                    continue
                for radio in fieldset.locator('input[type="radio"]').all():
                    lbl = self._label_for(radio)
                    if lbl and answer.lower() in lbl.lower():
                        radio.check()
                        break
            except Exception:
                pass

    def _label_for(self, element) -> str:
        try:
            eid = element.get_attribute("id")
            if eid:
                lbl = self.page.locator(f'label[for="{eid}"]').first
                if lbl.count() > 0:
                    return lbl.text_content() or ""
            return element.evaluate(
                "el => { const l = el.closest('label') || "
                "el.closest('[class*=\"formGroup\"]')?.querySelector('label') || "
                "el.closest('[class*=\"field\"]')?.querySelector('label'); "
                "return l ? l.innerText : ''; }"
            )
        except Exception:
            return ""

    def _advance(self) -> bool:
        for text in ["Submit", "Continue", "Next", "Apply"]:
            btn = self.page.locator(f'button:has-text("{text}")').last
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                time.sleep(1.5)
                return True
        return False
