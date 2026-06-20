// claude.js
import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";

const client = new Anthropic();
const profile = JSON.parse(fs.readFileSync("./candidate.json", "utf8"));

export async function analyzeJob(jobText) {
  const response = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 1000,
    messages: [
      {
        role: "user",
        content: `Extract the following from this job posting as JSON only. No markdown, no explanation.

Return this exact shape:
{
  "title": "",
  "company": "",
  "location": "",
  "keyRequirements": [],
  "preferredSkills": [],
  "applicationUrl": "",
  "isRemote": false,
  "requiresLicense": false,
  "notes": ""
}

Job posting:
${jobText}`,
      },
    ],
  });

  return JSON.parse(response.content[0].text);
}

export async function tailorResumeSummary(jobAnalysis) {
  const response = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 500,
    messages: [
      {
        role: "user",
        content: `Write a 3-sentence professional summary for a resume targeting this role.

Rules:
- First person, no "I" at the start
- Natural, human tone — no em dashes
- Highlight the most relevant match between the candidate profile and job requirements
- Do not fabricate credentials or experience

Candidate profile: ${JSON.stringify(profile)}
Job: ${JSON.stringify(jobAnalysis)}

Return only the summary paragraph, nothing else.`,
      },
    ],
  });

  return response.content[0].text.trim();
}

export async function writeCoverLetter(jobAnalysis) {
  const response = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 800,
    messages: [
      {
        role: "user",
        content: `Write a professional cover letter for this job application.

Rules:
- 3 paragraphs max
- Natural, conversational but professional tone
- No em dashes
- No generic filler phrases ("I am excited to apply...")
- Lead with a specific clinical skill or accomplishment that matches the role
- Close with a clear call to action

Candidate: ${JSON.stringify(profile)}
Job: ${JSON.stringify(jobAnalysis)}

Return only the letter body (no date, no address block), starting with "Dear Hiring Manager,"`,
      },
    ],
  });

  return response.content[0].text.trim();
}

export async function shouldApply(jobAnalysis) {
  const response = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 200,
    messages: [
      {
        role: "user",
        content: `Given this candidate profile and job posting, should the candidate apply?

Return JSON only:
{
  "recommend": true or false,
  "matchScore": 0-100,
  "reason": "one sentence"
}

Profile: ${JSON.stringify(profile)}
Job: ${JSON.stringify(jobAnalysis)}`,
      },
    ],
  });

  return JSON.parse(response.content[0].text);
}
