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

// Mock the privacy center config query
const mockUseGetPrivacyCenterConfigQuery = jest.fn();
jest.mock("../privacy-requests.slice", () => ({
  useGetPrivacyCenterConfigQuery: () => mockUseGetPrivacyCenterConfigQuery(),
}));

// Mock fidesui with testable implementations
jest.mock("fidesui", () => ({
  AntDatePicker: {
    RangePicker: ({ placeholder, onChange, value }: any) => (
      <div data-testid="date-range-filter">
        <input
          data-testid="date-range-from"
          type="text"
          placeholder={placeholder?.[0]}
          value={value?.[0]?.format("YYYY-MM-DD") || ""}
          onChange={(e) => {
            const newValue = e.target.value;
            // eslint-disable-next-line global-require
            const dayjs = require("dayjs");
            onChange?.(newValue ? [dayjs(newValue), value?.[1]] : null);
          }}
        />
        <input
          data-testid="date-range-to"
          type="text"
          placeholder={placeholder?.[1]}
          value={value?.[1]?.format("YYYY-MM-DD") || ""}
          onChange={(e) => {
            const newValue = e.target.value;
            // eslint-disable-next-line global-require
            const dayjs = require("dayjs");
            onChange?.(newValue ? [value?.[0], dayjs(newValue)] : null);
          }}
        />
      </div>
    ),
  },
  AntDisplayValueType: {} as any,
  AntFlex: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  AntSelect: ({ children, value, onChange, mode, ...props }: any) => {
    const isMultiple = mode === "multiple";
    return (
      <select
        {...props}
        multiple={isMultiple}
        value={isMultiple ? value || [] : value}
        onChange={(e) => {
          if (isMultiple) {
            const selectedOptions = Array.from(e.target.selectedOptions).map(
              (opt: any) => opt.value,
            );
            onChange?.(selectedOptions);
          } else {
            onChange?.(e.target.value);
          }
        }}
      >
        {children}
      </select>
    );
  },
  LocationSelect: ({ value, onChange, ...props }: any) => (
    <select
      {...props}
      value={value || ""}
      onChange={(e) => onChange?.(e.target.value || null)}
    >
      <option value="">Select location</option>
      <option value="US">United States</option>
      <option value="EU">European Union</option>
    </select>
  ),
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
    value,
    onChange,
  }: {
    fieldName: string;
    value: string | null;
    onChange: (value: string | null) => void;
  }) => (
    <div data-testid={`custom-field-filter-${fieldName}`}>
      <input
        data-testid={`custom-field-input-${fieldName}`}
        value={value || ""}
        onChange={(e) => onChange(e.target.value || null)}
      />
      <button
        type="button"
        data-testid={`custom-field-clear-${fieldName}`}
        onClick={() => onChange(null)}
      >
        Clear
      </button>
    </div>
  ),
}));

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
      render(<PrivacyRequestFiltersBar {...defaultProps} />);

      expect(
        screen.getByPlaceholderText("Request ID or identity value"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("date-range-filter")).toBeInTheDocument();
      expect(screen.getByTestId("request-status-filter")).toBeInTheDocument();
      expect(
        screen.getByTestId("request-action-type-filter"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("request-location-filter")).toBeInTheDocument();
      expect(screen.getByTestId("sort-menu")).toBeInTheDocument();
    });

    it("should display existing filter values", () => {
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

      expect(
        screen.getByPlaceholderText("Request ID or identity value"),
      ).toHaveValue("test@example.com");
      expect(screen.getByTestId("date-range-from")).toHaveValue("2024-01-01");
      expect(screen.getByTestId("date-range-to")).toHaveValue("2024-01-31");
      expect(screen.getByTestId("request-location-filter")).toHaveValue("US");
    });
  });

  describe("Complete filtering workflows", () => {
    it("should apply multiple filters in sequence", async () => {
      const user = userEvent.setup();
      render(<PrivacyRequestFiltersBar {...defaultProps} />);

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

      // Set date range
      const fromInput = screen.getByTestId("date-range-from");
      await user.type(fromInput, "2024-01-01");

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

      // Clear search
      const searchInput = screen.getByPlaceholderText(
        "Request ID or identity value",
      );
      await user.clear(searchInput);

      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalledWith({ search: null });
      });

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
        "custom-field-input-department",
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
      const clearButton = screen.getByTestId("custom-field-clear-department");
      await user.click(clearButton);

      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalledWith({
          custom_privacy_request_fields: null,
        });
      });
    });
  });
});
