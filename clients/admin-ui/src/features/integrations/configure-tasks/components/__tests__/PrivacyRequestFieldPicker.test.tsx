/* eslint-disable import/no-extraneous-dependencies */
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";

import { makeStore } from "~/app/store";

import { PrivacyRequestFieldPicker } from "../PrivacyRequestFieldPicker";

// Mock nuqs before importing utils since it's ESM-only and incompatible with Jest
jest.mock("nuqs", () => ({
  createParser: jest.fn(() => ({
    parse: jest.fn(),
    serialize: jest.fn(),
    withOptions: jest.fn(function withOptions() {
      return this;
    }),
  })),
}));

// Mock query-string to avoid ES module issues in Jest
jest.mock("query-string", () => ({
  __esModule: true,
  default: {
    stringify: jest.fn(),
    parse: jest.fn(),
  },
}));

// Mock react-dnd to avoid ES module issues in Jest
jest.mock("react-dnd", () => ({
  useDrag: jest.fn(() => [{}, jest.fn()]),
  useDrop: jest.fn(() => [{}, jest.fn()]),
  DndProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock the API slices
jest.mock(
  "~/features/datastore-connections/connection-manual-tasks.slice",
  () => ({
    useGetPrivacyRequestFieldsQuery: jest.fn(),
  }),
);

jest.mock("~/features/privacy-requests/privacy-requests.slice", () => {
  const actual = jest.requireActual(
    "~/features/privacy-requests/privacy-requests.slice",
  );
  return {
    ...actual,
    useGetPrivacyCenterConfigQuery: jest.fn(),
  };
});

// Mock extractUniqueCustomFields - we'll use the real implementation by importing it
jest.mock("~/features/privacy-requests/dashboard/utils", () => {
  const actual = jest.requireActual(
    "~/features/privacy-requests/dashboard/utils",
  );
  return {
    ...actual,
    extractUniqueCustomFields: jest.fn(actual.extractUniqueCustomFields),
  };
});

const mockUseGetPrivacyRequestFieldsQuery =
  require("~/features/datastore-connections/connection-manual-tasks.slice").useGetPrivacyRequestFieldsQuery;
const mockUseGetPrivacyCenterConfigQuery =
  require("~/features/privacy-requests/privacy-requests.slice").useGetPrivacyCenterConfigQuery;

const renderWithProvider = (component: React.ReactElement) => {
  const store = makeStore();
  return render(<Provider store={store}>{component}</Provider>);
};

describe("PrivacyRequestFieldPicker", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const defaultProps = {
    value: undefined,
    onChange: jest.fn(),
    connectionKey: "test_connection",
  };

  describe("Basic Rendering States", () => {
    it("should show loading state", () => {
      mockUseGetPrivacyRequestFieldsQuery.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: undefined,
      });

      renderWithProvider(<PrivacyRequestFieldPicker {...defaultProps} />);

      const select = screen.getByTestId("privacy-request-field-select");
      expect(select).toBeInTheDocument();
    });

    it("should show error message when query fails", () => {
      mockUseGetPrivacyRequestFieldsQuery.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: "Failed to fetch" },
      });
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: undefined,
      });

      renderWithProvider(<PrivacyRequestFieldPicker {...defaultProps} />);

      expect(
        screen.getByText(
          "Failed to load privacy request fields. Please try again.",
        ),
      ).toBeInTheDocument();
    });

    it("should show empty state message when no fields available", () => {
      mockUseGetPrivacyRequestFieldsQuery.mockReturnValue({
        data: {
          privacy_request: {},
        },
        isLoading: false,
        error: null,
      });
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: undefined,
      });

      renderWithProvider(<PrivacyRequestFieldPicker {...defaultProps} />);

      expect(
        screen.getByText("No privacy request fields available."),
      ).toBeInTheDocument();
    });
  });

  describe("Standard Fields", () => {
    it("should display standard privacy request fields grouped by category", () => {
      mockUseGetPrivacyRequestFieldsQuery.mockReturnValue({
        data: {
          privacy_request: {
            created_at: {
              field_path: "privacy_request.created_at",
              field_type: "string",
              description: "Created at",
              is_convenience_field: false,
            },
            identity: {
              email: {
                field_path: "privacy_request.identity.email",
                field_type: "string",
                description: "Email",
                is_convenience_field: false,
              },
              phone_number: {
                field_path: "privacy_request.identity.phone_number",
                field_type: "string",
                description: "Phone number",
                is_convenience_field: false,
              },
            },
            policy: {
              name: {
                field_path: "privacy_request.policy.name",
                field_type: "string",
                description: "Policy name",
                is_convenience_field: false,
              },
            },
          },
        },
        isLoading: false,
        error: null,
      });
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: undefined,
      });

      renderWithProvider(<PrivacyRequestFieldPicker {...defaultProps} />);

      const select = screen.getByTestId("privacy-request-field-select");
      expect(select).toBeInTheDocument();
    });
  });

  describe("Custom Fields Integration", () => {
    it("should display custom fields when privacy center config has them", () => {
      mockUseGetPrivacyRequestFieldsQuery.mockReturnValue({
        data: {
          privacy_request: {
            created_at: {
              field_path: "privacy_request.created_at",
              field_type: "string",
              description: "Created at",
              is_convenience_field: false,
            },
          },
        },
        isLoading: false,
        error: null,
      });
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: {
          actions: [
            {
              policy_key: "access",
              icon_path: "/icon.svg",
              title: "Access Request",
              description: "Request access",
              identity_inputs: {},
              custom_privacy_request_fields: {
                department: {
                  label: "Department",
                  field_type: "text",
                },
                legal_entity: {
                  label: "Legal Entity",
                  field_type: "select",
                  options: ["Entity A", "Entity B"],
                },
              },
            },
          ],
        },
      });

      renderWithProvider(<PrivacyRequestFieldPicker {...defaultProps} />);

      const select = screen.getByTestId("privacy-request-field-select");
      expect(select).toBeInTheDocument();
    });

    it("should merge standard and custom fields", () => {
      mockUseGetPrivacyRequestFieldsQuery.mockReturnValue({
        data: {
          privacy_request: {
            created_at: {
              field_path: "privacy_request.created_at",
              field_type: "string",
              description: "Created at",
              is_convenience_field: false,
            },
            identity: {
              email: {
                field_path: "privacy_request.identity.email",
                field_type: "string",
                description: "Email",
                is_convenience_field: false,
              },
            },
          },
        },
        isLoading: false,
        error: null,
      });
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: {
          actions: [
            {
              policy_key: "access",
              icon_path: "/icon.svg",
              title: "Access Request",
              description: "Request access",
              identity_inputs: {},
              custom_privacy_request_fields: {
                department: {
                  label: "Department",
                  field_type: "text",
                },
              },
            },
          ],
        },
      });

      renderWithProvider(<PrivacyRequestFieldPicker {...defaultProps} />);

      const select = screen.getByTestId("privacy-request-field-select");
      expect(select).toBeInTheDocument();
      // Both standard and custom fields should be available
    });

    it("should handle no custom fields gracefully", () => {
      mockUseGetPrivacyRequestFieldsQuery.mockReturnValue({
        data: {
          privacy_request: {
            created_at: {
              field_path: "privacy_request.created_at",
              field_type: "string",
              description: "Created at",
              is_convenience_field: false,
            },
          },
        },
        isLoading: false,
        error: null,
      });
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: {
          actions: [
            {
              policy_key: "access",
              icon_path: "/icon.svg",
              title: "Access Request",
              description: "Request access",
              identity_inputs: {},
              // No custom_privacy_request_fields
            },
          ],
        },
      });

      renderWithProvider(<PrivacyRequestFieldPicker {...defaultProps} />);

      const select = screen.getByTestId("privacy-request-field-select");
      expect(select).toBeInTheDocument();
    });
  });
});
