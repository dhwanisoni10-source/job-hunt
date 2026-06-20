// apply.js
import { scrapeJobPosting } from "./scraper.js";
import {
  analyzeJob,
  tailorResumeSummary,
  writeCoverLetter,
  shouldApply,
} from "./claude.js";
import { logApplication } from "./tracker.js";
import fs from "fs";

async function processJob(input) {
  console.log("\n🔍 Processing job...");

  // Accept URL or raw text
  let jobText;
  if (input.startsWith("http")) {
    console.log("   Scraping URL...");
    jobText = await scrapeJobPosting(input);
  } else {
    jobText = input;
  }

  // Step 1: Analyze the job
  console.log("   Analyzing with Claude...");
  const jobAnalysis = await analyzeJob(jobText);
  console.log(`   ✓ Role: ${jobAnalysis.title} at ${jobAnalysis.company}`);

  // Step 2: Should we apply?
  const recommendation = await shouldApply(jobAnalysis);
  console.log(
    `   Match score: ${recommendation.matchScore}/100 — ${recommendation.reason}`
  );

  if (!recommendation.recommend) {
    console.log("   ⚠️  Claude recommends skipping this role.");
    const proceed = process.argv.includes("--force");
    if (!proceed) {
      console.log('   (Use --force to apply anyway)\n');
      return;
    }
  }

  // Step 3: Generate content
  console.log("   Writing tailored content...");
  const [summary, coverLetter] = await Promise.all([
    tailorResumeSummary(jobAnalysis),
    writeCoverLetter(jobAnalysis),
  ]);

  // Step 4: Save outputs
  const outputDir = `./outputs/${jobAnalysis.company.replace(/\s+/g, "_")}`;
  fs.mkdirSync(outputDir, { recursive: true });

  fs.writeFileSync(`${outputDir}/cover_letter.txt`, coverLetter);
  fs.writeFileSync(`${outputDir}/resume_summary.txt`, summary);
  fs.writeFileSync(
    `${outputDir}/job_analysis.json`,
    JSON.stringify(jobAnalysis, null, 2)
  );

  console.log(`   ✓ Files saved to ${outputDir}/`);

  // Step 5: Log to tracker
  logApplication(jobAnalysis, coverLetter, recommendation.matchScore);
  console.log("   ✓ Logged to applications.json");

  console.log("\n✅ Done! Review files before submitting.\n");
  return { jobAnalysis, coverLetter, summary };
}

// Run from command line: node apply.js "https://..." or node apply.js "paste job text here"
const input = process.argv.slice(2).join(" ");
if (!input || input === "--force") {
  console.log('Usage: node apply.js "https://job-url.com"');
  console.log('   or: node apply.js "paste job description text here"');
  process.exit(1);
}

processJob(input).catch(console.error);
