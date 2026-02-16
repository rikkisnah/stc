// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const MODEL_FILES = ["classifier.joblib", "category_map.json", "training_report.txt"];

type CompareResult = {
  working: { exists: boolean; sizeBytes: number; modifiedAt: string; report: string };
  golden: { exists: boolean; sizeBytes: number; modifiedAt: string; report: string };
  identical: boolean;
};

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

export async function GET() {
  const repoRoot = path.resolve(process.cwd(), "..");
  const scriptsDir = path.join(repoRoot, "scripts");
  const workingDir = path.join(scriptsDir, "trained-data", "ml-model");
  const goldenDir = path.join(scriptsDir, "trained-data", "golden-ml-model");

  const [working, golden] = await Promise.all([readDirInfo(workingDir), readDirInfo(goldenDir)]);

  let identical = false;
  if (working.exists && golden.exists && working.sizeBytes === golden.sizeBytes) {
    try {
      const wBuf = await fs.readFile(path.join(workingDir, "classifier.joblib"));
      const gBuf = await fs.readFile(path.join(goldenDir, "classifier.joblib"));
      identical = wBuf.equals(gBuf);
    } catch {
      identical = false;
    }
  }

  const result: CompareResult = { working, golden, identical };
  return NextResponse.json(result);
}

export async function POST() {
  const repoRoot = path.resolve(process.cwd(), "..");
  const scriptsDir = path.join(repoRoot, "scripts");
  const workingDir = path.join(scriptsDir, "trained-data", "ml-model");
  const goldenDir = path.join(scriptsDir, "trained-data", "golden-ml-model");

  // Verify working model exists
  try {
    await fs.stat(path.join(workingDir, "classifier.joblib"));
    await fs.stat(path.join(workingDir, "category_map.json"));
  } catch {
    return NextResponse.json({ error: "No working ML model found to promote." }, { status: 400 });
  }

  await fs.mkdir(goldenDir, { recursive: true });

  for (const file of MODEL_FILES) {
    const src = path.join(workingDir, file);
    const dst = path.join(goldenDir, file);
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
