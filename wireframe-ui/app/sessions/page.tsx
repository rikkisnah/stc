// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
"use client";

import { useCallback, useEffect, useState } from "react";

type SessionInfo = {
  runId: string;
  createdAt: string;
  status: "completed" | "paused" | "failed" | "in-progress";
  phase: number;
  ticketCount: number;
  rulesCount: number;
  outputDir: string;
};

type SessionDetail = {
  runId: string;
  outputDir: string;
  phaseMeta: Record<string, unknown> | null;
  ticketCount: number;
  rulesCount: number;
  mlReport: string;
  artifacts: {
    ticketsCsv: string | null;
    localRules: string | null;
    mlModel: string | null;
    mlLog: string | null;
    trainingLog: string | null;
  };
  files: string[];
};

const STATUS_COLORS: Record<string, string> = {
  completed: "#22c55e",
  paused: "#eab308",
  failed: "#ef4444",
  "in-progress": "#3b82f6",
};

export default function SessionsPage() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    fetch("/api/sessions/list")
      .then((r) => r.json())
      .then((data) => setSessions(data.sessions || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const loadDetail = useCallback(async (runId: string) => {
    setSelectedRunId(runId);
    setDetailLoading(true);
    setDetailError("");
    setDetail(null);
    try {
      const res = await fetch("/api/sessions/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ runId }),
      });
      if (!res.ok) throw new Error(`Failed to load session: ${res.status}`);
      setDetail(await res.json());
    } catch (e) {
      setDetailError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const deleteSession = useCallback(async (runId: string) => {
    try {
      const res = await fetch("/api/sessions/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ runId }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ error: "Delete failed" }));
        setError(data.error || `Delete failed: ${res.status}`);
        return;
      }
      setSessions((prev) => prev.filter((s) => s.runId !== runId));
      if (selectedRunId === runId) {
        setSelectedRunId(null);
        setDetail(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }, [selectedRunId]);

  function openFile(filePath: string) {
    window.open(`/api/open-file?path=${encodeURIComponent(filePath)}`, "_blank");
  }

  return (
    <div style={{ padding: "2rem", fontFamily: "monospace", maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <h1 style={{ margin: 0 }}>Past Training Sessions</h1>
        <a href="/" style={{ color: "#3b82f6" }}>&larr; Back to Dashboard</a>
      </div>

      {loading && <p>Loading sessions...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {!loading && sessions.length === 0 && (
        <p data-testid="empty-state" style={{ color: "#888" }}>No training sessions found. Run a training pipeline to see sessions here.</p>
      )}

      {!loading && sessions.length > 0 && (
        <div style={{ display: "flex", gap: "2rem" }}>
          {/* Sessions list */}
          <div style={{ flex: "0 0 400px", maxHeight: "80vh", overflowY: "auto" }}>
            {sessions.map((s) => (
              <div
                key={s.runId}
                data-testid="session-item"
                onClick={() => loadDetail(s.runId)}
                style={{
                  padding: "0.75rem",
                  marginBottom: "0.5rem",
                  border: selectedRunId === s.runId ? "2px solid #3b82f6" : "1px solid #ddd",
                  borderRadius: 6,
                  cursor: "pointer",
                  background: selectedRunId === s.runId ? "#f0f7ff" : "#fff",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong style={{ fontSize: "0.85rem" }}>{s.runId}</strong>
                  <span
                    data-testid="status-badge"
                    style={{
                      padding: "2px 8px",
                      borderRadius: 12,
                      fontSize: "0.75rem",
                      color: "#fff",
                      background: STATUS_COLORS[s.status] || "#888",
                    }}
                  >
                    {s.status}
                  </span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#666", marginTop: 4 }}>
                  Phase {s.phase} &middot; {s.ticketCount} tickets &middot; {s.rulesCount} rules
                </div>
                <div style={{ fontSize: "0.75rem", color: "#999", marginTop: 2, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span>{new Date(s.createdAt).toLocaleString()}</span>
                  <button
                    data-testid="delete-session-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(s.runId);
                    }}
                    style={{
                      background: "#ef4444",
                      color: "#fff",
                      border: "none",
                      borderRadius: 4,
                      padding: "2px 8px",
                      fontSize: "0.7rem",
                      cursor: "pointer",
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Detail panel */}
          <div style={{ flex: 1, minWidth: 0 }}>
            {!selectedRunId && <p style={{ color: "#888" }}>Select a session to view details.</p>}
            {detailLoading && <p>Loading session details...</p>}
            {detailError && <p style={{ color: "red" }}>{detailError}</p>}
            {detail && (
              <div>
                <h2 style={{ marginTop: 0 }}>{detail.runId}</h2>
                <table style={{ borderCollapse: "collapse", marginBottom: "1rem" }}>
                  <tbody>
                    <tr><td style={{ padding: "4px 12px 4px 0", fontWeight: "bold" }}>Tickets</td><td>{detail.ticketCount}</td></tr>
                    <tr><td style={{ padding: "4px 12px 4px 0", fontWeight: "bold" }}>Rules</td><td>{detail.rulesCount}</td></tr>
                    <tr><td style={{ padding: "4px 12px 4px 0", fontWeight: "bold" }}>Output</td><td style={{ fontSize: "0.8rem" }}>{detail.outputDir}</td></tr>
                    <tr><td style={{ padding: "4px 12px 4px 0", fontWeight: "bold" }}>Files</td><td style={{ fontSize: "0.8rem" }}>{detail.files.join(", ")}</td></tr>
                  </tbody>
                </table>

                <h3>Artifacts</h3>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                  {detail.artifacts.ticketsCsv && (
                    <button onClick={() => openFile(detail.artifacts.ticketsCsv!)}>Open tickets CSV</button>
                  )}
                  {detail.artifacts.localRules && (
                    <button onClick={() => openFile(detail.artifacts.localRules!)}>Open local rules</button>
                  )}
                  {detail.artifacts.mlLog && (
                    <button onClick={() => openFile(detail.artifacts.mlLog!)}>Open ML log</button>
                  )}
                  {detail.artifacts.trainingLog && (
                    <button onClick={() => openFile(detail.artifacts.trainingLog!)}>Open training log</button>
                  )}
                </div>

                {detail.mlReport && (
                  <>
                    <h3>ML Report Preview</h3>
                    <pre style={{ background: "#f5f5f5", padding: "1rem", borderRadius: 6, fontSize: "0.8rem", maxHeight: 300, overflow: "auto", whiteSpace: "pre-wrap" }}>
                      {detail.mlReport}
                    </pre>
                  </>
                )}

                {detail.phaseMeta && (
                  <>
                    <h3>Phase Metadata</h3>
                    <pre style={{ background: "#f5f5f5", padding: "1rem", borderRadius: 6, fontSize: "0.8rem" }}>
                      {JSON.stringify(detail.phaseMeta, null, 2)}
                    </pre>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
