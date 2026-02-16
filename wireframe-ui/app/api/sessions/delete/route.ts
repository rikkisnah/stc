// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(request: Request) {
  let body: { runId?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { runId } = body;
  if (!runId || typeof runId !== "string") {
    return NextResponse.json({ error: "Missing or invalid runId" }, { status: 400 });
  }

  if (!runId.startsWith("train-") || runId.includes("..") || runId.includes("/") || runId.includes("\\")) {
    return NextResponse.json({ error: "Invalid runId format" }, { status: 400 });
  }

  const repoRoot = path.resolve(process.cwd(), "..");
  const sessionDir = path.join(repoRoot, "scripts", "analysis", "ui-runs", runId);

  try {
    const stat = await fs.stat(sessionDir);
    if (!stat.isDirectory()) {
      return NextResponse.json({ error: "Session not found" }, { status: 404 });
    }
  } catch {
    return NextResponse.json({ error: "Session not found" }, { status: 404 });
  }

  await fs.rm(sessionDir, { recursive: true, force: true });

  return NextResponse.json({ deleted: true, runId });
}
