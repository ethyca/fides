import { fireEvent, screen } from "@testing-library/react";
import React from "react";

import { render } from "~/../__tests__/utils/test-utils";
import { useGetConnectorTemplateVersionsQuery } from "~/features/connector-templates/connector-template.slice";
import VersionHistoryTab from "~/features/integrations/VersionHistoryTab";

jest.mock("query-string", () => ({
  __esModule: true,
  default: { stringify: jest.fn(), parse: jest.fn() },
}));
jest.mock("react-dnd", () => ({
  useDrag: jest.fn(() => [{}, jest.fn()]),
  useDrop: jest.fn(() => [{}, jest.fn()]),
  DndProvider: ({ children }: { children: React.ReactNode }) => children,
}));
// eslint-disable-next-line global-require
jest.mock(
  "nuqs",
  () => require("../../../../__tests__/utils/nuqs-mock").nuqsMock,
);

jest.mock("~/features/connector-templates/connector-template.slice", () => ({
  useGetConnectorTemplateVersionsQuery: jest.fn(),
}));

// Stub SaaSVersionModal so its own RTK deps don't need wiring up
jest.mock("~/features/connector-templates/SaaSVersionModal", () => ({
  __esModule: true,
  default: ({
    isOpen,
    connectorType,
    version,
  }: {
    isOpen: boolean;
    connectorType: string;
    version: string;
    onClose: () => void;
  }) =>
    isOpen ? (
      <div data-testid="version-modal">
        {connectorType} v{version}
      </div>
    ) : null,
}));

// ── Typed mock ─────────────────────────────────────────────────────────────────

const mockUseVersions = useGetConnectorTemplateVersionsQuery as jest.Mock;

// ── Fixtures ───────────────────────────────────────────────────────────────────

const VERSIONS = [
  {
    connector_type: "stripe",
    version: "0.0.12",
    is_custom: false,
    created_at: "2026-03-01T10:00:00Z",
  },
  {
    connector_type: "stripe",
    version: "0.0.11",
    is_custom: true,
    created_at: "2026-02-15T08:00:00Z",
  },
];

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("VersionHistoryTab", () => {
  it("shows a spinner while loading", () => {
    mockUseVersions.mockReturnValue({ data: undefined, isLoading: true });

    render(<VersionHistoryTab connectorType="stripe" />);

    // Ant Design Spin renders with class ant-spin
    expect(document.querySelector(".ant-spin")).toBeInTheDocument();
  });

  it("shows an error message when the versions query fails", () => {
    mockUseVersions.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    render(<VersionHistoryTab connectorType="stripe" />);

    expect(
      screen.getByText("Could not load version history."),
    ).toBeInTheDocument();
  });

  it("shows empty-state message when no versions are available", () => {
    mockUseVersions.mockReturnValue({ data: [], isLoading: false });

    render(<VersionHistoryTab connectorType="stripe" />);

    expect(
      screen.getByText("No version history captured yet."),
    ).toBeInTheDocument();
  });

  it("renders a row for each captured version", () => {
    mockUseVersions.mockReturnValue({ data: VERSIONS, isLoading: false });

    render(<VersionHistoryTab connectorType="stripe" />);

    expect(screen.getByText("v0.0.12")).toBeInTheDocument();
    expect(screen.getByText("v0.0.11")).toBeInTheDocument();
  });

  it("shows OOB badge for non-custom and Custom badge for custom versions", () => {
    mockUseVersions.mockReturnValue({ data: VERSIONS, isLoading: false });

    render(<VersionHistoryTab connectorType="stripe" />);

    expect(screen.getByText("OOB")).toBeInTheDocument();
    expect(screen.getByText("Custom")).toBeInTheDocument();
  });

  it("opens the version modal when a View button is clicked", () => {
    mockUseVersions.mockReturnValue({ data: VERSIONS, isLoading: false });

    render(<VersionHistoryTab connectorType="stripe" />);

    const viewButtons = screen.getAllByRole("button", { name: /view/i });
    fireEvent.click(viewButtons[0]);

    expect(screen.getByTestId("version-modal")).toBeInTheDocument();
    expect(screen.getByText("stripe v0.0.12")).toBeInTheDocument();
  });

  it("shows the second version's details when its View button is clicked", () => {
    mockUseVersions.mockReturnValue({ data: VERSIONS, isLoading: false });

    render(<VersionHistoryTab connectorType="stripe" />);

    const viewButtons = screen.getAllByRole("button", { name: /view/i });
    fireEvent.click(viewButtons[1]);

    expect(screen.getByText("stripe v0.0.11")).toBeInTheDocument();
  });

  it("passes the connector type to the query", () => {
    mockUseVersions.mockReturnValue({ data: [], isLoading: false });

    render(<VersionHistoryTab connectorType="hubspot" />);

    expect(mockUseVersions).toHaveBeenCalledWith("hubspot");
  });
});
