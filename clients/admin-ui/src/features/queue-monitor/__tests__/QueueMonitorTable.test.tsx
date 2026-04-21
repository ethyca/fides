import { render, screen } from "@testing-library/react";
import fc from "fast-check";

import QueueMonitorTable from "../QueueMonitorTable";
import { QueueStats } from "../types";

const makeQueue = (
  queue_name: string,
  available = 0,
  delayed = 0,
  in_flight = 0,
): QueueStats => ({ queue_name, available, delayed, in_flight });

describe("QueueMonitorTable", () => {
  describe("unit tests", () => {
    it("renders all queues with correct counts", () => {
      const queues: QueueStats[] = [
        makeQueue("fides", 3, 1, 0),
        makeQueue("fidesops.messaging", 0, 0, 5),
      ];
      render(<QueueMonitorTable queues={queues} />);

      expect(screen.getByText("fides")).toBeInTheDocument();
      expect(screen.getByText("fidesops.messaging")).toBeInTheDocument();
      expect(screen.getByText("3")).toBeInTheDocument();
      expect(screen.getByText("1")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument();
    });

    it("shows empty state when queues is empty", () => {
      render(<QueueMonitorTable queues={[]} />);
      expect(screen.getByText("No queues configured")).toBeInTheDocument();
    });

    it("renders queues with all-zero counts", () => {
      const queues = [makeQueue("fides", 0, 0, 0)];
      render(<QueueMonitorTable queues={queues} />);
      expect(screen.getByText("fides")).toBeInTheDocument();
      // Three cells with value 0
      const zeroCells = screen.getAllByText("0");
      expect(zeroCells.length).toBeGreaterThanOrEqual(3);
    });

    it("does not render action buttons", () => {
      const queues = [makeQueue("fides", 1, 0, 0)];
      render(<QueueMonitorTable queues={queues} />);
      expect(screen.queryByRole("button")).toBeNull();
    });

    it("renders column headers", () => {
      render(<QueueMonitorTable queues={[makeQueue("q", 0, 0, 0)]} />);
      expect(screen.getAllByText("Queue Name").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Available").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Delayed").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("In Flight").length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("Property 5: Queue Table Rendering Completeness", () => {
    /**
     * Feature: queue-monitor, Property 5: Queue Table Rendering Completeness
     * For any non-empty list of QueueStats objects (including all-zero counts),
     * the table SHALL render exactly one row per queue with all four columns populated.
     * Validates: Requirements 4.1, 4.5
     */
    it("renders exactly one row per queue with all columns populated", () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.record({
              queue_name: fc.string({ minLength: 1, maxLength: 50 }),
              available: fc.nat({ max: 100000 }),
              delayed: fc.nat({ max: 100000 }),
              in_flight: fc.nat({ max: 100000 }),
            }),
            { minLength: 1, maxLength: 20 },
          ),
          (queues) => {
            // Deduplicate by queue_name to avoid rowKey conflicts
            const unique = [
              ...new Map(queues.map((q) => [q.queue_name, q])).values(),
            ];

            const { getAllByRole, unmount } = render(
              <QueueMonitorTable queues={unique} />,
            );
            const rows = getAllByRole("row").slice(1); // exclude header row
            expect(rows).toHaveLength(unique.length);
            // Each row should have 4 cells
            rows.forEach((row) => {
              expect(row.querySelectorAll("td").length).toBe(4);
            });
            unmount();
          },
        ),
        { numRuns: 100 },
      );
    });
  });

  describe("Property 7: Queue Alphabetical Sorting", () => {
    /**
     * Feature: queue-monitor, Property 7: Queue Alphabetical Sorting
     * For any set of queue names, the UI shall display rows in ascending
     * alphabetical order by queue name, regardless of input order.
     * Validates: Requirements 6.2
     */
    it("displays queue rows in alphabetical order", () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.record({
              queue_name: fc
                .string({ minLength: 1, maxLength: 50 })
                .filter((s) => s.trim().length > 0),
              available: fc.nat({ max: 100000 }),
              delayed: fc.nat({ max: 100000 }),
              in_flight: fc.nat({ max: 100000 }),
            }),
            { minLength: 2, maxLength: 20 },
          ),
          (queues) => {
            // Deduplicate by queue_name
            const unique = [
              ...new Map(queues.map((q) => [q.queue_name, q])).values(),
            ];
            if (unique.length < 2) return;

            const { getAllByRole, unmount } = render(
              <QueueMonitorTable queues={unique} />,
            );
            const rows = getAllByRole("row").slice(1);
            const displayedNames = rows.map(
              (row) => row.querySelectorAll("td")[0].textContent,
            );
            const sortedNames = [...unique.map((q) => q.queue_name)].sort(
              (a, b) => a.localeCompare(b),
            );
            expect(displayedNames).toEqual(sortedNames);
            unmount();
          },
        ),
        { numRuns: 100 },
      );
    });
  });

  describe("Property 6: Queue Name Display Format", () => {
    /**
     * Feature: queue-monitor, Property 6: Queue Name Display Format
     * For any queue name returned by the backend, the displayed name shall
     * exactly match the queue_name field with no transformation.
     * Validates: Requirements 6.1
     */
    it("displays queue names exactly as returned without transformation", () => {
      fc.assert(
        fc.property(
          fc
            .string({ minLength: 1, maxLength: 50 })
            .filter((s) => s.trim().length > 0),
          (queue_name) => {
            const queues: QueueStats[] = [
              { queue_name, available: 0, delayed: 0, in_flight: 0 },
            ];
            const { getAllByRole, unmount } = render(
              <QueueMonitorTable queues={queues} />,
            );
            const rows = getAllByRole("row").slice(1);
            const displayedName = rows[0].querySelectorAll("td")[0].textContent;
            expect(displayedName).toBe(queue_name);
            unmount();
          },
        ),
        { numRuns: 100 },
      );
    });
  });
});
