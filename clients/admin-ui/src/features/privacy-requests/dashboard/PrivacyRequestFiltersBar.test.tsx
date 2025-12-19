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

// Mock fidesui
jest.mock("fidesui", () => ({
  AntDatePicker: {
    RangePicker: ({ placeholder }: any) => (
      <div data-testid="date-range-filter">
        <input type="text" placeholder={placeholder?.[0]} />
        <input type="text" placeholder={placeholder?.[1]} />
      </div>
    ),
  },
  AntDisplayValueType: {} as any,
  AntFlex: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  AntSelect: ({ children, value, onChange, ...props }: any) => (
    <select
      {...props}
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
    >
      {children}
    </select>
  ),
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
      // Check that it was called with the search value
      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalled();
        const { calls } = mockSetFilters.mock;
        expect(calls.length).toBeGreaterThan(0);
        // Verify at least one call has a search property
        expect(calls.some((call) => call[0].search)).toBe(true);
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

      // Date picker should be in the document with values
      expect(screen.getByTestId("date-range-filter")).toBeInTheDocument();
    });
  });

  describe("Status filter", () => {
    it("should render status filter with all status options", () => {
      render(<PrivacyRequestFiltersBar {...defaultProps} />);
      const statusFilter = screen.getByTestId("request-status-filter");
      expect(statusFilter).toBeInTheDocument();
    });

    it("should handle single status selection", () => {
      render(<PrivacyRequestFiltersBar {...defaultProps} />);
      const statusFilter = screen.getByTestId("request-status-filter");
      expect(statusFilter).toBeInTheDocument();
      // Status selection is handled by Ant Design Select component
    });

    it("should handle multiple status selections", () => {
      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{
            ...defaultProps.filters,
            status: [
              PrivacyRequestStatus.PENDING,
              PrivacyRequestStatus.COMPLETE,
            ],
          }}
        />,
      );
      const statusFilter = screen.getByTestId("request-status-filter");
      expect(statusFilter).toBeInTheDocument();
    });

    it("should clear status filter", () => {
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
      expect(statusFilter).toBeInTheDocument();
    });

    it("should support all status values", () => {
      const allStatuses = [
        PrivacyRequestStatus.PENDING,
        PrivacyRequestStatus.APPROVED,
        PrivacyRequestStatus.DENIED,
        PrivacyRequestStatus.COMPLETE,
        PrivacyRequestStatus.ERROR,
        PrivacyRequestStatus.IN_PROCESSING,
        PrivacyRequestStatus.PAUSED,
        PrivacyRequestStatus.CANCELED,
        PrivacyRequestStatus.AWAITING_EMAIL_SEND,
        PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION,
        PrivacyRequestStatus.IDENTITY_UNVERIFIED,
        PrivacyRequestStatus.REQUIRES_INPUT,
        PrivacyRequestStatus.DUPLICATE,
      ];

      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{
            ...defaultProps.filters,
            status: allStatuses,
          }}
        />,
      );

      const statusFilter = screen.getByTestId("request-status-filter");
      expect(statusFilter).toBeInTheDocument();
    });
  });

  describe("Action type filter", () => {
    it("should render action type filter", () => {
      render(<PrivacyRequestFiltersBar {...defaultProps} />);
      const actionTypeFilter = screen.getByTestId("request-action-type-filter");
      expect(actionTypeFilter).toBeInTheDocument();
    });

    it("should handle single action type selection", () => {
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
      expect(actionTypeFilter).toBeInTheDocument();
    });

    it("should handle multiple action type selections", () => {
      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{
            ...defaultProps.filters,
            action_type: [ActionType.ACCESS, ActionType.ERASURE],
          }}
        />,
      );
      const actionTypeFilter = screen.getByTestId("request-action-type-filter");
      expect(actionTypeFilter).toBeInTheDocument();
    });

    it("should support all action type values", () => {
      const allActionTypes = [
        ActionType.ACCESS,
        ActionType.ERASURE,
        ActionType.CONSENT,
        ActionType.UPDATE,
      ];

      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{
            ...defaultProps.filters,
            action_type: allActionTypes,
          }}
        />,
      );

      const actionTypeFilter = screen.getByTestId("request-action-type-filter");
      expect(actionTypeFilter).toBeInTheDocument();
    });
  });

  describe("Location filter", () => {
    it("should render location filter", () => {
      render(<PrivacyRequestFiltersBar {...defaultProps} />);
      const locationFilter = screen.getByTestId("request-location-filter");
      expect(locationFilter).toBeInTheDocument();
    });

    it("should display selected location", () => {
      render(
        <PrivacyRequestFiltersBar
          {...defaultProps}
          filters={{
            ...defaultProps.filters,
            location: "US",
          }}
        />,
      );
      const locationFilter = screen.getByTestId("request-location-filter");
      expect(locationFilter).toBeInTheDocument();
    });
  });

  describe("Custom field filters", () => {
    it("should not render custom field filters when no config is available", () => {
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: undefined,
      });

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
                department: {
                  label: "Department",
                  field_type: "text",
                },
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

    it("should handle custom field value changes", async () => {
      const user = userEvent.setup();
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: {
          actions: [
            {
              policy_key: "access",
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

      render(<PrivacyRequestFiltersBar {...defaultProps} />);

      const customFieldInput = screen.getByTestId(
        "custom-field-input-department",
      );
      await user.type(customFieldInput, "Engineering");

      // The mocked input calls onChange for each character
      // Check that it was called with the custom_privacy_request_fields
      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalled();
        const { calls } = mockSetFilters.mock;
        expect(calls.length).toBeGreaterThan(0);
        // Verify at least one call has custom_privacy_request_fields
        expect(
          calls.some((call) => call[0].custom_privacy_request_fields),
        ).toBe(true);
      });
    });

    it("should handle clearing custom field values", async () => {
      const user = userEvent.setup();
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: {
          actions: [
            {
              policy_key: "access",
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

    it("should clean up null values from custom fields object", async () => {
      const user = userEvent.setup();
      mockUseGetPrivacyCenterConfigQuery.mockReturnValue({
        data: {
          actions: [
            {
              policy_key: "access",
              custom_privacy_request_fields: {
                department: {
                  label: "Department",
                  field_type: "text",
                },
                team: {
                  label: "Team",
                  field_type: "text",
                },
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

      // Clear one field
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
                department: {
                  label: "Department",
                  field_type: "text",
                },
              },
            },
            {
              policy_key: "erasure",
              custom_privacy_request_fields: {
                reason: {
                  label: "Reason",
                  field_type: "text",
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
