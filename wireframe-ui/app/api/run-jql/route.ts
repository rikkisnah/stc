// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

type SummaryRow = {
  "Tickets Category": string;
  "Percentage of Total Tickets": string;
  "Count of Tickets": string;
  "JQL Query": string;
};

function runCommand(
  args: string[],
  cwd: string,
  signal?: AbortSignal,
  setActiveChild?: (child: ChildProcessWithoutNullStreams | null) => void,
  onStdout?: (line: string) => void,
  onStderr?: (line: string) => void
): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn("python3", args, { cwd });
    setActiveChild?.(child);
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
      setActiveChild?.(null);
      if (aborted) {
        reject(new Error("Run canceled by user."));
        return;
      }
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(new Error(stderr || stdout || `Command failed: python3 ${args.join(" ")}`));
      }
    });
  });
}

function parseCsv(csvText: string): SummaryRow[] {
  const lines = csvText.trim().split(/\r?\n/);
  if (lines.length <= 1) {
    return [];
  }

  const header = lines[0].split(",");
  const rows: SummaryRow[] = [];

  for (const line of lines.slice(1)) {
    // create_summary.py emits simple CSV without embedded commas in these columns.
    const cells = line.split(",");
    const row: Record<string, string> = {};
    header.forEach((key, index) => {
      row[key] = (cells[index] || "").trim();
    });
    rows.push(row as SummaryRow);
  }

  return rows;
}

export async function POST(req: Request) {
  const body = (await req.json()) as {
    jql?: string;
    resolutionMode?: "all" | "unresolved-only" | "resolved-only";
  };
  const rawJql = body.jql?.trim();
  const resolutionMode = body.resolutionMode || "all";
  if (!rawJql) {
    return NextResponse.json({ error: "JQL is required." }, { status: 400 });
  }

  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();
      const emit = (event: Record<string, unknown>) => {
        controller.enqueue(encoder.encode(`${JSON.stringify(event)}\n`));
      };
      let activeChild: ChildProcessWithoutNullStreams | null = null;
      let outputDir = "";
      let jqlFile = "";

      const abortHandler = async () => {
        try {
          if (activeChild) {
            activeChild.kill("SIGTERM");
          }
          if (outputDir) {
            await fs.rm(outputDir, { recursive: true, force: true });
          }
          if (jqlFile) {
            await fs.rm(jqlFile, { force: true });
          }
        } catch {
          // best effort cleanup
        }
      };
      req.signal.addEventListener("abort", abortHandler);

      try {
        const repoRoot = path.resolve(process.cwd(), "..");
        const scriptsDir = path.join(repoRoot, "scripts");
        const jqlDir = path.join(scriptsDir, "analysis", "ui-runs");
        const runId = new Date().toISOString().replace(/[:.]/g, "-");
        const normalizeDate = new Date().toISOString().slice(0, 10);
        jqlFile = path.join(jqlDir, `jql-${runId}.txt`);
        outputDir = path.join(scriptsDir, "analysis", "ui-runs", runId);
        const ingestDir = path.join(outputDir, "ingest");
        const normalizedBaseDir = path.join(outputDir, "normalized");
        const ticketsCsv = path.join(outputDir, "tickets-categorized.csv");
        const summaryCsv = path.join(outputDir, "tickets-summary.csv");
        const normalizedDir = path.join(normalizedBaseDir, normalizeDate);

        await fs.mkdir(jqlDir, { recursive: true });
        await fs.writeFile(jqlFile, rawJql, "utf-8");
        await fs.mkdir(outputDir, { recursive: true });
        await fs.mkdir(ingestDir, { recursive: true });

        const getTicketsArgs = ["scripts/get_tickets.py", "-a", "--jql-file", jqlFile, "-y"];
        if (resolutionMode === "unresolved-only") {
          getTicketsArgs.push("--unresolved-only");
        } else if (resolutionMode === "resolved-only") {
          getTicketsArgs.push("--include-resolved-only");
        } else {
          getTicketsArgs.push("--include-unresolved");
        }

        const commands: string[][] = [
          [
            ...getTicketsArgs,
            "--number-of-tickets",
            "100000",
            "--output-file",
            path.join(ingestDir, "limited-tickets.json")
          ],
          [
            "scripts/normalize_tickets.py",
            "--input-dir",
            ingestDir,
            "--output-dir",
            normalizedBaseDir,
            "--date",
            normalizeDate,
            "-y"
          ],
          [
            "scripts/rule_engine_categorize.py",
            "--tickets-dir",
            normalizedDir,
            "--output-dir",
            outputDir,
            "-y"
          ],
          ["scripts/create_summary.py", "--tickets", ticketsCsv, "--output", summaryCsv]
        ];

        for (const args of commands) {
          const cmd = `python3 ${args.join(" ")}`;
          emit({ type: "command-start", command: cmd });
          await runCommand(
            args,
            repoRoot,
            req.signal,
            (child) => {
              activeChild = child;
            },
            (line) => emit({ type: "stdout", command: cmd, line }),
            (line) => emit({ type: "stderr", command: cmd, line })
          );
          emit({ type: "command-end", command: cmd });
        }

        const summaryText = await fs.readFile(summaryCsv, "utf-8");
        const summaryRows = parseCsv(summaryText);
        emit({
          type: "done",
          runId,
          summaryRows,
          paths: { ticketsCsv, summaryCsv, normalizedDir }
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        if (req.signal.aborted || message.includes("Run canceled by user")) {
          emit({ type: "canceled", message: "Run canceled. Artifacts cleaned." });
        } else {
          emit({ type: "error", error: message });
        }
      } finally {
        req.signal.removeEventListener("abort", abortHandler);
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
