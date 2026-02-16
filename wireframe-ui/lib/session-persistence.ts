// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted

export type PipelineStepStatus = "pending" | "running" | "done" | "failed";

export type SessionState = {
  schemaVersion: number;
  workflow: "train-stc";
  trainRunId: string;
  trainPhase: 1 | 2 | 3;
  isRunning: boolean;
  startedAt: string;
  elapsedMs: number;
  pipelineStatus: PipelineStepStatus[];
  resultPaths: { ticketsCsv?: string; outputDir?: string; normalizedDir?: string; localRules?: string };
  trainStcResult: {
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
  error: string;
  wasCanceled: boolean;
  executedCommandsCount: number;
  lastCommandSnippet: string;
  savedAt: number;
};

const STORAGE_KEY = "stc-session-state";
const CURRENT_SCHEMA_VERSION = 1;
const STALE_THRESHOLD_MS = 24 * 60 * 60 * 1000; // 24 hours

export function saveSessionState(state: SessionState): void {
  try {
    const toStore: SessionState = { ...state, schemaVersion: CURRENT_SCHEMA_VERSION, savedAt: Date.now() };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore));
  } catch {
    // localStorage full or unavailable — best effort
  }
}

export function loadSessionState(): SessionState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as SessionState;
    if (parsed.schemaVersion !== CURRENT_SCHEMA_VERSION) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function clearSessionState(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // best effort
  }
}

export function isSessionStale(state: SessionState): boolean {
  if (!state.savedAt) return true;
  return Date.now() - state.savedAt > STALE_THRESHOLD_MS;
}
