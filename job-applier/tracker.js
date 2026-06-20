// tracker.js
import fs from "fs";

const TRACKER_FILE = "./applications.json";

function load() {
  if (!fs.existsSync(TRACKER_FILE)) return [];
  return JSON.parse(fs.readFileSync(TRACKER_FILE, "utf8"));
}

function save(data) {
  fs.writeFileSync(TRACKER_FILE, JSON.stringify(data, null, 2));
}

export function logApplication(job, coverLetter, matchScore, status = "applied") {
  const apps = load();
  apps.push({
    id: Date.now(),
    date: new Date().toISOString(),
    company: job.company,
    title: job.title,
    location: job.location,
    matchScore,
    status,
    coverLetterPreview: coverLetter.substring(0, 200),
  });
  save(apps);
}

export function getApplications() {
  return load();
}

export function markStatus(id, status) {
  const apps = load();
  const app = apps.find((a) => a.id === id);
  if (app) app.status = status;
  save(apps);
}
