// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

type TicketListItem = {
  key: string;
  summary: string;
  status: string;
  resolution: string;
  sourcePath: string;
  detailPath: string;
  hasRawTicketFile: boolean;
};

function asObject(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
}

function asString(value: unknown): string {
  if (typeof value === "string") {
    return value.trim();
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "";
}

function clip(text: string, maxLen = 160): string {
  if (!text) {
    return "";
  }
  if (text.length <= maxLen) {
    return text;
  }
  return `${text.slice(0, maxLen - 3)}...`;
}

function normalizeTicketKey(value: string): string {
  return value.trim().toUpperCase();
}

function isTicketFileName(fileName: string): boolean {
  return /^[A-Z]+-\d+\.json$/i.test(fileName);
}

function isValidTicketKey(ticketKey: string): boolean {
  return /^[A-Z]+-\d+$/.test(ticketKey);
}

function extractTicketKey(issue: Record<string, unknown>): string {
  const directKey = normalizeTicketKey(asString(issue.key));
  if (isValidTicketKey(directKey)) {
    return directKey;
  }

  const ticket = asObject(issue.ticket);
  const nestedKey = normalizeTicketKey(asString(ticket?.key));
  if (isValidTicketKey(nestedKey)) {
    return nestedKey;
  }

  return "";
}

function readNameField(value: unknown): string {
  const objectValue = asObject(value);
  if (!objectValue) {
    return asString(value);
  }
  return asString(objectValue.name || objectValue.value || objectValue.key);
}

function issueToTicketListItem(
  issue: Record<string, unknown>,
  sourcePath: string,
  rawTicketPathByKey: Map<string, string>
): TicketListItem | null {
  const ticketKey = extractTicketKey(issue);
  if (!ticketKey) {
    return null;
  }
  const fields = asObject(issue.fields);
  const ticket = asObject(issue.ticket);
  const normalizedStatus = asObject(issue.status);
  const summary = clip(asString(fields?.summary) || asString(ticket?.summary));
  const status = readNameField(fields?.status) || asString(normalizedStatus?.current);
  const resolution = readNameField(fields?.resolution) || asString(normalizedStatus?.resolution);
  const rawPath = rawTicketPathByKey.get(ticketKey);

  return {
    key: ticketKey,
    summary,
    status,
    resolution,
    sourcePath,
    detailPath: rawPath || sourcePath,
    hasRawTicketFile: Boolean(rawPath)
  };
}

function extractIssues(payload: unknown): Record<string, unknown>[] {
  const objectPayload = asObject(payload);
  if (!objectPayload) {
    return [];
  }

  const issues = objectPayload.issues;
  if (Array.isArray(issues)) {
    return issues
      .map((item) => asObject(item))
      .filter((item): item is Record<string, unknown> => item !== null);
  }

  if (typeof objectPayload.key === "string") {
    return [objectPayload];
  }

  const normalizedTicket = asObject(objectPayload.ticket);
  if (typeof normalizedTicket?.key === "string") {
    return [objectPayload];
  }

  return [];
}

async function safeReadJson(filePath: string): Promise<unknown | null> {
  try {
    const content = await fs.readFile(filePath, "utf-8");
    return JSON.parse(content) as unknown;
  } catch {
    return null;
  }
}

async function collectJsonFiles(rootDir: string): Promise<string[]> {
  const queue = [rootDir];
  const jsonFiles: string[] = [];

  while (queue.length > 0) {
    const currentDir = queue.pop() as string;
    const entries = await fs.readdir(currentDir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name);
      if (entry.isDirectory()) {
        queue.push(fullPath);
        continue;
      }
      if (entry.isFile() && entry.name.toLowerCase().endsWith(".json")) {
        jsonFiles.push(fullPath);
      }
    }
  }

  return jsonFiles.sort((a, b) => a.localeCompare(b));
}

async function collectTicketList(resolvedDir: string): Promise<TicketListItem[]> {
  const jsonFiles = await collectJsonFiles(resolvedDir);

  const rawTicketPathByKey = new Map<string, string>();
  for (const filePath of jsonFiles) {
    const fileName = path.basename(filePath);
    if (!isTicketFileName(fileName)) {
      continue;
    }
    const ticketKey = normalizeTicketKey(fileName.replace(/\.json$/i, ""));
    rawTicketPathByKey.set(ticketKey, filePath);
  }

  const ticketMap = new Map<string, TicketListItem>();
  for (const sourcePath of jsonFiles) {
    const payload = await safeReadJson(sourcePath);
    if (!payload) {
      continue;
    }

    const issues = extractIssues(payload);
    for (const issue of issues) {
      const item = issueToTicketListItem(issue, sourcePath, rawTicketPathByKey);
      if (!item) {
        continue;
      }
      const existing = ticketMap.get(item.key);
      if (!existing) {
        ticketMap.set(item.key, item);
        continue;
      }
      if (!existing.hasRawTicketFile && item.hasRawTicketFile) {
        ticketMap.set(item.key, item);
        continue;
      }
      if (!existing.summary && item.summary) {
        existing.summary = item.summary;
      }
      if (!existing.status && item.status) {
        existing.status = item.status;
      }
      if (!existing.resolution && item.resolution) {
        existing.resolution = item.resolution;
      }
    }
  }

  return Array.from(ticketMap.values()).sort((a, b) => a.key.localeCompare(b.key));
}

async function findTicketPayload(
  resolvedDir: string,
  ticketKey: string
): Promise<{ payload: unknown; sourcePath: string; hasRawTicketFile: boolean } | null> {
  const jsonFiles = await collectJsonFiles(resolvedDir);
  const expectedFileName = `${ticketKey}.JSON`;
  const exactMatchPath = jsonFiles.find(
    (sourcePath) => path.basename(sourcePath).toUpperCase() === expectedFileName
  );

  if (exactMatchPath) {
    const rawPayload = await safeReadJson(exactMatchPath);
    if (rawPayload) {
      return { payload: rawPayload, sourcePath: exactMatchPath, hasRawTicketFile: true };
    }
  }

  for (const sourcePath of jsonFiles) {
    const payload = await safeReadJson(sourcePath);
    if (!payload) {
      continue;
    }
    for (const issue of extractIssues(payload)) {
      const issueKey = extractTicketKey(issue);
      if (issueKey === ticketKey) {
        return {
          payload: issue,
          sourcePath,
          hasRawTicketFile: path.basename(sourcePath).toUpperCase() === expectedFileName
        };
      }
    }
  }
  return null;
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const dir = (url.searchParams.get("dir") || "scripts/normalized-tickets").trim();
  const ticketKey = normalizeTicketKey((url.searchParams.get("ticketKey") || "").trim());

  const repoRoot = path.resolve(process.cwd(), "..");
  const scriptsRoot = path.resolve(repoRoot, "scripts");
  const resolvedDir = path.resolve(repoRoot, dir);

  if (resolvedDir !== scriptsRoot && !resolvedDir.startsWith(scriptsRoot + path.sep)) {
    return NextResponse.json({ error: "Directory must stay within scripts/." }, { status: 403 });
  }

  try {
    const stat = await fs.stat(resolvedDir);
    if (!stat.isDirectory()) {
      return NextResponse.json({ error: "Ticket JSON dir is not a directory." }, { status: 400 });
    }
  } catch {
    return NextResponse.json({ error: "Ticket JSON dir not found." }, { status: 404 });
  }

  if (ticketKey) {
    if (!isValidTicketKey(ticketKey)) {
      return NextResponse.json({ error: "Invalid ticket key format." }, { status: 400 });
    }

    const found = await findTicketPayload(resolvedDir, ticketKey);
    if (!found) {
      return NextResponse.json({ error: `Ticket ${ticketKey} not found.` }, { status: 404 });
    }

    return NextResponse.json({
      ticketKey,
      sourcePath: found.sourcePath,
      detailPath: found.sourcePath,
      hasRawTicketFile: found.hasRawTicketFile,
      payload: found.payload
    });
  }

  const tickets = await collectTicketList(resolvedDir);
  return NextResponse.json({
    dir: resolvedDir,
    count: tickets.length,
    tickets
  });
}
