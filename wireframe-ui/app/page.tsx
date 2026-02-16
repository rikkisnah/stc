// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { loadSessionState, clearSessionState, isSessionStale, type SessionState } from "../lib/session-persistence";
import { useSessionPersistence } from "../lib/hooks/useSessionPersistence";

type Stage = "landing" | "input" | "results";
type Workflow =
  | "categorize"
  | "add-rule"
  | "browse-tickets"
  | "browse-categorized"
  | "browse-rules"
  | "browse-ml-model"
  | "train-stc"
  | "promote-to-golden";
type DiffRowStatus = "added" | "removed" | "changed" | "unchanged";
type DiffRow = {
  status: DiffRowStatus;
  ruleId: string;
  sourceRow?: string[];
  targetRow?: string[];
};
type InputMode = "jql" | "files" | "tickets";
type ResolutionMode = "all" | "unresolved-only" | "resolved-only";
type PipelineStepStatus = "pending" | "running" | "done" | "failed";
type SummaryRow = {
  "Tickets Category": string;
  "Percentage of Total Tickets": string;
  "Count of Tickets": string;
  "JQL Query": string;
};
type TicketListItem = {
  key: string;
  summary: string;
  status: string;
  resolution: string;
  sourcePath: string;
  detailPath: string;
  hasRawTicketFile: boolean;
};
type TicketDetailResponse = {
  ticketKey: string;
  sourcePath: string;
  detailPath: string;
  hasRawTicketFile: boolean;
  payload: unknown;
};
type BrowserFileItem = {
  path: string;
  name: string;
  sizeBytes: number;
  modifiedAt: string;
};
type RulesSource = "trained-data" | "golden";
type MlModelSource = "working" | "golden";
type MlModelInfo = {
  exists: boolean;
  sizeBytes: number;
  modifiedAt: string;
  report: string;
  categoryMap: Record<string, string> | null;
};

const PIPELINE_STEPS = [
  "get_tickets.py",
  "normalize_tickets.py",
  "rule_engine_categorize.py",
  "create_summary.py"
] as const;

const ADD_RULE_DEFAULTS = {
  ticketJsonDir: "scripts/tickets-json",
  normalizedRoot: "scripts/normalized-tickets",
  rulesEngine: "scripts/trained-data/rule-engine.local.csv",
  matchFieldDefault: "summary+description",
  priority: "85",
  confidence: "1",
  createdBy: "human-feedback",
  hitCount: "0"
};
const TRAIN_PIPELINE_STEPS = [
  "get_tickets.py",
  "normalize_tickets.py",
  "init local rules",
  "rule_engine_categorize.py (initial)",
  "Human audit #1",
  "ml_train.py",
  "rule_engine_categorize.py (ML)",
  "Human audit #2",
  "run_training.py",
  "rule_engine_categorize.py (final)"
] as const;

const TRAIN_STC_DEFAULTS = {
  trainingData: "scripts/trained-data/ml-training-data.csv",
  minSamples: "20",
  maxReviewRows: "200"
};

const PROMOTE_DEFAULTS = {
  sourcePath: "scripts/trained-data/rule-engine.local.csv",
  targetPath: "scripts/trained-data/golden-rules-engine/rule-engine.csv"
};

const CATEGORIZED_TICKETS_DIR = "scripts/analysis";
const DEFAULT_CATEGORIZED_FILE = "tickets-categorized.csv";
const RULES_SOURCE_DIRS: Record<RulesSource, string> = {
  "trained-data": "scripts/trained-data",
  golden: "scripts/trained-data/golden-rules-engine"
};
const ML_MODEL_SOURCE_DIRS: Record<MlModelSource, string> = {
  working: "scripts/trained-data/ml-model",
  golden: "scripts/trained-data/golden-ml-model"
};

const VALID_WORKFLOWS = new Set<Workflow>([
  "categorize", "add-rule", "browse-tickets", "browse-categorized",
  "browse-rules", "browse-ml-model", "train-stc", "promote-to-golden"
]);

function workflowFromHash(): Workflow {
  if (typeof window === "undefined") return "categorize";
  const hash = window.location.hash.replace("#", "");
  return VALID_WORKFLOWS.has(hash as Workflow) ? (hash as Workflow) : "categorize";
}

export default function HomePage() {
  const [stage, setStage] = useState<Stage>("landing");
  const [workflow, setWorkflowState] = useState<Workflow>("categorize");
  const [inputMode, setInputMode] = useState<InputMode>("jql");
  const [jql, setJql] = useState(
    'project="High Performance Computing" and createdDate >= "2026-02-10" and createdDate <= "2026-02-11"'
  );
  const [resolutionMode, setResolutionMode] = useState<ResolutionMode>("all");
  const [ticketsFile, setTicketsFile] = useState(
    "scripts/analysis/ui-runs/templates/tickets-template.txt"
  );
  const [ticketsText, setTicketsText] = useState("HPC-110621,HPC-110615");
  const [categorizeRulesEngine, setCategorizeRulesEngine] = useState(
    "scripts/trained-data/golden-rules-engine/rule-engine.csv"
  );
  const [categorizeMlModel, setCategorizeMlModel] = useState(
    "scripts/trained-data/golden-ml-model/classifier.joblib"
  );
  const [categorizeMlCategoryMap, setCategorizeMlCategoryMap] = useState(
    "scripts/trained-data/golden-ml-model/category_map.json"
  );
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");
  const [summaryRows, setSummaryRows] = useState<SummaryRow[]>([]);
  const [addRuleResult, setAddRuleResult] = useState<{
    ruleId?: string;
    rulesEngine?: string;
    ticketJson?: string;
    normalizedJson?: string;
    message?: string;
  }>({});
  const [executedCommands, setExecutedCommands] = useState<string[]>([]);
  const [commandLogs, setCommandLogs] = useState<string[]>([]);
  const [resultPaths, setResultPaths] = useState<{
    ticketsCsv?: string;
    summaryCsv?: string;
    normalizedDir?: string;
  }>({});
  const [startedAt, setStartedAt] = useState<string>("");
  const [finishedAt, setFinishedAt] = useState<string>("");
  const [elapsedMs, setElapsedMs] = useState<number>(0);
  const [wasCanceled, setWasCanceled] = useState(false);
  const [copyStatus, setCopyStatus] = useState<string>("");
  const [liveElapsedMs, setLiveElapsedMs] = useState<number>(0);
  const [lastLogAtMs, setLastLogAtMs] = useState<number | null>(null);
  const [heartbeatTick, setHeartbeatTick] = useState(0);
  const [renderedAt, setRenderedAt] = useState("-");
  const [wrapLogs, setWrapLogs] = useState(true);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStepStatus[]>(
    PIPELINE_STEPS.map(() => "pending")
  );
  const [ticketKey, setTicketKey] = useState("");
  const [reason, setReason] = useState("");
  const [failureCategory, setFailureCategory] = useState("");
  const [category, setCategory] = useState("");
  const [matchField, setMatchField] = useState("");
  const [rulePattern, setRulePattern] = useState("");
  const [ticketJsonDir, setTicketJsonDir] = useState(ADD_RULE_DEFAULTS.ticketJsonDir);
  const [normalizedRoot, setNormalizedRoot] = useState(ADD_RULE_DEFAULTS.normalizedRoot);
  const [rulesEngine, setRulesEngine] = useState(ADD_RULE_DEFAULTS.rulesEngine);
  const [matchFieldDefault, setMatchFieldDefault] = useState(ADD_RULE_DEFAULTS.matchFieldDefault);
  const [priority, setPriority] = useState(ADD_RULE_DEFAULTS.priority);
  const [confidence, setConfidence] = useState(ADD_RULE_DEFAULTS.confidence);
  const [createdBy, setCreatedBy] = useState(ADD_RULE_DEFAULTS.createdBy);
  const [hitCount, setHitCount] = useState(ADD_RULE_DEFAULTS.hitCount);
  const [ticketList, setTicketList] = useState<TicketListItem[]>([]);
  const [ticketListLoading, setTicketListLoading] = useState(false);
  const [ticketListError, setTicketListError] = useState("");
  const [ticketListLoadedDir, setTicketListLoadedDir] = useState("");
  const [ticketListExpanded, setTicketListExpanded] = useState(false);
  const [ticketFilter, setTicketFilter] = useState("");
  const [ticketDetail, setTicketDetail] = useState<TicketDetailResponse | null>(null);
  const [ticketDetailLoading, setTicketDetailLoading] = useState(false);
  const [ticketDetailError, setTicketDetailError] = useState("");
  const [ticketDetailCopyStatus, setTicketDetailCopyStatus] = useState("");
  const [categorizedFiles, setCategorizedFiles] = useState<BrowserFileItem[]>([]);
  const [categorizedFilesLoading, setCategorizedFilesLoading] = useState(false);
  const [categorizedFilesError, setCategorizedFilesError] = useState("");
  const [categorizedDir, setCategorizedDir] = useState(CATEGORIZED_TICKETS_DIR);
  const [categorizedFileName, setCategorizedFileName] = useState(DEFAULT_CATEGORIZED_FILE);
  const [categorizedLoadedDir, setCategorizedLoadedDir] = useState("");
  const [categorizedLoadedFileName, setCategorizedLoadedFileName] = useState("");
  const [categorizedFilter, setCategorizedFilter] = useState("");
  const [categorizedSelectedPath, setCategorizedSelectedPath] = useState("");
  const [categorizedPreview, setCategorizedPreview] = useState("");
  const [categorizedEditorText, setCategorizedEditorText] = useState("");
  const [categorizedTableRows, setCategorizedTableRows] = useState<string[][]>([]);
  const [categorizedTableError, setCategorizedTableError] = useState("");
  const [categorizedPreviewLoading, setCategorizedPreviewLoading] = useState(false);
  const [categorizedPreviewError, setCategorizedPreviewError] = useState("");
  const [categorizedCopyStatus, setCategorizedCopyStatus] = useState("");
  const [categorizedSaveStatus, setCategorizedSaveStatus] = useState("");
  const [categorizedSaving, setCategorizedSaving] = useState(false);
  const [categorizedScrollLeft, setCategorizedScrollLeft] = useState(0);
  const [categorizedScrollMax, setCategorizedScrollMax] = useState(0);
  const categorizedGridShellRef = useRef<HTMLDivElement | null>(null);
  const categorizedGridTopScrollRef = useRef<HTMLDivElement | null>(null);
  const categorizedGridTopSpacerRef = useRef<HTMLDivElement | null>(null);
  const categorizedScrollSyncRef = useRef<"top" | "body" | null>(null);
  const [rulesSource, setRulesSource] = useState<RulesSource>("trained-data");
  const [rulesFiles, setRulesFiles] = useState<BrowserFileItem[]>([]);
  const [rulesFilesLoading, setRulesFilesLoading] = useState(false);
  const [rulesFilesError, setRulesFilesError] = useState("");
  const [rulesLoadedDir, setRulesLoadedDir] = useState("");
  const [rulesFilter, setRulesFilter] = useState("");
  const [rulesSelectedPath, setRulesSelectedPath] = useState("");
  const [rulesPreview, setRulesPreview] = useState("");
  const [rulesPreviewLoading, setRulesPreviewLoading] = useState(false);
  const [rulesPreviewError, setRulesPreviewError] = useState("");
  const [rulesCopyStatus, setRulesCopyStatus] = useState("");
  const [rulesTableRows, setRulesTableRows] = useState<string[][]>([]);
  const [rulesTableError, setRulesTableError] = useState("");
  const [rulesEditorText, setRulesEditorText] = useState("");
  const [rulesSaving, setRulesSaving] = useState(false);
  const [rulesSaveStatus, setRulesSaveStatus] = useState("");
  const [rulesScrollLeft, setRulesScrollLeft] = useState(0);
  const [rulesScrollMax, setRulesScrollMax] = useState(0);
  const rulesGridShellRef = useRef<HTMLDivElement | null>(null);
  const rulesGridTopScrollRef = useRef<HTMLDivElement | null>(null);
  const rulesGridTopSpacerRef = useRef<HTMLDivElement | null>(null);
  const rulesScrollSyncRef = useRef<"top" | "body" | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const logBlockRef = useRef<HTMLPreElement | null>(null);

  // --- Train STC state ---
  const [trainInputMode, setTrainInputMode] = useState<InputMode>("jql");
  const [trainJql, setTrainJql] = useState(
    'project="High Performance Computing" and createdDate >= "2026-02-10" and createdDate <= "2026-02-11"'
  );
  const [trainResolutionMode, setTrainResolutionMode] = useState<ResolutionMode>("resolved-only");
  const [trainTicketsFile, setTrainTicketsFile] = useState(
    "scripts/analysis/ui-runs/templates/tickets-template.txt"
  );
  const [trainTicketsText, setTrainTicketsText] = useState("HPC-110621,HPC-110615");
  const [trainTrainingData, setTrainTrainingData] = useState(TRAIN_STC_DEFAULTS.trainingData);
  const [trainMinSamples, setTrainMinSamples] = useState(TRAIN_STC_DEFAULTS.minSamples);
  const [trainMaxReviewRows, setTrainMaxReviewRows] = useState(TRAIN_STC_DEFAULTS.maxReviewRows);
  const [trainStcResult, setTrainStcResult] = useState<{
    message?: string;
    trainingSamples?: number;
    cvAccuracy?: string;
    rulesAdded?: number;
    ticketsCsv?: string;
    localRules?: string;
    mlModel?: string;
    mlReport?: string;
    trainingLog?: string;
    outputDir?: string;
  }>({});
  const [trainStcPipelineStatus, setTrainStcPipelineStatus] = useState<PipelineStepStatus[]>([]);
  const [trainPhase, setTrainPhase] = useState<1 | 2 | 3>(1);
  const [trainRunId, setTrainRunId] = useState("");
  const [trainPaused, setTrainPaused] = useState(false);
  const [skipAudit1, setSkipAudit1] = useState(true);
  const [skipAudit2, setSkipAudit2] = useState(true);
  const [trainAuditCsvPath, setTrainAuditCsvPath] = useState("");
  const [trainAuditRows, setTrainAuditRows] = useState<string[][]>([]);
  const [trainAuditOriginal, setTrainAuditOriginal] = useState("");
  const [trainAuditSaving, setTrainAuditSaving] = useState(false);
  const [trainAuditSaveStatus, setTrainAuditSaveStatus] = useState("");

  // --- Promote to Golden state ---
  const [promoteSourcePath, setPromoteSourcePath] = useState(PROMOTE_DEFAULTS.sourcePath);
  const [promoteTargetPath, setPromoteTargetPath] = useState(PROMOTE_DEFAULTS.targetPath);
  const [promoteSourceText, setPromoteSourceText] = useState("");
  const [promoteTargetText, setPromoteTargetText] = useState("");
  const [promoteHeaders, setPromoteHeaders] = useState<string[]>([]);
  const [promoteDiff, setPromoteDiff] = useState<DiffRow[]>([]);
  const [promoteLoading, setPromoteLoading] = useState(false);
  const [promoteError, setPromoteError] = useState("");
  const [promoteConfirming, setPromoteConfirming] = useState(false);
  const [promoteSaving, setPromoteSaving] = useState(false);
  const [promoteResult, setPromoteResult] = useState("");
  const [promoteShowUnchanged, setPromoteShowUnchanged] = useState(false);

  // --- Promote ML Model state ---
  const [mlSourceDir, setMlSourceDir] = useState("scripts/trained-data/ml-model");
  const [mlTargetDir, setMlTargetDir] = useState("scripts/trained-data/golden-ml-model");
  const [mlPromoteLoading, setMlPromoteLoading] = useState(false);
  const [mlPromoteError, setMlPromoteError] = useState("");
  const [mlPromoteResult, setMlPromoteResult] = useState("");
  const [mlPromoteSaving, setMlPromoteSaving] = useState(false);
  const [mlPromoteConfirming, setMlPromoteConfirming] = useState(false);
  const [mlCompare, setMlCompare] = useState<{
    working: { exists: boolean; sizeBytes: number; modifiedAt: string; report: string };
    golden: { exists: boolean; sizeBytes: number; modifiedAt: string; report: string };
    identical: boolean;
  } | null>(null);

  // --- Browse ML Model state ---
  const [mlViewSource, setMlViewSource] = useState<MlModelSource>("golden");
  const [mlViewLoading, setMlViewLoading] = useState(false);
  const [mlViewError, setMlViewError] = useState("");
  const [mlViewData, setMlViewData] = useState<{
    working: MlModelInfo;
    golden: MlModelInfo;
    identical: boolean;
  } | null>(null);
  const [mlViewMode, setMlViewMode] = useState<"single" | "compare">("single");

  function formatBytes(bytes: number): string {
    if (bytes === 0) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  function formatTimestamp(iso: string): string {
    if (!iso) {
      return "-";
    }
    return new Date(iso).toLocaleString();
  }

  function nowTime(): string {
    return new Date().toLocaleTimeString();
  }

  function toDisplayFolderPath(filePath: string): string {
    const normalized = filePath.replace(/\\/g, "/");
    const scriptsIndex = normalized.lastIndexOf("/scripts/");
    const displayPath = scriptsIndex >= 0 ? normalized.slice(scriptsIndex + 1) : normalized;
    const lastSlash = displayPath.lastIndexOf("/");
    if (lastSlash <= 0) {
      return displayPath;
    }
    return displayPath.slice(0, lastSlash);
  }

  function parseCsvRows(text: string): string[][] {
    const rows: string[][] = [];
    let currentRow: string[] = [];
    let currentCell = "";
    let inQuotes = false;

    for (let index = 0; index < text.length; index += 1) {
      const ch = text[index];
      if (inQuotes) {
        if (ch === "\"") {
          if (text[index + 1] === "\"") {
            currentCell += "\"";
            index += 1;
          } else {
            inQuotes = false;
          }
        } else {
          currentCell += ch;
        }
        continue;
      }

      if (ch === "\"") {
        inQuotes = true;
        continue;
      }
      if (ch === ",") {
        currentRow.push(currentCell);
        currentCell = "";
        continue;
      }
      if (ch === "\n") {
        currentRow.push(currentCell);
        rows.push(currentRow);
        currentRow = [];
        currentCell = "";
        continue;
      }
      if (ch === "\r") {
        if (text[index + 1] === "\n") {
          index += 1;
        }
        currentRow.push(currentCell);
        rows.push(currentRow);
        currentRow = [];
        currentCell = "";
        continue;
      }
      currentCell += ch;
    }

    if (inQuotes) {
      throw new Error("CSV parse error: unterminated quoted field.");
    }
    if (currentCell || currentRow.length > 0 || rows.length === 0) {
      currentRow.push(currentCell);
      rows.push(currentRow);
    }
    return rows;
  }

  function csvEscapeCell(value: string): string {
    if (!/[",\r\n]/.test(value) && !/^\s|\s$/.test(value)) {
      return value;
    }
    return `"${value.replace(/"/g, "\"\"")}"`;
  }

  function serializeCsvRows(rows: string[][]): string {
    return rows.map((row) => row.map((cell) => csvEscapeCell(cell || "")).join(",")).join("\n");
  }

  function validateJql(query: string): string | null {
    const trimmed = query.trim();
    if (!trimmed) {
      return "JQL cannot be empty.";
    }

    // Guard against a common typo: `created "YYYY-MM-DD"` / `createdDate "YYYY-MM-DD"` without operator.
    if (/\b(created|createdDate)\s+"[\d-]+"\b/i.test(trimmed)) {
      return 'Invalid JQL near "created/createdDate". Use an operator, e.g. createdDate >= "YYYY-MM-DD".';
    }

    return null;
  }

  const setWorkflow = useCallback((w: Workflow) => {
    setWorkflowState(w);
    window.history.replaceState(null, "", `#${w}`);
  }, []);

  useEffect(() => {
    const initial = workflowFromHash();
    setWorkflowState(initial);
    if (window.location.hash) setStage("input");
    const onHashChange = () => {
      if (abortRef.current) {
        const leave = window.confirm("A training run is in progress. Leaving will cancel it. Continue?");
        if (!leave) {
          window.history.replaceState(null, "", `#train-stc`);
          return;
        }
        abortRef.current.abort();
      }
      setWorkflowState(workflowFromHash());
      setStage("input");
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    setRenderedAt(new Date().toLocaleString());
  }, []);

  // --- Session restore on mount ---
  useEffect(() => {
    const saved = loadSessionState();
    if (!saved || isSessionStale(saved)) {
      if (saved) clearSessionState();
      return;
    }
    if (!saved.isRunning && !saved.trainRunId) return;
    const shouldRestore = window.confirm(
      `An interrupted training session was found (run: ${saved.trainRunId}, phase ${saved.trainPhase}). Restore the session state?`
    );
    if (!shouldRestore) {
      clearSessionState();
      return;
    }
    setWorkflowState("train-stc");
    setStage("results");
    setTrainRunId(saved.trainRunId);
    setTrainPhase(saved.trainPhase);
    setStartedAt(saved.startedAt);
    setElapsedMs(saved.elapsedMs);
    setTrainStcPipelineStatus(saved.pipelineStatus as PipelineStepStatus[]);
    setResultPaths(saved.resultPaths);
    setTrainStcResult(saved.trainStcResult);
    setError(saved.error);
    setWasCanceled(saved.wasCanceled);
    if (saved.executedCommandsCount > 0 && saved.lastCommandSnippet) {
      setExecutedCommands([`... ${saved.executedCommandsCount} commands (restored). Last: ${saved.lastCommandSnippet}`]);
    }
  }, []);

  // --- Auto-save session state for train-stc ---
  useSessionPersistence(useCallback((): SessionState | null => {
    if (workflow !== "train-stc" || (!isRunning && !trainRunId)) return null;
    return {
      schemaVersion: 1,
      workflow: "train-stc",
      trainRunId,
      trainPhase,
      isRunning,
      startedAt,
      elapsedMs,
      pipelineStatus: trainStcPipelineStatus,
      resultPaths,
      trainStcResult,
      error,
      wasCanceled,
      executedCommandsCount: executedCommands.length,
      lastCommandSnippet: executedCommands.length > 0 ? executedCommands[executedCommands.length - 1].slice(0, 200) : "",
      savedAt: Date.now(),
    };
  }, [workflow, isRunning, trainRunId, trainPhase, startedAt, elapsedMs, trainStcPipelineStatus, resultPaths, trainStcResult, error, wasCanceled, executedCommands]));

  // --- Warn before leaving during active training ---
  const isTrainingActive = isRunning && workflow === "train-stc";
  useEffect(() => {
    if (!isTrainingActive) return;
    const handler = (e: BeforeUnloadEvent) => { e.preventDefault(); };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isTrainingActive]);

  useEffect(() => {
    if (!isRunning || !startedAt) {
      return;
    }

    const timer = window.setInterval(() => {
      const nowMs = Date.now();
      setLiveElapsedMs(Math.max(0, nowMs - Date.parse(startedAt)));
      setHeartbeatTick((prev) => prev + 1);
    }, 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, [isRunning, startedAt]);

  useEffect(() => {
    const el = logBlockRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [commandLogs]);

  async function loadTicketList(dirOverride?: string) {
    const directory = (dirOverride || normalizedRoot).trim();
    if (!directory) {
      setTicketList([]);
      setTicketDetail(null);
      setTicketListLoadedDir("");
      setTicketListError("Normalized root is required.");
      return;
    }

    setTicketListLoading(true);
    setTicketListError("");
    setTicketDetailError("");
    setTicketDetailCopyStatus("");

    try {
      const response = await fetch(`/api/tickets-json?dir=${encodeURIComponent(directory)}`);
      const data = (await response.json()) as { error?: string; tickets?: TicketListItem[] };
      if (!response.ok) {
        throw new Error(data.error || "Failed to load ticket list.");
      }
      setTicketList(data.tickets || []);
      setTicketListLoadedDir(directory);
    } catch (ticketError) {
      const message =
        ticketError instanceof Error ? ticketError.message : "Failed to load ticket list.";
      setTicketList([]);
      setTicketDetail(null);
      setTicketListError(message);
    } finally {
      setTicketListLoading(false);
    }
  }

  async function loadTicketDetail(ticket: string, dirOverride?: string) {
    const ticketKeyToLoad = ticket.trim().toUpperCase();
    if (!/^[A-Z]+-\d+$/.test(ticketKeyToLoad)) {
      setTicketDetail(null);
      setTicketDetailError("");
      setTicketDetailCopyStatus("");
      return;
    }

    const directory = (dirOverride || normalizedRoot).trim();
    if (!directory) {
      setTicketDetail(null);
      setTicketDetailError("Normalized root is required.");
      setTicketDetailCopyStatus("");
      return;
    }

    setTicketDetailLoading(true);
    setTicketDetailError("");
    setTicketDetailCopyStatus("");

    try {
      const response = await fetch(
        `/api/tickets-json?dir=${encodeURIComponent(directory)}&ticketKey=${encodeURIComponent(ticketKeyToLoad)}`
      );
      const data = (await response.json()) as TicketDetailResponse & { error?: string };
      if (!response.ok) {
        throw new Error(data.error || `Ticket ${ticketKeyToLoad} not found.`);
      }
      setTicketDetail(data);
    } catch (ticketError) {
      const message =
        ticketError instanceof Error ? ticketError.message : "Failed to load ticket details.";
      setTicketDetail(null);
      setTicketDetailError(message);
    } finally {
      setTicketDetailLoading(false);
    }
  }

  async function readJsonError(response: Response, fallbackMessage: string): Promise<string> {
    try {
      const payload = (await response.json()) as { error?: string };
      return payload.error || fallbackMessage;
    } catch {
      return fallbackMessage;
    }
  }

  async function loadCategorizedFiles(dirOverride?: string, fileNameOverride?: string) {
    const directory = (dirOverride || categorizedDir).trim() || CATEGORIZED_TICKETS_DIR;
    const exactFileName =
      typeof fileNameOverride === "string" ? fileNameOverride.trim() : categorizedFileName.trim();

    setCategorizedFilesLoading(true);
    setCategorizedFilesError("");
    setCategorizedCopyStatus("");
    setCategorizedSaveStatus("");
    setCategorizedPreviewError("");

    try {
      const query = new URLSearchParams({
        dir: directory,
        extensions: "csv",
        limit: "500"
      });
      if (exactFileName) {
        query.set("nameExact", exactFileName);
      }
      const response = await fetch(`/api/list-files?${query.toString()}`);
      const data = (await response.json()) as { error?: string; files?: BrowserFileItem[] };
      if (!response.ok) {
        throw new Error(data.error || "Failed to load categorized ticket files.");
      }
      const files = data.files || [];
      setCategorizedFiles(files);
      setCategorizedLoadedDir(directory);
      setCategorizedLoadedFileName(exactFileName);
      if (!files.some((file) => file.path === categorizedSelectedPath)) {
        setCategorizedSelectedPath("");
        setCategorizedPreview("");
        setCategorizedEditorText("");
        setCategorizedTableRows([]);
        setCategorizedTableError("");
        setCategorizedPreviewError("");
      }
    } catch (loadError) {
      const message =
        loadError instanceof Error ? loadError.message : "Failed to load categorized ticket files.";
      setCategorizedFiles([]);
      setCategorizedLoadedDir(directory);
      setCategorizedLoadedFileName(exactFileName);
      setCategorizedSelectedPath("");
      setCategorizedPreview("");
      setCategorizedEditorText("");
      setCategorizedTableRows([]);
      setCategorizedTableError("");
      setCategorizedPreviewError("");
      setCategorizedFilesError(message);
    } finally {
      setCategorizedFilesLoading(false);
    }
  }

  async function loadCategorizedPreview(filePath: string) {
    setCategorizedSelectedPath(filePath);
    setCategorizedPreviewLoading(true);
    setCategorizedPreviewError("");
    setCategorizedCopyStatus("");
    setCategorizedSaveStatus("");

    try {
      const response = await fetch(`/api/open-file?path=${encodeURIComponent(filePath)}`);
      if (!response.ok) {
        const message = await readJsonError(response, "Failed to load categorized ticket file.");
        throw new Error(message);
      }
      const content = await response.text();
      setCategorizedPreview(content);
      setCategorizedEditorText(content);
      try {
        setCategorizedTableRows(parseCsvRows(content));
        setCategorizedTableError("");
      } catch (csvError) {
        setCategorizedTableRows([]);
        const message =
          csvError instanceof Error ? csvError.message : "CSV parse error.";
        setCategorizedTableError(message);
      }
    } catch (loadError) {
      const message =
        loadError instanceof Error ? loadError.message : "Failed to load categorized ticket file.";
      setCategorizedPreview("");
      setCategorizedEditorText("");
      setCategorizedTableRows([]);
      setCategorizedTableError("");
      setCategorizedPreviewError(message);
    } finally {
      setCategorizedPreviewLoading(false);
    }
  }

  async function saveCategorizedFile() {
    if (!categorizedSelectedPath) {
      setCategorizedSaveStatus("Select a file before saving.");
      return;
    }

    setCategorizedSaving(true);
    setCategorizedSaveStatus("");
    const contentToSave = categorizedTableRows.length > 0
      ? serializeCsvRows(categorizedTableRows)
      : categorizedEditorText;

    try {
      const response = await fetch("/api/save-file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: categorizedSelectedPath,
          content: contentToSave
        })
      });
      if (!response.ok) {
        const message = await readJsonError(response, "Failed to save categorized ticket file.");
        throw new Error(message);
      }
      setCategorizedPreview(contentToSave);
      setCategorizedEditorText(contentToSave);
      if (categorizedLoadedDir) {
        await loadCategorizedFiles(categorizedLoadedDir, categorizedLoadedFileName);
      }
      setCategorizedSaveStatus("File saved.");
    } catch (saveError) {
      const message =
        saveError instanceof Error ? saveError.message : "Failed to save categorized ticket file.";
      setCategorizedSaveStatus(message);
    } finally {
      setCategorizedSaving(false);
    }
  }

  const rulesDirectory = RULES_SOURCE_DIRS[rulesSource];

  async function loadRulesFiles(dirOverride?: string) {
    const directory = (dirOverride || rulesDirectory).trim();
    setRulesFilesLoading(true);
    setRulesFilesError("");
    setRulesCopyStatus("");
    setRulesSaveStatus("");
    setRulesPreviewError("");

    try {
      const response = await fetch(
        `/api/list-files?dir=${encodeURIComponent(directory)}&extensions=csv&nameContains=rule-engine&limit=500`
      );
      const data = (await response.json()) as { error?: string; files?: BrowserFileItem[] };
      if (!response.ok) {
        throw new Error(data.error || "Failed to load rule engine files.");
      }
      const files = data.files || [];
      setRulesFiles(files);
      setRulesLoadedDir(directory);
      if (!files.some((file) => file.path === rulesSelectedPath)) {
        setRulesSelectedPath("");
        setRulesPreview("");
        setRulesEditorText("");
        setRulesTableRows([]);
        setRulesTableError("");
        setRulesPreviewError("");
      }
    } catch (loadError) {
      const message =
        loadError instanceof Error ? loadError.message : "Failed to load rule engine files.";
      setRulesFiles([]);
      setRulesSelectedPath("");
      setRulesPreview("");
      setRulesEditorText("");
      setRulesTableRows([]);
      setRulesTableError("");
      setRulesPreviewError("");
      setRulesFilesError(message);
    } finally {
      setRulesFilesLoading(false);
    }
  }

  async function loadRulesPreview(filePath: string) {
    setRulesSelectedPath(filePath);
    setRulesPreviewLoading(true);
    setRulesPreviewError("");
    setRulesCopyStatus("");
    setRulesSaveStatus("");

    try {
      const response = await fetch(`/api/open-file?path=${encodeURIComponent(filePath)}`);
      if (!response.ok) {
        const message = await readJsonError(response, "Failed to load rule engine file.");
        throw new Error(message);
      }
      const content = await response.text();
      setRulesPreview(content);
      setRulesEditorText(content);
      try {
        setRulesTableRows(parseCsvRows(content));
        setRulesTableError("");
      } catch (csvError) {
        setRulesTableRows([]);
        const csvMessage =
          csvError instanceof Error ? csvError.message : "CSV parse error.";
        setRulesTableError(csvMessage);
      }
    } catch (loadError) {
      const message =
        loadError instanceof Error ? loadError.message : "Failed to load rule engine file.";
      setRulesPreview("");
      setRulesEditorText("");
      setRulesTableRows([]);
      setRulesTableError("");
      setRulesPreviewError(message);
    } finally {
      setRulesPreviewLoading(false);
    }
  }

  async function saveRulesFile() {
    if (!rulesSelectedPath) {
      setRulesSaveStatus("Select a file before saving.");
      return;
    }

    setRulesSaving(true);
    setRulesSaveStatus("");
    const contentToSave = rulesTableRows.length > 0
      ? serializeCsvRows(rulesTableRows)
      : rulesEditorText;

    try {
      const response = await fetch("/api/save-file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: rulesSelectedPath,
          content: contentToSave
        })
      });
      if (!response.ok) {
        const message = await readJsonError(response, "Failed to save rule engine file.");
        throw new Error(message);
      }
      setRulesPreview(contentToSave);
      setRulesEditorText(contentToSave);
      if (rulesLoadedDir) {
        await loadRulesFiles(rulesLoadedDir);
      }
      setRulesSaveStatus("File saved.");
    } catch (saveError) {
      const message =
        saveError instanceof Error ? saveError.message : "Failed to save rule engine file.";
      setRulesSaveStatus(message);
    } finally {
      setRulesSaving(false);
    }
  }

  useEffect(() => {
    if (workflow !== "browse-tickets" || stage !== "input") {
      return;
    }
    const directory = normalizedRoot.trim();
    if (!directory || directory === ticketListLoadedDir) {
      return;
    }
    void loadTicketList(directory);
  }, [workflow, stage, normalizedRoot, ticketListLoadedDir]);

  useEffect(() => {
    if (workflow !== "browse-tickets" || stage !== "input") {
      return;
    }
    const normalized = ticketKey.trim().toUpperCase();
    if (!/^[A-Z]+-\d+$/.test(normalized)) {
      setTicketDetail(null);
      setTicketDetailError("");
      return;
    }
    if (!ticketList.some((ticket) => ticket.key === normalized)) {
      return;
    }
    if (ticketDetail?.ticketKey === normalized) {
      return;
    }
    void loadTicketDetail(normalized);
  }, [workflow, stage, ticketKey, ticketList, ticketDetail?.ticketKey, normalizedRoot]);

  useEffect(() => {
    if (workflow !== "browse-categorized" || stage !== "input") {
      return;
    }
    if (categorizedLoadedDir) {
      return;
    }
    void loadCategorizedFiles();
  }, [workflow, stage, categorizedLoadedDir]);

  useEffect(() => {
    if (workflow !== "browse-rules" || stage !== "input") {
      return;
    }
    if (rulesLoadedDir === rulesDirectory) {
      return;
    }
    void loadRulesFiles(rulesDirectory);
  }, [workflow, stage, rulesLoadedDir, rulesDirectory]);

  async function loadMlModelInfo() {
    setMlViewLoading(true);
    setMlViewError("");
    setMlViewData(null);
    try {
      const params = new URLSearchParams({
        source: ML_MODEL_SOURCE_DIRS.working,
        target: ML_MODEL_SOURCE_DIRS.golden
      });
      const resp = await fetch(`/api/promote-ml-model?${params}`);
      if (!resp.ok) throw new Error(`Failed to load ML model info: ${resp.statusText}`);
      setMlViewData(await resp.json());
    } catch (err) {
      setMlViewError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setMlViewLoading(false);
    }
  }

  useEffect(() => {
    if (workflow !== "browse-ml-model" || stage !== "input") return;
    if (mlViewData) return;
    void loadMlModelInfo();
  }, [workflow, stage, mlViewData]);

  // Auto-skip human audit when the corresponding skip flag is enabled
  useEffect(() => {
    if (!trainPaused) return;
    const shouldSkip =
      (trainPhase === 1 && skipAudit1) || (trainPhase === 2 && skipAudit2);
    if (shouldSkip) {
      handleContinueTraining();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trainPaused]);

  async function loadPromoteDiff() {
    setPromoteLoading(true);
    setPromoteError("");
    setPromoteDiff([]);
    setPromoteHeaders([]);
    setPromoteResult("");
    setPromoteConfirming(false);
    setPromoteShowUnchanged(false);

    try {
      const [sourceResp, targetResp] = await Promise.all([
        fetch(`/api/open-file?path=${encodeURIComponent(promoteSourcePath)}`),
        fetch(`/api/open-file?path=${encodeURIComponent(promoteTargetPath)}`)
      ]);
      if (!sourceResp.ok) {
        throw new Error(`Failed to load source: ${sourceResp.statusText}`);
      }
      if (!targetResp.ok) {
        throw new Error(`Failed to load target: ${targetResp.statusText}`);
      }
      const sourceText = await sourceResp.text();
      const targetText = await targetResp.text();
      setPromoteSourceText(sourceText);
      setPromoteTargetText(targetText);

      const sourceRows = parseCsvRows(sourceText);
      const targetRows = parseCsvRows(targetText);
      if (sourceRows.length === 0) {
        throw new Error("Source CSV is empty.");
      }
      if (targetRows.length === 0) {
        throw new Error("Target CSV is empty.");
      }

      const headers = sourceRows[0];
      setPromoteHeaders(headers);
      const ruleIdIdx = headers.findIndex((h) => h.trim().toLowerCase() === "ruleid");
      const idCol = ruleIdIdx >= 0 ? ruleIdIdx : 1;

      const sourceMap = new Map<string, string[]>();
      for (let i = 1; i < sourceRows.length; i++) {
        const row = sourceRows[i];
        if (row.every((c) => !c.trim())) continue;
        const id = (row[idCol] || "").trim();
        if (id) sourceMap.set(id, row);
      }
      const targetMap = new Map<string, string[]>();
      for (let i = 1; i < targetRows.length; i++) {
        const row = targetRows[i];
        if (row.every((c) => !c.trim())) continue;
        const id = (row[idCol] || "").trim();
        if (id) targetMap.set(id, row);
      }

      const diff: DiffRow[] = [];
      for (const [id, sRow] of sourceMap) {
        const tRow = targetMap.get(id);
        if (!tRow) {
          diff.push({ status: "added", ruleId: id, sourceRow: sRow });
        } else if (sRow.join(",") !== tRow.join(",")) {
          diff.push({ status: "changed", ruleId: id, sourceRow: sRow, targetRow: tRow });
        } else {
          diff.push({ status: "unchanged", ruleId: id, sourceRow: sRow, targetRow: tRow });
        }
      }
      for (const [id, tRow] of targetMap) {
        if (!sourceMap.has(id)) {
          diff.push({ status: "removed", ruleId: id, targetRow: tRow });
        }
      }

      diff.sort((a, b) => {
        const order: Record<DiffRowStatus, number> = { added: 0, changed: 1, removed: 2, unchanged: 3 };
        return order[a.status] - order[b.status];
      });
      setPromoteDiff(diff);
    } catch (err) {
      setPromoteError(err instanceof Error ? err.message : "Unknown error loading diff.");
    } finally {
      setPromoteLoading(false);
    }
  }

  async function handlePromote() {
    setPromoteSaving(true);
    setPromoteResult("");
    try {
      const resp = await fetch("/api/save-file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: promoteTargetPath, content: promoteSourceText })
      });
      if (!resp.ok) {
        const data = (await resp.json()) as { error?: string };
        throw new Error(data.error || "Failed to save.");
      }
      setPromoteResult("Golden rules updated successfully.");
      setPromoteConfirming(false);
    } catch (err) {
      setPromoteResult(`Promotion failed: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setPromoteSaving(false);
    }
  }

  async function loadMlCompare() {
    setMlPromoteLoading(true);
    setMlPromoteError("");
    setMlCompare(null);
    setMlPromoteResult("");
    setMlPromoteConfirming(false);
    try {
      const params = new URLSearchParams({ source: mlSourceDir, target: mlTargetDir });
      const resp = await fetch(`/api/promote-ml-model?${params}`);
      if (!resp.ok) throw new Error(`Failed to load ML model info: ${resp.statusText}`);
      setMlCompare(await resp.json());
    } catch (err) {
      setMlPromoteError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setMlPromoteLoading(false);
    }
  }

  async function handleMlPromote() {
    setMlPromoteSaving(true);
    setMlPromoteResult("");
    try {
      const resp = await fetch("/api/promote-ml-model", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: mlSourceDir, target: mlTargetDir }),
      });
      const data = (await resp.json()) as { error?: string; message?: string };
      if (!resp.ok) throw new Error(data.error || "Failed to promote.");
      setMlPromoteResult(data.message || "ML model promoted to golden successfully.");
      setMlPromoteConfirming(false);
      setMlCompare(null);
    } catch (err) {
      setMlPromoteResult(`Promotion failed: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setMlPromoteSaving(false);
    }
  }

  async function handleOk() {
    if (workflow === "categorize") {
      if (inputMode === "jql") {
        const jqlError = validateJql(jql);
        if (jqlError) {
          setError(jqlError);
          setStage("input");
          return;
        }
      } else if (inputMode === "files" && !ticketsFile.trim()) {
        setError("Ticket list file path is required.");
        setStage("input");
        return;
      } else if (inputMode === "tickets" && !ticketsText.trim()) {
        setError("Ticket list is required.");
        setStage("input");
        return;
      }
    } else if (workflow === "add-rule") {
      const normalizedTicketKey = ticketKey.trim().toUpperCase();
      if (!normalizedTicketKey) {
        setError("Ticket key is required.");
        setStage("input");
        return;
      }
      if (!/^[A-Z]+-\d+$/.test(normalizedTicketKey)) {
        setError("Ticket key must match format like HPC-123456.");
        setStage("input");
        return;
      }
      if (!reason.trim()) {
        setError("Reason is required.");
        setStage("input");
        return;
      }
      if (!failureCategory.trim()) {
        setError("Category of Issue is required.");
        setStage("input");
        return;
      }
      if (!category.trim()) {
        setError("Category is required.");
        setStage("input");
        return;
      }
      if (!ticketJsonDir.trim() || !normalizedRoot.trim() || !rulesEngine.trim()) {
        setError("Ticket JSON dir, normalized root, and rules engine are required.");
        setStage("input");
        return;
      }
      if (!matchFieldDefault.trim() || !createdBy.trim()) {
        setError("Match Field default and Created By are required.");
        setStage("input");
        return;
      }
      if (!Number.isInteger(Number(priority))) {
        setError("Priority must be an integer.");
        setStage("input");
        return;
      }
      if (Number.isNaN(Number(confidence))) {
        setError("Confidence must be numeric.");
        setStage("input");
        return;
      }
      if (!Number.isInteger(Number(hitCount))) {
        setError("Hit Count must be an integer.");
        setStage("input");
        return;
      }
    } else if (workflow === "train-stc") {
      if (trainInputMode === "jql" && !trainJql.trim()) {
        setError("JQL query is required.");
        setStage("input");
        return;
      }
      if (trainInputMode === "files" && !trainTicketsFile.trim()) {
        setError("Ticket list file path is required.");
        setStage("input");
        return;
      }
      if (trainInputMode === "tickets" && !trainTicketsText.trim()) {
        setError("Enter at least one ticket key.");
        setStage("input");
        return;
      }
      if (!trainTrainingData.trim()) {
        setError("Training data CSV path is required.");
        setStage("input");
        return;
      }
      const minSamplesNum = Number(trainMinSamples);
      if (!Number.isInteger(minSamplesNum) || minSamplesNum <= 0) {
        setError("Min samples must be a positive integer.");
        setStage("input");
        return;
      }
      const maxRows = Number(trainMaxReviewRows);
      if (!Number.isInteger(maxRows) || maxRows <= 0) {
        setError("Max review rows must be a positive integer.");
        setStage("input");
        return;
      }
    } else {
      setError("Select a runnable workflow to execute.");
      setStage("input");
      return;
    }

    setIsRunning(true);
    setError("");
    setSummaryRows([]);
    setAddRuleResult({});
    setTrainStcResult({});
    setTrainPhase(1);
    setTrainRunId("");
    setTrainPaused(false);
    setTrainAuditCsvPath("");
    setTrainAuditRows([]);
    setTrainAuditOriginal("");
    setTrainAuditSaving(false);
    setTrainAuditSaveStatus("");
    setResultPaths({});
    setExecutedCommands([]);
    setCommandLogs([]);
    const runStartedAt = new Date().toISOString();
    setStartedAt(runStartedAt);
    setFinishedAt("");
    setElapsedMs(0);
    setWasCanceled(false);
    setLastLogAtMs(null);
    setLiveElapsedMs(0);
    setHeartbeatTick(0);
    setStage("results");
    setPipelineStatus(
      workflow === "categorize" ? PIPELINE_STEPS.map(() => "pending") : []
    );
    setTrainStcPipelineStatus(
      workflow === "train-stc"
        ? TRAIN_PIPELINE_STEPS.map(() => "pending" as PipelineStepStatus)
        : []
    );

    let pausedDuringRun = false;

    try {
      const abortController = new AbortController();
      abortRef.current = abortController;
      const endpoint =
        workflow === "categorize"
          ? "/api/run-jql"
          : workflow === "train-stc"
            ? "/api/train-stc"
            : "/api/add-rule-from-ticket";
      const body =
        workflow === "categorize"
          ? { inputMode, jql, resolutionMode, ticketsFile, ticketsText, rulesEngine: categorizeRulesEngine.trim(), mlModel: categorizeMlModel.trim(), mlCategoryMap: categorizeMlCategoryMap.trim() }
          : workflow === "train-stc"
            ? {
                phase: 1 as const,
                inputMode: trainInputMode,
                jql: trainJql.trim(),
                resolutionMode: trainResolutionMode,
                ticketsFile: trainTicketsFile.trim(),
                ticketsText: trainTicketsText.trim(),
                trainingData: trainTrainingData.trim(),
                minSamples: Number(trainMinSamples),
                maxReviewRows: Number(trainMaxReviewRows)
              }
            : {
                ticketKey: ticketKey.trim().toUpperCase(),
                reason: reason.trim(),
                failureCategory: failureCategory.trim(),
                category: category.trim(),
                matchField: matchField.trim(),
                rulePattern: rulePattern.trim(),
                ticketJsonDir: ticketJsonDir.trim(),
                normalizedRoot: normalizedRoot.trim(),
                rulesEngine: rulesEngine.trim(),
                matchFieldDefault: matchFieldDefault.trim(),
                priority: Number(priority),
                confidence: Number(confidence),
                createdBy: createdBy.trim(),
                hitCount: Number(hitCount)
              };
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: abortController.signal
      });
      if (!response.ok) {
        const fallback = (await response.json()) as { error?: string };
        throw new Error(
          fallback.error ||
            (workflow === "categorize"
              ? "Failed to run pipeline."
              : workflow === "train-stc"
                ? "Failed to run training workflow."
                : "Failed to run add-rule workflow.")
        );
      }

      if (!response.body) {
        const data = (await response.json()) as {
          error?: string;
          summaryRows?: SummaryRow[];
          paths?: { ticketsCsv?: string; summaryCsv?: string; normalizedDir?: string };
          result?: {
            ruleId?: string;
            rulesEngine?: string;
            ticketJson?: string;
            normalizedJson?: string;
            message?: string;
          };
        };
        if (data.error) {
          throw new Error(data.error);
        }
        setSummaryRows(data.summaryRows || []);
        setResultPaths(data.paths || {});
        setAddRuleResult(data.result || {});
      } else {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) {
            break;
          }
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.trim()) {
              continue;
            }
            const event = JSON.parse(line) as {
              type: string;
              command?: string;
              line?: string;
              error?: string;
              summaryRows?: SummaryRow[];
              paths?: { ticketsCsv?: string; summaryCsv?: string; normalizedDir?: string; outputDir?: string; localRules?: string; mlModel?: string; mlReport?: string };
              phase?: number;
              runId?: string;
              partialResult?: { trainingSamples?: number; cvAccuracy?: string };
              result?: {
                ruleId?: string;
                rulesEngine?: string;
                ticketJson?: string;
                normalizedJson?: string;
                message?: string;
                trainingSamples?: number;
                cvAccuracy?: string;
                rulesAdded?: number;
                ticketsCsv?: string;
                localRules?: string;
                mlModel?: string;
                mlReport?: string;
                trainingLog?: string;
                outputDir?: string;
              };
            };

            if (event.type === "command-start" && event.command) {
              if (workflow === "categorize") {
                const startIdx = PIPELINE_STEPS.findIndex((step) => event.command?.includes(step));
                if (startIdx >= 0) {
                  setPipelineStatus((prev) =>
                    prev.map((status, idx) => {
                      if (idx < startIdx && status !== "done") {
                        return "done";
                      }
                      if (idx === startIdx) {
                        return "running";
                      }
                      return status;
                    })
                  );
                }
              }
              if (workflow === "train-stc") {
                setTrainStcPipelineStatus((prev) => {
                  const nextIdx = prev.findIndex((s) => s === "pending");
                  if (nextIdx === -1) return prev;
                  return prev.map((s, i) => {
                    if (i < nextIdx && s !== "done") return "done";
                    if (i === nextIdx) return "running";
                    return s;
                  });
                });
              }
              setLastLogAtMs(Date.now());
              setExecutedCommands((prev) =>
                prev.includes(event.command as string) ? prev : [...prev, event.command as string]
              );
              setCommandLogs((prev) => [...prev, `[${nowTime()}] > ${event.command}`]);
            } else if (event.type === "command-end" && event.command) {
              if (workflow === "categorize") {
                const endIdx = PIPELINE_STEPS.findIndex((step) => event.command?.includes(step));
                if (endIdx >= 0) {
                  setPipelineStatus((prev) =>
                    prev.map((status, idx) => (idx === endIdx ? "done" : status))
                  );
                }
              }
              if (workflow === "train-stc") {
                setTrainStcPipelineStatus((prev) => {
                  const runIdx = prev.findIndex((s) => s === "running");
                  if (runIdx === -1) return prev;
                  return prev.map((s, i) => (i === runIdx ? "done" : s));
                });
              }
            } else if ((event.type === "stdout" || event.type === "stderr") && event.line) {
              const linesFromEvent = event.line.split(/\r?\n/).filter((chunk) => chunk.trim());
              if (linesFromEvent.length > 0) {
                setLastLogAtMs(Date.now());
                setCommandLogs((prev) => [
                  ...prev,
                    ...linesFromEvent.map((entry) => `[${nowTime()}] ${entry}`)
                ]);
              }
            } else if (event.type === "paused" && workflow === "train-stc") {
              pausedDuringRun = true;
              const pausePhase = event.phase as number;
              setTrainRunId(event.runId || "");
              setTrainPaused(true);
              // Mark audit step as "running" (step 4 for phase 1, step 7 for phase 2)
              const auditIdx = pausePhase === 1 ? 4 : 7;
              setTrainStcPipelineStatus((prev) =>
                prev.map((s, i) => (i === auditIdx ? "running" : s))
              );
              // Store partial ML results from phase 2
              if (pausePhase === 2 && event.partialResult) {
                setTrainStcResult((prev) => ({
                  ...prev,
                  trainingSamples: event.partialResult?.trainingSamples ?? prev.trainingSamples,
                  cvAccuracy: event.partialResult?.cvAccuracy ?? prev.cvAccuracy
                }));
              }
              // Load tickets-categorized.csv into audit editor
              const csvPath = event.paths?.ticketsCsv;
              if (csvPath) {
                setTrainAuditCsvPath(csvPath);
                try {
                  const csvResp = await fetch(`/api/open-file?path=${encodeURIComponent(csvPath)}`);
                  if (csvResp.ok) {
                    const csvText = await csvResp.text();
                    setTrainAuditOriginal(csvText);
                    try {
                      setTrainAuditRows(parseCsvRows(csvText));
                    } catch {
                      setTrainAuditRows([]);
                    }
                  }
                } catch {
                  // Best effort — user can still edit externally via file path
                }
              }
            } else if (event.type === "done") {
              if (workflow === "categorize") {
                setPipelineStatus(PIPELINE_STEPS.map(() => "done"));
              }
              if (workflow === "train-stc") {
                setTrainStcPipelineStatus(TRAIN_PIPELINE_STEPS.map(() => "done"));
                setTrainStcResult((prev) => ({ ...prev, ...event.result }));
                clearSessionState();
              }
              setSummaryRows(event.summaryRows || []);
              setResultPaths(event.paths || {});
              setAddRuleResult(event.result || {});
            } else if (event.type === "canceled") {
              setWasCanceled(true);
              setError("Run canceled. Artifacts cleaned.");
              setSummaryRows([]);
              setResultPaths({});
              setAddRuleResult(
                workflow === "add-rule" ? { message: "Run canceled." } : {}
              );
              if (workflow === "train-stc") {
                setTrainStcResult({ message: "Run canceled." });
              }
            } else if (event.type === "error") {
              if (workflow === "add-rule") {
                setAddRuleResult({ message: `Run failed: ${event.error || "Unknown error"}` });
              }
              if (workflow === "train-stc") {
                setTrainStcResult({ message: `Run failed: ${event.error || "Unknown error"}` });
                setTrainStcPipelineStatus((prev) => {
                  const runningIdx = prev.findIndex((status) => status === "running");
                  if (runningIdx === -1) return prev;
                  return prev.map((status, idx) => (idx === runningIdx ? "failed" : status));
                });
              }
              if (workflow === "categorize") {
                setPipelineStatus((prev) => {
                  const runningIdx = prev.findIndex((status) => status === "running");
                  if (runningIdx === -1) {
                    return prev;
                  }
                  return prev.map((status, idx) => (idx === runningIdx ? "failed" : status));
                });
              }
              throw new Error(event.error || "Pipeline failed.");
            }
          }
        }
      }
    } catch (runError) {
      const message = runError instanceof Error ? runError.message : "Unexpected error.";
      if (message === "The operation was aborted.") {
        setWasCanceled(true);
        setError("Run canceled. Artifacts cleaned.");
        if (workflow === "add-rule") {
          setAddRuleResult({ message: "Run canceled." });
        }
        if (workflow === "train-stc") {
          setTrainStcResult({ message: "Run canceled." });
        }
      } else {
        setError(message);
        if (workflow === "add-rule") {
          setAddRuleResult({ message: `Run failed: ${message}` });
        }
        if (workflow === "train-stc") {
          setTrainStcResult({ message: `Run failed: ${message}` });
        }
      }
    } finally {
      abortRef.current = null;
      setIsRunning(false);
      // Don't mark as finished when paused — pipeline is still in progress
      if (!pausedDuringRun) {
        const ended = new Date().toISOString();
        setFinishedAt(ended);
        setElapsedMs(Math.max(0, Date.parse(ended) - Date.parse(runStartedAt)));
      }
    }
  }

  function handleCancel() {
    abortRef.current?.abort();
  }

  function updateTrainAuditCell(rowIndex: number, colIndex: number, value: string) {
    setTrainAuditRows((prevRows) => {
      const nextRows = prevRows.map((row) => [...row]);
      while (nextRows.length <= rowIndex) {
        nextRows.push([]);
      }
      while (nextRows[rowIndex].length <= colIndex) {
        nextRows[rowIndex].push("");
      }
      nextRows[rowIndex][colIndex] = value;
      return nextRows;
    });
    setTrainAuditSaveStatus("");
  }

  function resetTrainAudit() {
    try {
      setTrainAuditRows(parseCsvRows(trainAuditOriginal));
    } catch {
      setTrainAuditRows([]);
    }
    setTrainAuditSaveStatus("");
  }

  async function saveTrainAudit() {
    if (!trainAuditCsvPath) {
      setTrainAuditSaveStatus("No file path available.");
      return;
    }
    setTrainAuditSaving(true);
    setTrainAuditSaveStatus("");
    const contentToSave = trainAuditRows.length > 0
      ? serializeCsvRows(trainAuditRows)
      : trainAuditOriginal;
    try {
      const response = await fetch("/api/save-file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: trainAuditCsvPath, content: contentToSave })
      });
      if (!response.ok) {
        const errData = (await response.json()) as { error?: string };
        throw new Error(errData.error || "Save failed.");
      }
      setTrainAuditOriginal(contentToSave);
      setTrainAuditSaveStatus("Saved.");
    } catch (saveError) {
      const msg = saveError instanceof Error ? saveError.message : "Save failed.";
      setTrainAuditSaveStatus(msg);
    } finally {
      setTrainAuditSaving(false);
    }
  }

  async function handleContinueTraining() {
    const nextPhase = (trainPhase === 1 ? 2 : 3) as 1 | 2 | 3;

    // Mark audit step as done
    setTrainStcPipelineStatus((prev) => {
      const auditIdx = trainPhase === 1 ? 4 : 7;
      return prev.map((s, i) => (i === auditIdx ? "done" : s));
    });

    setTrainPaused(false);
    setTrainPhase(nextPhase);
    setTrainAuditCsvPath("");
    setTrainAuditRows([]);
    setTrainAuditOriginal("");
    setTrainAuditSaving(false);
    setTrainAuditSaveStatus("");
    setIsRunning(true);
    setError("");

    let pausedDuringRun = false;
    const phaseStartedAt = new Date().toISOString();

    try {
      const abortController = new AbortController();
      abortRef.current = abortController;
      const response = await fetch("/api/train-stc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phase: nextPhase, runId: trainRunId }),
        signal: abortController.signal
      });

      if (!response.ok) {
        const fallback = (await response.json()) as { error?: string };
        throw new Error(fallback.error || "Failed to run training workflow.");
      }

      if (response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.trim()) continue;
            const event = JSON.parse(line) as {
              type: string;
              command?: string;
              line?: string;
              error?: string;
              phase?: number;
              runId?: string;
              paths?: { ticketsCsv?: string; outputDir?: string; localRules?: string; mlModel?: string; mlReport?: string };
              partialResult?: { trainingSamples?: number; cvAccuracy?: string };
              result?: {
                message?: string;
                trainingSamples?: number;
                cvAccuracy?: string;
                rulesAdded?: number;
                ticketsCsv?: string;
                localRules?: string;
                mlModel?: string;
                mlReport?: string;
                trainingLog?: string;
                outputDir?: string;
              };
            };

            if (event.type === "command-start" && event.command) {
              setTrainStcPipelineStatus((prev) => {
                const nextIdx = prev.findIndex((s) => s === "pending");
                if (nextIdx === -1) return prev;
                return prev.map((s, i) => {
                  if (i < nextIdx && s !== "done") return "done";
                  if (i === nextIdx) return "running";
                  return s;
                });
              });
              setLastLogAtMs(Date.now());
              setExecutedCommands((prev) =>
                prev.includes(event.command as string) ? prev : [...prev, event.command as string]
              );
              setCommandLogs((prev) => [...prev, `[${nowTime()}] > ${event.command}`]);
            } else if (event.type === "command-end" && event.command) {
              setTrainStcPipelineStatus((prev) => {
                const runIdx = prev.findIndex((s) => s === "running");
                if (runIdx === -1) return prev;
                return prev.map((s, i) => (i === runIdx ? "done" : s));
              });
            } else if ((event.type === "stdout" || event.type === "stderr") && event.line) {
              const linesFromEvent = event.line.split(/\r?\n/).filter((chunk) => chunk.trim());
              if (linesFromEvent.length > 0) {
                setLastLogAtMs(Date.now());
                setCommandLogs((prev) => [
                  ...prev,
                  ...linesFromEvent.map((entry) => `[${nowTime()}] ${entry}`)
                ]);
              }
            } else if (event.type === "paused") {
              pausedDuringRun = true;
              const pausePhase = event.phase as number;
              setTrainPaused(true);
              const auditIdx = pausePhase === 1 ? 4 : 7;
              setTrainStcPipelineStatus((prev) =>
                prev.map((s, i) => (i === auditIdx ? "running" : s))
              );
              if (pausePhase === 2 && event.partialResult) {
                setTrainStcResult((prev) => ({
                  ...prev,
                  trainingSamples: event.partialResult?.trainingSamples ?? prev.trainingSamples,
                  cvAccuracy: event.partialResult?.cvAccuracy ?? prev.cvAccuracy
                }));
              }
              const csvPath = event.paths?.ticketsCsv;
              if (csvPath) {
                setTrainAuditCsvPath(csvPath);
                try {
                  const csvResp = await fetch(`/api/open-file?path=${encodeURIComponent(csvPath)}`);
                  if (csvResp.ok) {
                    const csvText = await csvResp.text();
                    setTrainAuditOriginal(csvText);
                    try {
                      setTrainAuditRows(parseCsvRows(csvText));
                    } catch {
                      setTrainAuditRows([]);
                    }
                  }
                } catch {
                  // Best effort
                }
              }
            } else if (event.type === "done") {
              setTrainStcPipelineStatus(TRAIN_PIPELINE_STEPS.map(() => "done"));
              setTrainStcResult((prev) => ({ ...prev, ...event.result }));
              clearSessionState();
            } else if (event.type === "canceled") {
              setWasCanceled(true);
              setError("Run canceled.");
              setTrainStcResult({ message: "Run canceled." });
            } else if (event.type === "error") {
              setTrainStcResult({ message: `Run failed: ${event.error || "Unknown error"}` });
              setTrainStcPipelineStatus((prev) => {
                const runningIdx = prev.findIndex((status) => status === "running");
                if (runningIdx === -1) return prev;
                return prev.map((status, idx) => (idx === runningIdx ? "failed" : status));
              });
              throw new Error(event.error || "Pipeline failed.");
            }
          }
        }
      }
    } catch (runError) {
      const message = runError instanceof Error ? runError.message : "Unexpected error.";
      if (message === "The operation was aborted.") {
        setWasCanceled(true);
        setError("Run canceled.");
        setTrainStcResult({ message: "Run canceled." });
      } else {
        setError(message);
        setTrainStcResult({ message: `Run failed: ${message}` });
      }
    } finally {
      abortRef.current = null;
      setIsRunning(false);
      if (!pausedDuringRun) {
        const ended = new Date().toISOString();
        setFinishedAt(ended);
        setElapsedMs(Math.max(0, Date.parse(ended) - Date.parse(phaseStartedAt)));
      }
    }
  }

  function handleCancelTrainAudit() {
    setTrainPaused(false);
    setTrainAuditCsvPath("");
    setTrainAuditRows([]);
    setTrainAuditOriginal("");
    setTrainAuditSaveStatus("");
    setWasCanceled(true);
    setError("Training canceled during audit.");
    setTrainStcResult({ message: "Training canceled during audit." });
    setTrainStcPipelineStatus((prev) => {
      const auditIdx = trainPhase === 1 ? 4 : 7;
      return prev.map((s, i) => (i === auditIdx ? "failed" : s));
    });
    const ended = new Date().toISOString();
    setFinishedAt(ended);
  }

  async function copyText(
    label: string,
    text: string,
    statusSetter: (message: string) => void = setCopyStatus
  ) {
    try {
      if (!text.trim()) {
        statusSetter(`No ${label.toLowerCase()} to copy.`);
        return;
      }
      await navigator.clipboard.writeText(text);
      statusSetter(`${label} copied.`);
    } catch {
      try {
        const area = document.createElement("textarea");
        area.value = text;
        document.body.appendChild(area);
        area.select();
        document.execCommand("copy");
        document.body.removeChild(area);
        statusSetter(`${label} copied.`);
      } catch {
        statusSetter(`Failed to copy ${label.toLowerCase()}.`);
      }
    }
  }

  function updateCategorizedCell(rowIndex: number, colIndex: number, value: string) {
    setCategorizedTableRows((prevRows) => {
      const nextRows = prevRows.map((row) => [...row]);
      while (nextRows.length <= rowIndex) {
        nextRows.push([]);
      }
      while (nextRows[rowIndex].length <= colIndex) {
        nextRows[rowIndex].push("");
      }
      nextRows[rowIndex][colIndex] = value;
      return nextRows;
    });
    setCategorizedCopyStatus("");
    setCategorizedSaveStatus("");
  }

  function resetCategorizedChanges() {
    try {
      const rows = parseCsvRows(categorizedPreview);
      setCategorizedTableRows(rows);
      setCategorizedTableError("");
    } catch {
      setCategorizedTableRows([]);
      setCategorizedTableError("CSV parse error. Showing raw editor fallback.");
      setCategorizedEditorText(categorizedPreview);
    }
    setCategorizedCopyStatus("");
    setCategorizedSaveStatus("");
  }

  function syncCategorizedScrollTracks() {
    const shell = categorizedGridShellRef.current;
    const topScroll = categorizedGridTopScrollRef.current;
    const topSpacer = categorizedGridTopSpacerRef.current;
    if (!shell || !topScroll || !topSpacer) {
      return;
    }
    const maxLeft = Math.max(0, shell.scrollWidth - shell.clientWidth);
    setCategorizedScrollLeft(shell.scrollLeft);
    setCategorizedScrollMax(maxLeft);
    topSpacer.style.width = `${shell.scrollWidth}px`;
    topScroll.scrollLeft = shell.scrollLeft;
  }

  function setCategorizedHorizontalScrollPosition(nextLeft: number, smooth = false) {
    const shell = categorizedGridShellRef.current;
    const topScroll = categorizedGridTopScrollRef.current;
    if (!shell) {
      return;
    }
    const maxLeft = Math.max(0, shell.scrollWidth - shell.clientWidth);
    const clamped = Math.min(Math.max(0, nextLeft), maxLeft);
    shell.scrollTo({ left: clamped, behavior: smooth ? "smooth" : "auto" });
    if (topScroll) {
      topScroll.scrollLeft = clamped;
    }
    setCategorizedScrollLeft(clamped);
    setCategorizedScrollMax(maxLeft);
  }

  function handleCategorizedGridShellScroll() {
    const shell = categorizedGridShellRef.current;
    const topScroll = categorizedGridTopScrollRef.current;
    if (!shell || !topScroll || categorizedScrollSyncRef.current === "top") {
      return;
    }
    categorizedScrollSyncRef.current = "body";
    topScroll.scrollLeft = shell.scrollLeft;
    setCategorizedScrollLeft(shell.scrollLeft);
    setCategorizedScrollMax(Math.max(0, shell.scrollWidth - shell.clientWidth));
    categorizedScrollSyncRef.current = null;
  }

  function handleCategorizedGridTopScroll() {
    const shell = categorizedGridShellRef.current;
    const topScroll = categorizedGridTopScrollRef.current;
    if (!shell || !topScroll || categorizedScrollSyncRef.current === "body") {
      return;
    }
    categorizedScrollSyncRef.current = "top";
    shell.scrollLeft = topScroll.scrollLeft;
    setCategorizedScrollLeft(shell.scrollLeft);
    setCategorizedScrollMax(Math.max(0, shell.scrollWidth - shell.clientWidth));
    categorizedScrollSyncRef.current = null;
  }

  function nudgeCategorizedHorizontal(direction: "left" | "right") {
    const shell = categorizedGridShellRef.current;
    if (!shell) {
      return;
    }
    const step = Math.max(220, Math.floor(shell.clientWidth * 0.35));
    const next = direction === "left" ? shell.scrollLeft - step : shell.scrollLeft + step;
    setCategorizedHorizontalScrollPosition(next, true);
  }

  function handleCategorizedHorizontalSlider(value: string) {
    const parsed = Number.parseInt(value, 10);
    if (Number.isNaN(parsed)) {
      return;
    }
    setCategorizedHorizontalScrollPosition(parsed);
  }

  function updateRulesCell(rowIndex: number, colIndex: number, value: string) {
    setRulesTableRows((prevRows) => {
      const nextRows = prevRows.map((row) => [...row]);
      while (nextRows.length <= rowIndex) {
        nextRows.push([]);
      }
      while (nextRows[rowIndex].length <= colIndex) {
        nextRows[rowIndex].push("");
      }
      nextRows[rowIndex][colIndex] = value;
      return nextRows;
    });
    setRulesCopyStatus("");
    setRulesSaveStatus("");
  }

  function resetRulesChanges() {
    try {
      const rows = parseCsvRows(rulesPreview);
      setRulesTableRows(rows);
      setRulesTableError("");
    } catch {
      setRulesTableRows([]);
      setRulesTableError("CSV parse error. Showing raw editor fallback.");
      setRulesEditorText(rulesPreview);
    }
    setRulesCopyStatus("");
    setRulesSaveStatus("");
  }

  function syncRulesScrollTracks() {
    const shell = rulesGridShellRef.current;
    const topScroll = rulesGridTopScrollRef.current;
    const topSpacer = rulesGridTopSpacerRef.current;
    if (!shell || !topScroll || !topSpacer) {
      return;
    }
    const maxLeft = Math.max(0, shell.scrollWidth - shell.clientWidth);
    setRulesScrollLeft(shell.scrollLeft);
    setRulesScrollMax(maxLeft);
    topSpacer.style.width = `${shell.scrollWidth}px`;
    topScroll.scrollLeft = shell.scrollLeft;
  }

  function setRulesHorizontalScrollPosition(nextLeft: number, smooth = false) {
    const shell = rulesGridShellRef.current;
    const topScroll = rulesGridTopScrollRef.current;
    if (!shell) {
      return;
    }
    const maxLeft = Math.max(0, shell.scrollWidth - shell.clientWidth);
    const clamped = Math.min(Math.max(0, nextLeft), maxLeft);
    shell.scrollTo({ left: clamped, behavior: smooth ? "smooth" : "auto" });
    if (topScroll) {
      topScroll.scrollLeft = clamped;
    }
    setRulesScrollLeft(clamped);
    setRulesScrollMax(maxLeft);
  }

  function handleRulesGridShellScroll() {
    const shell = rulesGridShellRef.current;
    const topScroll = rulesGridTopScrollRef.current;
    if (!shell || !topScroll || rulesScrollSyncRef.current === "top") {
      return;
    }
    rulesScrollSyncRef.current = "body";
    topScroll.scrollLeft = shell.scrollLeft;
    setRulesScrollLeft(shell.scrollLeft);
    setRulesScrollMax(Math.max(0, shell.scrollWidth - shell.clientWidth));
    rulesScrollSyncRef.current = null;
  }

  function handleRulesGridTopScroll() {
    const shell = rulesGridShellRef.current;
    const topScroll = rulesGridTopScrollRef.current;
    if (!shell || !topScroll || rulesScrollSyncRef.current === "body") {
      return;
    }
    rulesScrollSyncRef.current = "top";
    shell.scrollLeft = topScroll.scrollLeft;
    setRulesScrollLeft(shell.scrollLeft);
    setRulesScrollMax(Math.max(0, shell.scrollWidth - shell.clientWidth));
    rulesScrollSyncRef.current = null;
  }

  function nudgeRulesHorizontal(direction: "left" | "right") {
    const shell = rulesGridShellRef.current;
    if (!shell) {
      return;
    }
    const step = Math.max(220, Math.floor(shell.clientWidth * 0.35));
    const next = direction === "left" ? shell.scrollLeft - step : shell.scrollLeft + step;
    setRulesHorizontalScrollPosition(next, true);
  }

  function handleRulesHorizontalSlider(value: string) {
    const parsed = Number.parseInt(value, 10);
    if (Number.isNaN(parsed)) {
      return;
    }
    setRulesHorizontalScrollPosition(parsed);
  }

  const runState =
    isRunning ? "running" : error ? "failed" : finishedAt ? "success" : "idle";
  const normalizedTicketKey = ticketKey.trim().toUpperCase();
  const filteredTicketList = useMemo(() => {
    const filter = ticketFilter.trim().toUpperCase();
    if (!filter) {
      return ticketList;
    }
    return ticketList.filter(
      (ticket) =>
        ticket.key.includes(filter) || ticket.summary.toUpperCase().includes(filter)
    );
  }, [ticketFilter, ticketList]);
  const visibleTickets = filteredTicketList.slice(0, ticketListExpanded ? 200 : 1);
  const filteredCategorizedFiles = useMemo(() => {
    const filter = categorizedFilter.trim().toUpperCase();
    if (!filter) {
      return categorizedFiles;
    }
    return categorizedFiles.filter((file) => file.name.toUpperCase().includes(filter));
  }, [categorizedFilter, categorizedFiles]);
  const visibleCategorizedFiles = filteredCategorizedFiles.slice(0, 200);
  const categorizedMaxCols = useMemo(() => {
    if (categorizedTableRows.length === 0) {
      return 0;
    }
    return categorizedTableRows.reduce((maxCols, row) => Math.max(maxCols, row.length), 0);
  }, [categorizedTableRows]);
  const categorizedDisplayRows = useMemo(() => {
    if (categorizedMaxCols === 0) {
      return categorizedTableRows;
    }
    return categorizedTableRows.map((row) => {
      const nextRow = [...row];
      while (nextRow.length < categorizedMaxCols) {
        nextRow.push("");
      }
      return nextRow;
    });
  }, [categorizedTableRows, categorizedMaxCols]);
  const categorizedVisibleRows = useMemo(() => {
    if (categorizedDisplayRows.length <= 1) {
      return categorizedDisplayRows;
    }
    return [categorizedDisplayRows[0], ...categorizedDisplayRows.slice(1, 51)];
  }, [categorizedDisplayRows]);
  const categorizedHiddenRowCount = Math.max(
    0,
    categorizedDisplayRows.length - categorizedVisibleRows.length
  );
  const categorizedCanScrollLeft = categorizedScrollLeft > 0;
  const categorizedCanScrollRight = categorizedScrollLeft < categorizedScrollMax;
  useEffect(() => {
    syncCategorizedScrollTracks();
    function handleResize() {
      syncCategorizedScrollTracks();
    }
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [categorizedVisibleRows, categorizedMaxCols, categorizedSelectedPath, categorizedTableError]);
  const categorizedCurrentText = useMemo(() => {
    if (categorizedTableRows.length > 0) {
      return serializeCsvRows(categorizedTableRows);
    }
    return categorizedEditorText;
  }, [categorizedTableRows, categorizedEditorText]);
  const categorizedHasChanges =
    Boolean(categorizedSelectedPath) && categorizedCurrentText !== categorizedPreview;
  const trainAuditCurrentText = useMemo(() => {
    if (trainAuditRows.length > 0) {
      return serializeCsvRows(trainAuditRows);
    }
    return trainAuditOriginal;
  }, [trainAuditRows, trainAuditOriginal]);
  const trainAuditHasChanges =
    Boolean(trainAuditCsvPath) && trainAuditCurrentText !== trainAuditOriginal;
  const filteredRulesFiles = useMemo(() => {
    const filter = rulesFilter.trim().toUpperCase();
    if (!filter) {
      return rulesFiles;
    }
    return rulesFiles.filter((file) => file.name.toUpperCase().includes(filter));
  }, [rulesFilter, rulesFiles]);
  const visibleRulesFiles = filteredRulesFiles.slice(0, 200);
  const rulesMaxCols = useMemo(() => {
    if (rulesTableRows.length === 0) {
      return 0;
    }
    return rulesTableRows.reduce((maxCols, row) => Math.max(maxCols, row.length), 0);
  }, [rulesTableRows]);
  const rulesDisplayRows = useMemo(() => {
    if (rulesMaxCols === 0) {
      return rulesTableRows;
    }
    return rulesTableRows.map((row) => {
      const nextRow = [...row];
      while (nextRow.length < rulesMaxCols) {
        nextRow.push("");
      }
      return nextRow;
    });
  }, [rulesTableRows, rulesMaxCols]);
  const rulesVisibleRows = useMemo(() => {
    if (rulesDisplayRows.length <= 1) {
      return rulesDisplayRows;
    }
    return [rulesDisplayRows[0], ...rulesDisplayRows.slice(1, 51)];
  }, [rulesDisplayRows]);
  const rulesHiddenRowCount = Math.max(
    0,
    rulesDisplayRows.length - rulesVisibleRows.length
  );
  const rulesCanScrollLeft = rulesScrollLeft > 0;
  const rulesCanScrollRight = rulesScrollLeft < rulesScrollMax;
  useEffect(() => {
    syncRulesScrollTracks();
    function handleResize() {
      syncRulesScrollTracks();
    }
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [rulesVisibleRows, rulesMaxCols, rulesSelectedPath, rulesTableError]);
  const rulesCurrentText = useMemo(() => {
    if (rulesTableRows.length > 0) {
      return serializeCsvRows(rulesTableRows);
    }
    return rulesEditorText;
  }, [rulesTableRows, rulesEditorText]);
  const rulesHasChanges =
    Boolean(rulesSelectedPath) && rulesCurrentText !== rulesPreview;

  return (
    <main>
      <section className="panel">
        <header className="header">
          <h1 className="title">
            <a
              href="/"
              className="home-link"
              onClick={(e) => {
                if (isRunning && workflow === "train-stc") {
                  const leave = window.confirm("A training run is in progress. Leaving will cancel it. Continue?");
                  if (!leave) {
                    e.preventDefault();
                    return;
                  }
                  abortRef.current?.abort();
                }
                e.preventDefault();
                setStage("landing");
              }}
              aria-label="Go to home"
            >
              Smart Tickets&apos; Classifier (STC)
            </a>
          </h1>
          <p className="subtitle">v0.1 wireframe preview</p>
        </header>

        <div className="actions">
          <div className="mode-menu" role="group" aria-label="Workflow menu">
            {([
              ["categorize", "Categorize tickets"],
              ["add-rule", "Add Rule for a Ticket"],
              ["browse-tickets", "Tickets in Normalized root"],
              ["browse-categorized", "View Categorized Tickets"],
              ["browse-rules", "View Rules Engines"],
              ["browse-ml-model", "View ML Models"],
              ["promote-to-golden", "Promote to Golden"],
              ["train-stc", "Train STC model"],
            ] as [Workflow, string][]).map(([wf, label]) => (
              <a
                key={wf}
                href={`#${wf}`}
                className={`menu-btn ${workflow === wf ? "is-active" : ""}${isRunning ? " disabled" : ""}`}
                aria-label={label}
                aria-current={workflow === wf ? "page" : undefined}
                onClick={(e) => {
                  e.preventDefault();
                  if (isRunning) {
                    if (workflow === "train-stc") {
                      const leave = window.confirm("A training run is in progress. Leaving will cancel it. Continue?");
                      if (!leave) return;
                      abortRef.current?.abort();
                    } else {
                      return;
                    }
                  }
                  setWorkflow(wf);
                  setStage("input");
                }}
              >
                {label}
              </a>
            ))}
          </div>
          {isRunning && (
            <button onClick={handleCancel} aria-label="Cancel run">
              Cancel
            </button>
          )}
        </div>

        <div className="content">
          {stage === "landing" && (
            <>
              <p className="small">
                Click <strong>Categorize tickets</strong>, <strong>Add Rule for a Ticket</strong>,{" "}
                <strong>Tickets in Normalized root</strong>, <strong>View Categorized Tickets</strong>,{" "}
                <strong>View Rules Engines</strong>, <strong>Promote to Golden</strong>,{" "}
                or <strong>Train STC model</strong> to preview the next wireframe step.
              </p>
              <p style={{ marginTop: "1rem" }}>
                <a href="/sessions" style={{ color: "#3b82f6" }}>View Past Training Sessions &rarr;</a>
              </p>
            </>
          )}

          {stage === "input" && workflow === "categorize" && (
            <div className="grid" aria-label="Input section">
              <fieldset className="field">
                <legend>Input source (either-or)</legend>
                <label>
                  <input
                    type="radio"
                    name="input-mode"
                    value="jql"
                    checked={inputMode === "jql"}
                    onChange={() => setInputMode("jql")}
                    disabled={isRunning}
                  />{" "}
                  JQL
                </label>
                <label>
                  <input
                    type="radio"
                    name="input-mode"
                    value="files"
                    checked={inputMode === "files"}
                    onChange={() => setInputMode("files")}
                    disabled={isRunning}
                  />{" "}
                  Ticket list files
                </label>
                <label>
                  <input
                    type="radio"
                    name="input-mode"
                    value="tickets"
                    checked={inputMode === "tickets"}
                    onChange={() => setInputMode("tickets")}
                    disabled={isRunning}
                  />{" "}
                  Ticket IDs
                </label>
              </fieldset>
              <div className="field">
                <label htmlFor="jql">Enter JQL</label>
                <input
                  id="jql"
                  placeholder='project="High Performance Computing"'
                  value={jql}
                  onChange={(e) => setJql(e.target.value)}
                  disabled={inputMode !== "jql"}
                />
                <p className="small">
                  Example: project="High Performance Computing" and createdDate &gt;= "2026-02-10"
                  and createdDate &lt;= "2026-02-11"
                </p>
              </div>
              <div className="field">
                <label htmlFor="resolution-mode">Ticket resolution filter</label>
                <select
                  id="resolution-mode"
                  value={resolutionMode}
                  onChange={(e) => setResolutionMode(e.target.value as ResolutionMode)}
                  disabled={inputMode !== "jql"}
                >
                  <option value="all">All (resolved + unresolved)</option>
                  <option value="unresolved-only">Unresolved only</option>
                  <option value="resolved-only">Resolved only</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="ticket-files">Enter ticket list files</label>
                <input
                  id="ticket-files"
                  placeholder="scripts/analysis/ui-runs/templates/tickets-template.txt"
                  value={ticketsFile}
                  onChange={(e) => setTicketsFile(e.target.value)}
                  disabled={inputMode !== "files"}
                />
                <p className="small">
                  Template directory: <code>scripts/analysis/ui-runs/templates/</code>. One ticket
                  per line in file (example: <code>HPC-101</code> or <code>DO-202</code>).
                </p>
              </div>
              <div className="field">
                <label htmlFor="ticket-list">Enter list of ticket IDs</label>
                <textarea
                  id="ticket-list"
                  rows={4}
                  placeholder="HPC-110621,HPC-110615"
                  value={ticketsText}
                  onChange={(e) => setTicketsText(e.target.value)}
                  disabled={inputMode !== "tickets"}
                />
                <p className="small">
                  You can paste comma-separated tickets, e.g. <code>HPC-110621,HPC-110615</code>.
                </p>
              </div>
              <div className="field">
                <label htmlFor="categorize-rules-engine">Rules engine CSV</label>
                <input
                  id="categorize-rules-engine"
                  value={categorizeRulesEngine}
                  onChange={(e) => setCategorizeRulesEngine(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="categorize-ml-model">ML model (optional — leave empty for rules-only)</label>
                <input
                  id="categorize-ml-model"
                  value={categorizeMlModel}
                  onChange={(e) => setCategorizeMlModel(e.target.value)}
                  disabled={isRunning}
                  placeholder="e.g. scripts/trained-data/golden-ml-model/classifier.joblib"
                />
              </div>
              <div className="field">
                <label htmlFor="categorize-ml-category-map">ML category map (optional)</label>
                <input
                  id="categorize-ml-category-map"
                  value={categorizeMlCategoryMap}
                  onChange={(e) => setCategorizeMlCategoryMap(e.target.value)}
                  disabled={isRunning}
                  placeholder="e.g. scripts/trained-data/golden-ml-model/category_map.json"
                />
              </div>
              <div>
                <button className="primary" onClick={handleOk} disabled={isRunning}>
                  {isRunning ? "Running..." : "OK"}
                </button>
              </div>
              {error && (
                <p className="small" role="alert">
                  {error}
                </p>
              )}
            </div>
          )}

          {stage === "input" && workflow === "browse-tickets" && (
            <div className="grid" aria-label="Input section">
              <article className="card ticket-browser-card">
                <div className="ticket-browser-header">
                  <h2>Tickets in Normalized root</h2>
                  <div className="ticket-browser-controls">
                    <button
                      type="button"
                      onClick={() => setTicketListExpanded((prev) => !prev)}
                      disabled={ticketList.length === 0}
                    >
                      {ticketListExpanded ? "Compact list" : "Expand list"}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        void loadTicketList();
                      }}
                      disabled={isRunning || ticketListLoading}
                    >
                      {ticketListLoading ? "Refreshing..." : "Refresh list"}
                    </button>
                  </div>
                </div>
                <p className="small">
                  Choose a ticket key, then open JSON to read the normalized source payload.
                </p>
                <div className="field">
                  <label htmlFor="ticket-filter">Filter loaded tickets</label>
                  <input
                    id="ticket-filter"
                    placeholder="HPC-123 or summary text"
                    value={ticketFilter}
                    onChange={(e) => setTicketFilter(e.target.value)}
                    disabled={isRunning || ticketListLoading || ticketList.length === 0}
                  />
                </div>
                {ticketListError && (
                  <p className="small" role="alert">
                    {ticketListError}
                  </p>
                )}
                {!ticketListError && (
                  <p className="small">
                    {ticketListLoading
                      ? "Loading tickets..."
                      : `${ticketList.length} ticket(s) visible in ${ticketListLoadedDir || normalizedRoot}.`}
                  </p>
                )}
                {visibleTickets.length === 0 && !ticketListLoading ? (
                  <p className="small">
                    {ticketList.length === 0
                      ? `Directory is empty: ${ticketListLoadedDir || normalizedRoot}.`
                      : "No tickets match the current filter."}
                  </p>
                ) : (
                  <ul
                    className={`ticket-picker-list ${ticketListExpanded ? "is-expanded" : ""}`}
                    aria-label="Ticket picker list"
                  >
                    {visibleTickets.map((ticket) => (
                      <li
                        key={`${ticket.key}-${ticket.sourcePath}`}
                        className={`ticket-picker-item ${
                          ticket.key === normalizedTicketKey ? "is-selected" : ""
                        }`}
                      >
                        <button
                          type="button"
                          className="ticket-pick-btn"
                          onClick={() => {
                            setTicketKey(ticket.key);
                            void loadTicketDetail(ticket.key);
                          }}
                          disabled={isRunning}
                        >
                          {ticket.key}
                        </button>
                        <p className="ticket-summary">{ticket.summary || "(no summary)"}</p>
                        <p className="small ticket-meta">
                          Status: {ticket.status || "n/a"} | Resolution: {ticket.resolution || "n/a"}
                        </p>
                        <a
                          className="link small"
                          href={`/api/open-file?path=${encodeURIComponent(ticket.detailPath)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open JSON
                        </a>
                      </li>
                    ))}
                  </ul>
                )}
                {filteredTicketList.length > visibleTickets.length && (
                  <p className="small">
                    {ticketListExpanded
                      ? `Showing first ${visibleTickets.length} results. Keep filtering to narrow the list.`
                      : "Showing 1 ticket (compact view). Click Expand list to see more."}
                  </p>
                )}
                <div className="ticket-detail-view">
                  <h3>Selected Ticket Details (Read-only)</h3>
                  {ticketDetailLoading ? (
                    <p className="small">Loading ticket details...</p>
                  ) : ticketDetailError ? (
                    <p className="small" role="alert">
                      {ticketDetailError}
                    </p>
                  ) : ticketDetail ? (
                    <>
                      <div className="inline-actions">
                        <button
                          type="button"
                          onClick={() =>
                            copyText(
                              "Ticket details",
                              JSON.stringify(ticketDetail.payload, null, 2),
                              setTicketDetailCopyStatus
                            )
                          }
                        >
                          Copy details
                        </button>
                      </div>
                      {ticketDetailCopyStatus && <p className="small">{ticketDetailCopyStatus}</p>}
                      <p className="small">
                        Source:
                        {" "}
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(ticketDetail.detailPath)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {ticketDetail.detailPath}
                        </a>
                      </p>
                      <pre className="ticket-detail-json">
                        {JSON.stringify(ticketDetail.payload, null, 2)}
                      </pre>
                    </>
                  ) : (
                    <p className="small">Pick a ticket from the list to inspect details here.</p>
                  )}
                </div>
              </article>
            </div>
          )}

          {stage === "input" && workflow === "browse-categorized" && (
            <div className="grid" aria-label="Input section">
              <article className="card ticket-browser-card">
                <div className="ticket-browser-header">
                  <h2>View Categorized Tickets</h2>
                  <button
                    type="button"
                    onClick={() => {
                      void loadCategorizedFiles();
                    }}
                    disabled={isRunning || categorizedFilesLoading}
                  >
                    {categorizedFilesLoading ? "Refreshing..." : "Refresh list"}
                  </button>
                </div>
                <div className="field">
                  <label htmlFor="categorized-dir">Categorized directory (optional)</label>
                  <input
                    id="categorized-dir"
                    placeholder={CATEGORIZED_TICKETS_DIR}
                    value={categorizedDir}
                    onChange={(e) => setCategorizedDir(e.target.value)}
                    disabled={isRunning || categorizedFilesLoading}
                  />
                </div>
                <div className="field">
                  <label htmlFor="categorized-file-name">Exact file name (optional)</label>
                  <input
                    id="categorized-file-name"
                    placeholder={DEFAULT_CATEGORIZED_FILE}
                    value={categorizedFileName}
                    onChange={(e) => setCategorizedFileName(e.target.value)}
                    disabled={isRunning || categorizedFilesLoading}
                  />
                </div>
                <p className="small">
                  Source directory:
                  {" "}
                  <code>{categorizedLoadedDir || categorizedDir.trim() || CATEGORIZED_TICKETS_DIR}</code>
                  {" "}
                  | Exact file:
                  {" "}
                  <code>{categorizedLoadedFileName || categorizedFileName.trim() || "(none)"}</code>
                </p>
                <div className="field">
                  <label htmlFor="categorized-filter">Filter loaded files</label>
                  <input
                    id="categorized-filter"
                    placeholder="tickets-categorized"
                    value={categorizedFilter}
                    onChange={(e) => setCategorizedFilter(e.target.value)}
                    disabled={
                      isRunning || categorizedFilesLoading || categorizedFiles.length === 0
                    }
                  />
                </div>
                {categorizedFilesError && (
                  <p className="small" role="alert">
                    {categorizedFilesError}
                  </p>
                )}
                {!categorizedFilesError && (
                  <p className="small">
                    {categorizedFilesLoading
                      ? "Loading categorized ticket files..."
                      : `${categorizedFiles.length} file(s) visible in ${categorizedLoadedDir || categorizedDir.trim() || CATEGORIZED_TICKETS_DIR}.`}
                  </p>
                )}
                {visibleCategorizedFiles.length === 0 && !categorizedFilesLoading ? (
                  <p className="small">
                    {categorizedFiles.length === 0
                      ? categorizedLoadedFileName || categorizedFileName.trim()
                        ? `No files matched ${(categorizedLoadedFileName || categorizedFileName.trim())} in ${categorizedLoadedDir || categorizedDir.trim() || CATEGORIZED_TICKETS_DIR}.`
                        : `Directory is empty: ${categorizedLoadedDir || categorizedDir.trim() || CATEGORIZED_TICKETS_DIR}.`
                      : "No files match the current filter."}
                  </p>
                ) : (
                  <ul className="ticket-picker-list is-expanded" aria-label="Categorized ticket files list">
                    {visibleCategorizedFiles.map((file) => (
                      <li
                        key={file.path}
                        className={`ticket-picker-item ${
                          file.path === categorizedSelectedPath ? "is-selected" : ""
                        }`}
                      >
                        <button
                          type="button"
                          className="ticket-pick-btn"
                          onClick={() => {
                            void loadCategorizedPreview(file.path);
                          }}
                          disabled={isRunning}
                        >
                          {file.name}
                        </button>
                        <p className="small ticket-meta">
                          Updated: {formatTimestamp(file.modifiedAt)} | Size: {file.sizeBytes} bytes
                        </p>
                        <p className="small ticket-meta">
                          Folder: <code>{toDisplayFolderPath(file.path)}</code>
                        </p>
                        <p className="small">
                          <a
                            className="link small"
                            href={`/api/open-file?path=${encodeURIComponent(file.path)}&download=1`}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Download file
                          </a>
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
                {filteredCategorizedFiles.length > visibleCategorizedFiles.length && (
                  <p className="small">
                    Showing first {visibleCategorizedFiles.length} results. Keep filtering to narrow
                    the list.
                  </p>
                )}
                <div className="ticket-detail-view">
                  <h3>Selected File (View/Edit)</h3>
                  {categorizedPreviewLoading ? (
                    <p className="small">Loading file preview...</p>
                  ) : categorizedPreviewError ? (
                    <p className="small" role="alert">
                      {categorizedPreviewError}
                    </p>
                  ) : categorizedSelectedPath ? (
                    <>
                      <div className="inline-actions">
                        <button
                          type="button"
                          onClick={() =>
                            copyText(
                              "Categorized file contents",
                              categorizedCurrentText,
                              setCategorizedCopyStatus
                            )
                          }
                          disabled={categorizedPreviewLoading}
                        >
                          Copy details
                        </button>
                        <button
                          type="button"
                          onClick={resetCategorizedChanges}
                          disabled={categorizedSaving || !categorizedHasChanges}
                        >
                          Reset changes
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            void saveCategorizedFile();
                          }}
                          disabled={categorizedSaving || !categorizedHasChanges}
                        >
                          {categorizedSaving ? "Saving..." : "Save changes"}
                        </button>
                      </div>
                      {categorizedCopyStatus && <p className="small">{categorizedCopyStatus}</p>}
                      {categorizedSaveStatus && <p className="small">{categorizedSaveStatus}</p>}
                      <p className="small">
                        Source:
                        {" "}
                        <code>{categorizedSelectedPath}</code>
                      </p>
                      <p className="small">
                        Folder: <code>{toDisplayFolderPath(categorizedSelectedPath)}</code>
                      </p>
                      <p className="small">
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(categorizedSelectedPath)}&download=1`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Download selected file
                        </a>
                      </p>
                      <div className="field">
                        {categorizedTableError ? (
                          <label htmlFor="categorized-editor">In-place file editor</label>
                        ) : (
                          <p className="small">In-place file editor</p>
                        )}
                        {categorizedTableError ? (
                          <>
                            <p className="small" role="alert">
                              {categorizedTableError}
                            </p>
                            <textarea
                              id="categorized-editor"
                              rows={16}
                              value={categorizedEditorText}
                              onChange={(e) => {
                                setCategorizedEditorText(e.target.value);
                                setCategorizedCopyStatus("");
                                setCategorizedSaveStatus("");
                              }}
                              disabled={categorizedSaving}
                            />
                          </>
                        ) : (
                          <>
                            <div className="csv-grid-nav" aria-label="Horizontal scroll controls">
                              <button
                                type="button"
                                className="csv-grid-nav-btn"
                                onClick={() => nudgeCategorizedHorizontal("left")}
                                disabled={categorizedSaving}
                              >
                                Scroll left
                              </button>
                              <button
                                type="button"
                                className="csv-grid-nav-btn"
                                onClick={() => nudgeCategorizedHorizontal("right")}
                                disabled={categorizedSaving}
                              >
                                Scroll right
                              </button>
                            </div>
                            <div className="csv-grid-slider">
                              <label className="small" htmlFor="categorized-horizontal-scroll">
                                Drag left/right
                              </label>
                              <input
                                id="categorized-horizontal-scroll"
                                className="csv-grid-slider-input"
                                type="range"
                                min={0}
                                max={Math.max(1, categorizedScrollMax)}
                                value={Math.min(categorizedScrollLeft, Math.max(1, categorizedScrollMax))}
                                onChange={(e) => handleCategorizedHorizontalSlider(e.target.value)}
                                disabled={categorizedSaving || categorizedScrollMax <= 0}
                                aria-label="Horizontal drag scrollbar"
                              />
                            </div>
                            <div
                              className="csv-grid-top-scroll"
                              aria-hidden="true"
                              ref={categorizedGridTopScrollRef}
                              onScroll={handleCategorizedGridTopScroll}
                            >
                              <div className="csv-grid-top-spacer" ref={categorizedGridTopSpacerRef} />
                            </div>
                            <div className="csv-grid-frame">
                              <button
                                type="button"
                                className="csv-grid-edge-btn left"
                                onClick={() => nudgeCategorizedHorizontal("left")}
                                disabled={categorizedSaving || !categorizedCanScrollLeft}
                                aria-label="Scroll table left"
                              >
                                {"<"}
                              </button>
                              <button
                                type="button"
                                className="csv-grid-edge-btn right"
                                onClick={() => nudgeCategorizedHorizontal("right")}
                                disabled={categorizedSaving || !categorizedCanScrollRight}
                                aria-label="Scroll table right"
                              >
                                {">"}
                              </button>
                              <div
                                className="csv-grid-shell"
                                aria-label="In-place file editor"
                                ref={categorizedGridShellRef}
                                onScroll={handleCategorizedGridShellScroll}
                              >
                                <div className="csv-grid-content">
                                  <table className="csv-grid-table">
                                    <thead>
                                      <tr className="csv-grid-head">
                                        <th className="csv-grid-index">#</th>
                                        {(categorizedVisibleRows[0] || []).map((cell, colIndex) => (
                                          <th key={`header-${colIndex}`}>
                                            <input
                                              className="csv-grid-input"
                                              value={cell}
                                              onChange={(e) =>
                                                updateCategorizedCell(0, colIndex, e.target.value)
                                              }
                                              disabled={categorizedSaving}
                                            />
                                          </th>
                                        ))}
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {categorizedVisibleRows.slice(1).map((row, rowIndex) => (
                                        <tr key={`row-${rowIndex + 1}`}>
                                          <th className="csv-grid-index">{rowIndex + 2}</th>
                                          {row.map((cell, colIndex) => (
                                            <td key={`cell-${rowIndex + 1}-${colIndex}`}>
                                              <input
                                                className="csv-grid-input"
                                                value={cell}
                                                onChange={(e) =>
                                                  updateCategorizedCell(
                                                    rowIndex + 1,
                                                    colIndex,
                                                    e.target.value
                                                  )
                                                }
                                                disabled={categorizedSaving}
                                              />
                                            </td>
                                          ))}
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            </div>
                            {categorizedHiddenRowCount > 0 && (
                              <p className="small">
                                Showing first 50 tickets by default. {categorizedHiddenRowCount} more
                                row(s) are still in the file.
                              </p>
                            )}
                          </>
                        )}
                      </div>
                    </>
                  ) : (
                    <p className="small">Pick a file from the list to inspect details here.</p>
                  )}
                </div>
              </article>
            </div>
          )}

          {stage === "input" && workflow === "browse-rules" && (
            <div className="grid" aria-label="Input section">
              <article className="card ticket-browser-card">
                <div className="ticket-browser-header">
                  <h2>View Rules Engines</h2>
                  <button
                    type="button"
                    onClick={() => {
                      void loadRulesFiles();
                    }}
                    disabled={isRunning || rulesFilesLoading}
                  >
                    {rulesFilesLoading ? "Refreshing..." : "Refresh list"}
                  </button>
                </div>
                <div className="field">
                  <label htmlFor="rule-engine-source">Rules source</label>
                  <select
                    id="rule-engine-source"
                    value={rulesSource}
                    onChange={(e) => {
                      const nextSource = e.target.value as RulesSource;
                      setRulesSource(nextSource);
                      setRulesLoadedDir("");
                      setRulesFiles([]);
                      setRulesSelectedPath("");
                      setRulesPreview("");
                      setRulesEditorText("");
                      setRulesTableRows([]);
                      setRulesTableError("");
                      setRulesPreviewError("");
                      setRulesCopyStatus("");
                      setRulesSaveStatus("");
                    }}
                    disabled={isRunning || rulesFilesLoading}
                  >
                    <option value="trained-data">trained-data (default)</option>
                    <option value="golden">golden-rules-engine</option>
                  </select>
                </div>
                <p className="small">
                  Source directory: <code>{rulesDirectory}</code>
                </p>
                <div className="field">
                  <label htmlFor="rule-engine-filter">Filter loaded files</label>
                  <input
                    id="rule-engine-filter"
                    placeholder="rule-engine"
                    value={rulesFilter}
                    onChange={(e) => setRulesFilter(e.target.value)}
                    disabled={isRunning || rulesFilesLoading || rulesFiles.length === 0}
                  />
                </div>
                {rulesFilesError && (
                  <p className="small" role="alert">
                    {rulesFilesError}
                  </p>
                )}
                {!rulesFilesError && (
                  <p className="small">
                    {rulesFilesLoading
                      ? "Loading rule engine files..."
                      : `${rulesFiles.length} file(s) visible in ${rulesLoadedDir || rulesDirectory}.`}
                  </p>
                )}
                {visibleRulesFiles.length === 0 && !rulesFilesLoading ? (
                  <p className="small">
                    {rulesFiles.length === 0
                      ? `Directory is empty: ${rulesLoadedDir || rulesDirectory}.`
                      : "No files match the current filter."}
                  </p>
                ) : (
                  <ul className="ticket-picker-list is-expanded" aria-label="Rule engine files list">
                    {visibleRulesFiles.map((file) => (
                      <li
                        key={file.path}
                        className={`ticket-picker-item ${
                          file.path === rulesSelectedPath ? "is-selected" : ""
                        }`}
                      >
                        <button
                          type="button"
                          className="ticket-pick-btn"
                          onClick={() => {
                            void loadRulesPreview(file.path);
                          }}
                          disabled={isRunning}
                        >
                          {file.name}
                        </button>
                        <p className="small ticket-meta">
                          Updated: {formatTimestamp(file.modifiedAt)} | Size: {file.sizeBytes} bytes
                        </p>
                        <p className="small ticket-meta">
                          Folder: <code>{toDisplayFolderPath(file.path)}</code>
                        </p>
                        <a
                          className="link small"
                          href={`/api/open-file?path=${encodeURIComponent(file.path)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open file
                        </a>
                      </li>
                    ))}
                  </ul>
                )}
                {filteredRulesFiles.length > visibleRulesFiles.length && (
                  <p className="small">
                    Showing first {visibleRulesFiles.length} results. Keep filtering to narrow the
                    list.
                  </p>
                )}
                <div className="ticket-detail-view">
                  <h3>Selected File (View/Edit)</h3>
                  {rulesPreviewLoading ? (
                    <p className="small">Loading file preview...</p>
                  ) : rulesPreviewError ? (
                    <p className="small" role="alert">
                      {rulesPreviewError}
                    </p>
                  ) : rulesSelectedPath ? (
                    <>
                      <div className="inline-actions">
                        <button
                          type="button"
                          onClick={() =>
                            copyText(
                              "Rule engine file contents",
                              rulesCurrentText,
                              setRulesCopyStatus
                            )
                          }
                          disabled={rulesPreviewLoading}
                        >
                          Copy details
                        </button>
                        <button
                          type="button"
                          onClick={resetRulesChanges}
                          disabled={rulesSaving || !rulesHasChanges}
                        >
                          Reset changes
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            void saveRulesFile();
                          }}
                          disabled={rulesSaving || !rulesHasChanges}
                        >
                          {rulesSaving ? "Saving..." : "Save changes"}
                        </button>
                      </div>
                      {rulesCopyStatus && <p className="small">{rulesCopyStatus}</p>}
                      {rulesSaveStatus && <p className="small">{rulesSaveStatus}</p>}
                      <p className="small">
                        Source:
                        {" "}
                        <code>{rulesSelectedPath}</code>
                      </p>
                      <p className="small">
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(rulesSelectedPath)}&download=1`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Download selected file
                        </a>
                      </p>
                      <div className="field">
                        {rulesTableError ? (
                          <label htmlFor="rules-editor">In-place file editor</label>
                        ) : (
                          <p className="small">In-place file editor</p>
                        )}
                        {rulesTableError ? (
                          <>
                            <p className="small" role="alert">
                              {rulesTableError}
                            </p>
                            <textarea
                              id="rules-editor"
                              rows={16}
                              value={rulesEditorText}
                              onChange={(e) => {
                                setRulesEditorText(e.target.value);
                                setRulesCopyStatus("");
                                setRulesSaveStatus("");
                              }}
                              disabled={rulesSaving}
                            />
                          </>
                        ) : (
                          <>
                            <div className="csv-grid-nav" aria-label="Horizontal scroll controls">
                              <button
                                type="button"
                                className="csv-grid-nav-btn"
                                onClick={() => nudgeRulesHorizontal("left")}
                                disabled={rulesSaving}
                              >
                                Scroll left
                              </button>
                              <button
                                type="button"
                                className="csv-grid-nav-btn"
                                onClick={() => nudgeRulesHorizontal("right")}
                                disabled={rulesSaving}
                              >
                                Scroll right
                              </button>
                            </div>
                            <div className="csv-grid-slider">
                              <label className="small" htmlFor="rules-horizontal-scroll">
                                Drag left/right
                              </label>
                              <input
                                id="rules-horizontal-scroll"
                                className="csv-grid-slider-input"
                                type="range"
                                min={0}
                                max={Math.max(1, rulesScrollMax)}
                                value={Math.min(rulesScrollLeft, Math.max(1, rulesScrollMax))}
                                onChange={(e) => handleRulesHorizontalSlider(e.target.value)}
                                disabled={rulesSaving || rulesScrollMax <= 0}
                                aria-label="Horizontal drag scrollbar"
                              />
                            </div>
                            <div
                              className="csv-grid-top-scroll"
                              aria-hidden="true"
                              ref={rulesGridTopScrollRef}
                              onScroll={handleRulesGridTopScroll}
                            >
                              <div className="csv-grid-top-spacer" ref={rulesGridTopSpacerRef} />
                            </div>
                            <div className="csv-grid-frame">
                              <button
                                type="button"
                                className="csv-grid-edge-btn left"
                                onClick={() => nudgeRulesHorizontal("left")}
                                disabled={rulesSaving || !rulesCanScrollLeft}
                                aria-label="Scroll table left"
                              >
                                {"<"}
                              </button>
                              <button
                                type="button"
                                className="csv-grid-edge-btn right"
                                onClick={() => nudgeRulesHorizontal("right")}
                                disabled={rulesSaving || !rulesCanScrollRight}
                                aria-label="Scroll table right"
                              >
                                {">"}
                              </button>
                              <div
                                className="csv-grid-shell"
                                aria-label="In-place file editor"
                                ref={rulesGridShellRef}
                                onScroll={handleRulesGridShellScroll}
                              >
                                <div className="csv-grid-content">
                                  <table className="csv-grid-table">
                                    <thead>
                                      <tr className="csv-grid-head">
                                        <th className="csv-grid-index">#</th>
                                        {(rulesVisibleRows[0] || []).map((cell, colIndex) => (
                                          <th key={`rh-${colIndex}`}>
                                            <input
                                              className="csv-grid-input"
                                              value={cell}
                                              onChange={(e) =>
                                                updateRulesCell(0, colIndex, e.target.value)
                                              }
                                              disabled={rulesSaving}
                                            />
                                          </th>
                                        ))}
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {rulesVisibleRows.slice(1).map((row, rowIndex) => (
                                        <tr key={`rr-${rowIndex + 1}`}>
                                          <th className="csv-grid-index">{rowIndex + 2}</th>
                                          {row.map((cell, colIndex) => (
                                            <td key={`rc-${rowIndex + 1}-${colIndex}`}>
                                              <input
                                                className="csv-grid-input"
                                                value={cell}
                                                onChange={(e) =>
                                                  updateRulesCell(
                                                    rowIndex + 1,
                                                    colIndex,
                                                    e.target.value
                                                  )
                                                }
                                                disabled={rulesSaving}
                                              />
                                            </td>
                                          ))}
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            </div>
                            {rulesHiddenRowCount > 0 && (
                              <p className="small">
                                Showing first 50 rows by default. {rulesHiddenRowCount} more
                                row(s) are still in the file.
                              </p>
                            )}
                          </>
                        )}
                      </div>
                    </>
                  ) : (
                    <p className="small">Pick a file from the list to inspect details here.</p>
                  )}
                </div>
              </article>
            </div>
          )}

          {stage === "input" && workflow === "browse-ml-model" && (
            <div className="grid" aria-label="Input section">
              <article className="card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                  <h2>View ML Models</h2>
                  <button
                    type="button"
                    onClick={() => { setMlViewData(null); void loadMlModelInfo(); }}
                    disabled={mlViewLoading}
                  >
                    {mlViewLoading ? "Loading..." : "Refresh"}
                  </button>
                </div>

                <div className="field">
                  <label htmlFor="ml-view-mode">View mode</label>
                  <select
                    id="ml-view-mode"
                    value={mlViewMode}
                    onChange={(e) => setMlViewMode(e.target.value as "single" | "compare")}
                  >
                    <option value="single">Single source</option>
                    <option value="compare">Side-by-side comparison</option>
                  </select>
                </div>

                {mlViewMode === "single" && (
                  <div className="field">
                    <label htmlFor="ml-view-source">Model source</label>
                    <select
                      id="ml-view-source"
                      value={mlViewSource}
                      onChange={(e) => setMlViewSource(e.target.value as MlModelSource)}
                    >
                      <option value="working">Working (ml-model/)</option>
                      <option value="golden">Golden (golden-ml-model/)</option>
                    </select>
                    <p className="small">
                      Source directory: <code>{ML_MODEL_SOURCE_DIRS[mlViewSource]}</code>
                    </p>
                  </div>
                )}

                {mlViewError && (
                  <p className="small" role="alert" style={{ color: "var(--color-error, #c00)" }}>
                    {mlViewError}
                  </p>
                )}

                {mlViewLoading && <p className="small">Loading ML model information...</p>}

                {mlViewData && mlViewMode === "single" && (() => {
                  const model = mlViewData[mlViewSource];
                  return (
                    <div>
                      <p className="small" style={{ fontWeight: "bold", color: model.exists ? "#2a7" : "#c33" }}>
                        {model.exists ? "Available" : "Not found"}
                      </p>
                      {model.exists && (
                        <>
                          <table style={{ borderCollapse: "collapse", width: "100%", marginBottom: "1rem" }}>
                            <thead>
                              <tr>
                                <th style={{ textAlign: "left", padding: "4px 12px" }}>File</th>
                                <th style={{ textAlign: "left", padding: "4px 12px" }}>Details</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr>
                                <td style={{ padding: "4px 12px" }}>classifier.joblib</td>
                                <td style={{ padding: "4px 12px" }}>
                                  {formatBytes(model.sizeBytes)} — modified {model.modifiedAt ? new Date(model.modifiedAt).toLocaleString() : "-"}
                                  <br /><span className="small" style={{ color: "#888" }}>Binary model file (not viewable)</span>
                                </td>
                              </tr>
                              <tr>
                                <td style={{ padding: "4px 12px" }}>training_report.txt</td>
                                <td style={{ padding: "4px 12px" }}>{model.report ? "Present" : "Not available"}</td>
                              </tr>
                              <tr>
                                <td style={{ padding: "4px 12px" }}>category_map.json</td>
                                <td style={{ padding: "4px 12px" }}>{model.categoryMap ? `${Object.keys(model.categoryMap).length} categories` : "Not available"}</td>
                              </tr>
                            </tbody>
                          </table>
                          {model.report && (
                            <>
                              <h3>Training Report</h3>
                              <pre style={{ background: "#f5f5f5", padding: "0.75rem", borderRadius: 6, fontSize: "0.8rem", maxHeight: 300, overflow: "auto", whiteSpace: "pre-wrap" }}>
                                {model.report}
                              </pre>
                            </>
                          )}
                          {model.categoryMap && Object.keys(model.categoryMap).length > 0 && (
                            <>
                              <h3>Category Map</h3>
                              <table style={{ borderCollapse: "collapse", width: "100%", marginBottom: "1rem" }}>
                                <thead>
                                  <tr>
                                    <th style={{ textAlign: "left", padding: "4px 12px" }}>Internal Category</th>
                                    <th style={{ textAlign: "left", padding: "4px 12px" }}>Display Name</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {Object.entries(model.categoryMap).map(([key, val]) => (
                                    <tr key={key}>
                                      <td style={{ padding: "4px 12px" }}>{key}</td>
                                      <td style={{ padding: "4px 12px" }}>{val}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </>
                          )}
                        </>
                      )}
                    </div>
                  );
                })()}

                {mlViewData && mlViewMode === "compare" && (
                  <div>
                    {mlViewData.identical && (
                      <p className="small" style={{ color: "#2a7", fontWeight: "bold" }}>
                        Models are identical.
                      </p>
                    )}
                    <table style={{ borderCollapse: "collapse", width: "100%", marginBottom: "1rem" }}>
                      <thead>
                        <tr>
                          <th style={{ textAlign: "left", padding: "4px 12px" }}></th>
                          <th style={{ textAlign: "left", padding: "4px 12px" }}>Working (ml-model/)</th>
                          <th style={{ textAlign: "left", padding: "4px 12px" }}>Golden (golden-ml-model/)</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td style={{ padding: "4px 12px", fontWeight: "bold" }}>Status</td>
                          <td style={{ padding: "4px 12px", color: mlViewData.working.exists ? "#2a7" : "#c33" }}>
                            {mlViewData.working.exists ? "Available" : "Not found"}
                          </td>
                          <td style={{ padding: "4px 12px", color: mlViewData.golden.exists ? "#2a7" : "#c33" }}>
                            {mlViewData.golden.exists ? "Available" : "Not found"}
                          </td>
                        </tr>
                        <tr>
                          <td style={{ padding: "4px 12px", fontWeight: "bold" }}>Size</td>
                          <td style={{ padding: "4px 12px" }}>{mlViewData.working.exists ? formatBytes(mlViewData.working.sizeBytes) : "-"}</td>
                          <td style={{ padding: "4px 12px" }}>{mlViewData.golden.exists ? formatBytes(mlViewData.golden.sizeBytes) : "-"}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: "4px 12px", fontWeight: "bold" }}>Last Modified</td>
                          <td style={{ padding: "4px 12px" }}>{mlViewData.working.modifiedAt ? new Date(mlViewData.working.modifiedAt).toLocaleString() : "-"}</td>
                          <td style={{ padding: "4px 12px" }}>{mlViewData.golden.modifiedAt ? new Date(mlViewData.golden.modifiedAt).toLocaleString() : "-"}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: "4px 12px", fontWeight: "bold" }}>Categories</td>
                          <td style={{ padding: "4px 12px" }}>{mlViewData.working.categoryMap ? Object.keys(mlViewData.working.categoryMap).length : "-"}</td>
                          <td style={{ padding: "4px 12px" }}>{mlViewData.golden.categoryMap ? Object.keys(mlViewData.golden.categoryMap).length : "-"}</td>
                        </tr>
                      </tbody>
                    </table>

                    <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                      {mlViewData.working.report && (
                        <div style={{ flex: "1 1 45%", minWidth: 300 }}>
                          <h3>Working Model Report</h3>
                          <pre style={{ background: "#f5f5f5", padding: "0.75rem", borderRadius: 6, fontSize: "0.8rem", maxHeight: 300, overflow: "auto", whiteSpace: "pre-wrap" }}>
                            {mlViewData.working.report}
                          </pre>
                        </div>
                      )}
                      {mlViewData.golden.report && (
                        <div style={{ flex: "1 1 45%", minWidth: 300 }}>
                          <h3>Golden Model Report</h3>
                          <pre style={{ background: "#f5f5f5", padding: "0.75rem", borderRadius: 6, fontSize: "0.8rem", maxHeight: 300, overflow: "auto", whiteSpace: "pre-wrap" }}>
                            {mlViewData.golden.report}
                          </pre>
                        </div>
                      )}
                    </div>

                    <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", marginTop: "1rem" }}>
                      {mlViewData.working.categoryMap && Object.keys(mlViewData.working.categoryMap).length > 0 && (
                        <div style={{ flex: "1 1 45%", minWidth: 300 }}>
                          <h3>Working Category Map</h3>
                          <table style={{ borderCollapse: "collapse", width: "100%" }}>
                            <thead>
                              <tr>
                                <th style={{ textAlign: "left", padding: "4px 12px" }}>Internal Category</th>
                                <th style={{ textAlign: "left", padding: "4px 12px" }}>Display Name</th>
                              </tr>
                            </thead>
                            <tbody>
                              {Object.entries(mlViewData.working.categoryMap).map(([key, val]) => (
                                <tr key={key}>
                                  <td style={{ padding: "4px 12px" }}>{key}</td>
                                  <td style={{ padding: "4px 12px" }}>{val}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                      {mlViewData.golden.categoryMap && Object.keys(mlViewData.golden.categoryMap).length > 0 && (
                        <div style={{ flex: "1 1 45%", minWidth: 300 }}>
                          <h3>Golden Category Map</h3>
                          <table style={{ borderCollapse: "collapse", width: "100%" }}>
                            <thead>
                              <tr>
                                <th style={{ textAlign: "left", padding: "4px 12px" }}>Internal Category</th>
                                <th style={{ textAlign: "left", padding: "4px 12px" }}>Display Name</th>
                              </tr>
                            </thead>
                            <tbody>
                              {Object.entries(mlViewData.golden.categoryMap).map(([key, val]) => (
                                <tr key={key}>
                                  <td style={{ padding: "4px 12px" }}>{key}</td>
                                  <td style={{ padding: "4px 12px" }}>{val}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </article>
            </div>
          )}

          {stage === "input" && workflow === "add-rule" && (
            <div className="grid" aria-label="Input section">
              <div className="field">
                <label htmlFor="rule-ticket-key">Ticket key</label>
                <input
                  id="rule-ticket-key"
                  placeholder="HPC-123456"
                  value={ticketKey}
                  onChange={(e) => setTicketKey(e.target.value.toUpperCase())}
                  disabled={isRunning}
                />
                <p className="small">
                  Required. Matches script prompt: <code>Ticket key (e.g. HPC-123456)</code>.
                </p>
                <p className="small">
                  Use the <strong>Tickets in Normalized root</strong> tab to browse and inspect
                  ticket payloads.
                </p>
              </div>
              <div className="field">
                <label htmlFor="rule-reason">Why should a new rule be added?</label>
                <textarea
                  id="rule-reason"
                  rows={3}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-failure-category">Category of Issue</label>
                <input
                  id="rule-failure-category"
                  value={failureCategory}
                  onChange={(e) => setFailureCategory(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-category">Category</label>
                <input
                  id="rule-category"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-match-field">Match Field</label>
                <input
                  id="rule-match-field"
                  placeholder="Leave blank to use default"
                  value={matchField}
                  onChange={(e) => setMatchField(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-pattern">Rule Pattern</label>
                <input
                  id="rule-pattern"
                  placeholder="Leave blank to auto-generate"
                  value={rulePattern}
                  onChange={(e) => setRulePattern(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-ticket-json-dir">Ticket JSON dir</label>
                <input
                  id="rule-ticket-json-dir"
                  value={ticketJsonDir}
                  onChange={(e) => setTicketJsonDir(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-normalized-root">Normalized root</label>
                <input
                  id="rule-normalized-root"
                  value={normalizedRoot}
                  onChange={(e) => setNormalizedRoot(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-rules-engine">Rules engine</label>
                <input
                  id="rule-rules-engine"
                  value={rulesEngine}
                  onChange={(e) => setRulesEngine(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-match-field-default">CLI --match-field-default</label>
                <input
                  id="rule-match-field-default"
                  value={matchFieldDefault}
                  onChange={(e) => setMatchFieldDefault(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-priority">Priority</label>
                <input
                  id="rule-priority"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-confidence">Confidence</label>
                <input
                  id="rule-confidence"
                  value={confidence}
                  onChange={(e) => setConfidence(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-created-by">Created By</label>
                <input
                  id="rule-created-by"
                  value={createdBy}
                  onChange={(e) => setCreatedBy(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-hit-count">Hit Count</label>
                <input
                  id="rule-hit-count"
                  value={hitCount}
                  onChange={(e) => setHitCount(e.target.value)}
                  disabled={isRunning}
                />
              </div>
              <div>
                <button className="primary" onClick={handleOk} disabled={isRunning}>
                  {isRunning ? "Running..." : "OK"}
                </button>
              </div>
              {error && (
                <p className="small" role="alert">
                  {error}
                </p>
              )}
            </div>
          )}

          {stage === "input" && workflow === "train-stc" && (
            <div className="grid" aria-label="Input section">
              <fieldset className="field">
                <legend>Ticket source (either-or)</legend>
                <label>
                  <input
                    type="radio"
                    name="train-input-mode"
                    value="jql"
                    checked={trainInputMode === "jql"}
                    onChange={() => setTrainInputMode("jql")}
                    disabled={isRunning}
                  />{" "}
                  JQL
                </label>
                <label>
                  <input
                    type="radio"
                    name="train-input-mode"
                    value="files"
                    checked={trainInputMode === "files"}
                    onChange={() => setTrainInputMode("files")}
                    disabled={isRunning}
                  />{" "}
                  Ticket list files
                </label>
                <label>
                  <input
                    type="radio"
                    name="train-input-mode"
                    value="tickets"
                    checked={trainInputMode === "tickets"}
                    onChange={() => setTrainInputMode("tickets")}
                    disabled={isRunning}
                  />{" "}
                  Ticket IDs
                </label>
              </fieldset>

              <div className="field">
                <label htmlFor="train-jql">Enter JQL</label>
                <textarea
                  id="train-jql"
                  rows={3}
                  value={trainJql}
                  onChange={(e) => setTrainJql(e.target.value)}
                  disabled={isRunning || trainInputMode !== "jql"}
                />
              </div>
              <fieldset className="field">
                <legend>Ticket resolution filter</legend>
                <label>
                  <input
                    type="radio"
                    name="train-resolution-mode"
                    value="all"
                    checked={trainResolutionMode === "all"}
                    onChange={() => setTrainResolutionMode("all")}
                    disabled={isRunning || trainInputMode !== "jql"}
                  />{" "}
                  All (resolved + unresolved)
                </label>
                <label>
                  <input
                    type="radio"
                    name="train-resolution-mode"
                    value="resolved-only"
                    checked={trainResolutionMode === "resolved-only"}
                    onChange={() => setTrainResolutionMode("resolved-only")}
                    disabled={isRunning || trainInputMode !== "jql"}
                  />{" "}
                  Resolved only
                </label>
                <label>
                  <input
                    type="radio"
                    name="train-resolution-mode"
                    value="unresolved-only"
                    checked={trainResolutionMode === "unresolved-only"}
                    onChange={() => setTrainResolutionMode("unresolved-only")}
                    disabled={isRunning || trainInputMode !== "jql"}
                  />{" "}
                  Unresolved only
                </label>
              </fieldset>
              <div className="field">
                <label htmlFor="train-tickets-file">Enter ticket list files</label>
                <input
                  id="train-tickets-file"
                  value={trainTicketsFile}
                  onChange={(e) => setTrainTicketsFile(e.target.value)}
                  disabled={isRunning || trainInputMode !== "files"}
                />
              </div>
              <div className="field">
                <label htmlFor="train-tickets-text">Enter list of ticket IDs</label>
                <textarea
                  id="train-tickets-text"
                  rows={2}
                  value={trainTicketsText}
                  onChange={(e) => setTrainTicketsText(e.target.value)}
                  disabled={isRunning || trainInputMode !== "tickets"}
                />
                <p className="small">Comma or newline-separated, e.g. HPC-110621,HPC-110615</p>
              </div>

              <details>
                <summary className="small"><strong>Advanced training parameters</strong></summary>
                <div className="field">
                  <label htmlFor="train-training-data">Training data CSV</label>
                  <input
                    id="train-training-data"
                    value={trainTrainingData}
                    onChange={(e) => setTrainTrainingData(e.target.value)}
                    disabled={isRunning}
                  />
                  <p className="small">CSV with columns: Ticket, Category of Issue, Category</p>
                </div>
                <div className="field">
                  <label htmlFor="train-min-samples">Min samples</label>
                  <input
                    id="train-min-samples"
                    value={trainMinSamples}
                    onChange={(e) => setTrainMinSamples(e.target.value)}
                    disabled={isRunning}
                  />
                  <p className="small">Minimum labeled samples required to train (default: 20)</p>
                </div>
                <div className="field">
                  <label htmlFor="train-max-review-rows">Max review rows</label>
                  <input
                    id="train-max-review-rows"
                    value={trainMaxReviewRows}
                    onChange={(e) => setTrainMaxReviewRows(e.target.value)}
                    disabled={isRunning}
                  />
                  <p className="small">Maximum review rows for rule generation (default: 200)</p>
                </div>
              </details>

              <div style={{ display: "flex", gap: "1rem", margin: "0.5rem 0" }}>
                <label className="small">
                  <input
                    type="checkbox"
                    checked={skipAudit1}
                    onChange={(e) => setSkipAudit1(e.target.checked)}
                    disabled={isRunning}
                  />{" "}
                  Skip Human Audit #1
                </label>
                <label className="small">
                  <input
                    type="checkbox"
                    checked={skipAudit2}
                    onChange={(e) => setSkipAudit2(e.target.checked)}
                    disabled={isRunning}
                  />{" "}
                  Skip Human Audit #2
                </label>
              </div>

              <div>
                <button className="primary" onClick={handleOk} disabled={isRunning}>
                  {isRunning ? "Running..." : "OK"}
                </button>
              </div>
              {error && (
                <p className="small" role="alert">
                  {error}
                </p>
              )}
            </div>
          )}

          {stage === "input" && workflow === "promote-to-golden" && (
            <div className="grid" aria-label="Input section">
              <div className="field">
                <label htmlFor="promote-source">Source (trained-data rules)</label>
                <input
                  id="promote-source"
                  value={promoteSourcePath}
                  onChange={(e) => setPromoteSourcePath(e.target.value)}
                  disabled={promoteLoading || promoteSaving}
                />
              </div>
              <div className="field">
                <label htmlFor="promote-target">Target (golden rules)</label>
                <input
                  id="promote-target"
                  value={promoteTargetPath}
                  onChange={(e) => setPromoteTargetPath(e.target.value)}
                  disabled={promoteLoading || promoteSaving}
                />
              </div>
              <div>
                <button
                  className="primary"
                  onClick={loadPromoteDiff}
                  disabled={promoteLoading || promoteSaving || !promoteSourcePath.trim() || !promoteTargetPath.trim()}
                >
                  {promoteLoading ? "Loading..." : "Load Diff"}
                </button>
              </div>
              {promoteError && (
                <p className="small" role="alert" style={{ color: "var(--color-error, #c00)" }}>
                  {promoteError}
                </p>
              )}
              {promoteResult && (
                <p className="small" role="status">
                  {promoteResult}
                </p>
              )}
              {promoteDiff.length > 0 && (
                <>
                  <article className="card">
                    <h2>Diff Summary</h2>
                    <p className="small">
                      <span style={{ color: "#2a7" }}>{promoteDiff.filter((r) => r.status === "added").length} added</span>
                      {" · "}
                      <span style={{ color: "#c80" }}>{promoteDiff.filter((r) => r.status === "changed").length} changed</span>
                      {" · "}
                      <span style={{ color: "#c33" }}>{promoteDiff.filter((r) => r.status === "removed").length} removed</span>
                      {" · "}
                      {promoteDiff.filter((r) => r.status === "unchanged").length} unchanged
                    </p>
                  </article>
                  {promoteDiff.every((r) => r.status === "unchanged") ? (
                    <p className="small">Files are identical — nothing to promote.</p>
                  ) : (
                    <article className="card">
                      <h2>Changes</h2>
                      <div className="pipeline-scroll">
                        <table className="summary-table">
                          <thead>
                            <tr>
                              <th>Status</th>
                              {promoteHeaders.map((h) => (
                                <th key={h}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {promoteDiff
                              .filter((r) => r.status !== "unchanged" || promoteShowUnchanged)
                              .map((r) => (
                                <tr
                                  key={`${r.status}-${r.ruleId}`}
                                  style={{
                                    background:
                                      r.status === "added"
                                        ? "rgba(42,170,70,0.1)"
                                        : r.status === "removed"
                                          ? "rgba(204,51,51,0.1)"
                                          : r.status === "changed"
                                            ? "rgba(200,128,0,0.1)"
                                            : "transparent"
                                  }}
                                >
                                  <td>
                                    {r.status === "added" && <span style={{ color: "#2a7" }}>+ added</span>}
                                    {r.status === "removed" && <span style={{ color: "#c33" }}>- removed</span>}
                                    {r.status === "changed" && <span style={{ color: "#c80" }}>~ changed</span>}
                                    {r.status === "unchanged" && <span>= same</span>}
                                  </td>
                                  {(r.sourceRow || r.targetRow || []).map((cell, ci) => (
                                    <td key={ci}>{cell}</td>
                                  ))}
                                </tr>
                              ))}
                          </tbody>
                        </table>
                      </div>
                      {promoteDiff.some((r) => r.status === "unchanged") && (
                        <button
                          className="small"
                          onClick={() => setPromoteShowUnchanged(!promoteShowUnchanged)}
                          style={{ marginTop: "0.5rem" }}
                        >
                          {promoteShowUnchanged
                            ? "Hide unchanged rules"
                            : `Show ${promoteDiff.filter((r) => r.status === "unchanged").length} unchanged rules`}
                        </button>
                      )}
                    </article>
                  )}
                  {!promoteDiff.every((r) => r.status === "unchanged") && !promoteConfirming && (
                    <div>
                      <button
                        className="primary"
                        onClick={() => setPromoteConfirming(true)}
                        disabled={promoteSaving}
                      >
                        Promote to Golden
                      </button>
                    </div>
                  )}
                  {promoteConfirming && (
                    <article className="card" aria-label="Confirm promotion">
                      <h2>Confirm Promotion</h2>
                      <p className="small">
                        Overwrite <strong>golden rule-engine.csv</strong> with{" "}
                        {promoteDiff.filter((r) => r.status !== "removed").length} rules from trained-data?
                        This action is hard to reverse.
                      </p>
                      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
                        <button
                          className="primary"
                          onClick={handlePromote}
                          disabled={promoteSaving}
                        >
                          {promoteSaving ? "Saving..." : "Confirm Promote"}
                        </button>
                        <button
                          onClick={() => setPromoteConfirming(false)}
                          disabled={promoteSaving}
                        >
                          Cancel
                        </button>
                      </div>
                    </article>
                  )}
                </>
              )}

              {/* --- ML Model Promotion --- */}
              <hr style={{ margin: "1.5rem 0", border: "none", borderTop: "1px solid #ddd" }} />
              <h2>ML Model</h2>
              <div className="field">
                <label htmlFor="ml-source">Source (working ML model directory)</label>
                <input
                  id="ml-source"
                  value={mlSourceDir}
                  onChange={(e) => setMlSourceDir(e.target.value)}
                  disabled={mlPromoteLoading || mlPromoteSaving}
                />
              </div>
              <div className="field">
                <label htmlFor="ml-target">Target (golden ML model directory)</label>
                <input
                  id="ml-target"
                  value={mlTargetDir}
                  onChange={(e) => setMlTargetDir(e.target.value)}
                  disabled={mlPromoteLoading || mlPromoteSaving}
                />
              </div>
              <div>
                <button
                  className="primary"
                  onClick={loadMlCompare}
                  disabled={mlPromoteLoading || mlPromoteSaving || !mlSourceDir.trim() || !mlTargetDir.trim()}
                >
                  {mlPromoteLoading ? "Loading..." : "Compare ML Models"}
                </button>
              </div>
              {mlPromoteError && (
                <p className="small" role="alert" style={{ color: "var(--color-error, #c00)" }}>
                  {mlPromoteError}
                </p>
              )}
              {mlPromoteResult && (
                <p className="small" role="status">{mlPromoteResult}</p>
              )}
              {mlCompare && (
                <article className="card">
                  <h2>ML Model Comparison</h2>
                  <table style={{ borderCollapse: "collapse", width: "100%", marginBottom: "1rem" }}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: "left", padding: "4px 12px" }}></th>
                        <th style={{ textAlign: "left", padding: "4px 12px" }}>Working (trained-data/ml-model)</th>
                        <th style={{ textAlign: "left", padding: "4px 12px" }}>Golden (golden-ml-model)</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td style={{ padding: "4px 12px", fontWeight: "bold" }}>Status</td>
                        <td style={{ padding: "4px 12px", color: mlCompare.working.exists ? "#2a7" : "#c33" }}>
                          {mlCompare.working.exists ? "Available" : "Not found"}
                        </td>
                        <td style={{ padding: "4px 12px", color: mlCompare.golden.exists ? "#2a7" : "#c33" }}>
                          {mlCompare.golden.exists ? "Available" : "Not found"}
                        </td>
                      </tr>
                      <tr>
                        <td style={{ padding: "4px 12px", fontWeight: "bold" }}>Size</td>
                        <td style={{ padding: "4px 12px" }}>{mlCompare.working.exists ? `${(mlCompare.working.sizeBytes / 1024).toFixed(1)} KB` : "-"}</td>
                        <td style={{ padding: "4px 12px" }}>{mlCompare.golden.exists ? `${(mlCompare.golden.sizeBytes / 1024).toFixed(1)} KB` : "-"}</td>
                      </tr>
                      <tr>
                        <td style={{ padding: "4px 12px", fontWeight: "bold" }}>Last Modified</td>
                        <td style={{ padding: "4px 12px" }}>{mlCompare.working.modifiedAt ? new Date(mlCompare.working.modifiedAt).toLocaleString() : "-"}</td>
                        <td style={{ padding: "4px 12px" }}>{mlCompare.golden.modifiedAt ? new Date(mlCompare.golden.modifiedAt).toLocaleString() : "-"}</td>
                      </tr>
                    </tbody>
                  </table>
                  {mlCompare.identical && (
                    <p className="small">Models are identical — nothing to promote.</p>
                  )}
                  {mlCompare.working.report && (
                    <>
                      <h3>Working Model Report</h3>
                      <pre style={{ background: "#f5f5f5", padding: "0.75rem", borderRadius: 6, fontSize: "0.8rem", maxHeight: 200, overflow: "auto", whiteSpace: "pre-wrap" }}>
                        {mlCompare.working.report}
                      </pre>
                    </>
                  )}
                  {mlCompare.golden.report && (
                    <>
                      <h3>Golden Model Report</h3>
                      <pre style={{ background: "#f5f5f5", padding: "0.75rem", borderRadius: 6, fontSize: "0.8rem", maxHeight: 200, overflow: "auto", whiteSpace: "pre-wrap" }}>
                        {mlCompare.golden.report}
                      </pre>
                    </>
                  )}
                  {mlCompare.working.exists && !mlCompare.identical && !mlPromoteConfirming && (
                    <div style={{ marginTop: "0.5rem" }}>
                      <button
                        className="primary"
                        onClick={() => setMlPromoteConfirming(true)}
                        disabled={mlPromoteSaving}
                      >
                        Promote ML Model to Golden
                      </button>
                    </div>
                  )}
                  {mlPromoteConfirming && (
                    <div style={{ marginTop: "0.75rem", padding: "0.75rem", border: "1px solid #c80", borderRadius: 6, background: "rgba(200,128,0,0.05)" }}>
                      <p className="small" style={{ margin: "0 0 0.5rem 0" }}>
                        Overwrite <strong>golden ML model</strong> with the working model?
                        This replaces the audited production model. This action is hard to reverse.
                      </p>
                      <div style={{ display: "flex", gap: "0.5rem" }}>
                        <button
                          className="primary"
                          onClick={handleMlPromote}
                          disabled={mlPromoteSaving}
                        >
                          {mlPromoteSaving ? "Promoting..." : "Confirm Promote"}
                        </button>
                        <button
                          onClick={() => setMlPromoteConfirming(false)}
                          disabled={mlPromoteSaving}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </article>
              )}
            </div>
          )}

          {stage === "results" && (
            <div className="grid" aria-label="Results section">
              <span className={`badge run-state-${runState}`}>
                {isRunning
                  ? workflow === "categorize"
                    ? "Live local pipeline run (in progress)"
                    : workflow === "train-stc"
                      ? "Live training pipeline run (in progress)"
                      : "Live local add-rule run (in progress)"
                  : workflow === "categorize"
                    ? "Live local pipeline run"
                    : workflow === "train-stc"
                      ? "Live training pipeline run"
                      : "Live local add-rule run"}
              </span>
              {isRunning && (
                <p className={`small heartbeat-row run-state-${runState}`}>
                  <span className={`heartbeat-dot ${heartbeatTick % 2 === 0 ? "on" : ""} run-state-${runState}`} />
                  Heartbeat active
                  {lastLogAtMs
                    ? ` | Last log ${Math.floor((Date.now() - lastLogAtMs) / 1000)}s ago`
                    : " | Waiting for first log..."}
                </p>
              )}
              {workflow === "categorize" && (
                <p className="small">
                  Pipeline completed via: `get_tickets.py` → `normalize_tickets.py` →
                  `rule_engine_categorize.py` → `create_summary.py`
                </p>
              )}
              {workflow === "categorize" && inputMode === "jql" && (
                <p className="small">Resolution filter used: {resolutionMode}</p>
              )}
              {workflow === "categorize" && (
                <article className="card">
                  <h2>Pipeline Stages</h2>
                  <div className="pipeline-scroll">
                    <div className="pipeline-grid">
                      {PIPELINE_STEPS.map((step, idx) => (
                        <div key={step} className={`pipeline-step step-${pipelineStatus[idx]}`}>
                          <p className="pipeline-name">{step}</p>
                          <p className="pipeline-state">{pipelineStatus[idx]}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </article>
              )}
              {workflow === "train-stc" && (
                <article className="card">
                  <h2>Pipeline Stages</h2>
                  <div className="pipeline-scroll">
                    <div className="pipeline-grid">
                      {TRAIN_PIPELINE_STEPS.map((step, idx) => (
                        <div key={step} className={`pipeline-step step-${trainStcPipelineStatus[idx] || "pending"}`}>
                          <p className="pipeline-name">{step}</p>
                          <p className="pipeline-state">{trainStcPipelineStatus[idx] || "pending"}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </article>
              )}
              <p className="small">
                Started: {formatTimestamp(startedAt)} | Finished: {formatTimestamp(finishedAt)} |
                {" "}Elapsed: {isRunning
                  ? `${(liveElapsedMs / 1000).toFixed(2)}s`
                  : elapsedMs > 0
                    ? `${(elapsedMs / 1000).toFixed(2)}s`
                    : "-"}
              </p>
              {wasCanceled && (
                <p className="small">Run was canceled and artifacts were cleaned.</p>
              )}
              {workflow === "categorize" ? (
                <div className="cards">
                  <article className="card">
                    <h2>Summary Output</h2>
                    {summaryRows.length === 0 ? (
                      <p className="small">No summary rows returned.</p>
                    ) : (
                      <table className="summary-table">
                        <thead>
                          <tr>
                            <th>Category</th>
                            <th>Percent</th>
                            <th>Count</th>
                          </tr>
                        </thead>
                        <tbody>
                          {summaryRows.map((row) => (
                            <tr key={`${row["Tickets Category"]}-${row["Count of Tickets"]}`}>
                              <td>{row["Tickets Category"]}</td>
                              <td>{row["Percentage of Total Tickets"]}</td>
                              <td>{row["Count of Tickets"]}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </article>
                  <article className="card">
                    <h2>Raw Data</h2>
                    <p className="small">
                      {resultPaths.ticketsCsv ? (
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(resultPaths.ticketsCsv)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {resultPaths.ticketsCsv}
                        </a>
                      ) : (
                        "tickets-categorized.csv"
                      )}
                    </p>
                    <p className="small">
                      {resultPaths.summaryCsv ? (
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(resultPaths.summaryCsv)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {resultPaths.summaryCsv}
                        </a>
                      ) : (
                        "tickets-summary.csv"
                      )}
                    </p>
                  </article>
                </div>
              ) : workflow === "train-stc" ? (
                <div className="cards">
                  {trainPaused && (
                    <article className="card" aria-label="Human audit">
                      <h2>Human Audit — Phase {trainPhase}</h2>
                      <p className="small">
                        Review and optionally edit tickets-categorized.csv before continuing.
                      </p>
                      {trainAuditCsvPath && (
                        <p className="small">
                          File path:{" "}
                          <code>{trainAuditCsvPath}</code>
                          {" "}
                          <button
                            className="small"
                            onClick={() => copyText("File path", trainAuditCsvPath, setTrainAuditSaveStatus)}
                          >
                            Copy path
                          </button>
                        </p>
                      )}
                      {trainAuditRows.length > 0 && (
                        <div className="grid-shell" style={{ maxHeight: "400px", overflow: "auto" }}>
                          <table className="summary-table">
                            <thead>
                              <tr>
                                {trainAuditRows[0]?.map((header, colIdx) => (
                                  <th key={colIdx}>{header}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {trainAuditRows.slice(1).map((row, rowIdx) => (
                                <tr key={rowIdx}>
                                  {row.map((cell, colIdx) => (
                                    <td key={colIdx}>
                                      <input
                                        type="text"
                                        value={cell}
                                        onChange={(e) =>
                                          updateTrainAuditCell(rowIdx + 1, colIdx, e.target.value)
                                        }
                                        style={{ width: "100%", minWidth: "80px", border: "1px solid #ccc", padding: "2px 4px", fontSize: "0.85em" }}
                                      />
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                      {trainAuditRows.length === 0 && trainAuditCsvPath && (
                        <p className="small">Could not load CSV for inline editing. Use the file path above to edit externally.</p>
                      )}
                      <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                        <button
                          className="primary"
                          onClick={saveTrainAudit}
                          disabled={trainAuditSaving || !trainAuditHasChanges}
                        >
                          {trainAuditSaving ? "Saving..." : "Save Changes"}
                        </button>
                        <button onClick={resetTrainAudit} disabled={trainAuditSaving || !trainAuditHasChanges}>
                          Reset
                        </button>
                        <span className="small">
                          {trainAuditHasChanges ? "Unsaved changes" : "No changes"}
                        </span>
                        {trainAuditSaveStatus && (
                          <span className="small">{trainAuditSaveStatus}</span>
                        )}
                      </div>
                      <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem" }}>
                        <button
                          className="primary"
                          onClick={handleContinueTraining}
                          aria-label="Continue Pipeline"
                        >
                          Continue Pipeline
                        </button>
                        <button onClick={handleCancelTrainAudit} aria-label="Cancel Training">
                          Cancel Training
                        </button>
                      </div>
                    </article>
                  )}
                  {!trainPaused && (
                    <>
                  <article className="card">
                    <h2>Training Pipeline Result</h2>
                    <p className="small">{trainStcResult.message || "Waiting for completion..."}</p>
                    {trainStcResult.trainingSamples !== undefined && (
                      <p className="small">Training samples: {trainStcResult.trainingSamples}</p>
                    )}
                    {trainStcResult.cvAccuracy && (
                      <p className="small">CV Accuracy: {trainStcResult.cvAccuracy}</p>
                    )}
                    {trainStcResult.rulesAdded !== undefined && (
                      <p className="small">Rules added: {trainStcResult.rulesAdded}</p>
                    )}
                  </article>
                  <article className="card">
                    <h2>Output Artifacts</h2>
                    {trainStcResult.ticketsCsv && (
                      <p className="small">
                        Tickets CSV:{" "}
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(trainStcResult.ticketsCsv)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {trainStcResult.ticketsCsv}
                        </a>
                      </p>
                    )}
                    {trainStcResult.localRules && (
                      <p className="small">
                        Local rules:{" "}
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(trainStcResult.localRules)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {trainStcResult.localRules}
                        </a>
                      </p>
                    )}
                    {trainStcResult.mlModel && (
                      <p className="small">
                        ML model:{" "}
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(trainStcResult.mlModel)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {trainStcResult.mlModel}
                        </a>
                      </p>
                    )}
                    {trainStcResult.mlReport && (
                      <p className="small">
                        ML report:{" "}
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(trainStcResult.mlReport)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {trainStcResult.mlReport}
                        </a>
                      </p>
                    )}
                    {trainStcResult.trainingLog && (
                      <p className="small">
                        Training log:{" "}
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(trainStcResult.trainingLog)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {trainStcResult.trainingLog}
                        </a>
                      </p>
                    )}
                    {trainStcResult.outputDir && (
                      <p className="small">
                        Output directory:{" "}
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(trainStcResult.outputDir)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {trainStcResult.outputDir}
                        </a>
                      </p>
                    )}
                    {!trainStcResult.ticketsCsv && !trainStcResult.mlModel && !trainStcResult.trainingLog && (
                      <p className="small">No output artifacts yet.</p>
                    )}
                  </article>
                    </>
                  )}
                </div>
              ) : (
                <div className="cards">
                  <article className="card">
                    <h2>Add Rule Result</h2>
                    <p className="small">{addRuleResult.message || "Waiting for completion..."}</p>
                    {addRuleResult.ruleId && (
                      <p className="small">
                        Rule ID: <code>{addRuleResult.ruleId}</code>
                      </p>
                    )}
                  </article>
                  <article className="card">
                    <h2>Output Artifacts</h2>
                    <p className="small">
                      {addRuleResult.rulesEngine ? (
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(addRuleResult.rulesEngine)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {addRuleResult.rulesEngine}
                        </a>
                      ) : (
                        "Rules engine path not available."
                      )}
                    </p>
                    <p className="small">
                      {addRuleResult.ticketJson ? (
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(addRuleResult.ticketJson)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {addRuleResult.ticketJson}
                        </a>
                      ) : (
                        "Ticket JSON not found."
                      )}
                    </p>
                    <p className="small">
                      {addRuleResult.normalizedJson ? (
                        <a
                          className="link"
                          href={`/api/open-file?path=${encodeURIComponent(addRuleResult.normalizedJson)}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {addRuleResult.normalizedJson}
                        </a>
                      ) : (
                        "Normalized ticket JSON not found."
                      )}
                    </p>
                  </article>
                </div>
              )}
              <article className="card">
                <h2>Executed Commands</h2>
                <div className="copy-actions">
                  <button
                    onClick={() => copyText("Commands", executedCommands.join("\n"))}
                    disabled={executedCommands.length === 0}
                  >
                    Copy commands
                  </button>
                  <button
                    onClick={() => copyText("Logs", commandLogs.join("\n"))}
                    disabled={commandLogs.length === 0}
                  >
                    Copy logs
                  </button>
                </div>
                {copyStatus && <p className="small">{copyStatus}</p>}
                {executedCommands.length === 0 ? (
                  <p className="small">Waiting for first command...</p>
                ) : (
                  <ul className="cmd-list">
                    {executedCommands.map((command) => (
                      <li key={command}>
                        <code>{command}</code>
                      </li>
                    ))}
                  </ul>
                )}
                <h3>Live Logs</h3>
                <label className="small wrap-toggle">
                  <input
                    type="checkbox"
                    checked={wrapLogs}
                    onChange={(e) => setWrapLogs(e.target.checked)}
                  />{" "}
                  Wrap lines
                </label>
                <pre ref={logBlockRef} className={`log-block ${wrapLogs ? "wrap" : "no-wrap"}`}>
                  {commandLogs.length === 0
                    ? "No logs yet."
                    : commandLogs.join("\n")}
                </pre>
              </article>
              {workflow === "categorize" && (
                <article className="card">
                  <h2>Graphs of the data</h2>
                  <p className="small">Graph region placeholder for wireframe</p>
                </article>
              )}
            </div>
          )}
        </div>
      </section>
      <p className="footer-note">
        #ai-assisted author: Rik (Human) and OCA GPT5.1 codex (LLM) | {renderedAt}
      </p>
    </main>
  );
}
