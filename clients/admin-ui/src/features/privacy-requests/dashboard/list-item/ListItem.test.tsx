import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

import {
  ActionType,
  PrivacyRequestResponse,
  PrivacyRequestStatus,
} from "~/types/api";

import { ListItem } from "./ListItem";

// Mock nuqs (ESM-only package)
jest.mock("nuqs", () => ({
  createParser: jest.fn(() => ({
    parse: jest.fn(),
    serialize: jest.fn(),
    withOptions: jest.fn(function withOptions() {
      return this;
    }),
  })),
}));

// Mock next/router
jest.mock("next/router", () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: "/",
    query: {},
    asPath: "/",
  }),
}));

// Mock RequestStatusBadge
jest.mock("~/features/common/RequestStatusBadge", () => ({
  __esModule: true,
  default: ({ status }: any) => (
    <span data-testid="status-badge">{status}</span>
  ),
}));

// Mock factory to create complete PrivacyRequestResponse objects
const createMockRequest = (
  overrides?: Partial<PrivacyRequestResponse>,
): PrivacyRequestResponse =>
  ({
    id: "pri_123",
    status: PrivacyRequestStatus.PENDING,
    created_at: "2024-01-15T10:00:00Z",
    updated_at: "2024-01-15T10:00:00Z",
    started_processing_at: null,
    finished_processing_at: null,
    canceled_at: null,
    paused_at: null,
    days_left: 5,
    identity: {
      email: { label: "Email", value: "user@example.com" },
    },
    policy: {
      name: "Access Request Policy",
      key: "access_policy",
      execution_timeframe: 30,
      rules: [
        { action_type: ActionType.ACCESS, storage_destination_key: null },
      ],
    },
    source: "privacy_center",
    custom_privacy_request_fields: undefined,
    location: undefined,
    external_id: null,
    identity_verified_at: null,
    reviewer_id: null,
    reviewed_at: null,
    reviewed_by: null,
    cache_key: null,
    is_test_mode: false,
    duplicate_request_group_id: null,
    ...overrides,
  }) as PrivacyRequestResponse;

// Mock RequestTableActions since we're testing ListItem in isolation
jest.mock("../../RequestTableActions", () => ({
  RequestTableActions: ({ subjectRequest }: any) => (
    <div data-testid="request-table-actions">
      <span data-testid="actions-request-id">{subjectRequest.id}</span>
    </div>
  ),
}));

// Mock only the utility functions from fidesui
jest.mock("fidesui", () => {
  const actual = jest.requireActual("fidesui");
  return {
    ...actual,
    formatIsoLocation: ({ isoEntry }: any) =>
      `${isoEntry.country} - ${isoEntry.region}`,
    isoStringToEntry: (str: string) => {
      const parts = str.split("-");
      if (parts.length === 2) {
        return { country: parts[0], region: parts[1] };
      }
      throw new Error("Invalid ISO string");
    },
  };
});

describe("ListItem", () => {
  const baseRequest = createMockRequest();

  // Mock clipboard API for copy tests
  beforeEach(() => {
    Object.defineProperty(navigator, "clipboard", {
      value: {
        writeText: jest.fn(() => Promise.resolve()),
      },
      writable: true,
      configurable: true,
    });
  });

  describe("Identity rendering", () => {
    it("should display primary identity (email)", () => {
      render(<ListItem item={baseRequest} />);
      expect(screen.getByText("user@example.com")).toBeInTheDocument();
    });

    it("should display multiple identities with primary and others separated", () => {
      const request = createMockRequest({
        identity: {
          email: { label: "Email", value: "user@example.com" },
          phone_number: { label: "Phone", value: "+1234567890" },
          custom_id: { label: "Custom ID", value: "CUST123" },
        },
      });

      render(<ListItem item={request} />);

      // Primary identity displayed
      expect(screen.getByText("user@example.com")).toBeInTheDocument();

      // Other identities displayed with labels
      expect(screen.getByText("Phone:")).toBeInTheDocument();
      expect(screen.getByText("+1234567890")).toBeInTheDocument();
      expect(screen.getByText("Custom ID:")).toBeInTheDocument();
      expect(screen.getByText("CUST123")).toBeInTheDocument();
    });
  });

  describe("Basic fields rendering", () => {
    it("should display required fields (policy, source, actions)", () => {
      render(<ListItem item={baseRequest} />);

      expect(screen.getByText("Access Request Policy")).toBeInTheDocument();
      expect(screen.getByText("Policy:")).toBeInTheDocument();
      expect(screen.getByText("Source:")).toBeInTheDocument();
      expect(screen.getByText("privacy_center")).toBeInTheDocument();
      expect(screen.getByTestId("request-table-actions")).toBeInTheDocument();
      expect(screen.getByTestId("actions-request-id")).toHaveTextContent(
        "pri_123",
      );
    });

    it("should render status badge", () => {
      render(<ListItem item={baseRequest} />);
      const listItem = screen.getByRole("listitem");
      expect(listItem).toBeInTheDocument();
    });
  });

  describe("Location rendering", () => {
    it("should display formatted ISO location", () => {
      const request = createMockRequest({ location: "US-CA" });
      render(<ListItem item={request} />);

      expect(screen.getByText("Location:")).toBeInTheDocument();
      expect(screen.getByText(/US/)).toBeInTheDocument();
      expect(screen.getByText(/CA/)).toBeInTheDocument();
    });

    it("should display raw location when ISO parsing fails", () => {
      const request = createMockRequest({ location: "Invalid Location" });
      render(<ListItem item={request} />);

      expect(screen.getByText("Location:")).toBeInTheDocument();
      expect(screen.getByText("Invalid Location")).toBeInTheDocument();
    });

    it("should not display location when not present", () => {
      render(<ListItem item={baseRequest} />);
      expect(screen.queryByText("Location:")).not.toBeInTheDocument();
    });
  });

  describe("Custom fields rendering", () => {
    it("should display string custom fields", () => {
      const request = createMockRequest({
        custom_privacy_request_fields: {
          department: { label: "Department", value: "Engineering" },
        },
      });

      render(<ListItem item={request} />);

      expect(screen.getByText("Department:")).toBeInTheDocument();
      expect(screen.getByText("Engineering")).toBeInTheDocument();
    });

    it("should display numeric custom fields", () => {
      const request = createMockRequest({
        custom_privacy_request_fields: {
          priority: { label: "Priority", value: 5 },
        },
      });

      render(<ListItem item={request} />);

      expect(screen.getByText("Priority:")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument();
    });

    it("should display array custom fields joined with ' - '", () => {
      const request = createMockRequest({
        custom_privacy_request_fields: {
          departments: {
            label: "Departments",
            value: ["Engineering", "Sales"],
          },
        },
      });

      render(<ListItem item={request} />);

      expect(screen.getByText("Departments:")).toBeInTheDocument();
      expect(screen.getByText("Engineering - Sales")).toBeInTheDocument();
    });

    it("should not display custom fields when not present", () => {
      render(<ListItem item={baseRequest} />);
      expect(screen.queryByText("Department:")).not.toBeInTheDocument();
    });
  });

  describe("Checkbox rendering", () => {
    it("should render checkbox when provided", () => {
      const checkbox = <input type="checkbox" data-testid="checkbox" />;
      render(<ListItem item={baseRequest} checkbox={checkbox} />);
      expect(screen.getByTestId("checkbox")).toBeInTheDocument();
    });
  });

  describe("Copy functionality", () => {
    it("should copy value with mouse click and show tooltip", async () => {
      const user = userEvent.setup();
      const request = createMockRequest({
        identity: {
          phone_number: { label: "Phone", value: "+1234567890" },
        },
      });

      render(<ListItem item={request} />);

      const copyButtons = screen.getAllByTestId("copy-button");
      const phoneCopyButton = copyButtons.find(
        (btn) => btn.getAttribute("data-copy-value") === "+1234567890",
      );

      await user.click(phoneCopyButton!);

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith("+1234567890");
      expect(phoneCopyButton).toHaveAttribute("aria-label", "Copy phone");
    });

    it("should copy value using keyboard (Enter key)", async () => {
      const user = userEvent.setup();
      const request = createMockRequest({
        identity: {
          phone_number: { label: "Phone", value: "+1234567890" },
        },
      });

      render(<ListItem item={request} />);

      const copyButtons = screen.getAllByTestId("copy-button");
      const phoneCopyButton = copyButtons.find(
        (btn) => btn.getAttribute("data-copy-value") === "+1234567890",
      );

      phoneCopyButton!.focus();
      await user.keyboard("{Enter}");

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith("+1234567890");
    });
  });
});
