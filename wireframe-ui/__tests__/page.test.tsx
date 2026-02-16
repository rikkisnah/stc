// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import HomePage from "../app/page";

const originalFetch = global.fetch;

/**
 * Create a mock Response with an NDJSON body stream that works in jsdom.
 * Returns { ok, body } where body.getReader() returns a functioning reader.
 */
function mockNdjsonResponse(ndjsonLines: string[]) {
  const encoded = new TextEncoder().encode(ndjsonLines.join("\n") + "\n");
  let read = false;
  return {
    ok: true,
    body: {
      getReader() {
        return {
          read() {
            if (!read) {
              read = true;
              return Promise.resolve({ value: encoded, done: false });
            }
            return Promise.resolve({ value: undefined, done: true });
          }
        };
      }
    }
  };
}

describe("STC wireframe flow", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", window.location.pathname);
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ tickets: [] })
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    jest.restoreAllMocks();
    global.fetch = originalFetch;
    window.history.replaceState(null, "", window.location.pathname);
  });

  it("shows landing view by default", () => {
    render(<HomePage />);

    expect(
      screen.getByText(/smart.*tickets' classifier/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/to preview the next wireframe step/i)).toBeInTheDocument();
  });

  it("shows input fields after clicking categorize", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /categorize tickets/i }));

    expect(screen.getByLabelText(/enter jql/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/enter ticket list files/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/enter list of ticket ids/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/ticket resolution filter/i)).toBeInTheDocument();
    expect(
      screen.getByDisplayValue(
        'project="High Performance Computing" and createdDate >= "2026-02-10" and createdDate <= "2026-02-11"'
      )
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^ok$/i })).toBeInTheDocument();
  });

  it("shows add-rule inputs with script-matching defaults", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /add rule for a ticket/i }));

    expect(screen.getByLabelText(/ticket key/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/why should a new rule be added/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/category of issue/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^category$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/match field/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/rule pattern/i)).toBeInTheDocument();

    expect(screen.getByDisplayValue("scripts/tickets-json")).toBeInTheDocument();
    expect(screen.getByDisplayValue("scripts/normalized-tickets")).toBeInTheDocument();
    expect(
      screen.getByDisplayValue("scripts/trained-data/rule-engine.local.csv")
    ).toBeInTheDocument();
    expect(screen.getByDisplayValue("summary+description")).toBeInTheDocument();
    expect(screen.getByDisplayValue("85")).toBeInTheDocument();
    expect(screen.getByDisplayValue("1")).toBeInTheDocument();
    expect(screen.getByDisplayValue("human-feedback")).toBeInTheDocument();
    expect(screen.getByDisplayValue("0")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^ok$/i })).toBeInTheDocument();
    expect(screen.queryByLabelText(/filter loaded tickets/i)).not.toBeInTheDocument();
  });

  it("shows active workflow state in the top menu", async () => {
    render(<HomePage />);

    const categorizeBtn = screen.getByRole("link", { name: /categorize tickets/i });
    const addRuleBtn = screen.getByRole("link", { name: /add rule for a ticket/i });
    const browseBtn = screen.getByRole("link", { name: /tickets in normalized root/i });
    const categorizedBtn = screen.getByRole("link", { name: /view categorized tickets/i });
    const rulesBtn = screen.getByRole("link", { name: /view rules engines/i });
    const trainBtn = screen.getByRole("link", { name: /train stc model/i });

    expect(categorizeBtn).toHaveAttribute("aria-current", "page");
    expect(addRuleBtn).not.toHaveAttribute("aria-current");
    expect(browseBtn).not.toHaveAttribute("aria-current");
    expect(categorizedBtn).not.toHaveAttribute("aria-current");
    expect(rulesBtn).not.toHaveAttribute("aria-current");
    expect(trainBtn).not.toHaveAttribute("aria-current");

    fireEvent.click(addRuleBtn);
    expect(categorizeBtn).not.toHaveAttribute("aria-current");
    expect(addRuleBtn).toHaveAttribute("aria-current", "page");
    expect(browseBtn).not.toHaveAttribute("aria-current");
    expect(categorizedBtn).not.toHaveAttribute("aria-current");
    expect(rulesBtn).not.toHaveAttribute("aria-current");
    expect(trainBtn).not.toHaveAttribute("aria-current");

    fireEvent.click(browseBtn);
    expect(categorizeBtn).not.toHaveAttribute("aria-current");
    expect(addRuleBtn).not.toHaveAttribute("aria-current");
    expect(browseBtn).toHaveAttribute("aria-current", "page");
    expect(categorizedBtn).not.toHaveAttribute("aria-current");
    expect(rulesBtn).not.toHaveAttribute("aria-current");
    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith("/api/tickets-json?dir=scripts%2Fnormalized-tickets")
    );

    fireEvent.click(categorizedBtn);
    expect(categorizeBtn).not.toHaveAttribute("aria-current");
    expect(addRuleBtn).not.toHaveAttribute("aria-current");
    expect(browseBtn).not.toHaveAttribute("aria-current");
    expect(categorizedBtn).toHaveAttribute("aria-current", "page");
    expect(rulesBtn).not.toHaveAttribute("aria-current");
    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/list-files?dir=scripts%2Fanalysis&extensions=csv&limit=500&nameExact=tickets-categorized.csv"
      )
    );

    fireEvent.click(rulesBtn);
    expect(categorizeBtn).not.toHaveAttribute("aria-current");
    expect(addRuleBtn).not.toHaveAttribute("aria-current");
    expect(browseBtn).not.toHaveAttribute("aria-current");
    expect(categorizedBtn).not.toHaveAttribute("aria-current");
    expect(rulesBtn).toHaveAttribute("aria-current", "page");
    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/list-files?dir=scripts%2Ftrained-data&extensions=csv&nameContains=rule-engine&limit=500"
      )
    );
  });

  it("enforces either-or input mode", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /categorize tickets/i }));

    const jqlInput = screen.getByLabelText(/enter jql/i);
    const filesInput = screen.getByLabelText(/enter ticket list files/i);
    const ticketIdsInput = screen.getByLabelText(/enter list of ticket ids/i);

    expect(jqlInput).toBeEnabled();
    expect(filesInput).toBeDisabled();
    expect(ticketIdsInput).toBeDisabled();

    fireEvent.click(screen.getByRole("radio", { name: /ticket list files/i }));
    expect(jqlInput).toBeDisabled();
    expect(filesInput).toBeEnabled();
    expect(ticketIdsInput).toBeDisabled();

    fireEvent.click(screen.getByRole("radio", { name: /ticket ids/i }));
    expect(jqlInput).toBeDisabled();
    expect(filesInput).toBeDisabled();
    expect(ticketIdsInput).toBeEnabled();
  });

  it("runs jql flow and shows pipeline results after clicking ok", async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        summaryRows: [
          {
            "Tickets Category": "network",
            "Percentage of Total Tickets": "50.00%",
            "Count of Tickets": "2",
            "JQL Query": "issuekey in (DCOPS-101, DCOPS-102)"
          }
        ],
        paths: {
          ticketsCsv: "scripts/analysis/ui-runs/abc/tickets-categorized.csv",
          summaryCsv: "scripts/analysis/ui-runs/abc/tickets-summary.csv"
        }
      })
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /categorize tickets/i }));
    fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));

    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/run-jql",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          inputMode: "jql",
          jql: 'project="High Performance Computing" and createdDate >= "2026-02-10" and createdDate <= "2026-02-11"',
          resolutionMode: "all",
          ticketsFile: "scripts/analysis/ui-runs/templates/tickets-template.txt",
          ticketsText: "HPC-110621,HPC-110615",
          rulesEngine: "scripts/trained-data/golden-rules-engine/rule-engine.csv",
          mlModel: "scripts/trained-data/golden-ml-model/classifier.joblib",
          mlCategoryMap: "scripts/trained-data/golden-ml-model/category_map.json"
        })
      })
    );
    expect(await screen.findByText(/live local pipeline run/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /summary output/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /graphs of the data/i })).toBeInTheDocument();
  });

  it("shows pipeline stages and logs UI for ticket-id mode runs", async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      body: null,
      json: async () => ({
        summaryRows: [],
        paths: {}
      })
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /categorize tickets/i }));
    fireEvent.click(screen.getByRole("radio", { name: /ticket ids/i }));
    fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));

    expect(await screen.findByRole("heading", { name: /pipeline stages/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /executed commands/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /live logs/i })).toBeInTheDocument();
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/run-jql",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining('"inputMode":"tickets"')
      })
    );
  });

  it("runs add-rule flow and posts script inputs/defaults", async () => {
    const mockFetch = jest.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/add-rule-from-ticket") {
        return Promise.resolve({
          ok: true,
          body: null,
          json: async () => ({
            result: {
              ruleId: "R101",
              rulesEngine:
                "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/trained-data/rule-engine.local.csv",
              ticketJson: "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/tickets-json/HPC-123456.json",
              normalizedJson:
                "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/normalized-tickets/2026-02-15/HPC-123456.json",
              message:
                "Rule R101 appended to /mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/trained-data/rule-engine.local.csv"
            }
          })
        });
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /add rule for a ticket/i }));
    fireEvent.change(screen.getByLabelText(/ticket key/i), { target: { value: "HPC-123456" } });
    fireEvent.change(screen.getByLabelText(/why should a new rule be added/i), {
      target: { value: "Repeat incident pattern" }
    });
    fireEvent.change(screen.getByLabelText(/category of issue/i), {
      target: { value: "network" }
    });
    fireEvent.change(screen.getByLabelText(/^category$/i), { target: { value: "switch" } });
    fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/add-rule-from-ticket",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          ticketKey: "HPC-123456",
          reason: "Repeat incident pattern",
          failureCategory: "network",
          category: "switch",
          matchField: "",
          rulePattern: "",
          ticketJsonDir: "scripts/tickets-json",
          normalizedRoot: "scripts/normalized-tickets",
          rulesEngine: "scripts/trained-data/rule-engine.local.csv",
          matchFieldDefault: "summary+description",
          priority: 85,
          confidence: 1,
          createdBy: "human-feedback",
          hitCount: 0
        })
      })
    );
    expect(await screen.findByRole("heading", { name: /output artifacts/i })).toBeInTheDocument();
    expect(
      await screen.findByRole("link", {
        name: /\/mnt\/data\/src\/rikkisnah\/stc_ux_ml\/stc\/scripts\/trained-data\/rule-engine.local.csv/i
      })
    ).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: /executed commands/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /live logs/i })).toBeInTheDocument();
  });

  it("shows explicit add-rule failure message when the run errors", async () => {
    const mockFetch = jest.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/add-rule-from-ticket") {
        return Promise.resolve({
          ok: true,
          body: null,
          json: async () => ({
            error: "Ticket HPC-123 not found in tickets-json"
          })
        });
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /add rule for a ticket/i }));
    fireEvent.change(screen.getByLabelText(/ticket key/i), { target: { value: "HPC-123" } });
    fireEvent.change(screen.getByLabelText(/why should a new rule be added/i), {
      target: { value: "Repeat incident pattern" }
    });
    fireEvent.change(screen.getByLabelText(/category of issue/i), {
      target: { value: "network" }
    });
    fireEvent.change(screen.getByLabelText(/^category$/i), { target: { value: "switch" } });
    fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));

    expect(
      await screen.findByText(/run failed: ticket hpc-123 not found in tickets-json/i)
    ).toBeInTheDocument();
  });

  it("lists tickets from normalized root, shows details, and supports copy", async () => {
    const clipboardWrite = jest.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: clipboardWrite },
      configurable: true
    });

    const mockFetch = jest.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.startsWith("/api/tickets-json?dir=") && !url.includes("ticketKey=")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            tickets: [
              {
                key: "HPC-123",
                summary: "Switch flap in rack 12",
                status: "Open",
                resolution: "",
                sourcePath:
                  "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/normalized-tickets/2026-02-15/HPC-123.json",
                detailPath:
                  "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/normalized-tickets/2026-02-15/HPC-123.json",
                hasRawTicketFile: true
              },
              {
                key: "HPC-456",
                summary: "Power cycle needed",
                status: "Closed",
                resolution: "Done",
                sourcePath:
                  "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/normalized-tickets/2026-02-15/HPC-456.json",
                detailPath:
                  "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/normalized-tickets/2026-02-15/HPC-456.json",
                hasRawTicketFile: true
              }
            ]
          })
        });
      }
      if (url.includes("ticketKey=HPC-123")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            ticketKey: "HPC-123",
            sourcePath:
              "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/normalized-tickets/2026-02-15/HPC-123.json",
            detailPath:
              "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/normalized-tickets/2026-02-15/HPC-123.json",
            hasRawTicketFile: true,
            payload: {
              key: "HPC-123",
              fields: {
                summary: "Switch flap in rack 12",
                status: { name: "Open" }
              }
            }
          })
        });
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /tickets in normalized root/i }));

    const ticketButton = await screen.findByRole("button", { name: "HPC-123" });
    fireEvent.click(ticketButton);

    expect(await screen.findByText(/selected ticket details \(read-only\)/i)).toBeInTheDocument();
    expect(await screen.findByText(/"key": "HPC-123"/i)).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: /\/mnt\/data\/src\/rikkisnah\/stc_ux_ml\/stc\/scripts\/normalized-tickets\/2026-02-15\/hpc-123.json/i
      })
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /copy details/i }));
    await waitFor(() =>
      expect(clipboardWrite).toHaveBeenCalledWith(expect.stringContaining('"key": "HPC-123"'))
    );
    expect(await screen.findByText(/ticket details copied/i)).toBeInTheDocument();
  });

  it("starts ticket list in compact mode and expands on demand", async () => {
    const mockFetch = jest.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.startsWith("/api/tickets-json?dir=") && !url.includes("ticketKey=")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            tickets: [
              {
                key: "HPC-123",
                summary: "First ticket",
                status: "Open",
                resolution: "",
                sourcePath: "scripts/normalized-tickets/2026-02-15/HPC-123.json",
                detailPath: "scripts/normalized-tickets/2026-02-15/HPC-123.json",
                hasRawTicketFile: true
              },
              {
                key: "HPC-456",
                summary: "Second ticket",
                status: "Open",
                resolution: "",
                sourcePath: "scripts/normalized-tickets/2026-02-15/HPC-456.json",
                detailPath: "scripts/normalized-tickets/2026-02-15/HPC-456.json",
                hasRawTicketFile: true
              }
            ]
          })
        });
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /tickets in normalized root/i }));

    expect(await screen.findByRole("button", { name: "HPC-123" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "HPC-456" })).not.toBeInTheDocument();
    expect(
      screen.getByText(/showing 1 ticket \(compact view\). click expand list to see more\./i)
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /expand list/i }));
    expect(await screen.findByRole("button", { name: "HPC-456" })).toBeInTheDocument();
  });

  it("shows empty-directory message when normalized root has no tickets", async () => {
    const mockFetch = jest.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.startsWith("/api/tickets-json?dir=") && !url.includes("ticketKey=")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ tickets: [] })
        });
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /tickets in normalized root/i }));

    expect(
      await screen.findByText(/directory is empty: scripts\/normalized-tickets\./i)
    ).toBeInTheDocument();
  });

  it("lists categorized ticket files from analysis and previews selected content", async () => {
    const mockFetch = jest.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (
        url ===
        "/api/list-files?dir=scripts%2Fanalysis&extensions=csv&limit=500&nameExact=tickets-categorized.csv"
      ) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            files: [
              {
                path: "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/analysis/ui-runs/abc/tickets-categorized.csv",
                name: "tickets-categorized.csv",
                sizeBytes: 512,
                modifiedAt: "2026-02-16T01:02:03Z"
              }
            ]
          })
        });
      }
      if (
        url ===
        "/api/open-file?path=%2Fmnt%2Fdata%2Fsrc%2Frikkisnah%2Fstc_ux_ml%2Fstc%2Fscripts%2Fanalysis%2Fui-runs%2Fabc%2Ftickets-categorized.csv"
      ) {
        return Promise.resolve({
          ok: true,
          text: async () => "Ticket Key,Category\nHPC-1001,network"
        });
      }
      if (url === "/api/save-file") {
        return Promise.resolve({
          ok: true,
          json: async () => ({ saved: true })
        });
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /view categorized tickets/i }));

    const categorizedFile = await screen.findByRole("button", { name: "tickets-categorized.csv" });
    fireEvent.click(categorizedFile);

    expect(await screen.findByText(/selected file \(view\/edit\)/i)).toBeInTheDocument();
    expect(await screen.findByText(/in-place file editor/i)).toBeInTheDocument();
    expect(await screen.findByDisplayValue("HPC-1001")).toBeInTheDocument();
    const categorizedValueCell = await screen.findByDisplayValue("network");
    expect(screen.getAllByText(/scripts\/analysis\/ui-runs\/abc/i).length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: /download selected file/i })).toBeInTheDocument();

    fireEvent.change(categorizedValueCell, {
      target: { value: "storage" }
    });
    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/save-file",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            path: "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/analysis/ui-runs/abc/tickets-categorized.csv",
            content: "Ticket Key,Category\nHPC-1001,storage"
          })
        })
      )
    );
    expect(await screen.findByText(/file saved\./i)).toBeInTheDocument();
  });

  it("supports optional categorized directory and exact file overrides", async () => {
    const mockFetch = jest.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (
        url ===
        "/api/list-files?dir=scripts%2Fanalysis&extensions=csv&limit=500&nameExact=tickets-categorized.csv"
      ) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            files: []
          })
        });
      }
      if (url === "/api/list-files?dir=scripts%2Fanalysis%2Fui-runs%2Fabc&extensions=csv&limit=500") {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            files: [
              {
                path: "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/analysis/ui-runs/abc/tickets-categorized-backup.csv",
                name: "tickets-categorized-backup.csv",
                sizeBytes: 120,
                modifiedAt: "2026-02-16T01:02:03Z"
              }
            ]
          })
        });
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /view categorized tickets/i }));
    await screen.findByRole("button", { name: /refresh list/i });

    fireEvent.change(screen.getByLabelText(/categorized directory \(optional\)/i), {
      target: { value: "scripts/analysis/ui-runs/abc" }
    });
    fireEvent.change(screen.getByLabelText(/exact file name \(optional\)/i), {
      target: { value: "" }
    });
    fireEvent.click(screen.getByRole("button", { name: /refresh list/i }));

    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/list-files?dir=scripts%2Fanalysis%2Fui-runs%2Fabc&extensions=csv&limit=500"
      )
    );
    expect(
      await screen.findByRole("button", { name: "tickets-categorized-backup.csv" })
    ).toBeInTheDocument();
  });

  it("shows rules engines with trained-data default and golden switch", async () => {
    const mockFetch = jest.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (
        url ===
        "/api/list-files?dir=scripts%2Ftrained-data&extensions=csv&nameContains=rule-engine&limit=500"
      ) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            files: [
              {
                path: "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/trained-data/rule-engine.local.csv",
                name: "rule-engine.local.csv",
                sizeBytes: 1024,
                modifiedAt: "2026-02-16T01:02:03Z"
              }
            ]
          })
        });
      }
      if (
        url ===
        "/api/list-files?dir=scripts%2Ftrained-data%2Fgolden-rules-engine&extensions=csv&nameContains=rule-engine&limit=500"
      ) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            files: [
              {
                path: "/mnt/data/src/rikkisnah/stc_ux_ml/stc/scripts/trained-data/golden-rules-engine/rule-engine.csv",
                name: "rule-engine.csv",
                sizeBytes: 2048,
                modifiedAt: "2026-02-16T01:02:03Z"
              }
            ]
          })
        });
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /view rules engines/i }));

    expect(await screen.findByRole("button", { name: "rule-engine.local.csv" })).toBeInTheDocument();
    expect(screen.getByLabelText(/rules source/i)).toHaveDisplayValue("trained-data (default)");

    fireEvent.change(screen.getByLabelText(/rules source/i), { target: { value: "golden" } });

    expect(await screen.findByRole("button", { name: "rule-engine.csv" })).toBeInTheDocument();
    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/list-files?dir=scripts%2Ftrained-data%2Fgolden-rules-engine&extensions=csv&nameContains=rule-engine&limit=500"
      )
    );
  });

  it("shows Train STC model tab with JQL input mode and default advanced params", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));

    expect(screen.getByRole("radio", { name: /^jql$/i })).toBeChecked();
    expect(screen.getByRole("radio", { name: /ticket list files/i })).not.toBeChecked();
    expect(screen.getByRole("radio", { name: /^ticket ids$/i })).not.toBeChecked();
    expect(screen.getByRole("button", { name: /^ok$/i })).toBeInTheDocument();
  });

  it("shows advanced training params with defaults in details section", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));

    expect(screen.getByDisplayValue("scripts/trained-data/ml-training-data.csv")).toBeInTheDocument();
    expect(screen.getByDisplayValue("20")).toBeInTheDocument();
    expect(screen.getByDisplayValue("200")).toBeInTheDocument();
  });

  it("switches between ticket input modes on train-stc tab", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));

    fireEvent.click(screen.getByRole("radio", { name: /^ticket ids$/i }));
    expect(screen.getByRole("radio", { name: /^ticket ids$/i })).toBeChecked();
    expect(screen.getByRole("radio", { name: /^jql$/i })).not.toBeChecked();
  });

  it("posts correct pipeline payload with JQL defaults", async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      body: null,
      json: async () => ({})
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));

    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/train-stc",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          phase: 1,
          inputMode: "jql",
          jql: 'project="High Performance Computing" and createdDate >= "2026-02-10" and createdDate <= "2026-02-11"',
          resolutionMode: "resolved-only",
          ticketsFile: "scripts/analysis/ui-runs/templates/tickets-template.txt",
          ticketsText: "HPC-110621,HPC-110615",
          trainingData: "scripts/trained-data/ml-training-data.csv",
          minSamples: 20,
          maxReviewRows: 200
        })
      })
    );
  });

  it("validates JQL is required in JQL mode for train-stc", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    const jqlTextareas = screen.getAllByRole("textbox");
    const trainJql = jqlTextareas.find((el) => el.tagName === "TEXTAREA" && (el as HTMLTextAreaElement).value.includes("High Performance Computing"));
    expect(trainJql).toBeTruthy();
    fireEvent.change(trainJql!, { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(/jql query is required/i);
  });

  it("validates training data CSV is required for train-stc", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    const trainingDataInput = screen.getByDisplayValue("scripts/trained-data/ml-training-data.csv");
    fireEvent.change(trainingDataInput, { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(/training data csv path is required/i);
  });

  it("validates ticket IDs are required when tickets mode is selected", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    fireEvent.click(screen.getByRole("radio", { name: /^ticket ids$/i }));
    const ticketTextareas = screen.getAllByRole("textbox");
    const ticketIdInput = ticketTextareas.find((el) => (el as HTMLTextAreaElement).value === "HPC-110621,HPC-110615");
    expect(ticketIdInput).toBeTruthy();
    fireEvent.change(ticketIdInput!, { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(/enter at least one ticket key/i);
  });

  it("shows Train STC model active state in workflow menu", () => {
    render(<HomePage />);

    const trainBtn = screen.getByRole("link", { name: /train stc model/i });
    expect(trainBtn).not.toHaveAttribute("aria-current");

    fireEvent.click(trainBtn);
    expect(trainBtn).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: /categorize tickets/i })).not.toHaveAttribute("aria-current");
  });

  it("shows audit UI when train-stc pipeline emits paused event", async () => {
    const csvContent = "Ticket Key,Category\nHPC-1001,network\nHPC-1002,storage";
    const lines = [
      JSON.stringify({ type: "command-start", command: "uv run python3 scripts/get_tickets.py" }),
      JSON.stringify({ type: "command-end", command: "uv run python3 scripts/get_tickets.py" }),
      JSON.stringify({ type: "command-start", command: "uv run python3 scripts/normalize_tickets.py" }),
      JSON.stringify({ type: "command-end", command: "uv run python3 scripts/normalize_tickets.py" }),
      JSON.stringify({ type: "command-start", command: "cp golden rules" }),
      JSON.stringify({ type: "command-end", command: "cp golden rules" }),
      JSON.stringify({ type: "command-start", command: "uv run python3 scripts/rule_engine_categorize.py" }),
      JSON.stringify({ type: "command-end", command: "uv run python3 scripts/rule_engine_categorize.py" }),
      JSON.stringify({
        type: "paused",
        phase: 1,
        runId: "train-test-run-1",
        paths: { ticketsCsv: "/tmp/tickets-categorized.csv", outputDir: "/tmp/output" }
      })
    ];

    const mockFetch = jest.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url === "/api/train-stc") {
        return Promise.resolve(mockNdjsonResponse(lines));
      }
      if (typeof url === "string" && url.includes("/api/open-file")) {
        return Promise.resolve({ ok: true, text: async () => csvContent });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    // Uncheck skipAudit1 so the audit UI stays visible (default is checked/auto-skip)
    fireEvent.click(screen.getByLabelText(/skip human audit #1/i));
    // Use act to flush async state updates from the streaming NDJSON handler
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));
      // Allow microtasks (stream reads, fetch for open-file) to settle
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(screen.getByText(/review and optionally edit/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /complete training/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cancel training/i })).toBeInTheDocument();
  });

  it("sends phase 2 request when Continue Pipeline is clicked after audit pause", async () => {
    const phase1Lines = [
      JSON.stringify({ type: "command-start", command: "uv run python3 scripts/get_tickets.py" }),
      JSON.stringify({ type: "command-end", command: "uv run python3 scripts/get_tickets.py" }),
      JSON.stringify({ type: "command-start", command: "cp golden rules" }),
      JSON.stringify({ type: "command-end", command: "cp golden rules" }),
      JSON.stringify({ type: "command-start", command: "uv run python3 scripts/rule_engine_categorize.py" }),
      JSON.stringify({ type: "command-end", command: "uv run python3 scripts/rule_engine_categorize.py" }),
      JSON.stringify({
        type: "paused",
        phase: 1,
        runId: "train-test-run-2",
        paths: { ticketsCsv: "/tmp/tickets-categorized.csv" }
      })
    ];
    const phase2Lines = [
      JSON.stringify({ type: "command-start", command: "uv run python3 scripts/ml_train.py" }),
      JSON.stringify({ type: "command-end", command: "uv run python3 scripts/ml_train.py" }),
      JSON.stringify({
        type: "paused",
        phase: 2,
        runId: "train-test-run-2",
        paths: { ticketsCsv: "/tmp/tickets-categorized.csv" }
      })
    ];

    let callCount = 0;
    const mockFetch = jest.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url === "/api/train-stc") {
        callCount++;
        return Promise.resolve(mockNdjsonResponse(callCount === 1 ? phase1Lines : phase2Lines));
      }
      if (typeof url === "string" && url.includes("/api/open-file")) {
        return Promise.resolve({ ok: true, text: async () => "H1,H2\nA,B" });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    // Enable ML training so "Continue Pipeline" appears instead of "Complete Training"
    fireEvent.click(screen.getByLabelText(/enable ml training/i));
    // Uncheck skipAudit1 so the audit UI stays visible
    fireEvent.click(screen.getByLabelText(/skip human audit #1/i));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(screen.getByRole("button", { name: /continue pipeline/i })).toBeInTheDocument();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /continue pipeline/i }));
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/train-stc",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ phase: 2, runId: "train-test-run-2" })
      })
    );
  });

  it("cancels training during audit pause", async () => {
    const lines = [
      JSON.stringify({ type: "command-start", command: "uv run python3 scripts/get_tickets.py" }),
      JSON.stringify({ type: "command-end", command: "uv run python3 scripts/get_tickets.py" }),
      JSON.stringify({ type: "command-start", command: "cp golden rules" }),
      JSON.stringify({ type: "command-end", command: "cp golden rules" }),
      JSON.stringify({
        type: "paused",
        phase: 1,
        runId: "train-cancel-run",
        paths: { ticketsCsv: "/tmp/tc.csv" }
      })
    ];

    const mockFetch = jest.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url === "/api/train-stc") {
        return Promise.resolve(mockNdjsonResponse(lines));
      }
      if (typeof url === "string" && url.includes("/api/open-file")) {
        return Promise.resolve({ ok: true, text: async () => "H1\nV1" });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    // Uncheck skipAudit1 so the audit UI stays visible
    fireEvent.click(screen.getByLabelText(/skip human audit #1/i));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(screen.getByRole("button", { name: /cancel training/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /cancel training/i }));

    // After cancel, audit UI disappears and result card shows cancel message
    expect(screen.queryByText(/review and optionally edit/i)).toBeNull();
    expect(screen.getByText(/training canceled during audit/i)).toBeInTheDocument();
  });

  it("saves audit changes via save-file API during pause", async () => {
    const csvContent = "Ticket Key,Category\nHPC-1001,network";
    const lines = [
      JSON.stringify({ type: "command-start", command: "uv run python3 scripts/get_tickets.py" }),
      JSON.stringify({ type: "command-end", command: "uv run python3 scripts/get_tickets.py" }),
      JSON.stringify({ type: "command-start", command: "cp golden rules" }),
      JSON.stringify({ type: "command-end", command: "cp golden rules" }),
      JSON.stringify({
        type: "paused",
        phase: 1,
        runId: "train-save-run",
        paths: { ticketsCsv: "/tmp/tc-save.csv" }
      })
    ];

    const mockFetch = jest.fn().mockImplementation((url: string, opts?: RequestInit) => {
      if (typeof url === "string" && url === "/api/train-stc") {
        return Promise.resolve(mockNdjsonResponse(lines));
      }
      if (typeof url === "string" && url.includes("/api/open-file")) {
        return Promise.resolve({ ok: true, text: async () => csvContent });
      }
      if (typeof url === "string" && url === "/api/save-file" && opts?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => ({ saved: true }) });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    // Uncheck skipAudit1 so the audit UI stays visible
    fireEvent.click(screen.getByLabelText(/skip human audit #1/i));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(screen.getByText(/review and optionally edit/i)).toBeInTheDocument();

    // Edit a cell
    const cellInput = screen.getByDisplayValue("network");
    fireEvent.change(cellInput, { target: { value: "storage" } });
    expect(screen.getByText(/unsaved changes/i)).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/save-file",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          path: "/tmp/tc-save.csv",
          content: "Ticket Key,Category\nHPC-1001,storage"
        })
      })
    );
  });

  it("shows Promote to Golden tab with source and target path defaults", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /promote to golden/i }));

    expect(screen.getByDisplayValue("scripts/trained-data/rule-engine.local.csv")).toBeInTheDocument();
    expect(screen.getByDisplayValue("scripts/trained-data/golden-rules-engine/rule-engine.csv")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /load diff/i })).toBeInTheDocument();
  });

  it("shows Promote to Golden active state in workflow menu", () => {
    render(<HomePage />);

    const promoteBtn = screen.getByRole("link", { name: /promote to golden/i });
    expect(promoteBtn).not.toHaveAttribute("aria-current");

    fireEvent.click(promoteBtn);
    expect(promoteBtn).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: /categorize tickets/i })).not.toHaveAttribute("aria-current");
  });

  it("loads diff and shows added rules in summary", async () => {
    const goldenCsv = "Project Key,RuleID,Rule Pattern,Match Field,Failure Category,Category,Priority,Confidence,Created By,Hit Count\nDO,R001,pat1,summary,Cat1,C1,100,0.95,human,5";
    const trainedCsv = "Project Key,RuleID,Rule Pattern,Match Field,Failure Category,Category,Priority,Confidence,Created By,Hit Count\nDO,R001,pat1,summary,Cat1,C1,100,0.95,human,5\nHPC,R002,pat2,description,Cat2,C2,85,0.80,ml,0";
    const mockFetch = jest.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("golden")) {
        return Promise.resolve({ ok: true, text: async () => goldenCsv });
      }
      return Promise.resolve({ ok: true, text: async () => trainedCsv });
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /promote to golden/i }));
    fireEvent.click(screen.getByRole("button", { name: /load diff/i }));

    await waitFor(() => {
      expect(screen.getByText(/1 added/)).toBeInTheDocument();
    });
    expect(screen.getByText(/0 changed/)).toBeInTheDocument();
    expect(screen.getByText(/0 removed/)).toBeInTheDocument();
    expect(screen.getByText(/show 1 unchanged rules/i)).toBeInTheDocument();
  });

  it("shows changed rows when rules differ between source and target", async () => {
    const goldenCsv = "Project Key,RuleID,Rule Pattern,Match Field,Failure Category,Category,Priority,Confidence,Created By,Hit Count\nDO,R001,old_pattern,summary,Cat1,C1,100,0.95,human,5";
    const trainedCsv = "Project Key,RuleID,Rule Pattern,Match Field,Failure Category,Category,Priority,Confidence,Created By,Hit Count\nDO,R001,new_pattern,summary,Cat1,C1,100,0.99,human,10";
    const mockFetch = jest.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("golden")) {
        return Promise.resolve({ ok: true, text: async () => goldenCsv });
      }
      return Promise.resolve({ ok: true, text: async () => trainedCsv });
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /promote to golden/i }));
    fireEvent.click(screen.getByRole("button", { name: /load diff/i }));

    await waitFor(() => {
      expect(screen.getByText(/1 changed/)).toBeInTheDocument();
    });
    expect(screen.getByText(/~ changed/)).toBeInTheDocument();
  });

  it("shows identical message when files have no differences", async () => {
    const csv = "Project Key,RuleID,Rule Pattern,Match Field,Failure Category,Category,Priority,Confidence,Created By,Hit Count\nDO,R001,pat1,summary,Cat1,C1,100,0.95,human,5";
    const mockFetch = jest.fn().mockResolvedValue({ ok: true, text: async () => csv });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /promote to golden/i }));
    fireEvent.click(screen.getByRole("button", { name: /load diff/i }));

    await waitFor(() => {
      expect(screen.getByText(/files are identical/i)).toBeInTheDocument();
    });
  });

  it("shows confirm and cancel flow for promotion", async () => {
    const goldenCsv = "Project Key,RuleID,Rule Pattern,Match Field,Failure Category,Category,Priority,Confidence,Created By,Hit Count\nDO,R001,pat1,summary,Cat1,C1,100,0.95,human,5";
    const trainedCsv = "Project Key,RuleID,Rule Pattern,Match Field,Failure Category,Category,Priority,Confidence,Created By,Hit Count\nDO,R001,pat1,summary,Cat1,C1,100,0.95,human,5\nHPC,R002,pat2,description,Cat2,C2,85,0.80,ml,0";
    const mockFetch = jest.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("golden")) {
        return Promise.resolve({ ok: true, text: async () => goldenCsv });
      }
      if (typeof url === "string" && url.includes("save-file")) {
        return Promise.resolve({ ok: true, json: async () => ({ saved: true }) });
      }
      return Promise.resolve({ ok: true, text: async () => trainedCsv });
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /promote to golden/i }));
    fireEvent.click(screen.getByRole("button", { name: /load diff/i }));

    await waitFor(() => {
      expect(screen.getByText(/1 added/)).toBeInTheDocument();
    });

    expect(screen.queryByText(/confirm promotion/i)).not.toBeInTheDocument();
    const actionBtn = screen.getByRole("button", { name: /promote to golden/i });
    fireEvent.click(actionBtn);
    expect(screen.getByText(/confirm promotion/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.queryByText(/confirm promotion/i)).not.toBeInTheDocument();
  });

  it("shows error when source file fetch fails", async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: false,
      statusText: "Not Found"
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /promote to golden/i }));
    fireEvent.click(screen.getByRole("button", { name: /load diff/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/failed to load source/i);
    });
  });
});

describe("View ML Models workflow", () => {
  const mlModelResponse = {
    working: {
      exists: true,
      sizeBytes: 242940,
      modifiedAt: "2026-02-16T02:06:05.000Z",
      report: "Training Report\n===============\nCV Accuracy: 0.9663",
      categoryMap: {
        "CPV CDFP Fault - Auto Resolved (TRS)": "CDFP",
        "Potential Test Issue - Retest Passed": "Potential Test Issue"
      }
    },
    golden: {
      exists: true,
      sizeBytes: 242940,
      modifiedAt: "2026-02-16T02:06:05.000Z",
      report: "Training Report\n===============\nCV Accuracy: 0.9663",
      categoryMap: {
        "CPV CDFP Fault - Auto Resolved (TRS)": "CDFP",
        "Potential Test Issue - Retest Passed": "Potential Test Issue"
      }
    },
    identical: true
  };

  beforeEach(() => {
    window.history.replaceState(null, "", window.location.pathname);
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => mlModelResponse
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("shows View ML Models in workflow menu", () => {
    render(<HomePage />);
    const link = screen.getByRole("link", { name: /view ml models/i });
    expect(link).toBeInTheDocument();
  });

  it("auto-loads ML model info when entering workflow", async () => {
    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /view ml models/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/promote-ml-model?")
      );
    });
  });

  it("displays model metadata for golden source", async () => {
    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /view ml models/i }));

    await waitFor(() => {
      expect(screen.getByText("Available")).toBeInTheDocument();
    });

    expect(screen.getByText("classifier.joblib")).toBeInTheDocument();
    expect(screen.getByText(/237\.2 KB/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /training report/i })).toBeInTheDocument();
    expect(screen.getByText(/CV Accuracy: 0.9663/)).toBeInTheDocument();
    expect(screen.getByText("2 categories")).toBeInTheDocument();
    expect(screen.getByText("CDFP")).toBeInTheDocument();
  });

  it("shows Not found when model does not exist", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        ...mlModelResponse,
        working: { exists: false, sizeBytes: 0, modifiedAt: "", report: "", categoryMap: null }
      })
    }) as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /view ml models/i }));

    // Switch to working source
    await waitFor(() => {
      expect(screen.getByLabelText(/model source/i)).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText(/model source/i), { target: { value: "working" } });

    expect(screen.getByText("Not found")).toBeInTheDocument();
  });

  it("shows side-by-side comparison when compare mode selected", async () => {
    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /view ml models/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/view mode/i)).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText(/view mode/i), { target: { value: "compare" } });

    expect(screen.getByText(/Working \(ml-model\/\)/)).toBeInTheDocument();
    expect(screen.getByText(/Golden \(golden-ml-model\/\)/)).toBeInTheDocument();
  });

  it("shows identical badge when models match", async () => {
    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /view ml models/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/view mode/i)).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText(/view mode/i), { target: { value: "compare" } });

    expect(screen.getByText(/models are identical/i)).toBeInTheDocument();
  });

  it("shows error on API failure", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      statusText: "Internal Server Error"
    }) as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /view ml models/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/failed to load ml model info/i);
    });
  });

  it("refresh button reloads model info", async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => mlModelResponse
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /view ml models/i }));

    // Wait for initial load to complete (button text changes from Loading... to Refresh)
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /refresh/i })).toBeInTheDocument();
    });
    const callsAfterLoad = mockFetch.mock.calls.length;

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /refresh/i }));
    });

    await waitFor(() => {
      expect(mockFetch.mock.calls.length).toBeGreaterThan(callsAfterLoad);
    });
  });

  // --- ML opt-in tests ---

  it("ML training and rule generation checkboxes default to unchecked", () => {
    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    const mlTraining = screen.getByLabelText(/enable ml training/i) as HTMLInputElement;
    const mlRuleGen = screen.getByLabelText(/enable ml rule generation/i) as HTMLInputElement;
    expect(mlTraining.checked).toBe(false);
    expect(mlRuleGen.checked).toBe(false);
  });

  it("Phase 3 checkbox is disabled when Phase 2 is unchecked", () => {
    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    const mlRuleGen = screen.getByLabelText(/enable ml rule generation/i) as HTMLInputElement;
    expect(mlRuleGen.disabled).toBe(true);
  });

  it("Enabling Phase 2 enables Phase 3 checkbox", () => {
    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    fireEvent.click(screen.getByLabelText(/enable ml training/i));
    const mlRuleGen = screen.getByLabelText(/enable ml rule generation/i) as HTMLInputElement;
    expect(mlRuleGen.disabled).toBe(false);
  });

  it("Unchecking Phase 2 cascades to uncheck Phase 3", () => {
    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    // Enable both
    fireEvent.click(screen.getByLabelText(/enable ml training/i));
    fireEvent.click(screen.getByLabelText(/enable ml rule generation/i));
    const mlRuleGen = screen.getByLabelText(/enable ml rule generation/i) as HTMLInputElement;
    expect(mlRuleGen.checked).toBe(true);
    // Uncheck Phase 2 — Phase 3 should cascade off
    fireEvent.click(screen.getByLabelText(/enable ml training/i));
    expect(mlRuleGen.checked).toBe(false);
    expect(mlRuleGen.disabled).toBe(true);
  });

  it("Skip Audit #2 only visible when ML training is enabled", () => {
    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    expect(screen.queryByLabelText(/skip human audit #2/i)).toBeNull();
    fireEvent.click(screen.getByLabelText(/enable ml training/i));
    expect(screen.getByLabelText(/skip human audit #2/i)).toBeInTheDocument();
  });

  it("rules-only pipeline: does not POST phase 2 when ML is disabled", async () => {
    const phase1Lines = [
      JSON.stringify({ type: "command-start", command: "uv run python3 scripts/get_tickets.py" }),
      JSON.stringify({ type: "command-end", command: "uv run python3 scripts/get_tickets.py" }),
      JSON.stringify({
        type: "paused",
        phase: 1,
        runId: "train-rules-only",
        paths: { ticketsCsv: "/tmp/tickets-categorized.csv" }
      })
    ];

    const mockFetch = jest.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url === "/api/train-stc") {
        return Promise.resolve(mockNdjsonResponse(phase1Lines));
      }
      if (typeof url === "string" && url.includes("/api/open-file")) {
        return Promise.resolve({ ok: true, text: async () => "H1,H2\nA,B" });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    // Uncheck skipAudit1 so the audit UI stays visible
    fireEvent.click(screen.getByLabelText(/skip human audit #1/i));
    // ML is off by default — run the pipeline
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));
      await new Promise((r) => setTimeout(r, 100));
    });

    // Click "Complete Training" (not "Continue Pipeline")
    expect(screen.getByRole("button", { name: /complete training/i })).toBeInTheDocument();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /complete training/i }));
      await new Promise((r) => setTimeout(r, 50));
    });

    // Verify only 1 POST to /api/train-stc (phase 1 only, no phase 2)
    const trainStcCalls = mockFetch.mock.calls.filter(
      ([url]: [string]) => url === "/api/train-stc"
    );
    expect(trainStcCalls).toHaveLength(1);
  });

  it("shows Continue Pipeline when ML is enabled at phase 1 audit", async () => {
    const phase1Lines = [
      JSON.stringify({ type: "command-start", command: "uv run python3 scripts/get_tickets.py" }),
      JSON.stringify({ type: "command-end", command: "uv run python3 scripts/get_tickets.py" }),
      JSON.stringify({
        type: "paused",
        phase: 1,
        runId: "train-ml-enabled",
        paths: { ticketsCsv: "/tmp/tickets-categorized.csv" }
      })
    ];

    const mockFetch = jest.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url === "/api/train-stc") {
        return Promise.resolve(mockNdjsonResponse(phase1Lines));
      }
      if (typeof url === "string" && url.includes("/api/open-file")) {
        return Promise.resolve({ ok: true, text: async () => "H1,H2\nA,B" });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);
    fireEvent.click(screen.getByRole("link", { name: /train stc model/i }));
    fireEvent.click(screen.getByLabelText(/enable ml training/i));
    // Uncheck skipAudit1 so the audit UI stays visible
    fireEvent.click(screen.getByLabelText(/skip human audit #1/i));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(screen.getByRole("button", { name: /continue pipeline/i })).toBeInTheDocument();
  });
});

describe("Stale session banner", () => {
  const STORAGE_KEY = "stc-session-state";

  const validSession = {
    schemaVersion: 2,
    workflow: "train-stc",
    trainRunId: "train-2026-02-16T04-00-00-000Z",
    trainPhase: 2,
    isRunning: false,
    startedAt: "",
    elapsedMs: 0,
    pipelineStatus: [],
    resultPaths: {},
    trainStcResult: {},
    error: "",
    wasCanceled: false,
    executedCommandsCount: 0,
    lastCommandSnippet: "",
    savedAt: Date.now(),
  };

  beforeEach(() => {
    window.history.replaceState(null, "", window.location.pathname);
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ tickets: [] }),
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    jest.restoreAllMocks();
    global.fetch = originalFetch;
    localStorage.removeItem(STORAGE_KEY);
    window.history.replaceState(null, "", window.location.pathname);
  });

  it("renders warning banner when stale session exists in localStorage", async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...validSession, trainRunId: "train-2026-02-16T04-00-00-000Z" }));

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByTestId("stale-session-banner")).toBeInTheDocument();
    });
    expect(screen.getByText(/interrupted training session was found/)).toBeInTheDocument();
    expect(screen.getByText(/train-2026-02-16T04-00-00-000Z/)).toBeInTheDocument();
  });

  it("clicking Dismiss clears the banner and localStorage", async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(validSession));

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByTestId("stale-session-banner")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /dismiss/i }));

    expect(screen.queryByTestId("stale-session-banner")).not.toBeInTheDocument();
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it("clicking Restore restores session state and clears banner", async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(validSession));

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByTestId("stale-session-banner")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /restore/i }));

    expect(screen.queryByTestId("stale-session-banner")).not.toBeInTheDocument();
  });

  it("does not show banner when no session in localStorage", () => {
    localStorage.removeItem(STORAGE_KEY);

    render(<HomePage />);

    expect(screen.queryByTestId("stale-session-banner")).not.toBeInTheDocument();
  });
});

describe("Get Tickets & Normalize workflow", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", window.location.pathname);
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ tickets: [] })
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    jest.restoreAllMocks();
    global.fetch = originalFetch;
    window.history.replaceState(null, "", window.location.pathname);
  });

  it("shows Get Tickets & Normalize in workflow menu and displays input fields", () => {
    render(<HomePage />);

    const gnLink = screen.getByRole("link", { name: /get tickets & normalize/i });
    expect(gnLink).toBeInTheDocument();

    fireEvent.click(gnLink);
    expect(gnLink).toHaveAttribute("aria-current", "page");

    expect(screen.getByLabelText(/enter jql/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/enter ticket list files/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/enter list of ticket ids/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/ticket resolution filter/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^ok$/i })).toBeInTheDocument();
  });

  it("does NOT show rules engine or ML model fields", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /get tickets & normalize/i }));

    expect(screen.queryByLabelText(/rules engine csv/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/ml model \(optional/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/ml category map/i)).not.toBeInTheDocument();
  });

  it("posts correct payload to /api/get-normalize", async () => {
    const mockFetch = jest.fn().mockResolvedValue(
      mockNdjsonResponse([
        JSON.stringify({ type: "command-start", command: "uv run python3 scripts/get_tickets.py" }),
        JSON.stringify({ type: "command-end", command: "uv run python3 scripts/get_tickets.py" }),
        JSON.stringify({ type: "command-start", command: "uv run python3 scripts/normalize_tickets.py" }),
        JSON.stringify({ type: "command-end", command: "uv run python3 scripts/normalize_tickets.py" }),
        JSON.stringify({
          type: "done",
          runId: "test-run",
          paths: {
            ingestDir: "scripts/analysis/ui-runs/test-run/ingest",
            normalizedDir: "scripts/analysis/ui-runs/test-run/normalized/2026-02-16"
          }
        })
      ])
    );
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /get tickets & normalize/i }));
    fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/get-normalize",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          inputMode: "jql",
          jql: 'project="High Performance Computing" and createdDate >= "2026-02-10" and createdDate <= "2026-02-11"',
          resolutionMode: "all",
          ticketsFile: "scripts/analysis/ui-runs/templates/tickets-template.txt",
          ticketsText: "HPC-110621,HPC-110615"
        })
      })
    );

    expect(await screen.findByText(/live get & normalize pipeline run/i)).toBeInTheDocument();
  });

  it("shows 2-step pipeline stages in results", async () => {
    const mockFetch = jest.fn().mockResolvedValue(
      mockNdjsonResponse([
        JSON.stringify({ type: "command-start", command: "uv run python3 scripts/get_tickets.py" }),
        JSON.stringify({ type: "command-end", command: "uv run python3 scripts/get_tickets.py" }),
        JSON.stringify({ type: "command-start", command: "uv run python3 scripts/normalize_tickets.py" }),
        JSON.stringify({ type: "command-end", command: "uv run python3 scripts/normalize_tickets.py" }),
        JSON.stringify({
          type: "done",
          runId: "test-run",
          paths: {
            ingestDir: "scripts/analysis/ui-runs/test-run/ingest",
            normalizedDir: "scripts/analysis/ui-runs/test-run/normalized/2026-02-16"
          }
        })
      ])
    );
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /get tickets & normalize/i }));
    fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));

    expect(await screen.findByRole("heading", { name: /pipeline stages/i })).toBeInTheDocument();

    const pipelineNames = screen.getAllByText(/^get_tickets\.py$|^normalize_tickets\.py$/);
    expect(pipelineNames).toHaveLength(2);

    expect(await screen.findByRole("heading", { name: /output/i })).toBeInTheDocument();
  });

  it("shows Browse Tickets card with source dropdown after run completes", async () => {
    const mockFetch = jest.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/get-normalize") {
        return Promise.resolve(
          mockNdjsonResponse([
            JSON.stringify({ type: "command-start", command: "uv run python3 scripts/get_tickets.py" }),
            JSON.stringify({ type: "command-end", command: "uv run python3 scripts/get_tickets.py" }),
            JSON.stringify({ type: "command-start", command: "uv run python3 scripts/normalize_tickets.py" }),
            JSON.stringify({ type: "command-end", command: "uv run python3 scripts/normalize_tickets.py" }),
            JSON.stringify({
              type: "done",
              runId: "test-run",
              paths: {
                ingestDir: "scripts/analysis/ui-runs/test-run/ingest",
                normalizedDir: "scripts/analysis/ui-runs/test-run/normalized/2026-02-16"
              }
            })
          ])
        );
      }
      if (url.startsWith("/api/tickets-json?dir=")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ dir: "test", count: 0, tickets: [] })
        });
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    render(<HomePage />);

    fireEvent.click(screen.getByRole("link", { name: /get tickets & normalize/i }));
    fireEvent.click(screen.getByRole("button", { name: /^ok$/i }));

    expect(await screen.findByRole("heading", { name: /browse tickets/i })).toBeInTheDocument();

    const sourceDropdown = screen.getByLabelText(/ticket source/i);
    expect(sourceDropdown).toBeInTheDocument();

    const options = sourceDropdown.querySelectorAll("option");
    expect(options).toHaveLength(2);
    expect(options[0].textContent).toMatch(/ingest/i);
    expect(options[1].textContent).toMatch(/normalized/i);
  });
});
