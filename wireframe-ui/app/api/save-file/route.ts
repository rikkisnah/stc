// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

type SaveFileRequest = {
  path?: string;
  content?: string;
};

export async function POST(req: Request) {
  let payload: SaveFileRequest;
  try {
    payload = (await req.json()) as SaveFileRequest;
  } catch {
    return NextResponse.json({ error: "Invalid JSON payload." }, { status: 400 });
  }

  const inputPath = (payload.path || "").trim();
  if (!inputPath) {
    return NextResponse.json({ error: "Missing file path." }, { status: 400 });
  }
  if (typeof payload.content !== "string") {
    return NextResponse.json({ error: "Content must be a string." }, { status: 400 });
  }

  const repoRoot = path.resolve(process.cwd(), "..");
  const allowedRoots = [
    path.resolve(repoRoot, "scripts", "analysis"),
    path.resolve(repoRoot, "scripts", "trained-data")
  ];
  const resolvedPath = path.resolve(repoRoot, inputPath);
  const isAllowed = allowedRoots.some(
    (root) => resolvedPath === root || resolvedPath.startsWith(root + path.sep)
  );

  if (!isAllowed) {
    return NextResponse.json(
      { error: "Path is outside editable directories (scripts/analysis, scripts/trained-data)." },
      { status: 403 }
    );
  }

  try {
    const stat = await fs.stat(resolvedPath);
    if (!stat.isFile()) {
      return NextResponse.json({ error: "Path is not a file." }, { status: 400 });
    }
  } catch {
    return NextResponse.json({ error: "File not found." }, { status: 404 });
  }

  await fs.writeFile(resolvedPath, payload.content, "utf-8");
  return NextResponse.json({ path: resolvedPath, saved: true });
}
