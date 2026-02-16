// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import SessionsPage from "../app/sessions/page";

const originalFetch = global.fetch;

describe("SessionsPage", () => {
  beforeEach(() => {
    global.fetch = jest.fn() as unknown as typeof fetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  it("shows empty state when no sessions exist", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sessions: [] }),
    });

    render(<SessionsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    });
    expect(screen.getByText(/No training sessions found/)).toBeInTheDocument();
  });

  it("renders session list with status badges", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        sessions: [
          {
            runId: "train-2026-02-16T04-08-00-167Z",
            createdAt: "2026-02-16T04:08:00.167Z",
            status: "completed",
            phase: 3,
            ticketCount: 10,
            rulesCount: 25,
            outputDir: "/some/path",
          },
          {
            runId: "train-2026-02-16T05-00-00-000Z",
            createdAt: "2026-02-16T05:00:00.000Z",
            status: "paused",
            phase: 1,
            ticketCount: 5,
            rulesCount: 12,
            outputDir: "/other/path",
          },
        ],
      }),
    });

    render(<SessionsPage />);
    await waitFor(() => {
      expect(screen.getAllByTestId("session-item")).toHaveLength(2);
    });

    const badges = screen.getAllByTestId("status-badge");
    expect(badges[0]).toHaveTextContent("completed");
    expect(badges[1]).toHaveTextContent("paused");
  });

  it("loads session detail on click", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          sessions: [
            {
              runId: "train-2026-02-16T04-08-00-167Z",
              createdAt: "2026-02-16T04:08:00.167Z",
              status: "completed",
              phase: 3,
              ticketCount: 10,
              rulesCount: 25,
              outputDir: "/some/path",
            },
          ],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          runId: "train-2026-02-16T04-08-00-167Z",
          outputDir: "/some/path",
          phaseMeta: { normalizeDate: "2026-02-16" },
          ticketCount: 10,
          rulesCount: 25,
          mlReport: "Accuracy: 0.85",
          artifacts: { ticketsCsv: "/some/path/tickets.csv", localRules: null, mlLog: null, trainingLog: null, mlModel: null },
          files: ["tickets-categorized.csv", "phase-meta.json"],
        }),
      });

    render(<SessionsPage />);
    await waitFor(() => {
      expect(screen.getAllByTestId("session-item")).toHaveLength(1);
    });

    fireEvent.click(screen.getByTestId("session-item"));

    await waitFor(() => {
      expect(screen.getByText("Accuracy: 0.85")).toBeInTheDocument();
    });
    expect(screen.getByText("Open tickets CSV")).toBeInTheDocument();
  });

  it("shows error when fetch fails", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error("Network down"));

    render(<SessionsPage />);
    await waitFor(() => {
      expect(screen.getByText("Network down")).toBeInTheDocument();
    });
  });

  it("shows delete button for each session", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        sessions: [
          {
            runId: "train-2026-02-16T04-08-00-167Z",
            createdAt: "2026-02-16T04:08:00.167Z",
            status: "completed",
            phase: 3,
            ticketCount: 10,
            rulesCount: 25,
            outputDir: "/some/path",
          },
          {
            runId: "train-2026-02-16T05-00-00-000Z",
            createdAt: "2026-02-16T05:00:00.000Z",
            status: "paused",
            phase: 1,
            ticketCount: 5,
            rulesCount: 12,
            outputDir: "/other/path",
          },
        ],
      }),
    });

    render(<SessionsPage />);
    await waitFor(() => {
      expect(screen.getAllByTestId("delete-session-btn")).toHaveLength(2);
    });
  });

  it("clicking delete calls API and removes the session row", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        sessions: [
          {
            runId: "train-2026-02-16T04-08-00-167Z",
            createdAt: "2026-02-16T04:08:00.167Z",
            status: "completed",
            phase: 3,
            ticketCount: 10,
            rulesCount: 25,
            outputDir: "/some/path",
          },
        ],
      }),
    });

    render(<SessionsPage />);
    await waitFor(() => {
      expect(screen.getAllByTestId("session-item")).toHaveLength(1);
    });

    // Mock the delete API response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ deleted: true, runId: "train-2026-02-16T04-08-00-167Z" }),
    });

    fireEvent.click(screen.getByTestId("delete-session-btn"));

    await waitFor(() => {
      expect(screen.queryByTestId("session-item")).not.toBeInTheDocument();
    });

    // Verify the delete API was called
    const calls = (global.fetch as jest.Mock).mock.calls;
    const deleteCall = calls.find(
      (c: unknown[]) => typeof c[0] === "string" && c[0].includes("/api/sessions/delete")
    );
    expect(deleteCall).toBeDefined();
    expect(JSON.parse(deleteCall[1].body)).toEqual({ runId: "train-2026-02-16T04-08-00-167Z" });
  });
});
