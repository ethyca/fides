import { jest } from "@jest/globals";

/**
 * Creates a mock table state for testing table-related hooks
 */
export function createMockTableState<TSortKey = string>(
  overrides: Partial<{
    pageIndex: number;
    pageSize: number;
    sortKey?: TSortKey;
    sortOrder?: "ascend" | "descend";
    columnFilters: Record<string, any>;
    searchQuery?: string;
    updatePagination: jest.MockedFunction<
      (pageIndex: number, pageSize?: number) => void
    >;
    updateSorting: jest.MockedFunction<
      (sortKey?: TSortKey, sortOrder?: "ascend" | "descend") => void
    >;
    updateFilters: jest.MockedFunction<(filters: Record<string, any>) => void>;
    updateSearch: jest.MockedFunction<(query?: string) => void>;
    resetState: jest.MockedFunction<() => void>;
    paginationConfig?: {
      pageSizeOptions: number[];
      showSizeChanger: boolean;
    };
  }> = {},
) {
  return {
    pageIndex: 1,
    pageSize: 25,
    sortKey: undefined,
    sortOrder: undefined,
    columnFilters: {},
    searchQuery: undefined,
    updatePagination: jest.fn(),
    updateSorting: jest.fn(),
    updateFilters: jest.fn(),
    updateSearch: jest.fn(),
    resetState: jest.fn(),
    paginationConfig: {
      pageSizeOptions: [10, 25, 50],
      showSizeChanger: true,
    },
    ...overrides,
  };
}
