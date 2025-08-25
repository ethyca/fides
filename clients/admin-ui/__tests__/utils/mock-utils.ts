import { jest } from "@jest/globals";

import { TableStateWithHelpers } from "~/features/common/table/hooks";

/**
 * Creates a mock table state for testing table-related hooks
 */
export const createMockTableState = <TSortKey extends string = string>(
  overrides: Partial<TableStateWithHelpers<TSortKey>> = {},
): TableStateWithHelpers<TSortKey> => {
  return {
    tableId: "test-table",
    pageIndex: 1,
    pageSize: 25,
    sortKey: undefined,
    sortOrder: undefined,
    columnFilters: {},
    searchQuery: undefined,
    columnWidths: {},
    updatePageIndex: jest.fn(),
    updatePageSize: jest.fn(),
    updateSorting: jest.fn(),
    updateFilters: jest.fn(),
    updateSearch: jest.fn(),
    updateColumnWidth: jest.fn(),
    resetColumnWidths: jest.fn(),
    resetState: jest.fn(),
    paginationConfig: {
      pageSizeOptions: [10, 25, 50],
      showSizeChanger: true,
    },
    ...overrides,
  };
};
