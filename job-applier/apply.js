// apply.js
import { scrapeJobPosting } from "./scraper.js";
import {
  analyzeJob,
  tailorResumeSummary,
  writeCoverLetter,
  shouldApply,
} from "./claude.js";
import { logApplication } from "./tracker.js";
import { fillApplication } from "./autofill.js";
import fs from "fs";

const RESUME_PATH = "./resume.pdf";

async function processJob(input) {
  const autofill = process.argv.includes("--autofill");
  const force = process.argv.includes("--force");

  console.log("\n🔍 Processing job...");

  // Accept URL or raw text
  let jobText;
  let jobUrl = null;
  if (input.startsWith("http")) {
    jobUrl = input;
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
    if (!force) {
      console.log("   (Use --force to apply anyway)\n");
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
  logApplication(jobAnalysis, coverLetter, recommendation.matchScore, "generated");
  console.log("   ✓ Logged to applications.json");

  // Step 6: Autofill (optional)
  if (autofill) {
    const applyUrl = jobUrl || jobAnalysis.applicationUrl;
    if (!applyUrl) {
      console.log("\n⚠️  --autofill requires a URL. No application URL found in job posting.");
    } else {
      const candidate = JSON.parse(fs.readFileSync("./candidate.json", "utf8"));
      console.log("\n🤖 Opening browser to fill application...");
      console.log("   Review carefully before submitting!\n");
      await fillApplication(applyUrl, {
        name: candidate.name,
        email: candidate.email,
        phone: candidate.phone,
        coverLetter,
        resumePath: fs.existsSync(RESUME_PATH) ? RESUME_PATH : null,
      });
      logApplication(jobAnalysis, coverLetter, recommendation.matchScore, "submitted");
      console.log("   ✓ Status updated to submitted in applications.json");
    }
  } else {
    console.log("\n✅ Done! Review files before submitting.");
    console.log(`   Tip: Re-run with --autofill to fill the form automatically.\n`);
  }

  return { jobAnalysis, coverLetter, summary };
}

// Parse input — strip flags from the joined string
const args = process.argv.slice(2).filter((a) => !a.startsWith("--"));
const input = args.join(" ");

if (!input) {
  console.log('Usage: node apply.js "https://job-url.com" [--autofill] [--force]');
  console.log('   or: node apply.js "paste job description text here" [--force]');
  process.exit(1);
}

processJob(input).catch(console.error);
