// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

type PhaseMeta = {
  normalizeDate: string;
  trainingData: string;
  minSamples: number;
  maxReviewRows: number;
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
    const child = spawn("uv", ["run", "python3", ...args], { cwd });
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
    phase?: 1 | 2 | 3;
    runId?: string;
    inputMode?: "jql" | "files" | "tickets";
    jql?: string;
    resolutionMode?: "all" | "unresolved-only" | "resolved-only";
    ticketsFile?: string;
    ticketsText?: string;
    trainingData?: string;
    minSamples?: number;
    maxReviewRows?: number;
  };

  const phase = body.phase || 1;
  const existingRunId = body.runId?.trim();

  if ((phase === 2 || phase === 3) && !existingRunId) {
    return NextResponse.json({ error: "runId is required for phases 2 and 3." }, { status: 400 });
  }

  if (phase === 1) {
    const inputMode = body.inputMode || "jql";
    const rawJql = body.jql?.trim();
    if (inputMode === "jql" && !rawJql) {
      return NextResponse.json({ error: "JQL is required." }, { status: 400 });
    }
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
          // Only delete outputDir on phase 1 cancel — preserve checkpoint for phases 2/3
          if (phase === 1 && outputDir) {
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

        if (phase === 1) {
          await runPhase1(body, repoRoot, scriptsDir, jqlDir, req.signal, emit, (child) => { activeChild = child; }, (dir) => { outputDir = dir; }, (file) => { jqlFile = file; });
        } else {
          const runId = existingRunId as string;
          outputDir = path.join(scriptsDir, "analysis", "ui-runs", runId);

          try {
            await fs.stat(outputDir);
          } catch {
            throw new Error(`Run directory not found: ${outputDir}`);
          }

          const metaPath = path.join(outputDir, "phase-meta.json");
          const metaText = await fs.readFile(metaPath, "utf-8");
          const meta = JSON.parse(metaText) as PhaseMeta;

          if (phase === 2) {
            await runPhase2(runId, outputDir, meta, repoRoot, req.signal, emit, (child) => { activeChild = child; });
          } else {
            await runPhase3(runId, outputDir, meta, repoRoot, req.signal, emit, (child) => { activeChild = child; });
          }
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        if (req.signal.aborted || message.includes("Run canceled by user")) {
          emit({ type: "canceled", message: "Run canceled." });
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

// ---------------------------------------------------------------------------
// Phase 1: Fetch tickets → Normalize → Init rules → Initial categorize
// ---------------------------------------------------------------------------
async function runPhase1(
  body: {
    inputMode?: "jql" | "files" | "tickets";
    jql?: string;
    resolutionMode?: "all" | "unresolved-only" | "resolved-only";
    ticketsFile?: string;
    ticketsText?: string;
    trainingData?: string;
    minSamples?: number;
    maxReviewRows?: number;
  },
  repoRoot: string,
  scriptsDir: string,
  jqlDir: string,
  signal: AbortSignal,
  emit: (event: Record<string, unknown>) => void,
  setActiveChild: (child: ChildProcessWithoutNullStreams | null) => void,
  setOutputDir: (dir: string) => void,
  setJqlFile: (file: string) => void
) {
  const inputMode = body.inputMode || "jql";
  const rawJql = body.jql?.trim();
  const resolutionMode = body.resolutionMode || "all";

  const runId = `train-${new Date().toISOString().replace(/[:.]/g, "-")}`;
  const normalizeDate = new Date().toISOString().slice(0, 10);
  const jqlFile = path.join(jqlDir, `jql-${runId}.txt`);
  setJqlFile(jqlFile);
  const outputDir = path.join(scriptsDir, "analysis", "ui-runs", runId);
  setOutputDir(outputDir);
  const ingestDir = path.join(outputDir, "ingest");
  const normalizedBaseDir = path.join(outputDir, "normalized");
  const normalizedDir = path.join(normalizedBaseDir, normalizeDate);
  const localRules = path.join(outputDir, "rule-engine.local.csv");
  const goldenRules = path.join(scriptsDir, "trained-data", "golden-rules-engine", "rule-engine.csv");
  const ticketsCsv = path.join(outputDir, "tickets-categorized.csv");
  const mlModelDir = path.join(outputDir, "ml-model");

  const trainingData = body.trainingData?.trim() ||
    path.join(scriptsDir, "trained-data", "ml-training-data.csv");
  const minSamples = body.minSamples ?? 20;
  const maxReviewRows = body.maxReviewRows ?? 200;

  await fs.mkdir(jqlDir, { recursive: true });
  await fs.mkdir(outputDir, { recursive: true });
  await fs.mkdir(ingestDir, { recursive: true });
  await fs.mkdir(mlModelDir, { recursive: true });

  // --- Step 1: Fetch tickets ---
  const fetchCommands: string[][] = [];

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
    fetchCommands.push([
      ...getTicketsArgs,
      "--number-of-tickets",
      "100000",
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

    for (const ticket of ticketKeys) {
      fetchCommands.push(["scripts/get_tickets.py", "-t", ticket]);
    }
  }

  for (const args of fetchCommands) {
    const cmd = `uv run python3 ${args.join(" ")}`;
    emit({ type: "command-start", command: cmd });
    await runCommand(
      args, repoRoot, signal, setActiveChild,
      (line) => emit({ type: "stdout", command: cmd, line }),
      (line) => emit({ type: "stderr", command: cmd, line })
    );
    if (inputMode !== "jql" && args[0] === "scripts/get_tickets.py" && args[1] === "-t") {
      const ticketKey = args[2];
      const sourcePath = path.join(scriptsDir, "tickets-json", `${ticketKey}.json`);
      const targetPath = path.join(ingestDir, `${ticketKey}.json`);
      await fs.copyFile(sourcePath, targetPath);
      emit({ type: "stdout", command: cmd, line: `Copied ${ticketKey}.json to ${ingestDir}` });
    }
    emit({ type: "command-end", command: cmd });
  }

  // --- Step 2: Normalize ---
  const normalizeArgs = [
    "scripts/normalize_tickets.py",
    "--input-dir", inputMode === "jql" ? ingestDir : path.join(scriptsDir, "tickets-json"),
    "--output-dir", normalizedBaseDir,
    "--date", normalizeDate,
    "-y"
  ];
  const normalizeCmd = `uv run python3 ${normalizeArgs.join(" ")}`;
  emit({ type: "command-start", command: normalizeCmd });
  await runCommand(
    normalizeArgs, repoRoot, signal, setActiveChild,
    (line) => emit({ type: "stdout", command: normalizeCmd, line }),
    (line) => emit({ type: "stderr", command: normalizeCmd, line })
  );
  emit({ type: "command-end", command: normalizeCmd });

  // --- Step 3: Init local rules from golden ---
  const cpCmd = `cp ${goldenRules} ${localRules}`;
  emit({ type: "command-start", command: cpCmd });
  await fs.copyFile(goldenRules, localRules);
  emit({ type: "stdout", command: cpCmd, line: `Copied golden rules to ${localRules}` });
  emit({ type: "command-end", command: cpCmd });

  // --- Step 4: Initial categorization (rules only) ---
  const cat1Args = [
    "scripts/rule_engine_categorize.py",
    "--tickets-dir", normalizedDir,
    "--rule-engine", localRules,
    "--output-dir", outputDir,
    "-y"
  ];
  const cat1Cmd = `uv run python3 ${cat1Args.join(" ")}`;
  emit({ type: "command-start", command: cat1Cmd });
  await runCommand(
    cat1Args, repoRoot, signal, setActiveChild,
    (line) => emit({ type: "stdout", command: cat1Cmd, line }),
    (line) => emit({ type: "stderr", command: cat1Cmd, line })
  );
  emit({ type: "command-end", command: cat1Cmd });

  // --- Write phase metadata for subsequent phases ---
  const meta: PhaseMeta = { normalizeDate, trainingData, minSamples, maxReviewRows };
  await fs.writeFile(path.join(outputDir, "phase-meta.json"), JSON.stringify(meta), "utf-8");

  // --- Pause for human audit ---
  emit({
    type: "paused",
    phase: 1,
    runId,
    paths: { ticketsCsv, outputDir, normalizedDir, localRules }
  });
}

// ---------------------------------------------------------------------------
// Phase 2: ML train → ML categorize (rules + ML fallback)
// ---------------------------------------------------------------------------
async function runPhase2(
  runId: string,
  outputDir: string,
  meta: PhaseMeta,
  repoRoot: string,
  signal: AbortSignal,
  emit: (event: Record<string, unknown>) => void,
  setActiveChild: (child: ChildProcessWithoutNullStreams | null) => void
) {
  const normalizedBaseDir = path.join(outputDir, "normalized");
  const normalizedDir = path.join(normalizedBaseDir, meta.normalizeDate);
  const localRules = path.join(outputDir, "rule-engine.local.csv");
  const mlModelDir = path.join(outputDir, "ml-model");
  const mlModel = path.join(mlModelDir, "classifier.joblib");
  const mlCategoryMap = path.join(mlModelDir, "category_map.json");
  const mlReport = path.join(mlModelDir, "training_report.txt");
  const ticketsCsv = path.join(outputDir, "tickets-categorized.csv");

  // --- Step 5: Train ML classifier ---
  const mlTrainArgs = [
    "scripts/ml_train.py",
    "--training-data", meta.trainingData,
    "--tickets-categorized", ticketsCsv,
    "--tickets-dir", normalizedDir,
    "--output-model", mlModel,
    "--output-category-map", mlCategoryMap,
    "--output-report", mlReport,
    "--min-samples", String(meta.minSamples),
    "-y"
  ];
  const mlTrainCmd = `uv run python3 ${mlTrainArgs.join(" ")}`;
  emit({ type: "command-start", command: mlTrainCmd });
  let mlTrainStdout = "";
  await runCommand(
    mlTrainArgs, repoRoot, signal, setActiveChild,
    (line) => { mlTrainStdout += line; emit({ type: "stdout", command: mlTrainCmd, line }); },
    (line) => emit({ type: "stderr", command: mlTrainCmd, line })
  );
  emit({ type: "command-end", command: mlTrainCmd });

  // --- Step 6: ML categorize (rules + ML fallback) ---
  const cat2Args = [
    "scripts/rule_engine_categorize.py",
    "--tickets-dir", normalizedDir,
    "--rule-engine", localRules,
    "--ml-model", mlModel,
    "--ml-category-map", mlCategoryMap,
    "--output-dir", outputDir,
    "-y"
  ];
  const cat2Cmd = `uv run python3 ${cat2Args.join(" ")}`;
  emit({ type: "command-start", command: cat2Cmd });
  await runCommand(
    cat2Args, repoRoot, signal, setActiveChild,
    (line) => emit({ type: "stdout", command: cat2Cmd, line }),
    (line) => emit({ type: "stderr", command: cat2Cmd, line })
  );
  emit({ type: "command-end", command: cat2Cmd });

  // --- Store partial results for phase 3 ---
  const samplesMatch = mlTrainStdout.match(/Training samples:\s*(\d+)/i);
  const accuracyMatch = mlTrainStdout.match(/Cross-validation accuracy:\s*([\d.]+)/i);

  // --- Pause for human audit ---
  emit({
    type: "paused",
    phase: 2,
    runId,
    paths: { ticketsCsv, outputDir, localRules, mlModel, mlReport },
    partialResult: {
      trainingSamples: samplesMatch ? Number(samplesMatch[1]) : undefined,
      cvAccuracy: accuracyMatch ? accuracyMatch[1] : undefined
    }
  });
}

// ---------------------------------------------------------------------------
// Phase 3: Generate rule proposals → Final re-categorize
// ---------------------------------------------------------------------------
async function runPhase3(
  runId: string,
  outputDir: string,
  meta: PhaseMeta,
  repoRoot: string,
  signal: AbortSignal,
  emit: (event: Record<string, unknown>) => void,
  setActiveChild: (child: ChildProcessWithoutNullStreams | null) => void
) {
  const normalizedBaseDir = path.join(outputDir, "normalized");
  const normalizedDir = path.join(normalizedBaseDir, meta.normalizeDate);
  const localRules = path.join(outputDir, "rule-engine.local.csv");
  const mlModelDir = path.join(outputDir, "ml-model");
  const mlModel = path.join(mlModelDir, "classifier.joblib");
  const mlCategoryMap = path.join(mlModelDir, "category_map.json");
  const mlReport = path.join(mlModelDir, "training_report.txt");
  const ticketsCsv = path.join(outputDir, "tickets-categorized.csv");
  const trainingLog = path.join(outputDir, "run_training_ml.log");

  // --- Step 7: Generate rule proposals (ML engine) ---
  const genRulesArgs = [
    "scripts/run_training.py",
    "--tickets-categorized", ticketsCsv,
    "--rules-engine-file", localRules,
    "--output-rule-engine", localRules,
    "--engine", "ml",
    "--ml-model", mlModel,
    "--ml-category-map", mlCategoryMap,
    "--max-review-rows", String(meta.maxReviewRows),
    "--log-file", trainingLog,
    "-y"
  ];
  const genRulesCmd = `uv run python3 ${genRulesArgs.join(" ")}`;
  emit({ type: "command-start", command: genRulesCmd });
  let genRulesStdout = "";
  await runCommand(
    genRulesArgs, repoRoot, signal, setActiveChild,
    (line) => { genRulesStdout += line; emit({ type: "stdout", command: genRulesCmd, line }); },
    (line) => emit({ type: "stderr", command: genRulesCmd, line })
  );
  emit({ type: "command-end", command: genRulesCmd });

  // --- Step 8: Re-categorize with updated rules + ML ---
  const cat3Args = [
    "scripts/rule_engine_categorize.py",
    "--tickets-dir", normalizedDir,
    "--rule-engine", localRules,
    "--ml-model", mlModel,
    "--ml-category-map", mlCategoryMap,
    "--output-dir", outputDir,
    "-y"
  ];
  const cat3Cmd = `uv run python3 ${cat3Args.join(" ")}`;
  emit({ type: "command-start", command: cat3Cmd });
  await runCommand(
    cat3Args, repoRoot, signal, setActiveChild,
    (line) => emit({ type: "stdout", command: cat3Cmd, line }),
    (line) => emit({ type: "stderr", command: cat3Cmd, line })
  );
  emit({ type: "command-end", command: cat3Cmd });

  // --- Parse results ---
  const rulesAddedMatch = genRulesStdout.match(/Rules added:\s*(\d+)/i);

  emit({
    type: "done",
    runId,
    result: {
      message: "Training pipeline completed.",
      rulesAdded: rulesAddedMatch ? Number(rulesAddedMatch[1]) : undefined,
      ticketsCsv,
      localRules,
      mlModel,
      mlReport,
      trainingLog,
      outputDir
    }
  });
}
