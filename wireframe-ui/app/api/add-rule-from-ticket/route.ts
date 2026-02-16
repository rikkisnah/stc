// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { promises as fs } from "node:fs";
import { spawn } from "node:child_process";
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
  ticketJsonDir?: string;
  normalizedRoot?: string;
  rulesEngine?: string;
  matchFieldDefault?: string;
  priority?: number;
  confidence?: number;
  createdBy?: string;
  hitCount?: number;
};

function isValidTicketKey(ticketKey: string): boolean {
  return /^[A-Z]+-\d+$/.test(ticketKey);
}

async function fileExists(filePath: string): Promise<boolean> {
  try {
    const stat = await fs.stat(filePath);
    return stat.isFile();
  } catch {
    return false;
  }
}

async function findLatestNormalizedTicket(
  normalizedRootPath: string,
  ticketKey: string
): Promise<string | undefined> {
  try {
    const entries = await fs.readdir(normalizedRootPath, { withFileTypes: true });
    const dateDirs = entries
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name)
      .sort();

    for (let idx = dateDirs.length - 1; idx >= 0; idx -= 1) {
      const candidate = path.join(normalizedRootPath, dateDirs[idx], `${ticketKey}.json`);
      if (await fileExists(candidate)) {
        return candidate;
      }
    }
  } catch {
    // Best-effort only; leave undefined if normalized artifact cannot be found.
  }
  return undefined;
}

function runUvCommand(
  args: string[],
  cwd: string,
  inputText: string,
  signal?: AbortSignal,
  onStdout?: (line: string) => void,
  onStderr?: (line: string) => void
): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn("uv", args, { cwd });
    let stdout = "";
    let stderr = "";
    let aborted = false;

    const abortHandler = () => {
      aborted = true;
      child.kill("SIGTERM");
    };
    signal?.addEventListener("abort", abortHandler);

    child.stdout.on("data", (chunk) => {
      const text = String(chunk);
      stdout += text;
      onStdout?.(text);
    });
    child.stderr.on("data", (chunk) => {
      const text = String(chunk);
      stderr += text;
      onStderr?.(text);
    });

    child.on("error", reject);
    child.on("close", (code) => {
      signal?.removeEventListener("abort", abortHandler);
      if (aborted) {
        reject(new Error("Run canceled by user."));
        return;
      }
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(new Error(stderr || stdout || `Command failed: uv ${args.join(" ")}`));
      }
    });

    child.stdin.write(inputText);
    child.stdin.end();
  });
}

export async function POST(req: Request) {
  const body = (await req.json()) as AddRuleRequest;

  const ticketKey = (body.ticketKey || "").trim().toUpperCase();
  const reason = (body.reason || "").trim();
  const failureCategory = (body.failureCategory || "").trim();
  const category = (body.category || "").trim();

  if (!ticketKey || !isValidTicketKey(ticketKey)) {
    return NextResponse.json({ error: "Valid ticket key is required." }, { status: 400 });
  }
  if (!reason) {
    return NextResponse.json({ error: "Reason is required." }, { status: 400 });
  }
  if (!failureCategory) {
    return NextResponse.json({ error: "Category of Issue is required." }, { status: 400 });
  }
  if (!category) {
    return NextResponse.json({ error: "Category is required." }, { status: 400 });
  }

  const ticketJsonDir = (body.ticketJsonDir || "scripts/tickets-json").trim();
  const normalizedRoot = (body.normalizedRoot || "scripts/normalized-tickets").trim();
  const rulesEngine = (body.rulesEngine || "scripts/trained-data/rule-engine.local.csv").trim();
  const matchFieldDefault = (body.matchFieldDefault || "summary+description").trim();
  const priority = Number.isInteger(Number(body.priority)) ? Number(body.priority) : 85;
  const confidence = Number.isNaN(Number(body.confidence)) ? 1.0 : Number(body.confidence);
  const createdBy = (body.createdBy || "human-feedback").trim();
  const hitCount = Number.isInteger(Number(body.hitCount)) ? Number(body.hitCount) : 0;

  const matchField = (body.matchField || "").trim();
  const rulePattern = (body.rulePattern || "").trim();

  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();
      const emit = (event: Record<string, unknown>) => {
        controller.enqueue(encoder.encode(`${JSON.stringify(event)}\n`));
      };

      try {
        const repoRoot = path.resolve(process.cwd(), "..");
        const resolvedTicketJsonDir = path.resolve(repoRoot, ticketJsonDir);
        const resolvedNormalizedRoot = path.resolve(repoRoot, normalizedRoot);
        const commandArgs = [
          "run",
          "python3",
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
        const command = `uv ${commandArgs.join(" ")}`;
        const stdinPayload = [
          ticketKey,
          reason,
          failureCategory,
          category,
          matchField,
          rulePattern,
          "y"
        ].join("\n") + "\n";

        emit({ type: "command-start", command });
        const { stdout } = await runUvCommand(
          commandArgs,
          repoRoot,
          stdinPayload,
          req.signal,
          (line) => emit({ type: "stdout", command, line }),
          (line) => emit({ type: "stderr", command, line })
        );
        emit({ type: "command-end", command });

        const appendedMatch = stdout.match(/Rule\s+(R\d+)\s+appended to\s+([^\n]+)/);
        const ruleId = appendedMatch?.[1];
        const outputRulesEngine = path.resolve(repoRoot, appendedMatch?.[2]?.trim() || rulesEngine);
        const ticketJsonPath = path.join(resolvedTicketJsonDir, `${ticketKey}.json`);
        const normalizedJsonPath = await findLatestNormalizedTicket(resolvedNormalizedRoot, ticketKey);
        const message = ruleId
          ? `Rule ${ruleId} appended to ${outputRulesEngine}`
          : "Rule command completed.";

        emit({
          type: "done",
          result: {
            ruleId,
            rulesEngine: outputRulesEngine,
            ticketJson: (await fileExists(ticketJsonPath)) ? ticketJsonPath : undefined,
            normalizedJson: normalizedJsonPath,
            message
          }
        });
      } catch (error) {
        if (req.signal.aborted) {
          emit({ type: "canceled", message: "Run canceled." });
        } else {
          const message = error instanceof Error ? error.message : "Unknown error";
          emit({ type: "error", error: message });
        }
      } finally {
        controller.close();
      }
    }
  });

  return new NextResponse(stream, {
    headers: {
      "Content-Type": "application/x-ndjson; charset=utf-8",
      "Cache-Control": "no-cache"
    }
  });
}
