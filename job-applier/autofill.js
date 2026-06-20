// autofill.js
import { chromium } from "playwright";

export async function fillApplication(url, { name, email, phone, coverLetter, resumePath }) {
  const browser = await chromium.launch({ headless: false }); // set true for silent
  const page = await browser.newPage();
  await page.goto(url);

  // Generic field mapping — customize per site
  const fieldMap = {
    'input[name*="name"], input[placeholder*="name" i]': name,
    'input[name*="email"], input[type="email"]': email,
    'input[name*="phone"], input[type="tel"]': phone,
    'textarea[name*="cover"], textarea[placeholder*="cover" i]': coverLetter,
  };

  for (const [selector, value] of Object.entries(fieldMap)) {
    try {
      await page.fill(selector, value);
    } catch {
      // Field not found, skip
    }
  }

  // Upload resume if field exists
  try {
    const fileInput = await page.$('input[type="file"]');
    if (fileInput && resumePath) await fileInput.setInputFiles(resumePath);
  } catch {}

  // PAUSE before submitting — review first!
  console.log("⚠️  Review the form before submitting. Press Enter to submit or Ctrl+C to cancel.");
  await new Promise((r) => process.stdin.once("data", r));

  // await page.click('button[type="submit"]'); // Uncomment when ready
  await browser.close();
}
