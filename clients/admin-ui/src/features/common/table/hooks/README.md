# Table Hooks Documentation

A reusable table system with URL synchronization and Ant Design integration for the Admin UI.

Note: URL sync currently only works for one table per page.

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
import { useTableState, useAntTable } from '~/features/common/table/hooks';

const MyTable = ({ filters }) => {
  // 1. Table state with URL sync
  const tableState = useTableState({
    urlSync: { pagination: true, sorting: true, search: true },
    pagination: { defaultPageSize: 25 },
  });

  // 2. API data
  const queryResult = useGetDataQuery({
    ...tableState.queryParams,
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

  return <Table {...tableProps} columns={columns} rowSelection={selectionProps} />;
};
```

## Recommended Pattern

For complex tables, use a dedicated business logic hook:

### Business Logic Hook

```tsx
// hooks/useMyTable.tsx
export const useMyTable = ({ filters }: Config) => {
  // ...

  // Business actions
  const handleBulkAction = useCallback(async () => {
    // Use antTable.selectedRows, antTable.resetSelections()
  }, [antTable.selectedRows]);

  return {
    ...antTable,
    searchQuery: tableState.searchQuery,
    updateSearch: tableState.updateSearch,
    handleBulkAction,
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
      {selectedRows.length > 0 && (
        <BulkActions onAction={handleBulkAction} />
      )}
      <Table {...tableProps} columns={columns} rowSelection={selectionProps} />
    </>
  );
};
```

## Hook Reference

### `useTableState(config)`

Manages table state with optional URL synchronization.

**Config:**
```tsx
{
  urlSync?: { pagination?, sorting?, filtering?, search? };
  pagination?: { defaultPageSize?, pageSizeOptions? };
  sorting?: { defaultSortField?, defaultSortOrder? };
}
```

**Returns:** State management utilities and `queryParams` for API calls.

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
  bulkActions?: BulkActionsConfig;
}
```

**Returns:** `tableProps`, `selectionProps`, selection utilities.

## Features

- **URL Synchronization**: Deep linking support for pagination, sorting, filtering, and search
- **Selection Management**: Cross-page row selection with bulk actions
- **Type Safety**: Full TypeScript support with generic column keys
- **Performance**: Optimized re-renders and change detection
- **Consistency**: Standardized table behavior across the app

## Configuration Examples

### URL Sync
```tsx
urlSync: {
  pagination: true,    // Sync page/size to URL
  sorting: true,       // Sync sort field/order to URL
  filtering: true,     // Sync filters to URL
  search: true,        // Sync search query to URL
}
```

### Bulk Actions
```tsx
bulkActions: {
  getRowKey: (row) => row.id,
  actions: [{
    key: 'delete',
    label: 'Delete Selected',
    onClick: async (selectedRows) => { /* action */ },
    disabled: (selectedRows) => selectedRows.length === 0,
  }],
}
```

## Migration Guide

To update existing tables:

1. **Replace manual state** with `useTableState`
2. **Use RTK Query** with `tableState.queryParams`
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
const queryResult = useGetDataQuery(tableState.queryParams);
const { tableProps, selectionProps } = useAntTable(tableState, {
  dataSource: queryResult.data?.items,
  isLoading: queryResult.isLoading,
});
```

## Best Practices

1. **Use dedicated hooks** for complex table logic
2. **Memoize column definitions** to prevent re-renders
3. **Enable URL sync** for user-facing tables
4. **Disable URL sync** for modal/drawer tables
5. **Reset selections** when filters change
6. **Provide loading states** for better UX
