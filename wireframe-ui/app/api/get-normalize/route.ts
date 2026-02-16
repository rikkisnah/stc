// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

function runCommand(
  args: string[],
  cwd: string,
  signal?: AbortSignal,
  setActiveChild?: (child: ChildProcessWithoutNullStreams | null) => void,
  onStdout?: (line: string) => void,
  onStderr?: (line: string) => void
): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn("uv", ["run", "python3", "-u", ...args], { cwd });
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
        reject(new Error(stderr || stdout || `Command failed: uv run python3 ${args.join(" ")}`));
      }
    });
  });
}

export async function POST(req: Request) {
  const body = (await req.json()) as {
    inputMode?: "jql" | "files" | "tickets";
    jql?: string;
    resolutionMode?: "all" | "unresolved-only" | "resolved-only";
    ticketsFile?: string;
    ticketsText?: string;
    maxTickets?: number;
  };
  const inputMode = body.inputMode || "jql";
  const rawJql = body.jql?.trim();
  const resolutionMode = body.resolutionMode || "all";
  const maxTickets = body.maxTickets && body.maxTickets > 0 ? body.maxTickets : 0;
  if (inputMode === "jql" && !rawJql) {
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
      let ticketsTempFile = "";

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
          if (ticketsTempFile) {
            await fs.rm(ticketsTempFile, { force: true });
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
        const normalizedDir = path.join(normalizedBaseDir, normalizeDate);

        await fs.mkdir(jqlDir, { recursive: true });
        await fs.mkdir(outputDir, { recursive: true });
        await fs.mkdir(ingestDir, { recursive: true });

        const commands: string[][] = [];

        if (inputMode === "jql") {
          await fs.writeFile(jqlFile, rawJql || "", "utf-8");
          const getTicketsArgs = ["scripts/get_tickets.py", "-a", "--jql-file", jqlFile, "-y"];
          if (resolutionMode === "unresolved-only") {
            getTicketsArgs.push("--unresolved-only");
          } else if (resolutionMode === "resolved-only") {
            getTicketsArgs.push("--include-resolved-only");
          } else {
            getTicketsArgs.push("--include-unresolved");
          }
          commands.push([
            ...getTicketsArgs,
            "--number-of-tickets",
            String(maxTickets > 0 ? maxTickets : 100000),
            "--output-file",
            path.join(ingestDir, "limited-tickets.json")
          ]);
        } else {
          const parseTickets = (text: string) => {
            const items = text
              .split(/[\n,]+/)
              .map((item) => item.trim())
              .filter(Boolean)
              .filter((item) => !item.startsWith("#"));
            const unique = Array.from(new Set(items));
            const invalid = unique.filter((item) => !/^[A-Z]+-\d+$/.test(item));
            if (invalid.length > 0) {
              throw new Error(`Invalid ticket key(s): ${invalid.join(", ")}`);
            }
            return unique;
          };

          let ticketKeys: string[] = [];
          if (inputMode === "files") {
            const filePath = (body.ticketsFile || "").trim();
            if (!filePath) {
              throw new Error("Ticket list file path is required.");
            }
            const resolved = path.isAbsolute(filePath)
              ? filePath
              : path.resolve(repoRoot, filePath);
            const content = await fs.readFile(resolved, "utf-8");
            ticketKeys = parseTickets(content);
          } else {
            ticketKeys = parseTickets(body.ticketsText || "");
          }

          if (ticketKeys.length === 0) {
            throw new Error("No ticket keys provided.");
          }
          if (maxTickets > 0 && ticketKeys.length > maxTickets) {
            ticketKeys = ticketKeys.slice(0, maxTickets);
          }

          for (const ticket of ticketKeys) {
            commands.push(["scripts/get_tickets.py", "-t", ticket]);
          }
        }

        commands.push([
          "scripts/normalize_tickets.py",
          "--input-dir",
          inputMode === "jql" ? ingestDir : path.join(scriptsDir, "tickets-json"),
          "--output-dir",
          normalizedBaseDir,
          "--date",
          normalizeDate,
          "-y"
        ]);

        for (const args of commands) {
          const cmd = `uv run python3 ${args.join(" ")}`;
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
          if (inputMode !== "jql" && args[0] === "scripts/get_tickets.py" && args[1] === "-t") {
            const ticketKey = args[2];
            const sourcePath = path.join(scriptsDir, "tickets-json", `${ticketKey}.json`);
            const targetPath = path.join(ingestDir, `${ticketKey}.json`);
            await fs.copyFile(sourcePath, targetPath);
            emit({
              type: "stdout",
              command: cmd,
              line: `Copied ${ticketKey}.json to ${ingestDir}`
            });
          }
          emit({ type: "command-end", command: cmd });
        }

        emit({
          type: "done",
          runId,
          paths: { ingestDir, normalizedDir }
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
