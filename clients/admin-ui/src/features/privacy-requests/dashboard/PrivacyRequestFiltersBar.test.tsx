import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ActionType, ColumnSort, PrivacyRequestStatus } from "~/types/api";

import { PrivacyRequestFiltersBar } from "./PrivacyRequestFiltersBar";

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

// Mock iso-3166 which is ESM-only and causes issues in Jest
jest.mock("iso-3166", () => ({
  iso31661: [
    { alpha2: "US", name: "United States" },
    { alpha2: "CA", name: "Canada" },
    { alpha2: "GB", name: "United Kingdom" },
  ],
  iso31662: [
    { code: "US-CA", name: "California", parent: "US" },
    { code: "US-NY", name: "New York", parent: "US" },
  ],
}));

// Mock only AntSelect to make it testable with native select interactions
jest.mock(
  "fidesui",
  () =>
    new Proxy(jest.requireActual("fidesui"), {
      get(target, prop) {
        if (prop === "AntSelect") {
          const MockAntSelect = ({
            value,
            onChange,
            mode,
            options,
            ...props
          }: any) => {
            const isMultiple = mode === "multiple";
            return (
              <select
                {...props}
                multiple={isMultiple}
                value={isMultiple ? value || [] : value || ""}
                onChange={(e) => {
                  if (isMultiple) {
                    const selectedOptions = Array.from(
                      e.target.selectedOptions,
                    ).map((opt: any) => opt.value);
                    onChange?.(
                      selectedOptions.length > 0 ? selectedOptions : null,
                    );
                  } else {
                    const selectedValue = e.target.value;
                    onChange?.(selectedValue || null);
                  }
                }}
              >
                {options?.map((opt: any) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            );
          };
          MockAntSelect.displayName = "MockAntSelect";
          return MockAntSelect;
        }
        return target[prop as keyof typeof target];
      },
    }),
);

// Mock the privacy center config query
const mockUseGetPrivacyCenterConfigQuery = jest.fn();
jest.mock("../privacy-requests.slice", () => ({
  useGetPrivacyCenterConfigQuery: () => mockUseGetPrivacyCenterConfigQuery(),
}));

jest.mock("~/features/common/DebouncedSearchInput", () => ({
  DebouncedSearchInput: ({
    onChange,
    value,
    placeholder,
    ...props
  }: {
    onChange: (value: string) => void;
    value: string;
    placeholder: string;
  }) => (
    <input
      {...props}
      type="text"
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
}));

// Mock PrivacyRequestSortMenu
jest.mock("./PrivacyRequestSortMenu", () => ({
  __esModule: true,
  default: ({ setSortState }: any) => (
    <button
      type="button"
      data-testid="sort-menu"
      onClick={() =>
        setSortState({
          sort_field: "created_at",
          sort_direction: "desc" as const,
        })
      }
    >
      Sort Menu
    </button>
  ),
}));

// Mock CustomFieldFilter
jest.mock("./CustomFieldFilter", () => ({
  CustomFieldFilter: ({
    fieldName,
    fieldDefinition,
    value,
    onChange,
  }: {
    fieldName: string;
    fieldDefinition: any;
    value: string | null;
    onChange: (value: string | null) => void;
  }) => (
    <input
      data-testid={`custom-field-filter-${fieldName}`}
      placeholder={fieldDefinition.label}
      value={value || ""}
      onChange={(e) => onChange(e.target.value || null)}
    />
  ),
}));

// Helper functions to query date range inputs by Ant Design's date-range attribute
const getDateRangeInput = {
  from: (container: HTMLElement) =>
    container.querySelector('input[date-range="start"]') as HTMLInputElement,
  to: (container: HTMLElement) =>
    container.querySelector('input[date-range="end"]') as HTMLInputElement,
};

describe("PrivacyRequestFiltersBar", () => {
  const mockSetFilters = jest.fn();
  const mockSetSortState = jest.fn();

  const defaultProps = {
    filters: {
      search: null,
      from: null,
      to: null,
      status: null,
      action_type: null,
      location: null,
      custom_privacy_request_fields: null,
    },
    setFilters: mockSetFilters,
    sortState: {
      sort_field: "created_at" as const,
      sort_direction: ColumnSort.ASC,
    },
    setSortState: mockSetSortState,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
      data: undefined,
    });
  });

  describe("Initial render", () => {
    it("should render all filter controls", () => {
      const { container } = render(
        <PrivacyRequestFiltersBar {...defaultProps} />,
      );

      expect(
        screen.getByPlaceholderText("Request ID or identity value"),
      ).toBeInTheDocument();

      // Check date range picker by verifying both inputs exist
      expect(screen.getByPlaceholderText("From")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("To")).toBeInTheDocument();

      expect(screen.getByTestId("request-status-filter")).toBeInTheDocument();
      expect(
        screen.getByTestId("request-action-type-filter"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("request-location-filter")).toBeInTheDocument();
      expect(screen.getByTestId("sort-menu")).toBeInTheDocument();
    });

    it("should display existing filter values", () => {
      const { container } = render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{
            search: "test@example.com",
            from: "2024-01-01",
            to: "2024-01-31",
            status: [PrivacyRequestStatus.PENDING],
            action_type: [ActionType.ACCESS],
            location: "US",
            custom_privacy_request_fields: null,
          }}
        />,
      );

      expect(
        screen.getByPlaceholderText("Request ID or identity value"),
      ).toHaveValue("test@example.com");

      // Use helper to get date range inputs
      const fromInput = getDateRangeInput.from(container);
      const toInput = getDateRangeInput.to(container);
      expect(fromInput).toHaveValue("2024-01-01");
      expect(toInput).toHaveValue("2024-01-31");

      expect(screen.getByTestId("request-location-filter")).toHaveValue("US");
    });
  });

  describe("Complete filtering workflows", () => {
    it("should apply multiple filters in sequence", async () => {
      const user = userEvent.setup();
      const { container } = render(<PrivacyRequestFiltersBar {...defaultProps} />);

      // Search for a request
      const searchInput = screen.getByPlaceholderText(
        "Request ID or identity value",
      );
      await user.type(searchInput, "test@example.com");

      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalled();
        const lastCall =
          mockSetFilters.mock.calls[mockSetFilters.mock.calls.length - 1];
        expect(lastCall[0].search).toBeTruthy();
      });

      // Set date range using helper
      const fromInput = getDateRangeInput.from(container);
      await user.click(fromInput);
      await user.keyboard("2024-01-01");

      await waitFor(() => {
        const lastCall =
          mockSetFilters.mock.calls[mockSetFilters.mock.calls.length - 1];
        expect(lastCall[0].from).toBe("2024-01-01");
      });

      // Select status
      const statusFilter = screen.getByTestId("request-status-filter");
      await user.selectOptions(statusFilter, [
        PrivacyRequestStatus.PENDING,
        PrivacyRequestStatus.COMPLETE,
      ]);

      expect(mockSetFilters).toHaveBeenCalledWith({
        status: [PrivacyRequestStatus.PENDING, PrivacyRequestStatus.COMPLETE],
      });

      // Select action type
      const actionTypeFilter = screen.getByTestId("request-action-type-filter");
      await user.selectOptions(actionTypeFilter, [
        ActionType.ACCESS,
        ActionType.ERASURE,
      ]);

      expect(mockSetFilters).toHaveBeenCalledWith({
        action_type: [ActionType.ACCESS, ActionType.ERASURE],
      });

      // Select location
      const locationFilter = screen.getByTestId("request-location-filter");
      await user.selectOptions(locationFilter, "US");

      expect(mockSetFilters).toHaveBeenCalledWith({ location: "US" });
    });

    it("should clear all filters", async () => {
      const user = userEvent.setup();
      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{
            search: "test@example.com",
            from: "2024-01-01",
            to: "2024-01-31",
            status: [PrivacyRequestStatus.PENDING],
            action_type: [ActionType.ACCESS],
            location: "US",
            custom_privacy_request_fields: null,
          }}
        />,
      );

      // Clear status
      const statusFilter = screen.getByTestId("request-status-filter");
      await user.selectOptions(statusFilter, []);

      expect(mockSetFilters).toHaveBeenCalledWith({ status: null });

      // Clear action type
      const actionTypeFilter = screen.getByTestId("request-action-type-filter");
      await user.selectOptions(actionTypeFilter, []);

      expect(mockSetFilters).toHaveBeenCalledWith({ action_type: null });

      // Clear location
      const locationFilter = screen.getByTestId("request-location-filter");
      await user.selectOptions(locationFilter, "");

      expect(mockSetFilters).toHaveBeenCalledWith({ location: null });

      // Clear search
      const searchInput = screen.getByPlaceholderText(
        "Request ID or identity value",
      );
      await user.clear(searchInput);

      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalledWith({ search: null });
      });
    });

    it("should handle sorting changes", async () => {
      const user = userEvent.setup();
      render(<PrivacyRequestFiltersBar {...defaultProps} />);

      const sortMenu = screen.getByTestId("sort-menu");
      await user.click(sortMenu);

      expect(mockSetSortState).toHaveBeenCalledWith({
        sort_field: "created_at",
        sort_direction: "desc",
      });
    });
  });

  describe("Custom field filtering", () => {
    it("should apply standard and custom filters together", async () => {
      const user = userEvent.setup();
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: {
          actions: [
            {
              policy_key: "access",
              custom_privacy_request_fields: {
                department: { label: "Department", field_type: "text" },
              },
            },
          ],
        },
      });

      render(<PrivacyRequestFiltersBar {...defaultProps} />);

      // Verify custom field is rendered alongside standard filters
      expect(
        screen.getByTestId("custom-field-filter-department"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("request-status-filter")).toBeInTheDocument();

      // Apply a standard filter
      const statusFilter = screen.getByTestId("request-status-filter");
      await user.selectOptions(statusFilter, [PrivacyRequestStatus.PENDING]);

      expect(mockSetFilters).toHaveBeenCalledWith({
        status: [PrivacyRequestStatus.PENDING],
      });

      // Apply a custom field filter
      const departmentInput = screen.getByTestId(
        "custom-field-filter-department",
      );
      await user.type(departmentInput, "Engineering");

      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalledWith({
          custom_privacy_request_fields: { department: "Engineering" },
        });
      });
    });

    it("should clear custom fields", async () => {
      const user = userEvent.setup();
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: {
          actions: [
            {
              policy_key: "access",
              custom_privacy_request_fields: {
                department: { label: "Department", field_type: "text" },
              },
            },
          ],
        },
      });

      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{
            ...defaultProps.filters,
            custom_privacy_request_fields: {
              department: "Engineering",
            },
          }}
        />,
      );

      // Clear the custom field
      const departmentInput = screen.getByTestId(
        "custom-field-filter-department",
      );
      await user.clear(departmentInput);

      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalledWith({
          custom_privacy_request_fields: null,
        });
      });
    });
  });
});
