import { render, screen } from "@testing-library/react";
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

// Mock the components
jest.mock("./components", () => ({
  Header: ({ privacyRequest, primaryIdentity }: any) => (
    <div data-testid="header">
      <span data-testid="header-identity">{primaryIdentity?.value}</span>
      <span data-testid="header-status">{privacyRequest.status}</span>
    </div>
  ),
  LabeledText: ({ label, children, copyValue }: any) => (
    <div
      data-testid={`labeled-text-${label.toLowerCase().replace(/\s+/g, "-")}`}
    >
      <span data-testid="label">{label}</span>
      <span data-testid="value">{children}</span>
      {copyValue && <span data-testid="copy-value">{copyValue}</span>}
    </div>
  ),
  DaysLeft: ({ daysLeft, status, timeframe }: any) => (
    <div data-testid="days-left">
      {daysLeft !== null && (
        <span data-testid="days-left-value">{daysLeft}</span>
      )}
      <span data-testid="days-left-status">{status}</span>
      <span data-testid="days-left-timeframe">{timeframe}</span>
    </div>
  ),
  ReceivedOn: ({ createdAt }: any) => (
    <div data-testid="received-on">
      <span data-testid="received-on-date">{createdAt}</span>
    </div>
  ),
}));

jest.mock("../../RequestTableActions", () => ({
  RequestTableActions: ({ subjectRequest }: any) => (
    <div data-testid="request-table-actions">
      <span data-testid="actions-request-id">{subjectRequest.id}</span>
    </div>
  ),
}));

// Mock fidesui
jest.mock("fidesui", () => ({
  AntFlex: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  AntList: {
    Item: ({ children }: any) => <div data-testid="list-item">{children}</div>,
  },
  formatIsoLocation: ({ isoEntry }: any) =>
    `${isoEntry.country} - ${isoEntry.region}`,
  isoStringToEntry: (str: string) => {
    const parts = str.split("-");
    return { country: parts[0], region: parts[1] };
  },
}));

describe("ListItem", () => {
  const baseRequest = createMockRequest();

  describe("Primary identity rendering", () => {
    it("should display email as primary identity", () => {
      render(<ListItem item={baseRequest} />);

      expect(screen.getByTestId("header-identity")).toHaveTextContent(
        "user@example.com",
      );
    });

    it("should display phone as primary identity when email is not available", () => {
      const request = createMockRequest({
        identity: {
          phone_number: { label: "Phone", value: "+1234567890" },
        },
      });

      render(<ListItem item={request} />);

      expect(screen.getByTestId("header-identity")).toHaveTextContent(
        "+1234567890",
      );
    });

    it("should display first available identity when email and phone are not available", () => {
      const request = createMockRequest({
        identity: {
          custom_id: { label: "Custom ID", value: "CUST123" },
        },
      });

      render(<ListItem item={request} />);

      expect(screen.getByTestId("header-identity")).toHaveTextContent(
        "CUST123",
      );
    });

    it("should prefer email over phone when both are available", () => {
      const request = createMockRequest({
        identity: {
          email: { label: "Email", value: "user@example.com" },
          phone_number: { label: "Phone", value: "+1234567890" },
        },
      });

      render(<ListItem item={request} />);

      expect(screen.getByTestId("header-identity")).toHaveTextContent(
        "user@example.com",
      );
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

      expect(screen.getByTestId("labeled-text-phone")).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-custom-id")).toBeInTheDocument();
    });

    it("should not display other identities when only primary exists", () => {
      render(<ListItem item={baseRequest} />);

      expect(
        screen.queryByTestId("labeled-text-phone"),
      ).not.toBeInTheDocument();
    });

    it("should filter out identities with empty values", () => {
      const request = createMockRequest({
        identity: {
          email: { label: "Email", value: "user@example.com" },
          phone_number: { label: "Phone", value: "" },
        },
      });

      render(<ListItem item={request} />);

      expect(
        screen.queryByTestId("labeled-text-phone"),
      ).not.toBeInTheDocument();
    });
  });

  describe("Policy and source rendering", () => {
    it("should display policy name", () => {
      render(<ListItem item={baseRequest} />);

      const policyLabel = screen.getByTestId("labeled-text-policy");
      expect(policyLabel).toBeInTheDocument();
      expect(policyLabel).toHaveTextContent("Access Request Policy");
    });

    it("should display source", () => {
      render(<ListItem item={baseRequest} />);

      const sourceLabel = screen.getByTestId("labeled-text-source");
      expect(sourceLabel).toBeInTheDocument();
      expect(sourceLabel).toHaveTextContent("privacy_center");
    });
  });

  describe("Location rendering", () => {
    it("should display location with ISO formatting when present", () => {
      const request = createMockRequest({
        location: "US-CA",
      });

      render(<ListItem item={request} />);

      const locationLabel = screen.getByTestId("labeled-text-location");
      expect(locationLabel).toBeInTheDocument();
      expect(locationLabel).toHaveTextContent("US - CA");
    });

    it("should display raw location when ISO parsing fails", () => {
      const request = createMockRequest({
        location: "Invalid Location",
      });

      render(<ListItem item={request} />);

      const locationLabel = screen.getByTestId("labeled-text-location");
      expect(locationLabel).toBeInTheDocument();
      expect(locationLabel).toHaveTextContent("Invalid Location");
    });

    it("should not display location when not present", () => {
      render(<ListItem item={baseRequest} />);

      expect(
        screen.queryByTestId("labeled-text-location"),
      ).not.toBeInTheDocument();
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

      expect(screen.getByTestId("labeled-text-department")).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-department")).toHaveTextContent(
        "Engineering",
      );
      expect(
        screen.getByTestId("labeled-text-employee-id"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-employee-id")).toHaveTextContent(
        "EMP123",
      );
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

      const departmentsLabel = screen.getByTestId("labeled-text-departments");
      expect(departmentsLabel).toBeInTheDocument();
      expect(departmentsLabel).toHaveTextContent(
        "Engineering - Sales - Marketing",
      );
    });

    it("should display numeric custom field values", () => {
      const request = createMockRequest({
        custom_privacy_request_fields: {
          priority: { label: "Priority", value: 5 },
        },
      });

      render(<ListItem item={request} />);

      const priorityLabel = screen.getByTestId("labeled-text-priority");
      expect(priorityLabel).toBeInTheDocument();
      expect(priorityLabel).toHaveTextContent("5");
    });

    it("should not display custom fields when not present", () => {
      render(<ListItem item={baseRequest} />);

      expect(
        screen.queryByTestId("labeled-text-department"),
      ).not.toBeInTheDocument();
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

      expect(screen.getByTestId("labeled-text-department")).toBeInTheDocument();
      expect(screen.queryByTestId("labeled-text-team")).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("labeled-text-location"),
      ).not.toBeInTheDocument();
    });
  });

  describe("Days left and received date rendering", () => {
    it("should display days left with correct props", () => {
      render(<ListItem item={baseRequest} />);

      const daysLeft = screen.getByTestId("days-left");
      expect(daysLeft).toBeInTheDocument();
      expect(screen.getByTestId("days-left-value")).toHaveTextContent("5");
      expect(screen.getByTestId("days-left-status")).toHaveTextContent(
        "pending",
      );
      expect(screen.getByTestId("days-left-timeframe")).toHaveTextContent("30");
    });

    it("should display received date", () => {
      render(<ListItem item={baseRequest} />);

      const receivedOn = screen.getByTestId("received-on");
      expect(receivedOn).toBeInTheDocument();
      expect(screen.getByTestId("received-on-date")).toHaveTextContent(
        "2024-01-15T10:00:00Z",
      );
    });
  });

  describe("Status rendering", () => {
    it("should display request status in header", () => {
      render(<ListItem item={baseRequest} />);

      expect(screen.getByTestId("header-status")).toHaveTextContent("pending");
    });

    it("should handle different status values", () => {
      const statuses = [
        PrivacyRequestStatus.PENDING,
        PrivacyRequestStatus.APPROVED,
        PrivacyRequestStatus.DENIED,
        PrivacyRequestStatus.COMPLETE,
        PrivacyRequestStatus.ERROR,
      ];

      statuses.forEach((status) => {
        const request = createMockRequest({ status });
        const { unmount } = render(<ListItem item={request} />);
        expect(screen.getByTestId("header-status")).toHaveTextContent(status);
        unmount();
      });
    });
  });

  describe("Actions rendering", () => {
    it("should render RequestTableActions component", () => {
      render(<ListItem item={baseRequest} />);

      expect(screen.getByTestId("request-table-actions")).toBeInTheDocument();
    });

    it("should pass correct request to RequestTableActions", () => {
      render(<ListItem item={baseRequest} />);

      expect(screen.getByTestId("actions-request-id")).toHaveTextContent(
        "pri_123",
      );
    });
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

  describe("Complex rendering scenarios", () => {
    it("should render complete request with all fields", () => {
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

      // Should render all components
      expect(screen.getByTestId("header")).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-policy")).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-source")).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-location")).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-phone")).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-custom-id")).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-department")).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-priority")).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-tags")).toBeInTheDocument();
      expect(screen.getByTestId("days-left")).toBeInTheDocument();
      expect(screen.getByTestId("received-on")).toBeInTheDocument();
      expect(screen.getByTestId("request-table-actions")).toBeInTheDocument();
    });

    it("should render minimal request with only required fields", () => {
      const minimalRequest = createMockRequest({
        identity: {
          email: { label: "Email", value: "user@example.com" },
        },
        location: undefined,
        custom_privacy_request_fields: undefined,
      });

      render(<ListItem item={minimalRequest} />);

      // Should render basic components
      expect(screen.getByTestId("header")).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-policy")).toBeInTheDocument();
      expect(screen.getByTestId("labeled-text-source")).toBeInTheDocument();

      // Should not render optional components
      expect(
        screen.queryByTestId("labeled-text-location"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("labeled-text-phone"),
      ).not.toBeInTheDocument();
    });
  });
});
