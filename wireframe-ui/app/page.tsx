// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
"use client";

import { useEffect, useRef, useState } from "react";

type Stage = "landing" | "input" | "results";
type InputMode = "jql" | "files" | "tickets";
type ResolutionMode = "all" | "unresolved-only" | "resolved-only";
type PipelineStepStatus = "pending" | "running" | "done" | "failed";
type SummaryRow = {
  "Tickets Category": string;
  "Percentage of Total Tickets": string;
  "Count of Tickets": string;
  "JQL Query": string;
};

const PIPELINE_STEPS = [
  "get_tickets.py",
  "normalize_tickets.py",
  "rule_engine_categorize.py",
  "create_summary.py"
] as const;

export default function HomePage() {
  const [stage, setStage] = useState<Stage>("landing");
  const [inputMode, setInputMode] = useState<InputMode>("jql");
  const [jql, setJql] = useState(
    'project="High Performance Computing" and createdDate >= "2026-02-10" and createdDate <= "2026-02-11"'
  );
  const [resolutionMode, setResolutionMode] = useState<ResolutionMode>("all");
  const [ticketsFile, setTicketsFile] = useState(
    "scripts/analysis/ui-runs/templates/tickets-template.txt"
  );
  const [ticketsText, setTicketsText] = useState("HPC-110621,HPC-110615");
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
  const [wrapLogs, setWrapLogs] = useState(true);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStepStatus[]>(
    PIPELINE_STEPS.map(() => "pending")
  );
  const abortRef = useRef<AbortController | null>(null);

  function formatTimestamp(iso: string): string {
    if (!iso) {
      return "-";
    }
    return new Date(iso).toLocaleString();
  }

  function nowTime(): string {
    return new Date().toLocaleTimeString();
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
    setPipelineStatus(PIPELINE_STEPS.map(() => "pending"));

    try {
      const abortController = new AbortController();
      abortRef.current = abortController;
      const response = await fetch("/api/run-jql", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ inputMode, jql, resolutionMode, ticketsFile, ticketsText }),
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
              setLastLogAtMs(Date.now());
              setExecutedCommands((prev) =>
                prev.includes(event.command as string) ? prev : [...prev, event.command as string]
              );
              setCommandLogs((prev) => [...prev, `[${nowTime()}] > ${event.command}`]);
            } else if (event.type === "command-end" && event.command) {
              const endIdx = PIPELINE_STEPS.findIndex((step) => event.command?.includes(step));
              if (endIdx >= 0) {
                setPipelineStatus((prev) =>
                  prev.map((status, idx) => (idx === endIdx ? "done" : status))
                );
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
            } else if (event.type === "done") {
              setPipelineStatus(PIPELINE_STEPS.map(() => "done"));
              setSummaryRows(event.summaryRows || []);
              setResultPaths(event.paths || {});
            } else if (event.type === "canceled") {
              setWasCanceled(true);
              setError("Run canceled. Artifacts cleaned.");
              setSummaryRows([]);
              setResultPaths({});
            } else if (event.type === "error") {
              setPipelineStatus((prev) => {
                const runningIdx = prev.findIndex((status) => status === "running");
                if (runningIdx === -1) {
                  return prev;
                }
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

  const runState =
    isRunning ? "running" : error ? "failed" : finishedAt ? "success" : "idle";

  return (
    <main>
      <section className="panel">
        <header className="header">
          <h1 className="title">
            <button
              className="home-link"
              onClick={() => setStage("landing")}
              aria-label="Go to home"
            >
              Smart (Sudha&apos;s) Tickets&apos; Classifier (STC)
            </button>
          </h1>
          <p className="subtitle">v0.1 wireframe preview</p>
        </header>

        <div className="actions">
          <button
            className="primary"
            onClick={() => setStage("input")}
            aria-label="Categorize tickets"
            disabled={isRunning}
          >
            Categorize tickets
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
              Click <strong>Categorize tickets</strong> to preview the next
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
              <span className={`badge run-state-${runState}`}>
                {isRunning
                  ? "Live local pipeline run (in progress)"
                  : "Live local pipeline run"}
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
              {stage === "results" && (
                <p className="small">
                  Pipeline completed via: `get_tickets.py` → `normalize_tickets.py` →
                  `rule_engine_categorize.py` → `create_summary.py`
                </p>
              )}
              {inputMode === "jql" && (
                <p className="small">Resolution filter used: {resolutionMode}</p>
              )}
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
                <pre className={`log-block ${wrapLogs ? "wrap" : "no-wrap"}`}>
                  {commandLogs.length === 0
                    ? "No logs yet."
                    : commandLogs.join("\n")}
                </pre>
              </article>
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
