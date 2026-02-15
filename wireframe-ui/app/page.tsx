// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
"use client";

import { useEffect, useRef, useState } from "react";

type Stage = "landing" | "input" | "results";
type InputMode = "jql" | "files" | "tickets";
type ResolutionMode = "all" | "unresolved-only" | "resolved-only";
type SummaryRow = {
  "Tickets Category": string;
  "Percentage of Total Tickets": string;
  "Count of Tickets": string;
  "JQL Query": string;
};

export default function HomePage() {
  const [stage, setStage] = useState<Stage>("landing");
  const [inputMode, setInputMode] = useState<InputMode>("jql");
  const [jql, setJql] = useState('project="High Performance Computing"');
  const [resolutionMode, setResolutionMode] = useState<ResolutionMode>("all");
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");
  const [summaryRows, setSummaryRows] = useState<SummaryRow[]>([]);
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
  const abortRef = useRef<AbortController | null>(null);

  function formatTimestamp(iso: string): string {
    if (!iso) {
      return "-";
    }
    return new Date(iso).toLocaleString();
  }

  useEffect(() => {
    setRenderedAt(new Date().toLocaleString());
  }, []);

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

  async function handleOk() {
    if (inputMode !== "jql") {
      setStage("results");
      return;
    }

    setIsRunning(true);
    setError("");
    setSummaryRows([]);
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

    try {
      const abortController = new AbortController();
      abortRef.current = abortController;
      const response = await fetch("/api/run-jql", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jql, resolutionMode }),
        signal: abortController.signal
      });
      if (!response.ok) {
        const fallback = (await response.json()) as { error?: string };
        throw new Error(fallback.error || "Failed to run pipeline.");
      }

      if (!response.body) {
        const data = (await response.json()) as {
          error?: string;
          summaryRows?: SummaryRow[];
          paths?: { ticketsCsv?: string; summaryCsv?: string; normalizedDir?: string };
        };
        if (data.error) {
          throw new Error(data.error);
        }
        setSummaryRows(data.summaryRows || []);
        setResultPaths(data.paths || {});
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
              paths?: { ticketsCsv?: string; summaryCsv?: string; normalizedDir?: string };
            };

            if (event.type === "command-start" && event.command) {
              setLastLogAtMs(Date.now());
              setExecutedCommands((prev) =>
                prev.includes(event.command as string) ? prev : [...prev, event.command as string]
              );
              setCommandLogs((prev) => [...prev, `> ${event.command}`]);
            } else if ((event.type === "stdout" || event.type === "stderr") && event.line) {
              const linesFromEvent = event.line.split(/\r?\n/).filter((chunk) => chunk.trim());
              if (linesFromEvent.length > 0) {
                setLastLogAtMs(Date.now());
                setCommandLogs((prev) => [...prev, ...linesFromEvent]);
              }
            } else if (event.type === "done") {
              setSummaryRows(event.summaryRows || []);
              setResultPaths(event.paths || {});
            } else if (event.type === "canceled") {
              setWasCanceled(true);
              setError("Run canceled. Artifacts cleaned.");
              setSummaryRows([]);
              setResultPaths({});
            } else if (event.type === "error") {
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
      } else {
        setError(message);
      }
    } finally {
      abortRef.current = null;
      const ended = new Date().toISOString();
      setFinishedAt(ended);
      setElapsedMs(Math.max(0, Date.parse(ended) - Date.parse(runStartedAt)));
      setIsRunning(false);
    }
  }

  function handleCancel() {
    abortRef.current?.abort();
  }

  async function copyText(label: string, text: string) {
    try {
      if (!text.trim()) {
        setCopyStatus(`No ${label.toLowerCase()} to copy.`);
        return;
      }
      await navigator.clipboard.writeText(text);
      setCopyStatus(`${label} copied.`);
    } catch {
      try {
        const area = document.createElement("textarea");
        area.value = text;
        document.body.appendChild(area);
        area.select();
        document.execCommand("copy");
        document.body.removeChild(area);
        setCopyStatus(`${label} copied.`);
      } catch {
        setCopyStatus(`Failed to copy ${label.toLowerCase()}.`);
      }
    }
  }

  return (
    <main>
      <section className="panel">
        <header className="header">
          <h1 className="title">Smart (Sudha&apos;s) Tickets&apos; Classifier (STC)</h1>
          <p className="subtitle">v0.1 wireframe preview</p>
        </header>

        <div className="actions">
          <button
            className="primary"
            onClick={() => setStage("input")}
            aria-label="Categorize unresolved tickets"
            disabled={isRunning}
          >
            Categorize unresolved tickets
          </button>
          <button disabled aria-label="Train Learn WIP">
            Train Learn (WIP)
          </button>
          {isRunning && (
            <button onClick={handleCancel} aria-label="Cancel run">
              Cancel
            </button>
          )}
        </div>

        <div className="content">
          {stage === "landing" && (
            <p className="small">
              Click <strong>Categorize unresolved tickets</strong> to preview the next
              wireframe step.
            </p>
          )}

          {stage === "input" && (
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
                  placeholder="scripts/normalized-tickets/2026-02-15"
                  disabled={inputMode !== "files"}
                />
              </div>
              <div className="field">
                <label htmlFor="ticket-list">Enter list of ticket IDs</label>
                <textarea
                  id="ticket-list"
                  rows={4}
                  placeholder="DCOPS-101, DCOPS-102, DCOPS-103"
                  disabled={inputMode !== "tickets"}
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

          {stage === "results" && (
            <div className="grid" aria-label="Results section">
              <span className="badge">
                {inputMode === "jql"
                  ? isRunning
                    ? "Live local pipeline run (in progress)"
                    : "Live local pipeline run"
                  : "Mocked output only (no backend call)"}
              </span>
              {isRunning && (
                <p className="small heartbeat-row">
                  <span className={`heartbeat-dot ${heartbeatTick % 2 === 0 ? "on" : ""}`} />
                  Heartbeat active
                  {lastLogAtMs
                    ? ` | Last log ${Math.floor((Date.now() - lastLogAtMs) / 1000)}s ago`
                    : " | Waiting for first log..."}
                </p>
              )}
              {inputMode === "jql" && (
                <p className="small">
                  Pipeline completed via: `get_tickets.py` → `normalize_tickets.py` →
                  `rule_engine_categorize.py` → `create_summary.py`
                </p>
              )}
              {inputMode === "jql" && (
                <p className="small">Resolution filter used: {resolutionMode}</p>
              )}
              {inputMode === "jql" && (
                <p className="small">
                  Started: {formatTimestamp(startedAt)} | Finished: {formatTimestamp(finishedAt)} |
                  {" "}Elapsed: {isRunning
                    ? `${(liveElapsedMs / 1000).toFixed(2)}s`
                    : elapsedMs > 0
                      ? `${(elapsedMs / 1000).toFixed(2)}s`
                      : "-"}
                </p>
              )}
              {wasCanceled && (
                <p className="small">Run was canceled and artifacts were cleaned.</p>
              )}
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
                    {resultPaths.ticketsCsv || "tickets-categorized.csv"}
                  </p>
                  <p className="small">
                    {resultPaths.summaryCsv || "tickets-summary.csv"}
                  </p>
                </article>
              </div>
              {inputMode === "jql" && (
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
                  <pre className="log-block">
                    {commandLogs.length === 0
                      ? "No logs yet."
                      : commandLogs.join("\n")}
                  </pre>
                </article>
              )}
              <article className="card">
                <h2>Graphs of the data</h2>
                <p className="small">Graph region placeholder for wireframe</p>
              </article>
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
