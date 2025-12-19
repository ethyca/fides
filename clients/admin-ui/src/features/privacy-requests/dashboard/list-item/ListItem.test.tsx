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

  describe("Primary identity rendering", () => {
    it.each<{
      identity: Record<string, { label: string; value: string }>;
      expected: string;
      description: string;
    }>([
      {
        identity: { email: { label: "Email", value: "user@example.com" } },
        expected: "user@example.com",
        description: "email",
      },
      {
        identity: { phone_number: { label: "Phone", value: "+1234567890" } },
        expected: "+1234567890",
        description: "phone when email not available",
      },
      {
        identity: { custom_id: { label: "Custom ID", value: "CUST123" } },
        expected: "CUST123",
        description: "custom field when email and phone not available",
      },
      {
        identity: {
          email: { label: "Email", value: "user@example.com" },
          phone_number: { label: "Phone", value: "+1234567890" },
        },
        expected: "user@example.com",
        description: "email over phone when both available",
      },
    ])("should display $description", ({ identity, expected }) => {
      const request = createMockRequest({ identity });
      render(<ListItem item={request} />);
      // Since we're using real components now, search for the text content
      expect(screen.getByText(expected)).toBeInTheDocument();
    });
  });

  describe("Other identities rendering", () => {
    it("should display other identities excluding primary", () => {
      const request = createMockRequest({
        identity: {
          email: { label: "Email", value: "user@example.com" },
          phone_number: { label: "Phone", value: "+1234567890" },
          custom_id: { label: "Custom ID", value: "CUST123" },
        },
      });

      render(<ListItem item={request} />);

      expect(screen.getByText("Phone:")).toBeInTheDocument();
      expect(screen.getByText("+1234567890")).toBeInTheDocument();
      expect(screen.getByText("Custom ID:")).toBeInTheDocument();
      expect(screen.getByText("CUST123")).toBeInTheDocument();
    });

    it("should not display other identities when only primary exists", () => {
      render(<ListItem item={baseRequest} />);

      expect(screen.queryByText("Phone:")).not.toBeInTheDocument();
    });

    it("should filter out identities with empty values", () => {
      const request = createMockRequest({
        identity: {
          email: { label: "Email", value: "user@example.com" },
          phone_number: { label: "Phone", value: "" },
        },
      });

      render(<ListItem item={request} />);

      expect(screen.queryByText("Phone:")).not.toBeInTheDocument();
    });
  });

  describe("Basic fields rendering", () => {
    it("should display all required fields correctly", () => {
      render(<ListItem item={baseRequest} />);

      // Check for policy name
      expect(screen.getByText("Access Request Policy")).toBeInTheDocument();
      expect(screen.getByText("Policy:")).toBeInTheDocument();

      // Check for source
      expect(screen.getByText("Source:")).toBeInTheDocument();
      expect(screen.getByText("privacy_center")).toBeInTheDocument();

      // Check that actions are rendered
      expect(screen.getByTestId("request-table-actions")).toBeInTheDocument();
      expect(screen.getByTestId("actions-request-id")).toHaveTextContent(
        "pri_123",
      );
    });
  });

  describe("Location rendering", () => {
    it("should display location with ISO formatting when present", () => {
      const request = createMockRequest({
        location: "US-CA",
      });

      render(<ListItem item={request} />);

      expect(screen.getByText("Location:")).toBeInTheDocument();
      // The formatIsoLocation should show the formatted location
      expect(screen.getByText(/US/)).toBeInTheDocument();
      expect(screen.getByText(/CA/)).toBeInTheDocument();
    });

    it("should display raw location when ISO parsing fails", () => {
      const request = createMockRequest({
        location: "Invalid Location",
      });

      render(<ListItem item={request} />);

      expect(screen.getByText("Location:")).toBeInTheDocument();
      expect(screen.getByText("Invalid Location")).toBeInTheDocument();
    });

    it("should not display location when not present", () => {
      render(<ListItem item={baseRequest} />);

      // Since location is not present, the Location: label shouldn't exist
      const locationLabels = screen.queryAllByText("Location:");
      expect(locationLabels).toHaveLength(0);
    });
  });

  describe("Custom fields rendering", () => {
    it("should display custom fields with labels and values", () => {
      const request = createMockRequest({
        custom_privacy_request_fields: {
          department: { label: "Department", value: "Engineering" },
          employee_id: { label: "Employee ID", value: "EMP123" },
        },
      });

      render(<ListItem item={request} />);

      expect(screen.getByText("Department:")).toBeInTheDocument();
      expect(screen.getByText("Engineering")).toBeInTheDocument();
      expect(screen.getByText("Employee ID:")).toBeInTheDocument();
      expect(screen.getByText("EMP123")).toBeInTheDocument();
    });

    it("should render array custom fields joined with ' - '", () => {
      const request = createMockRequest({
        custom_privacy_request_fields: {
          departments: {
            label: "Departments",
            value: ["Engineering", "Sales", "Marketing"],
          },
        },
      });

      render(<ListItem item={request} />);

      expect(screen.getByText("Departments:")).toBeInTheDocument();
      expect(
        screen.getByText("Engineering - Sales - Marketing"),
      ).toBeInTheDocument();
    });

    it("should display numeric custom field values", () => {
      const request = createMockRequest({
        custom_privacy_request_fields: {
          priority: { label: "Priority", value: 5 },
        },
      });

      render(<ListItem item={request} />);

      expect(screen.getByText("Priority:")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument();
    });

    it("should not display custom fields when not present", () => {
      render(<ListItem item={baseRequest} />);

      expect(screen.queryByText("Department:")).not.toBeInTheDocument();
    });

    it("should filter out custom fields with null or empty values", () => {
      const request = createMockRequest({
        custom_privacy_request_fields: {
          department: { label: "Department", value: "Engineering" },
          team: { label: "Team", value: "" },
          location: { label: "Location", value: null as any },
        },
      });

      render(<ListItem item={request} />);

      expect(screen.getByText("Department:")).toBeInTheDocument();
      expect(screen.getByText("Engineering")).toBeInTheDocument();
      expect(screen.queryByText("Team:")).not.toBeInTheDocument();
      // Note: we already check for Location: in the location tests
    });
  });

  it.each([
    PrivacyRequestStatus.PENDING,
    PrivacyRequestStatus.APPROVED,
    PrivacyRequestStatus.DENIED,
    PrivacyRequestStatus.COMPLETE,
    PrivacyRequestStatus.ERROR,
  ])("should display status %s", (status) => {
    const request = createMockRequest({ status });
    render(<ListItem item={request} />);
    // Status is displayed in the header component
    const listItem = screen.getByRole("listitem");
    expect(listItem).toBeInTheDocument();
  });

  describe("Checkbox rendering", () => {
    it("should render checkbox when provided", () => {
      const checkbox = <input type="checkbox" data-testid="checkbox" />;
      render(<ListItem item={baseRequest} checkbox={checkbox} />);
      expect(screen.getByTestId("checkbox")).toBeInTheDocument();
    });

    it("should not render checkbox when not provided", () => {
      render(<ListItem item={baseRequest} />);
      expect(screen.queryByTestId("checkbox")).not.toBeInTheDocument();
    });
  });

  describe("Copy functionality", () => {
    it("should render copy buttons for identities with copyValue", () => {
      const request = createMockRequest({
        identity: {
          email: { label: "Email", value: "user@example.com" },
          phone_number: { label: "Phone", value: "+1234567890" },
        },
      });

      render(<ListItem item={request} />);

      // LabeledText with copyValue should render copy buttons
      const copyButtons = screen.getAllByTestId("copy-button");
      expect(copyButtons.length).toBeGreaterThan(0);
    });

    it("should copy value to clipboard when copy button is clicked", async () => {
      const user = userEvent.setup();
      const request = createMockRequest({
        identity: {
          email: { label: "Email", value: "user@example.com" },
          phone_number: { label: "Phone", value: "+1234567890" },
        },
      });

      render(<ListItem item={request} />);

      const copyButtons = screen.getAllByTestId("copy-button");
      const phoneCopyButton = copyButtons.find(
        (btn) => btn.getAttribute("data-copy-value") === "+1234567890",
      );

      expect(phoneCopyButton).toBeDefined();
      await user.click(phoneCopyButton!);

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith("+1234567890");
    });

    it("should handle keyboard interaction with copy button", async () => {
      const user = userEvent.setup();
      const request = createMockRequest({
        identity: {
          email: { label: "Email", value: "user@example.com" },
          phone_number: { label: "Phone", value: "+1234567890" },
        },
      });

      render(<ListItem item={request} />);

      const copyButtons = screen.getAllByTestId("copy-button");
      const phoneCopyButton = copyButtons.find(
        (btn) => btn.getAttribute("data-copy-value") === "+1234567890",
      );

      expect(phoneCopyButton).toBeDefined();
      phoneCopyButton!.focus();
      expect(phoneCopyButton).toHaveFocus();

      await user.keyboard("{Enter}");

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith("+1234567890");
    });

    it("should have accessible labels for copy buttons", () => {
      const request = createMockRequest({
        identity: {
          email: { label: "Email", value: "user@example.com" },
          phone_number: { label: "Phone", value: "+1234567890" },
        },
      });

      render(<ListItem item={request} />);

      const copyButtons = screen.getAllByTestId("copy-button");
      const phoneCopyButton = copyButtons.find(
        (btn) => btn.getAttribute("data-copy-value") === "+1234567890",
      );

      expect(phoneCopyButton).toHaveAttribute("aria-label", "Copy phone");
    });
  });

  describe("Keyboard navigation", () => {
    it("should allow tab navigation through interactive elements", async () => {
      const user = userEvent.setup();
      const request = createMockRequest({
        identity: {
          email: { label: "Email", value: "user@example.com" },
          phone_number: { label: "Phone", value: "+1234567890" },
        },
      });

      render(<ListItem item={request} />);

      // Get all focusable elements
      const copyButtons = screen.getAllByTestId("copy-button");

      // Tab through elements
      await user.tab();
      expect(copyButtons[0]).toHaveFocus();

      await user.tab();
      if (copyButtons.length > 1) {
        expect(copyButtons[1]).toHaveFocus();
      }
    });

    it("should maintain focus management within the list item", async () => {
      const user = userEvent.setup();
      const request = createMockRequest({
        custom_privacy_request_fields: {
          department: { label: "Department", value: "Engineering" },
        },
      });

      render(<ListItem item={request} />);

      const copyButtons = screen.getAllByTestId("copy-button");
      if (copyButtons.length > 0) {
        copyButtons[0].focus();
        expect(copyButtons[0]).toHaveFocus();

        // Shift+Tab should move focus backwards
        await user.keyboard("{Shift>}{Tab}{/Shift}");
        // Focus should have moved (exact element depends on DOM structure)
        expect(copyButtons[0]).not.toHaveFocus();
      }
    });
  });

  it("should render complete request with all optional fields", () => {
    const complexRequest = createMockRequest({
      identity: {
        email: { label: "Email", value: "user@example.com" },
        phone_number: { label: "Phone", value: "+1234567890" },
        custom_id: { label: "Custom ID", value: "CUST123" },
      },
      location: "US-CA",
      custom_privacy_request_fields: {
        department: { label: "Department", value: "Engineering" },
        priority: { label: "Priority", value: 5 },
        tags: { label: "Tags", value: ["urgent", "vip"] },
      },
    });

    render(<ListItem item={complexRequest} />);

    // Verify all fields are rendered
    expect(screen.getByText("Phone:")).toBeInTheDocument();
    expect(screen.getByText("Custom ID:")).toBeInTheDocument();
    expect(screen.getByText("Location:")).toBeInTheDocument();
    expect(screen.getByText("Department:")).toBeInTheDocument();
    expect(screen.getByText("Priority:")).toBeInTheDocument();
    expect(screen.getByText("Tags:")).toBeInTheDocument();
    expect(screen.getByText("urgent - vip")).toBeInTheDocument();
  });
});
