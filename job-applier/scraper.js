// scraper.js
import axios from "axios";
import * as cheerio from "cheerio";

export async function scrapeJobPosting(url) {
  const { data } = await axios.get(url, {
    headers: {
      "User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    },
  });

  const $ = cheerio.load(data);

  // Remove noise
  $("script, style, nav, footer, header, .cookie-banner").remove();

  // Try common job content selectors first
  const selectors = [
    ".job-description",
    "#job-description",
    '[data-testid="jobDescriptionText"]', // Indeed
    ".description__text", // LinkedIn
    ".jobsearch-jobDescriptionText", // Indeed alt
    "main",
    "article",
    "body",
  ];

  for (const selector of selectors) {
    const text = $(selector).text().trim();
    if (text.length > 300) {
      return text.replace(/\s+/g, " ").substring(0, 8000);
    }
  }

  return $("body").text().replace(/\s+/g, " ").substring(0, 8000);
}
