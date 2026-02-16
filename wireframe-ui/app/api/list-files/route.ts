// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

type ListedFile = {
  path: string;
  name: string;
  sizeBytes: number;
  modifiedAt: string;
};

function parseExtensions(raw: string | null): string[] {
  if (!raw) {
    return [];
  }
  return raw
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean)
    .map((item) => (item.startsWith(".") ? item : `.${item}`));
}

async function collectFiles(rootDir: string): Promise<string[]> {
  const stack = [rootDir];
  const files: string[] = [];

  while (stack.length > 0) {
    const currentDir = stack.pop() as string;
    const entries = await fs.readdir(currentDir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name);
      if (entry.isDirectory()) {
        stack.push(fullPath);
        continue;
      }
      if (entry.isFile()) {
        files.push(fullPath);
      }
    }
  }

  return files.sort((a, b) => a.localeCompare(b));
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const dir = (url.searchParams.get("dir") || "scripts/analysis").trim();
  const nameContains = (url.searchParams.get("nameContains") || "").trim().toLowerCase();
  const nameExact = (url.searchParams.get("nameExact") || "").trim().toLowerCase();
  const extensions = parseExtensions(url.searchParams.get("extensions"));
  const requestedLimit = Number.parseInt((url.searchParams.get("limit") || "500").trim(), 10);
  const limit = Number.isInteger(requestedLimit) && requestedLimit > 0
    ? Math.min(requestedLimit, 2000)
    : 500;

  const repoRoot = path.resolve(process.cwd(), "..");
  const scriptsRoot = path.resolve(repoRoot, "scripts");
  const resolvedDir = path.resolve(repoRoot, dir);

  if (resolvedDir !== scriptsRoot && !resolvedDir.startsWith(scriptsRoot + path.sep)) {
    return NextResponse.json({ error: "Directory must stay within scripts/." }, { status: 403 });
  }

  try {
    const stat = await fs.stat(resolvedDir);
    if (!stat.isDirectory()) {
      return NextResponse.json({ error: "Directory is not a folder." }, { status: 400 });
    }
  } catch {
    return NextResponse.json({ error: "Directory not found." }, { status: 404 });
  }

  const allFiles = await collectFiles(resolvedDir);
  const listedFiles: ListedFile[] = [];
  let totalMatches = 0;

  for (const filePath of allFiles) {
    const fileName = path.basename(filePath);
    const normalizedName = fileName.toLowerCase();

    if (extensions.length > 0 && !extensions.some((ext) => normalizedName.endsWith(ext))) {
      continue;
    }
    if (nameExact && normalizedName !== nameExact) {
      continue;
    }
    if (nameContains && !normalizedName.includes(nameContains)) {
      continue;
    }

    totalMatches += 1;
    if (listedFiles.length >= limit) {
      continue;
    }

    const stat = await fs.stat(filePath);
    if (!stat.isFile()) {
      continue;
    }
    listedFiles.push({
      path: filePath,
      name: fileName,
      sizeBytes: stat.size,
      modifiedAt: stat.mtime.toISOString()
    });
  }

  return NextResponse.json({
    dir: resolvedDir,
    count: listedFiles.length,
    totalMatches,
    truncated: totalMatches > listedFiles.length,
    files: listedFiles
  });
}
