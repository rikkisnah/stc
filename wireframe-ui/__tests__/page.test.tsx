// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { fireEvent, render, screen } from "@testing-library/react";
import HomePage from "../app/page";

const originalFetch = global.fetch;

describe("STC wireframe flow", () => {
  afterEach(() => {
    jest.restoreAllMocks();
    global.fetch = originalFetch;
  });

  it("shows landing view by default", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { name: /smart \(sudha's\) tickets' classifier/i })
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
});
