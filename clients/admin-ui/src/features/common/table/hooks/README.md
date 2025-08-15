# Table Hooks Documentation

A reusable, standardized table system with always-on URL synchronization and Ant Design integration for the Admin UI.

> **Note:** URL sync currently only works for one table per page.

## Architecture

```
useTableState (State + URL Sync) + RTK Query
    ↓
useAntTable (Ant Design Integration)
    ↓
Table Component
```

## Quick Start

### Basic Usage

```tsx
import { useTableState, useAntTable } from "~/features/common/table/hooks";

const MyTable = ({ filters }) => {
  // 1. Table state with URL sync (pagination, sorting, filtering, search)
  const tableState = useTableState({
    pagination: { defaultPageSize: 10, pageSizeOptions: [10, 50] },
    sorting: { defaultSortKey: "name", defaultSortOrder: "ascend" },
    search: { defaultSearchQuery: "gtm" },
  });

  // 2. API data
  const queryResult = useGetDataQuery({
    ...tableState.state, // Use .state for all query params
    ...filters,
  });

  // 3. Ant Design integration
  const { tableProps, selectionProps } = useAntTable(tableState, {
    enableSelection: true,
    getRowKey: (record) => record.id,
    dataSource: queryResult.data?.items,
    totalRows: queryResult.data?.total,
    isLoading: queryResult.isLoading,
  });

  return (
    <Table {...tableProps} columns={columns} rowSelection={selectionProps} />
  );
};
```

## Recommended Pattern

For complex tables, use a dedicated business logic hook to encapsulate all table logic, actions, and column definitions.

### Business Logic Hook

```tsx
// hooks/useMyTable.tsx
export const useMyTable = ({ filters }: Config) => {
  const tableState = useTableState({
    // ...config
  });
  const antTable = useAntTable(tableState, {
    // ...config
  });

  // Business actions
  const handleBulkAction = useCallback(async () => {
    // Use antTable.selectedRows, antTable.resetSelections()
  }, [antTable.selectedRows]);

  return {
    ...antTable,
    searchQuery: tableState.searchQuery,
    updateSearch: tableState.updateSearch,
    handleBulkAction,
    columns: useMemo(() => [...], []), // Memoize columns
  };
};
```

### Component

```tsx
// MyTable.tsx
export const MyTable = ({ filters }: Props) => {
  const {
    columns,
    tableProps,
    selectionProps,
    selectedRows,
    searchQuery,
    updateSearch,
    handleBulkAction,
  } = useMyTable({ filters });

  return (
    <>
      <SearchInput value={searchQuery} onChange={updateSearch} />
      {selectedRows.length > 0 && <BulkActions onAction={handleBulkAction} />}
      <Table {...tableProps} columns={columns} rowSelection={selectionProps} />
    </>
  );
};
```

## Hook Reference

### `useTableState(config)`

Manages table state (pagination, sorting, filtering, search) with always-on URL synchronization.

**Config:**

```tsx
{
  pagination?: { defaultPageSize?, pageSizeOptions? };
  sorting?: { defaultSortKey?, defaultSortOrder?, validColumns? };
  search?: { defaultSearchQuery? };
  onStateChange?: (state) => void;
}
```

**Returns:** State management utilities and `.state` for API calls.

### `useAntTable(tableState, config)`

Integrates table state with Ant Design Table components.

**Config:**

```tsx
{
  enableSelection?: boolean;
  getRowKey?: (record) => string;
  dataSource?: any[];
  totalRows?: number;
  isLoading?: boolean;
  isFetching?: boolean;
  bulkActions?: BulkActionsConfig;
  currentPage?: number;
  pageSize?: number;
  customTableProps?: Partial<TableProps<TData>>;
}
```

**Returns:** `tableProps`, `selectionProps`, selection utilities, and helpers for bulk actions and loading state.

### Standalone Hooks

- `usePagination(config)`: Manage pagination state with URL sync.
- `useSorting(config)`: Manage sorting state with URL sync.
- `useSearch(config)`: Manage search state with URL sync.

## Features

- **URL Synchronization**: Deep linking for pagination, sorting, filtering, and search (always enabled)
- **Selection Management**: Cross-page row selection with bulk actions
- **Bulk Actions**: Configurable, with helpers for disabling/loading state
- **Type Safety**: Full TypeScript support with generic column keys
- **Performance**: Optimized re-renders and change detection
- **Consistency**: Standardized table behavior across the app
- **Accessibility**: Designed for keyboard and screen reader accessibility (see below)

## Configuration Examples

### Table State Config

```tsx
const tableState = useTableState({
  pagination: { defaultPageSize: 25, pageSizeOptions: [25, 50, 100] },
  sorting: {
    validColumns: ["name", "status", "created_at"],
    defaultSortKey: "name",
    defaultSortOrder: "descend",
  },
  search: { defaultSearchQuery: "" },
  onStateChange: (state) => handleStateChange(state),
});
```

### Bulk Actions

```tsx
bulkActions: {
  getRowKey: (row) => row.id,
  actions: [
    {
      key: "delete",
      label: "Delete selected",
      onClick: async (selectedRows) => { /* action */ },
      disabled: (selectedRows) => selectedRows.length === 0,
      loading: false,
    },
  ],
}
```

## Migration Guide

To update existing tables:

1. **Replace manual state** with `useTableState`
2. **Use RTK Query** with `tableState.state` for query params
3. **Replace Table props** with `useAntTable` results
4. **Move business logic** to dedicated hooks

### Before

```tsx
const [pageIndex, setPageIndex] = useState(1);
const [pageSize, setPageSize] = useState(25);
const [selectedRows, setSelectedRows] = useState([]);
// ... 100+ lines of state management
```

### After

```tsx
const tableState = useTableState(config);
const queryResult = useGetDataQuery(tableState.state);
const { tableProps, selectionProps } = useAntTable(tableState, {
  dataSource: queryResult.data?.items,
  isLoading: queryResult.isLoading,
});
```

## Best Practices

1. **Use dedicated hooks** for complex table logic
2. **Memoize column definitions** to prevent re-renders
3. **Reset selections** when filters change
4. **Use type-safe column keys** for sorting and filtering
5. **Test with keyboard and screen readers** for accessibility

## Accessibility

- All interactive elements (bulk actions, pagination, search) should be reachable by keyboard.
- Use semantic HTML and ARIA attributes for custom cell renderers.
- Use descriptive labels for all action buttons, especially if they are icon only.

---

For more advanced usage, see the source code and tests for each hook. If you add new features, update this documentation accordingly.
