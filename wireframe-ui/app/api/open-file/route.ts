// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

function guessContentType(filePath: string): string {
  if (filePath.endsWith(".csv")) {
    return "text/csv; charset=utf-8";
  }
  if (filePath.endsWith(".json")) {
    return "application/json; charset=utf-8";
  }
  if (filePath.endsWith(".txt")) {
    return "text/plain; charset=utf-8";
  }
  return "application/octet-stream";
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const inputPath = url.searchParams.get("path");
  const asDownload = (url.searchParams.get("download") || "").trim() === "1";
  if (!inputPath) {
    return NextResponse.json({ error: "Missing path query parameter." }, { status: 400 });
  }

  const repoRoot = path.resolve(process.cwd(), "..");
  const allowedRoots = [
    path.resolve(repoRoot, "scripts", "analysis"),
    path.resolve(repoRoot, "scripts", "trained-data"),
    path.resolve(repoRoot, "scripts", "tickets-json"),
    path.resolve(repoRoot, "scripts", "normalized-tickets")
  ];
  const resolvedPath = path.resolve(repoRoot, inputPath);
  const isAllowed = allowedRoots.some(
    (allowedRoot) => resolvedPath === allowedRoot || resolvedPath.startsWith(allowedRoot + path.sep)
  );

  if (!isAllowed) {
    return NextResponse.json({ error: "Path is outside allowed scripts directories." }, { status: 403 });
  }

  try {
    const stat = await fs.stat(resolvedPath);
    if (!stat.isFile()) {
      return NextResponse.json({ error: "Path is not a file." }, { status: 400 });
    }

    const content = await fs.readFile(resolvedPath);
    return new NextResponse(content, {
      headers: {
        "Content-Type": guessContentType(resolvedPath),
        "Content-Disposition": `${asDownload ? "attachment" : "inline"}; filename="${path.basename(resolvedPath)}"`
      }
    });
  } catch {
    return NextResponse.json({ error: "File not found." }, { status: 404 });
  }
}
