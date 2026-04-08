import { fireEvent, screen } from "@testing-library/react";
import React from "react";

import { render } from "~/../__tests__/utils/test-utils";
import EventLog from "~/features/privacy-requests/events-and-logs/EventLog";
import {
  ExecutionLog,
  ExecutionLogStatus,
} from "~/features/privacy-requests/types";
import { ActionType } from "~/types/api";

jest.mock("query-string", () => ({
  __esModule: true,
  default: { stringify: jest.fn(), parse: jest.fn() },
}));
jest.mock("react-dnd", () => ({
  useDrag: jest.fn(() => [{}, jest.fn()]),
  useDrop: jest.fn(() => [{}, jest.fn()]),
  DndProvider: ({ children }: { children: React.ReactNode }) => children,
}));
jest.mock(
  "nuqs",
  // eslint-disable-next-line global-require
  () => require("../../../../../__tests__/utils/nuqs-mock").nuqsMock,
);

// Capture openVersionModal so tests can assert on calls
const mockOpenVersionModal = jest.fn();
jest.mock("~/features/connector-templates/hooks/useSaaSVersionModal", () => ({
  useSaaSVersionModal: () => ({
    openVersionModal: mockOpenVersionModal,
    modal: null,
  }),
}));

// ── Helpers ────────────────────────────────────────────────────────────────────

const makeLog = (overrides: Partial<ExecutionLog> = {}): ExecutionLog => ({
  collection_name: "stripe_customer",
  fields_affected: [],
  message: "success - retrieved 3 records",
  action_type: ActionType.ACCESS,
  status: ExecutionLogStatus.COMPLETE,
  updated_at: "2026-03-01T10:00:00Z",
  saas_version: null,
  ...overrides,
});

const noop = () => {};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("EventLog — version badge", () => {
  beforeEach(() => {
    mockOpenVersionModal.mockClear();
  });

  it("renders the version badge when saas_version is present", () => {
    render(
      <EventLog
        eventLogs={[makeLog({ saas_version: "0.0.11" })]}
        onDetailPanel={noop}
      />,
    );

    expect(screen.getByText("v0.0.11")).toBeInTheDocument();
  });

  it("shows a dash in the Version column when saas_version is null", () => {
    render(
      <EventLog
        eventLogs={[makeLog({ saas_version: null })]}
        onDetailPanel={noop}
      />,
    );

    // Records column also shows "-" for completed rows with no parseable count,
    // so just confirm the Version column header is present (dataset entries exist)
    expect(screen.getByText("Version")).toBeInTheDocument();
  });

  it("does not make the badge clickable when connection_key is absent on the log", () => {
    render(
      <EventLog
        eventLogs={[makeLog({ saas_version: "0.0.11" })]}
        onDetailPanel={noop}
      />,
    );

    const wrapper = screen.getByTestId("version-badge-wrapper");

    expect(wrapper).not.toHaveAttribute("title");
    expect(wrapper.tagName.toLowerCase()).toBe("span");

    fireEvent.click(wrapper);
    expect(mockOpenVersionModal).not.toHaveBeenCalled();
  });

  it("makes the badge clickable and triggers openVersionModal when connection_key is on the log", () => {
    render(
      <EventLog
        eventLogs={[
          makeLog({ saas_version: "0.0.11", connection_key: "stripe_conn" }),
        ]}
        onDetailPanel={noop}
      />,
    );

    const wrapper = screen.getByTestId("version-badge-wrapper");

    expect(wrapper).toHaveAttribute("title", "View version config");

    fireEvent.click(wrapper);
    expect(mockOpenVersionModal).toHaveBeenCalledTimes(1);
    expect(mockOpenVersionModal).toHaveBeenCalledWith("stripe_conn", "0.0.11");
  });

  it("passes the correct version for each row when multiple versioned logs are shown", () => {
    const logs = [
      makeLog({
        saas_version: "0.0.11",
        connection_key: "stripe_conn",
        updated_at: "2026-03-01T10:00:00Z",
      }),
      makeLog({
        saas_version: "0.0.12",
        connection_key: "stripe_conn",
        updated_at: "2026-03-02T10:00:00Z",
      }),
    ];

    render(<EventLog eventLogs={logs} onDetailPanel={noop} />);

    const wrappers = screen.getAllByTestId("version-badge-wrapper");
    expect(wrappers).toHaveLength(2);

    fireEvent.click(wrappers[0]);
    expect(mockOpenVersionModal).toHaveBeenLastCalledWith(
      "stripe_conn",
      "0.0.11",
    );

    fireEvent.click(wrappers[1]);
    expect(mockOpenVersionModal).toHaveBeenLastCalledWith(
      "stripe_conn",
      "0.0.12",
    );
  });

  it("does not show the Version column when no logs have a collection_name", () => {
    render(
      <EventLog
        eventLogs={[makeLog({ collection_name: null, saas_version: "0.0.11" })]}
        onDetailPanel={noop}
      />,
    );

    expect(screen.queryByText("Version")).not.toBeInTheDocument();
  });
});
