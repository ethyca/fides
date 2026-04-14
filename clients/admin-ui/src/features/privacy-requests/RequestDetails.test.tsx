import { render, screen } from "@testing-library/react";
import React from "react";

import { PrivacyRequestStatus } from "~/types/api";

import RequestDetails from "./RequestDetails";
import { PrivacyRequestEntity } from "./types";

// Mock features
const mockUseFeatures = jest.fn();
jest.mock("~/features/common/features", () => ({
  useFeatures: () => mockUseFeatures(),
  useFlags: () => ({ flags: { jiraIntegration: false } }),
}));

// Mock property query
const mockUseGetPropertyByIdQuery = jest.fn();
jest.mock("~/features/properties/property.slice", () => ({
  useGetPropertyByIdQuery: (...args: any[]) =>
    mockUseGetPropertyByIdQuery(...args),
}));

// Mock sub-components that have their own Redux/API requirements
jest.mock("./attachments/RequestAttachments", () => ({
  __esModule: true,
  default: () => <div data-testid="request-attachments" />,
}));
jest.mock("./jira-tickets/RequestJiraTickets", () => ({
  __esModule: true,
  default: () => <div data-testid="request-jira-tickets" />,
}));
jest.mock("./RequestCustomFields", () => ({
  __esModule: true,
  default: () => <div data-testid="request-custom-fields" />,
}));
jest.mock("~/features/common/RequestStatusBadge", () => ({
  __esModule: true,
  default: ({ status }: any) => (
    <span data-testid="status-badge">{status}</span>
  ),
}));
jest.mock("~/features/common/RequestType", () => ({
  __esModule: true,
  default: () => <span data-testid="request-type" />,
}));
jest.mock("~/features/common/DaysLeftTag", () => ({
  __esModule: true,
  default: () => <span data-testid="days-left-tag" />,
}));
jest.mock("../common/ClipboardButton", () => ({
  __esModule: true,
  default: () => <span data-testid="clipboard-button" />,
}));

const baseRequest: PrivacyRequestEntity = {
  id: "pri_123",
  status: PrivacyRequestStatus.PENDING,
  created_at: "2024-01-15T10:00:00Z",
  days_left: 5,
  identity: {
    email: { label: "Email", value: "user@example.com" },
  },
  policy: {
    name: "Access Policy",
    key: "access_policy",
    rules: [],
  },
};

describe("RequestDetails", () => {
  beforeEach(() => {
    mockUseFeatures.mockReturnValue({ plus: false });
    mockUseGetPropertyByIdQuery.mockReturnValue({ data: undefined });
  });

  describe("Property row", () => {
    it("does not render when property_id is absent", () => {
      mockUseFeatures.mockReturnValue({ plus: true });
      render(<RequestDetails subjectRequest={baseRequest} />);
      expect(screen.queryByText("Property")).not.toBeInTheDocument();
    });

    it("does not render when hasPlus is false even if property_id is set", () => {
      mockUseFeatures.mockReturnValue({ plus: false });
      render(
        <RequestDetails
          subjectRequest={{ ...baseRequest, property_id: "FDS-123" }}
        />,
      );
      expect(screen.queryByText("Property")).not.toBeInTheDocument();
    });

    it("renders the property name as a link when hasPlus and property_id are set", () => {
      mockUseFeatures.mockReturnValue({ plus: true });
      mockUseGetPropertyByIdQuery.mockReturnValue({
        data: { name: "My Website", id: "FDS-123" },
      });
      render(
        <RequestDetails
          subjectRequest={{ ...baseRequest, property_id: "FDS-123" }}
        />,
      );
      const link = screen.getByRole("link", { name: "My Website" });
      expect(link).toHaveAttribute("href", "/properties/FDS-123");
    });

    it("falls back to property_id when property data has not loaded", () => {
      mockUseFeatures.mockReturnValue({ plus: true });
      mockUseGetPropertyByIdQuery.mockReturnValue({ data: undefined });
      render(
        <RequestDetails
          subjectRequest={{ ...baseRequest, property_id: "FDS-123" }}
        />,
      );
      expect(screen.getByText("FDS-123")).toBeInTheDocument();
    });

    it("skips the query when hasPlus is false", () => {
      mockUseFeatures.mockReturnValue({ plus: false });
      render(
        <RequestDetails
          subjectRequest={{ ...baseRequest, property_id: "FDS-123" }}
        />,
      );
      expect(mockUseGetPropertyByIdQuery).toHaveBeenCalledWith("FDS-123", {
        skip: true,
      });
    });

    it("skips the query when property_id is absent", () => {
      mockUseFeatures.mockReturnValue({ plus: true });
      render(<RequestDetails subjectRequest={baseRequest} />);
      expect(mockUseGetPropertyByIdQuery).toHaveBeenCalledWith(undefined, {
        skip: true,
      });
    });
  });
});
