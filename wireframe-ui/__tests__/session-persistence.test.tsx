// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import {
  saveSessionState,
  loadSessionState,
  clearSessionState,
  isSessionStale,
  type SessionState,
} from "../lib/session-persistence";

function makeState(overrides: Partial<SessionState> = {}): SessionState {
  return {
    schemaVersion: 2,
    workflow: "train-stc",
    trainRunId: "train-2026-02-16T04-08-00-167Z",
    trainPhase: 1,
    isRunning: true,
    startedAt: "2026-02-16T04:08:00.167Z",
    elapsedMs: 5000,
    pipelineStatus: ["done", "running", "pending", "pending", "pending", "pending", "pending", "pending", "pending", "pending"],
    resultPaths: {},
    trainStcResult: {},
    error: "",
    wasCanceled: false,
    executedCommandsCount: 3,
    lastCommandSnippet: "normalize_tickets.py",
    savedAt: Date.now(),
    ...overrides,
  };
}

describe("session-persistence", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe("saveSessionState / loadSessionState", () => {
    it("round-trips a session state", () => {
      const state = makeState();
      saveSessionState(state);
      const loaded = loadSessionState();
      expect(loaded).not.toBeNull();
      expect(loaded!.trainRunId).toBe(state.trainRunId);
      expect(loaded!.trainPhase).toBe(1);
      expect(loaded!.isRunning).toBe(true);
      expect(loaded!.schemaVersion).toBe(2);
    });

    it("overwrites previous state on save", () => {
      saveSessionState(makeState({ trainPhase: 1 }));
      saveSessionState(makeState({ trainPhase: 2 }));
      const loaded = loadSessionState();
      expect(loaded!.trainPhase).toBe(2);
    });

    it("returns null when nothing is stored", () => {
      expect(loadSessionState()).toBeNull();
    });

    it("returns null for invalid JSON", () => {
      localStorage.setItem("stc-session-state", "not json");
      expect(loadSessionState()).toBeNull();
    });

    it("returns null for wrong schema version", () => {
      saveSessionState(makeState());
      const raw = JSON.parse(localStorage.getItem("stc-session-state")!);
      raw.schemaVersion = 999;
      localStorage.setItem("stc-session-state", JSON.stringify(raw));
      expect(loadSessionState()).toBeNull();
    });
  });

  describe("clearSessionState", () => {
    it("removes stored state", () => {
      saveSessionState(makeState());
      expect(loadSessionState()).not.toBeNull();
      clearSessionState();
      expect(loadSessionState()).toBeNull();
    });

    it("does not throw when nothing is stored", () => {
      expect(() => clearSessionState()).not.toThrow();
    });
  });

  describe("isSessionStale", () => {
    it("returns false for recent state", () => {
      const state = makeState({ savedAt: Date.now() - 1000 });
      expect(isSessionStale(state)).toBe(false);
    });

    it("returns true for state older than 24 hours", () => {
      const state = makeState({ savedAt: Date.now() - 25 * 60 * 60 * 1000 });
      expect(isSessionStale(state)).toBe(true);
    });

    it("returns true when savedAt is 0", () => {
      const state = makeState({ savedAt: 0 });
      expect(isSessionStale(state)).toBe(true);
    });
  });
});
