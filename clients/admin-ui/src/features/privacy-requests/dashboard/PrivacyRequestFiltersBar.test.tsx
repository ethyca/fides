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

  describe("Search filter", () => {
    it("should update search filter when text is entered", async () => {
      const user = userEvent.setup();
      render(<PrivacyRequestFiltersBar {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText(
        "Request ID or identity value",
      );
      await user.type(searchInput, "test@example.com");

      // The mocked DebouncedSearchInput calls onChange for each character
      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalled();
        const lastCall =
          mockSetFilters.mock.calls[mockSetFilters.mock.calls.length - 1];
        expect(lastCall[0].search).toBeTruthy();
      });
    });

    it("should clear search filter when input is cleared", async () => {
      const user = userEvent.setup();
      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{ ...defaultProps.filters, search: "test" }}
        />,
      );

      const searchInput = screen.getByPlaceholderText(
        "Request ID or identity value",
      );
      await user.clear(searchInput);

      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalledWith({ search: null });
      });
    });
  });

  describe("Date range filter", () => {
    it("should render date range picker", () => {
      render(<PrivacyRequestFiltersBar {...defaultProps} />);
      expect(screen.getByTestId("date-range-filter")).toBeInTheDocument();
    });

    it("should display selected date range", () => {
      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{
            ...defaultProps.filters,
            from: "2024-01-01",
            to: "2024-01-31",
          }}
        />,
      );

      const fromInput = screen.getByTestId("date-range-from");
      const toInput = screen.getByTestId("date-range-to");

      expect(fromInput).toHaveValue("2024-01-01");
      expect(toInput).toHaveValue("2024-01-31");
    });

    it("should update filters when date range is selected", async () => {
      const user = userEvent.setup();
      render(<PrivacyRequestFiltersBar {...defaultProps} />);

      const fromInput = screen.getByTestId("date-range-from");
      await user.type(fromInput, "2024-01-01");

      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalled();
        const lastCall =
          mockSetFilters.mock.calls[mockSetFilters.mock.calls.length - 1];
        expect(lastCall[0].from).toBe("2024-01-01");
      });
    });

    it("should clear date range when cleared", async () => {
      const user = userEvent.setup();
      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{
            ...defaultProps.filters,
            from: "2024-01-01",
            to: "2024-01-31",
          }}
        />,
      );

      const fromInput = screen.getByTestId("date-range-from");
      await user.clear(fromInput);

      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalled();
      });
    });
  });

  describe("Status filter", () => {
    it("should render status filter with options", () => {
      render(<PrivacyRequestFiltersBar {...defaultProps} />);
      const statusFilter = screen.getByTestId("request-status-filter");
      expect(statusFilter).toBeInTheDocument();
    });

    it("should call setFilters when status is selected", async () => {
      const user = userEvent.setup();
      render(<PrivacyRequestFiltersBar {...defaultProps} />);

      const statusFilter = screen.getByTestId("request-status-filter");
      await user.selectOptions(statusFilter, [PrivacyRequestStatus.PENDING]);

      expect(mockSetFilters).toHaveBeenCalledWith({
        status: [PrivacyRequestStatus.PENDING],
      });
    });

    it("should handle multiple status selections", async () => {
      const user = userEvent.setup();
      render(<PrivacyRequestFiltersBar {...defaultProps} />);

      const statusFilter = screen.getByTestId("request-status-filter");
      await user.selectOptions(statusFilter, [
        PrivacyRequestStatus.PENDING,
        PrivacyRequestStatus.COMPLETE,
      ]);

      expect(mockSetFilters).toHaveBeenCalledWith({
        status: [PrivacyRequestStatus.PENDING, PrivacyRequestStatus.COMPLETE],
      });
    });

    it("should clear status filter when selection is cleared", async () => {
      const user = userEvent.setup();
      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{
            ...defaultProps.filters,
            status: [PrivacyRequestStatus.PENDING],
          }}
        />,
      );

      const statusFilter = screen.getByTestId("request-status-filter");
      await user.selectOptions(statusFilter, []);

      expect(mockSetFilters).toHaveBeenCalledWith({ status: null });
    });
  });

  describe("Action type filter", () => {
    it("should render action type filter with options", () => {
      render(<PrivacyRequestFiltersBar {...defaultProps} />);
      const actionTypeFilter = screen.getByTestId("request-action-type-filter");
      expect(actionTypeFilter).toBeInTheDocument();
    });

    it("should call setFilters when action type is selected", async () => {
      const user = userEvent.setup();
      render(<PrivacyRequestFiltersBar {...defaultProps} />);

      const actionTypeFilter = screen.getByTestId("request-action-type-filter");
      await user.selectOptions(actionTypeFilter, [ActionType.ACCESS]);

      expect(mockSetFilters).toHaveBeenCalledWith({
        action_type: [ActionType.ACCESS],
      });
    });

    it("should handle multiple action type selections", async () => {
      const user = userEvent.setup();
      render(<PrivacyRequestFiltersBar {...defaultProps} />);

      const actionTypeFilter = screen.getByTestId("request-action-type-filter");
      await user.selectOptions(actionTypeFilter, [
        ActionType.ACCESS,
        ActionType.ERASURE,
      ]);

      expect(mockSetFilters).toHaveBeenCalledWith({
        action_type: [ActionType.ACCESS, ActionType.ERASURE],
      });
    });

    it("should clear action type filter when selection is cleared", async () => {
      const user = userEvent.setup();
      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{
            ...defaultProps.filters,
            action_type: [ActionType.ACCESS],
          }}
        />,
      );

      const actionTypeFilter = screen.getByTestId("request-action-type-filter");
      await user.selectOptions(actionTypeFilter, []);

      expect(mockSetFilters).toHaveBeenCalledWith({ action_type: null });
    });
  });

  describe("Location filter", () => {
    it("should render location filter", () => {
      render(<PrivacyRequestFiltersBar {...defaultProps} />);
      expect(screen.getByTestId("request-location-filter")).toBeInTheDocument();
    });

    it("should call setFilters when location is selected", async () => {
      const user = userEvent.setup();
      render(<PrivacyRequestFiltersBar {...defaultProps} />);

      const locationFilter = screen.getByTestId("request-location-filter");
      await user.selectOptions(locationFilter, "US");

      expect(mockSetFilters).toHaveBeenCalledWith({ location: "US" });
    });

    it("should display selected location value", () => {
      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{ ...defaultProps.filters, location: "US" }}
        />,
      );

      const locationFilter = screen.getByTestId(
        "request-location-filter",
      ) as HTMLSelectElement;
      expect(locationFilter.value).toBe("US");
    });

    it("should clear location filter when cleared", async () => {
      const user = userEvent.setup();
      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{ ...defaultProps.filters, location: "US" }}
        />,
      );

      const locationFilter = screen.getByTestId("request-location-filter");
      await user.selectOptions(locationFilter, "");

      expect(mockSetFilters).toHaveBeenCalledWith({ location: null });
    });
  });

  describe("Custom field filters", () => {
    it("should not render when no config is available", () => {
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({ data: undefined });
      render(<PrivacyRequestFiltersBar {...defaultProps} />);
      expect(
        screen.queryByTestId("custom-field-filter-department"),
      ).not.toBeInTheDocument();
    });

    it("should render custom field filters from config", () => {
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: {
          actions: [
            {
              policy_key: "access",
              custom_privacy_request_fields: {
                department: { label: "Department", field_type: "text" },
                location: {
                  label: "Location",
                  field_type: "select",
                  options: ["US", "EU"],
                },
              },
            },
          ],
        },
      });

      render(<PrivacyRequestFiltersBar {...defaultProps} />);
      expect(
        screen.getByTestId("custom-field-filter-department"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("custom-field-filter-location"),
      ).toBeInTheDocument();
    });

    it("should handle custom field value changes and clearing", async () => {
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
            custom_privacy_request_fields: { department: "Engineering" },
          }}
        />,
      );

      const clearButton = screen.getByTestId("custom-field-clear-department");
      await user.click(clearButton);

      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalledWith({
          custom_privacy_request_fields: null,
        });
      });
    });

    it("should clean up null values when clearing one field from multiple", async () => {
      const user = userEvent.setup();
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: {
          actions: [
            {
              policy_key: "access",
              custom_privacy_request_fields: {
                department: { label: "Department", field_type: "text" },
                team: { label: "Team", field_type: "text" },
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
              team: "Backend",
            },
          }}
        />,
      );

      const clearButton = screen.getByTestId("custom-field-clear-team");
      await user.click(clearButton);

      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalledWith({
          custom_privacy_request_fields: { department: "Engineering" },
        });
      });
    });

    it("should merge custom fields from multiple actions", () => {
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: {
          actions: [
            {
              policy_key: "access",
              custom_privacy_request_fields: {
                department: { label: "Department", field_type: "text" },
              },
            },
            {
              policy_key: "erasure",
              custom_privacy_request_fields: {
                reason: { label: "Reason", field_type: "text" },
              },
            },
          ],
        },
      });

      render(<PrivacyRequestFiltersBar {...defaultProps} />);
      expect(
        screen.getByTestId("custom-field-filter-department"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("custom-field-filter-reason"),
      ).toBeInTheDocument();
    });
  });

  describe("Sort menu", () => {
    it("should render sort menu", () => {
      render(<PrivacyRequestFiltersBar {...defaultProps} />);
      expect(screen.getByTestId("sort-menu")).toBeInTheDocument();
    });

    it("should call setSortState when sort changes", async () => {
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
});
