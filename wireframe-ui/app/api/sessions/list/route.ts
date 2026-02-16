// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

type SessionInfo = {
  runId: string;
  createdAt: string;
  status: "completed" | "paused" | "failed" | "in-progress";
  phase: number;
  ticketCount: number;
  rulesCount: number;
  outputDir: string;
};

export async function GET() {
  const repoRoot = path.resolve(process.cwd(), "..");
  const uiRunsDir = path.join(repoRoot, "scripts", "analysis", "ui-runs");

  let entries: string[];
  try {
    entries = await fs.readdir(uiRunsDir);
  } catch {
    return NextResponse.json({ sessions: [] });
  }

  const trainDirs = entries.filter((e) => e.startsWith("train-")).sort().reverse();

  const sessions: SessionInfo[] = [];
  for (const dir of trainDirs) {
    const fullDir = path.join(uiRunsDir, dir);
    const stat = await fs.stat(fullDir).catch(() => null);
    if (!stat?.isDirectory()) continue;

    const files = await fs.readdir(fullDir).catch(() => [] as string[]);
    const hasMeta = files.includes("phase-meta.json");
    const hasTicketsCsv = files.includes("tickets-categorized.csv");
    const hasMlModel = files.includes("ml-model");
    const hasMlLog = files.includes("run_training_ml.log");

    let phase = 1;
    if (hasMeta) {
      try {
        const meta = JSON.parse(await fs.readFile(path.join(fullDir, "phase-meta.json"), "utf-8"));
        phase = meta.lastCompletedPhase || (hasMlLog ? 3 : hasMlModel ? 2 : 1);
      } catch {
        phase = hasMlLog ? 3 : hasMlModel ? 2 : 1;
      }
    }

    let status: SessionInfo["status"] = "in-progress";
    if (hasMlLog && hasTicketsCsv) {
      status = "completed";
    } else if (hasMeta && hasTicketsCsv) {
      status = "paused";
    } else if (!hasTicketsCsv && files.length <= 1) {
      status = "failed";
    }

    let ticketCount = 0;
    if (hasTicketsCsv) {
      try {
        const csv = await fs.readFile(path.join(fullDir, "tickets-categorized.csv"), "utf-8");
        ticketCount = Math.max(0, csv.split("\n").filter((l) => l.trim()).length - 1);
      } catch { /* best effort */ }
    }

    let rulesCount = 0;
    if (files.includes("rule-engine.local.csv")) {
      try {
        const csv = await fs.readFile(path.join(fullDir, "rule-engine.local.csv"), "utf-8");
        rulesCount = Math.max(0, csv.split("\n").filter((l) => l.trim()).length - 1);
      } catch { /* best effort */ }
    }

    const createdAt = dir.replace("train-", "").replace(/-/g, (m, offset: number, str: string) => {
      // Convert train-2026-02-16T04-08-00-167Z back to ISO
      // Pattern: YYYY-MM-DDTHH-MM-SS-mmmZ
      if (offset <= 9) return m; // keep date dashes
      return offset === str.indexOf("T") + 3 || offset === str.indexOf("T") + 6 ? ":" : offset === str.indexOf("T") + 9 ? "." : m;
    });

    sessions.push({
      runId: dir,
      createdAt: stat.mtime.toISOString(),
      status,
      phase,
      ticketCount,
      rulesCount,
      outputDir: fullDir,
    });
  }

  return NextResponse.json({ sessions });
}
