// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const { runId } = (await req.json()) as { runId: string };
  if (!runId || !runId.startsWith("train-")) {
    return NextResponse.json({ error: "Invalid runId" }, { status: 400 });
  }

  const repoRoot = path.resolve(process.cwd(), "..");
  const outputDir = path.join(repoRoot, "scripts", "analysis", "ui-runs", runId);

  try {
    await fs.stat(outputDir);
  } catch {
    return NextResponse.json({ error: "Run not found" }, { status: 404 });
  }

  const files = await fs.readdir(outputDir).catch(() => [] as string[]);

  let phaseMeta = null;
  if (files.includes("phase-meta.json")) {
    try {
      phaseMeta = JSON.parse(await fs.readFile(path.join(outputDir, "phase-meta.json"), "utf-8"));
    } catch { /* best effort */ }
  }

  let ticketCount = 0;
  const ticketsCsvPath = files.includes("tickets-categorized.csv") ? path.join(outputDir, "tickets-categorized.csv") : null;
  if (ticketsCsvPath) {
    try {
      const csv = await fs.readFile(ticketsCsvPath, "utf-8");
      ticketCount = Math.max(0, csv.split("\n").filter((l) => l.trim()).length - 1);
    } catch { /* best effort */ }
  }

  let rulesCount = 0;
  const localRulesPath = files.includes("rule-engine.local.csv") ? path.join(outputDir, "rule-engine.local.csv") : null;
  if (localRulesPath) {
    try {
      const csv = await fs.readFile(localRulesPath, "utf-8");
      rulesCount = Math.max(0, csv.split("\n").filter((l) => l.trim()).length - 1);
    } catch { /* best effort */ }
  }

  let mlReport = "";
  if (files.includes("run_training_ml.log")) {
    try {
      const text = await fs.readFile(path.join(outputDir, "run_training_ml.log"), "utf-8");
      mlReport = text.slice(0, 5000);
    } catch { /* best effort */ }
  }

  return NextResponse.json({
    runId,
    outputDir,
    phaseMeta,
    ticketCount,
    rulesCount,
    mlReport,
    artifacts: {
      ticketsCsv: ticketsCsvPath,
      localRules: localRulesPath,
      mlModel: files.includes("ml-model") ? path.join(outputDir, "ml-model") : null,
      mlLog: files.includes("run_training_ml.log") ? path.join(outputDir, "run_training_ml.log") : null,
      trainingLog: files.includes("training.log") ? path.join(outputDir, "training.log") : null,
    },
    files,
  });
}
