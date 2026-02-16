// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import HomePage from "../app/page";

const originalFetch = global.fetch;

describe("STC wireframe flow", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ tickets: [] })
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    jest.restoreAllMocks();
    global.fetch = originalFetch;
  });

  it("shows landing view by default", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { name: /smart.*tickets' classifier/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/to preview the next wireframe step/i)).toBeInTheDocument();
  });

  it("shows input fields after clicking categorize", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("button", { name: /categorize tickets/i }));

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

    fireEvent.click(screen.getByRole("button", { name: /add rule for a ticket/i }));

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

    const categorizeBtn = screen.getByRole("button", { name: /categorize tickets/i });
    const addRuleBtn = screen.getByRole("button", { name: /add rule for a ticket/i });
    const browseBtn = screen.getByRole("button", { name: /tickets in normalized root/i });
    const categorizedBtn = screen.getByRole("button", { name: /view categorized tickets/i });
    const rulesBtn = screen.getByRole("button", { name: /view rules engines/i });

    expect(categorizeBtn).toHaveAttribute("aria-pressed", "true");
    expect(addRuleBtn).toHaveAttribute("aria-pressed", "false");
    expect(browseBtn).toHaveAttribute("aria-pressed", "false");
    expect(categorizedBtn).toHaveAttribute("aria-pressed", "false");
    expect(rulesBtn).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(addRuleBtn);
    expect(categorizeBtn).toHaveAttribute("aria-pressed", "false");
    expect(addRuleBtn).toHaveAttribute("aria-pressed", "true");
    expect(browseBtn).toHaveAttribute("aria-pressed", "false");
    expect(categorizedBtn).toHaveAttribute("aria-pressed", "false");
    expect(rulesBtn).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(browseBtn);
    expect(categorizeBtn).toHaveAttribute("aria-pressed", "false");
    expect(addRuleBtn).toHaveAttribute("aria-pressed", "false");
    expect(browseBtn).toHaveAttribute("aria-pressed", "true");
    expect(categorizedBtn).toHaveAttribute("aria-pressed", "false");
    expect(rulesBtn).toHaveAttribute("aria-pressed", "false");
    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith("/api/tickets-json?dir=scripts%2Fnormalized-tickets")
    );

    fireEvent.click(categorizedBtn);
    expect(categorizeBtn).toHaveAttribute("aria-pressed", "false");
    expect(addRuleBtn).toHaveAttribute("aria-pressed", "false");
    expect(browseBtn).toHaveAttribute("aria-pressed", "false");
    expect(categorizedBtn).toHaveAttribute("aria-pressed", "true");
    expect(rulesBtn).toHaveAttribute("aria-pressed", "false");
    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/list-files?dir=scripts%2Fanalysis&extensions=csv&limit=500&nameExact=tickets-categorized.csv"
      )
    );

    fireEvent.click(rulesBtn);
    expect(categorizeBtn).toHaveAttribute("aria-pressed", "false");
    expect(addRuleBtn).toHaveAttribute("aria-pressed", "false");
    expect(browseBtn).toHaveAttribute("aria-pressed", "false");
    expect(categorizedBtn).toHaveAttribute("aria-pressed", "false");
    expect(rulesBtn).toHaveAttribute("aria-pressed", "true");
    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/list-files?dir=scripts%2Ftrained-data&extensions=csv&nameContains=rule-engine&limit=500"
      )
    );
  });

  it("enforces either-or input mode", () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole("button", { name: /categorize tickets/i }));

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

    fireEvent.click(screen.getByRole("button", { name: /categorize tickets/i }));
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
          ticketsText: "HPC-110621,HPC-110615"
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

    fireEvent.click(screen.getByRole("button", { name: /categorize tickets/i }));
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

    fireEvent.click(screen.getByRole("button", { name: /add rule for a ticket/i }));
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

    fireEvent.click(screen.getByRole("button", { name: /add rule for a ticket/i }));
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
    fireEvent.click(screen.getByRole("button", { name: /tickets in normalized root/i }));

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
    fireEvent.click(screen.getByRole("button", { name: /tickets in normalized root/i }));

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
    fireEvent.click(screen.getByRole("button", { name: /tickets in normalized root/i }));

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
    fireEvent.click(screen.getByRole("button", { name: /view categorized tickets/i }));

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
    fireEvent.click(screen.getByRole("button", { name: /view categorized tickets/i }));
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
    fireEvent.click(screen.getByRole("button", { name: /view rules engines/i }));

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
});
