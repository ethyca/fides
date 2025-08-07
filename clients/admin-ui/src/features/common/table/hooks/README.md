# Reusable Table Hooks with NuQS Integration

This document describes the table hook system that provides reusable state management, URL synchronization, and deep linking capabilities for tables in the Admin UI.

## Architecture Overview

The table hook system consists of two main hooks that work together:

```
useTableState (Core State + URL Sync)
    ↓
useAntTable (Ant Design Integration) + RTK Query
    ↓
Table Component
```

## Hooks

### 1. `useTableState`

**Purpose**: Core table state management with NuQS integration for URL synchronization.

**Features**:
- Pagination state (page, size)
- Sorting state (field, order)
- Filtering state (column filters)
- Search state
- URL synchronization with NuQS
- Deep linking support

**Usage**:
```tsx
const tableState = useTableState({
  urlSync: {
    pagination: true,
    sorting: true,
    filtering: true,
    search: true,
  },
  pagination: {
    defaultPageSize: 25,
    pageSizeOptions: [10, 25, 50, 100],
  },
  sorting: {
    defaultSortField: 'name',
    defaultSortOrder: 'ascend',
  },
});
```

### 2. `useAntTable`

**Purpose**: Ant Design Table component integration.

**Features**:
- Converts table state to Ant Design props
- Handles row selection
- Manages bulk actions
- Provides event handlers

**Usage**:
```tsx
const {
  tableProps,
  selectionProps,
  selectedRows,
  hasSelectedRows,
  resetSelections,
  getBulkActionProps,
} = useAntTable(tableState, {
  enableSelection: true,
  getRowKey: (record) => record.id,
  bulkActions: bulkActionsConfig,
  dataSource: queryResult.data?.items,
  totalRows: queryResult.data?.total,
});

return (
  <Table
    {...tableProps}
    columns={columns}
    rowSelection={selectionProps}
  />
);
```

## Complete Example

Here's how to build a complete table with the hook system:

```tsx
import { useTableState, useAntTable } from '~/features/common/table/hooks';

const MyTable = ({ additionalParams }) => {
  // 1. Set up table state with URL sync
  const tableState = useTableState({
    urlSync: { pagination: true, sorting: true, filtering: true, search: true },
    pagination: { defaultPageSize: 25 },
    sorting: { defaultSortField: 'name' },
  });

  // 2. Connect to server data with RTK Query
  const queryResult = useGetMyDataQuery({
    ...tableState.queryParams,
    ...additionalParams,
  }, {
    skip: !additionalParams.id
  });

  // 3. Configure Ant Design integration
  const {
    tableProps,
    selectionProps,
    selectedRows,
    resetSelections,
  } = useAntTable(tableState, {
    enableSelection: true,
    getRowKey: (record) => record.id,
    dataSource: queryResult.data?.items,
    totalRows: queryResult.data?.total,
    isLoading: queryResult.isLoading,
  });

  return (
    <div>
      {/* Search and filters */}
      <DebouncedSearchInput
        value={tableState.searchQuery || ""}
        onChange={tableState.updateSearch}
        placeholder="Search..."
      />

      {/* Table */}
      <Table
        {...tableProps}
        columns={columns}
        rowSelection={selectionProps}
      />
    </div>
  );
};
```

## URL Synchronization

The hooks automatically sync table state to URL parameters:

- `page`: Current page number
- `size`: Page size
- `sortField`: Current sort field
- `sortOrder`: Sort direction (`ascend` | `descend`)
- `filters`: Column filters (as JSON)
- `search`: Search query

This enables deep linking - users can bookmark or share URLs that restore the exact table state.

## Migration Guide

To migrate existing tables to the hook system:

1. **Replace manual state management** with `useTableState`
2. **Integrate RTK Query directly** with table state query parameters
3. **Replace Table props** with `useAntTable` output
4. **Remove manual event handlers** (handled by hooks)
5. **Update selection logic** to use hook-provided utilities

### Before (Original DiscoveredAssetsTable):
```tsx
// 100+ lines of state management
const [pageIndex, setPageIndex] = useState(1);
const [pageSize, setPageSize] = useState(25);
const [columnFilters, setColumnFilters] = useState({});
const [sortField, setSortField] = useState();
const [sortOrder, setSortOrder] = useState();
const [selectedRowKeys, setSelectedRowKeys] = useState([]);
// ... complex event handlers
```

### After (With hooks):
```tsx
// Simple, declarative configuration
const tableState = useTableState(/* config */);
const queryResult = useGetDiscoveredAssetsQuery(tableState.queryParams);
const { tableProps, selectionProps, selectedRows } = useAntTable(tableState, {
  enableSelection: true,
  getRowKey: (record) => record.urn,
  dataSource: queryResult.data?.items,
  isLoading: queryResult.isLoading,
});
```

## Benefits

1. **Reduced Boilerplate**: ~80% less state management code
2. **URL Synchronization**: Automatic deep linking support
3. **Consistency**: Standardized table behavior across the app
4. **Type Safety**: Full TypeScript support
5. **Testability**: Hooks can be tested independently
6. **Reusability**: Same hooks work for any table
7. **Performance**: Optimized re-renders and memoization

## Configuration Options

### URL Sync Configuration
```tsx
urlSync: {
  pagination: boolean;  // Sync page/size to URL
  sorting: boolean;     // Sync sort field/order to URL
  filtering: boolean;   // Sync filters to URL
  search: boolean;      // Sync search query to URL
}
```

### Pagination Configuration
```tsx
pagination: {
  defaultPageSize: number;
  pageSizeOptions: number[];
  showSizeChanger: boolean;
}
```

### Sorting Configuration
```tsx
sorting: {
  defaultSortField: string;
  defaultSortOrder: "ascend" | "descend";
  allowMultiSort: boolean;
}
```

### Bulk Actions Configuration
```tsx
bulkActions: {
  getRowKey: (row) => string;
  actions: Array<{
    key: string;
    label: string;
    onClick: (selectedRows) => void | Promise<void>;
    disabled?: (selectedRows) => boolean;
    loading?: boolean;
  }>;
}
```

## Best Practices

1. **Always use `getRowKey`** to ensure proper row identification
2. **Reset selections** when changing tabs or filters
3. **Use URL sync** for user-facing tables where deep linking is valuable
4. **Disable URL sync** for modal/drawer tables where URL changes aren't desired
5. **Memoize column definitions** to prevent unnecessary re-renders
6. **Use bulk actions** for consistent multi-row operations
7. **Provide loading states** for better UX during server operations
