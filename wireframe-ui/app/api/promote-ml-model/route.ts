// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const MODEL_FILES = ["classifier.joblib", "category_map.json", "training_report.txt"];
const DEFAULT_SOURCE = "scripts/trained-data/ml-model";
const DEFAULT_TARGET = "scripts/trained-data/golden-ml-model";

async function readDirInfo(dirPath: string) {
  const info: { exists: boolean; sizeBytes: number; modifiedAt: string; report: string } = {
    exists: false,
    sizeBytes: 0,
    modifiedAt: "",
    report: "",
  };
  try {
    const modelStat = await fs.stat(path.join(dirPath, "classifier.joblib"));
    info.exists = true;
    info.sizeBytes = modelStat.size;
    info.modifiedAt = modelStat.mtime.toISOString();
  } catch {
    return info;
  }
  try {
    info.report = await fs.readFile(path.join(dirPath, "training_report.txt"), "utf-8");
  } catch {
    // no report available
  }
  return info;
}

function resolveDirs(source?: string | null, target?: string | null) {
  const repoRoot = path.resolve(process.cwd(), "..");
  const allowedRoot = path.resolve(repoRoot, "scripts");

  const sourceDir = path.resolve(repoRoot, source?.trim() || DEFAULT_SOURCE);
  const targetDir = path.resolve(repoRoot, target?.trim() || DEFAULT_TARGET);

  // Security: both paths must be under scripts/
  if (!sourceDir.startsWith(allowedRoot + path.sep) && sourceDir !== allowedRoot) {
    throw new Error("Source directory must be under scripts/.");
  }
  if (!targetDir.startsWith(allowedRoot + path.sep) && targetDir !== allowedRoot) {
    throw new Error("Target directory must be under scripts/.");
  }

  return { repoRoot, sourceDir, targetDir };
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const source = url.searchParams.get("source");
  const target = url.searchParams.get("target");

  let sourceDir: string, targetDir: string;
  try {
    ({ sourceDir, targetDir } = resolveDirs(source, target));
  } catch (err) {
    return NextResponse.json({ error: err instanceof Error ? err.message : "Invalid paths" }, { status: 400 });
  }

  const [working, golden] = await Promise.all([readDirInfo(sourceDir), readDirInfo(targetDir)]);

  let identical = false;
  if (working.exists && golden.exists && working.sizeBytes === golden.sizeBytes) {
    try {
      const wBuf = await fs.readFile(path.join(sourceDir, "classifier.joblib"));
      const gBuf = await fs.readFile(path.join(targetDir, "classifier.joblib"));
      identical = wBuf.equals(gBuf);
    } catch {
      identical = false;
    }
  }

  return NextResponse.json({ working, golden, identical });
}

export async function POST(req: Request) {
  const body = (await req.json()) as { source?: string; target?: string };

  let sourceDir: string, targetDir: string;
  try {
    ({ sourceDir, targetDir } = resolveDirs(body.source, body.target));
  } catch (err) {
    return NextResponse.json({ error: err instanceof Error ? err.message : "Invalid paths" }, { status: 400 });
  }

  // Verify source model exists
  try {
    await fs.stat(path.join(sourceDir, "classifier.joblib"));
    await fs.stat(path.join(sourceDir, "category_map.json"));
  } catch {
    return NextResponse.json({ error: "No ML model found in source directory." }, { status: 400 });
  }

  await fs.mkdir(targetDir, { recursive: true });

  for (const file of MODEL_FILES) {
    const src = path.join(sourceDir, file);
    const dst = path.join(targetDir, file);
    try {
      await fs.copyFile(src, dst);
    } catch {
      // training_report.txt may not exist — skip optional files
      if (file === "classifier.joblib" || file === "category_map.json") {
        return NextResponse.json({ error: `Failed to copy required file: ${file}` }, { status: 500 });
      }
    }
  }

  return NextResponse.json({ promoted: true, message: "ML model promoted to golden successfully." });
}
