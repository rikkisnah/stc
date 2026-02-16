// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

type AddRuleRequest = {
  ticketKey?: string;
  reason?: string;
  failureCategory?: string;
  category?: string;
  matchField?: string;
  rulePattern?: string;
  append?: boolean;
  ticketJsonDir?: string;
  normalizedRoot?: string;
  rulesEngine?: string;
  matchFieldDefault?: string;
  priority?: number;
  confidence?: number;
  createdBy?: string;
  hitCount?: number;
};

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as AddRuleRequest;
    const ticketKey = (body.ticketKey || "").trim().toUpperCase();
    const reason = (body.reason || "").trim();
    const failureCategory = (body.failureCategory || "").trim();
    const category = (body.category || "").trim();

    if (!ticketKey || !reason || !failureCategory || !category) {
      return NextResponse.json(
        { error: "ticketKey, reason, failureCategory, and category are required." },
        { status: 400 }
      );
    }

    const repoRoot = path.resolve(process.cwd(), "..");
    const scriptPath = path.join(repoRoot, "scripts", "create_rule_from_ticket.py");
    try {
      await fs.access(scriptPath);
    } catch {
      return NextResponse.json(
        { error: `Script not found: ${scriptPath}` },
        { status: 404 }
      );
    }

    const ticketJsonDir = (body.ticketJsonDir || "scripts/tickets-json").trim();
    const normalizedRoot = (body.normalizedRoot || "scripts/normalized-tickets").trim();
    const rulesEngine = (body.rulesEngine || "scripts/trained-data/rule-engine.local.csv").trim();
    const matchFieldDefault = (body.matchFieldDefault || "summary+description").trim();
    const priority = Number.isFinite(body.priority) ? Number(body.priority) : 85;
    const confidence = Number.isFinite(body.confidence) ? Number(body.confidence) : 1.0;
    const createdBy = (body.createdBy || "human-feedback").trim();
    const hitCount = Number.isFinite(body.hitCount) ? Number(body.hitCount) : 0;
    const append = body.append !== false;

    const args = [
      "scripts/create_rule_from_ticket.py",
      "--ticket-json-dir",
      ticketJsonDir,
      "--normalized-root",
      normalizedRoot,
      "--rules-engine",
      rulesEngine,
      "--match-field-default",
      matchFieldDefault,
      "--priority",
      String(priority),
      "--confidence",
      String(confidence),
      "--created-by",
      createdBy,
      "--hit-count",
      String(hitCount)
    ];

    const stdinPayload = [
      ticketKey,
      reason,
      failureCategory,
      category,
      body.matchField?.trim() || "",
      body.rulePattern?.trim() || "",
      append ? "y" : "n"
    ].join("\n") + "\n";

    const command = `python3 ${args.join(" ")}`;
    const result = await new Promise<{ stdout: string; stderr: string }>((resolve, reject) => {
      const child = spawn("python3", args, { cwd: repoRoot });
      let stdout = "";
      let stderr = "";

      child.stdout.on("data", (chunk) => {
        stdout += String(chunk);
      });
      child.stderr.on("data", (chunk) => {
        stderr += String(chunk);
      });
      child.on("error", (error) => {
        reject(error);
      });
      child.on("close", (code) => {
        if (code === 0) {
          resolve({ stdout, stderr });
        } else {
          reject(new Error(stderr || stdout || `Command failed: ${command}`));
        }
      });

      child.stdin.write(stdinPayload);
      child.stdin.end();
    });

    return NextResponse.json({
      command,
      stdout: result.stdout,
      stderr: result.stderr
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unexpected error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

