# PBAC UI: Data Purposes & Data Consumers Management

**Source:** feat/dataset-data-purposes branch (fides repo)

## Problem Statement

The PBAC backend has full CRUD APIs for data purposes and data consumers, but there's no UI to manage them. Users must use the API directly or the demo script. We need two new management pages under "Core configuration" in the admin nav — one for data purposes, one for data consumers — following Ant Design v5 patterns and the conventions in the Talos frontend guidance.

## Requirements Summary

- **Data Purposes page**: List, create, edit, delete data purposes. Filterable by data use.
- **Data Consumers page**: List, create, edit, delete data consumers. Assign/unassign purposes to consumers. Filterable by type and assigned purpose.
- Both pages gated behind `alphaPurposeBasedAccessControl` feature flag and `requiresPlus`.
- Follow the feature-folder pattern: table with search → add/edit form pages → delete confirmation modal.

## API Contract

### Data Purpose API (`/api/v1/data-purpose`)

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/data-purpose` | `DataPurposeCreate` | `DataPurposeResponse` |
| GET | `/data-purpose` | `?data_use=&page=&size=` | `Page[DataPurposeResponse]` |
| GET | `/data-purpose/{fides_key}` | — | `DataPurposeResponse` |
| PUT | `/data-purpose/{fides_key}` | `DataPurposeUpdate` | `DataPurposeResponse` |
| DELETE | `/data-purpose/{fides_key}` | `?force=true` | 204 |

**Key fields:** `fides_key` (user-provided unique key), `name`, `data_use` (required), `data_subject`, `data_categories[]`, `description`

### Data Consumer API (`/api/v1/data-consumer`)

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/data-consumer` | `DataConsumerCreate` | `DataConsumerResponse` |
| GET | `/data-consumer` | `?type=&purpose_fides_key=&tags=&page=&size=` | `Page[DataConsumerResponse]` |
| GET | `/data-consumer/{id}` | — | `DataConsumerResponse` |
| PUT | `/data-consumer/{id}` | `DataConsumerUpdate` | `DataConsumerResponse` |
| DELETE | `/data-consumer/{id}` | — | 204 |
| PUT | `/data-consumer/{id}/purpose` | `{purpose_fides_keys: [...]}` | `DataConsumerResponse` |

**Key fields:** `id` (UUID, system-generated), `name`, `type` (required), `contact_email`, `tags[]`, `purposes[]` (embedded refs), `purpose_fides_keys[]`

## Frontend Conventions (Talos Guidance)

These conventions **must** be followed — they supersede patterns in older pages like Properties:

- **Ant Design v5 first** — always prefer Ant components over custom code
- **Mutations**: always `.unwrap()` inside `try/catch`, never `isErrorResult()`
- **User feedback**: use Ant `message.success()` / `message.error()`, never `useToast()` (deprecated Chakra)
- **Error messages**: use `getErrorMessage()` from `~/features/common/helpers`
- **Enums**: define TypeScript `enum` for finite backend value sets; keep label/color maps in `constants.ts`
- **Styling**: Ant theme tokens → FidesUI palette → Tailwind (layout only) → SCSS modules. Never arbitrary hex or sizing.
- **Navigation**: `<NextLink href={ROUTE} passHref>` wrapping buttons, never `router.push()` in onClick
- **Pages are thin shells**: fetch data, handle loading/errors, compose the root feature component
- **One component per file**, split early
- **Type safety**: no `any`, no `@ts-expect-error`; use `interface` over `type`; override generated types with `Omit`

## Implementation Approach

Each entity gets a feature folder following the Talos file organization pattern:

1. **Types & constants** — enums, label maps, interfaces
2. **RTK Query API slice** — CRUD endpoints with `providesTags` / `invalidatesTags`
3. **List page** — Ant `<Table>` with search, pagination, filters
4. **Add page** — Formik form with validation
5. **Edit page** — Same form, pre-populated, with delete button
6. **Nav registration** — Under "Core configuration" with feature flag

### File Structure

Per Talos guidance (`features/my-feature/` template):

```
clients/admin-ui/src/
├── features/
│   ├── data-purposes/
│   │   ├── types.d.ts                    # interfaces and type overrides
│   │   ├── constants.ts                  # enums, label maps, display config
│   │   ├── data-purpose.slice.ts         # RTK Query endpoints
│   │   ├── DataPurposesTable.tsx         # root feature component (Ant Table)
│   │   ├── useDataPurposesTable.tsx      # table hook (state, columns, data)
│   │   ├── DataPurposeForm.tsx           # Formik add/edit form
│   │   ├── DeleteDataPurposeModal.tsx    # confirm delete modal
│   │   ├── DataPurposeActionsCell.tsx    # edit/delete cell in table
│   │   └── index.ts                      # barrel export of public API
│   │
│   └── data-consumers/
│       ├── types.d.ts
│       ├── constants.ts
│       ├── data-consumer.slice.ts
│       ├── DataConsumersTable.tsx
│       ├── useDataConsumersTable.tsx
│       ├── DataConsumerForm.tsx           # includes purpose assignment
│       ├── DeleteDataConsumerModal.tsx
│       ├── DataConsumerActionsCell.tsx
│       └── index.ts
│
├── pages/                                # thin routing shells only
│   ├── data-purposes/
│   │   ├── index.tsx                     # list page
│   │   ├── new.tsx                       # add page
│   │   └── [fidesKey].tsx                # edit page
│   │
│   └── data-consumers/
│       ├── index.tsx
│       ├── new.tsx
│       └── [id].tsx
```

Notes on Talos conventions:
- **`types.d.ts`** — interfaces and type aliases (including `Omit`-based overrides of generated types)
- **`constants.ts`** — TypeScript enums, label/color maps, static option arrays
- **`index.ts`** — required barrel file in every feature directory
- **Pages** are thin shells — fetch data, handle loading/error, compose root feature component; no business logic

### Detailed Component Design

#### 1. Types & Constants

**`features/data-consumers/types.d.ts`**:
```ts
import { DataConsumerType } from "./constants";

// Override too-generic generated types
export interface DataConsumerResponse extends Omit<GeneratedDataConsumerResponse, "type"> {
  type: DataConsumerType;
}
```

**`features/data-consumers/constants.ts`**:
```ts
// Enums and label maps per Talos convention

export enum DataConsumerType {
  SERVICE = "service",
  APPLICATION = "application",
  GROUP = "group",
  USER = "user",
}

export const CONSUMER_TYPE_LABELS: Record<DataConsumerType, string> = {
  [DataConsumerType.SERVICE]: "Service",
  [DataConsumerType.APPLICATION]: "Application",
  [DataConsumerType.GROUP]: "Group",
  [DataConsumerType.USER]: "User",
};

export const CONSUMER_TYPE_OPTIONS = Object.entries(CONSUMER_TYPE_LABELS).map(
  ([value, label]) => ({ value, label })
);
```

#### 2. RTK Query API Slices

**`data-purpose.slice.ts`**:
```ts
const dataPurposeApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAllDataPurposes: builder.query<Page_DataPurposeResponse_, DataPurposeParams>({
      query: (params) => ({ url: "plus/data-purpose", params }),
      providesTags: ["DataPurpose"],
    }),
    getDataPurposeByKey: builder.query<DataPurposeResponse, string>({
      query: (fidesKey) => ({ url: `plus/data-purpose/${fidesKey}` }),
      providesTags: ["DataPurpose"],
    }),
    createDataPurpose: builder.mutation<DataPurposeResponse, DataPurposeCreate>({
      query: (body) => ({ url: "plus/data-purpose", method: "POST", body }),
      invalidatesTags: ["DataPurpose"],
    }),
    updateDataPurpose: builder.mutation<
      DataPurposeResponse,
      { fidesKey: string } & DataPurposeUpdate
    >({
      query: ({ fidesKey, ...body }) => ({
        url: `plus/data-purpose/${fidesKey}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: ["DataPurpose"],
    }),
    deleteDataPurpose: builder.mutation<void, { fidesKey: string; force?: boolean }>({
      query: ({ fidesKey, force }) => ({
        url: `plus/data-purpose/${fidesKey}`,
        method: "DELETE",
        params: force ? { force: true } : undefined,
      }),
      invalidatesTags: ["DataPurpose", "DataConsumer"],
    }),
  }),
});

export const {
  useGetAllDataPurposesQuery,
  useGetDataPurposeByKeyQuery,
  useCreateDataPurposeMutation,
  useUpdateDataPurposeMutation,
  useDeleteDataPurposeMutation,
} = dataPurposeApi;
```

**`data-consumer.slice.ts`** — same pattern plus:
```ts
assignConsumerPurposes: builder.mutation<
  DataConsumerResponse,
  { id: string; purposeFidesKeys: string[] }
>({
  query: ({ id, purposeFidesKeys }) => ({
    url: `plus/data-consumer/${id}/purpose`,
    method: "PUT",
    body: { purpose_fides_keys: purposeFidesKeys },
  }),
  invalidatesTags: ["DataConsumer"],
}),
```

#### 3. Page Components (Thin Shells)

**`pages/data-purposes/index.tsx`** (list):
```tsx
const DataPurposesPage: NextPage = () => {
  return (
    <Layout title="Data purposes">
      <PageHeader heading="Data purposes" />
      <DataPurposesTable />
    </Layout>
  );
};
```

**`pages/data-purposes/new.tsx`** (add):
```tsx
const AddDataPurposePage: NextPage = () => {
  const [createDataPurpose] = useCreateDataPurposeMutation();
  const router = useRouter();

  const handleSubmit = async (values: DataPurposeCreate) => {
    try {
      await createDataPurpose(values).unwrap();
      message.success(`Data purpose "${values.name}" created`);
      router.push(DATA_PURPOSES_ROUTE);
    } catch (error) {
      message.error(getErrorMessage(error));
    }
  };

  return (
    <Layout title="Add data purpose">
      <PageHeader
        heading="Data purposes"
        breadcrumbItems={[
          { title: "All data purposes", href: DATA_PURPOSES_ROUTE },
          { title: "Add data purpose" },
        ]}
      />
      <DataPurposeForm onSubmit={handleSubmit} />
    </Layout>
  );
};
```

**`pages/data-purposes/[fidesKey].tsx`** (edit):
```tsx
const EditDataPurposePage: NextPage = () => {
  const router = useRouter();
  const { fidesKey } = router.query;
  const { data: purpose, isLoading, error } = useGetDataPurposeByKeyQuery(
    fidesKey as string,
    { skip: !fidesKey }
  );
  const [updateDataPurpose] = useUpdateDataPurposeMutation();

  if (error) {
    return <ErrorPage error={error} />;
  }

  const handleSubmit = async (values: DataPurposeUpdate) => {
    try {
      await updateDataPurpose({ fidesKey: fidesKey as string, ...values }).unwrap();
      message.success(`Data purpose "${values.name}" updated`);
      router.push(DATA_PURPOSES_ROUTE);
    } catch (error) {
      message.error(getErrorMessage(error));
    }
  };

  return (
    <Layout title="Edit data purpose">
      <PageHeader
        heading="Data purposes"
        breadcrumbItems={[
          { title: "All data purposes", href: DATA_PURPOSES_ROUTE },
          { title: purpose?.name ?? "Edit" },
        ]}
      />
      {isLoading ? <Spin /> : <DataPurposeForm purpose={purpose} onSubmit={handleSubmit} />}
    </Layout>
  );
};
```

#### 4. Table Hook

**`useDataPurposesTable.tsx`**:
```tsx
const useDataPurposesTable = () => {
  const tableState = useTableState({
    pagination: { defaultPageSize: 25, pageSizeOptions: [25, 50, 100] },
    search: { defaultSearchQuery: "" },
  });

  const { pageIndex, pageSize, searchQuery, updateSearch } = tableState;
  const { data, error, isLoading, isFetching } = useGetAllDataPurposesQuery({
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
  });

  const columns: ColumnsType<DataPurposeResponse> = useMemo(
    () => [
      {
        title: "Name",
        dataIndex: "name",
        render: (_, record) => (
          <NextLink href={`${DATA_PURPOSES_ROUTE}/${record.fides_key}`} passHref>
            {record.name}
          </NextLink>
        ),
      },
      { title: "Key", dataIndex: "fides_key" },
      {
        title: "Data use",
        dataIndex: "data_use",
        render: (value: string) => <Tag>{value}</Tag>,
      },
      {
        title: "Categories",
        dataIndex: "data_categories",
        render: (categories: string[]) =>
          categories.length > 0 ? (
            <Space wrap>{categories.map((c) => <Tag key={c}>{c}</Tag>)}</Space>
          ) : (
            "N/A"
          ),
      },
      {
        title: "Actions",
        render: (_, record) => <DataPurposeActionsCell purpose={record} />,
      },
    ],
    []
  );

  const tableProps = useAntTable({ tableState, data });

  return { tableProps, columns, error, isLoading, isFetching, searchQuery, updateSearch };
};
```

#### 5. Delete Modal

**`DeleteDataPurposeModal.tsx`**:
```tsx
interface DeleteDataPurposeModalProps {
  purpose: DataPurposeResponse;
}

const DeleteDataPurposeModal = ({ purpose }: DeleteDataPurposeModalProps) => {
  const [modal, contextHolder] = Modal.useModal();
  const [deleteDataPurpose] = useDeleteDataPurposeMutation();
  const router = useRouter();

  const handleDelete = () => {
    modal.confirm({
      title: "Delete data purpose?",
      content: `This will permanently delete "${purpose.name}". This action cannot be undone.`,
      okText: "Delete",
      okButtonProps: { danger: true },
      centered: true,
      onOk: async () => {
        try {
          await deleteDataPurpose({ fidesKey: purpose.fides_key, force: true }).unwrap();
          message.success(`Data purpose "${purpose.name}" deleted`);
          router.push(DATA_PURPOSES_ROUTE);
        } catch (error) {
          message.error(getErrorMessage(error));
        }
      },
    });
  };

  return (
    <>
      {contextHolder}
      <Button danger onClick={handleDelete}>
        Delete
      </Button>
    </>
  );
};
```

#### 6. Data Purpose Form

Fields:
- **Name** (required, Ant `<Input>`)
- **Key** (required, auto-generated from name if blank, disabled on edit, Ant `<Input>`)
- **Data use** (required, Ant `<Select>` — populated from taxonomy data uses)
- **Data subject** (optional, Ant `<Select>`)
- **Data categories** (Ant `<Select mode="multiple">`)
- **Description** (optional, Ant `<Input.TextArea>`)
- **Legal basis** (optional, Ant `<Select>`)
- **Retention period** (optional, Ant `<Input>`)

#### 7. Data Consumer Form

Fields:
- **Name** (required, Ant `<Input>`)
- **Type** (required, Ant `<Select>` — options from `CONSUMER_TYPE_OPTIONS` constant)
- **Contact email** (optional, Ant `<Input>`)
- **Description** (optional, Ant `<Input.TextArea>`)
- **Tags** (Ant `<Select mode="tags">`)
- **Assigned purposes** (Ant `<Select mode="multiple">` — populated from `useGetAllDataPurposesQuery`; on save calls `assignConsumerPurposes` mutation with full list)
- **External ID** (optional, Ant `<Input>`, advanced section)
- **Contact Slack channel** (optional, Ant `<Input>`, advanced section)

On the edit form, if `purpose_fides_keys` changed from the loaded value, the submit handler calls `assignConsumerPurposes` after `updateDataConsumer`.

#### 8. Data Consumers Table

| Column | Source | Notes |
|--------|--------|-------|
| Name | `name` | `<NextLink>` → `/data-consumers/{id}` |
| Type | `type` | `<Tag>` with label from `CONSUMER_TYPE_LABELS` |
| Contact | `contact_email` | Text, show "N/A" if empty |
| Purposes | `purposes` | `<Space wrap>` of `<Tag>` showing purpose names |
| Tags | `tags` | `<Space wrap>` of `<Tag>` |
| Actions | — | Edit / Delete |

- Search filters by name
- Optional `<Select>` filter by `type` (uses `CONSUMER_TYPE_OPTIONS`)
- Optional `<Select>` filter by assigned purpose (fetches purposes for options)

### 9. Navigation & Routing

**Route constants** (`routes.ts`):
```ts
export const DATA_PURPOSES_ROUTE = "/data-purposes";
export const DATA_PURPOSES_NEW_ROUTE = "/data-purposes/new";
export const DATA_PURPOSES_EDIT_ROUTE = "/data-purposes/[fidesKey]";

export const DATA_CONSUMERS_ROUTE = "/data-consumers";
export const DATA_CONSUMERS_NEW_ROUTE = "/data-consumers/new";
export const DATA_CONSUMERS_EDIT_ROUTE = "/data-consumers/[id]";
```

**Nav config** — add to "Core configuration" group:
```tsx
{
  title: "Data purposes",
  path: routes.DATA_PURPOSES_ROUTE,
  requiresPlus: true,
  requiresFlag: "alphaPurposeBasedAccessControl",
  scopes: [ScopeRegistryEnum.DATA_PURPOSE_READ],
},
{
  title: "Data consumers",
  path: routes.DATA_CONSUMERS_ROUTE,
  requiresPlus: true,
  requiresFlag: "alphaPurposeBasedAccessControl",
  scopes: [ScopeRegistryEnum.DATA_CONSUMER_READ],
},
```

### 10. Query Log Config Tab (Integration Detail Page)

Query log configs sit on top of an existing `ConnectionConfig`, following the same two-step pattern as discovery monitors. The UI adds a **"Query logging" tab** to the integration detail page.

#### Reference pattern

The "Data discovery" tab (`MonitorConfigTab`) is the direct reference:
- Tab rendered conditionally via `useFeatureBasedTabs` when `IntegrationFeature.DATA_DISCOVERY` is enabled
- Tab lists existing configs in a table, with an "Add" button opening a modal
- Modal contains a form for create/edit; mutations invalidate cache tags to refresh the table

#### Backend integration feature

Add `QUERY_LOGGING = "QUERY_LOGGING"` to the `IntegrationFeature` enum (backend, in fides). BigQuery and `test_datastore` connection types include this feature. The frontend enum in `types/api/models/IntegrationFeature.ts` is auto-generated.

#### Tab registration

In `useFeatureBasedTabs.tsx`, add after the DATA_DISCOVERY block:

```tsx
if (enabledFeatures?.includes(IntegrationFeature.QUERY_LOGGING)) {
  tabItems.push({
    label: "Query logging",
    key: "query-logging",
    children: (
      <QueryLogConfigTab
        integration={connection!}
        integrationOption={integrationOption}
      />
    ),
  });
}
```

#### File structure

```
features/integrations/configure-query-log/
  types.d.ts                        # QueryLogConfig interfaces
  constants.ts                      # poll interval options, status labels
  query-log-config.slice.ts         # RTK Query endpoints
  QueryLogConfigTab.tsx             # tab root: description + add button + table + modal
  useQueryLogConfigTable.tsx         # table hook (columns, data, pagination)
  ConfigureQueryLogModal.tsx         # create/edit modal with form
  QueryLogConfigActionsCell.tsx      # edit / delete / test / poll actions
```

#### RTK Query slice (`query-log-config.slice.ts`)

```ts
const queryLogConfigApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getQueryLogConfigs: builder.query<Page_QueryLogConfigResponse_, QueryLogConfigParams>({
      query: (params) => ({ url: "plus/query-log-config", params }),
      providesTags: ["QueryLogConfig"],
    }),
    getQueryLogConfigByKey: builder.query<QueryLogConfigResponse, string>({
      query: (configKey) => ({ url: `plus/query-log-config/${configKey}` }),
      providesTags: ["QueryLogConfig"],
    }),
    createQueryLogConfig: builder.mutation<QueryLogConfigResponse, QueryLogConfigCreate>({
      query: (body) => ({ url: "plus/query-log-config", method: "POST", body }),
      invalidatesTags: ["QueryLogConfig"],
    }),
    updateQueryLogConfig: builder.mutation<
      QueryLogConfigResponse,
      { configKey: string } & QueryLogConfigUpdate
    >({
      query: ({ configKey, ...body }) => ({
        url: `plus/query-log-config/${configKey}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: ["QueryLogConfig"],
    }),
    deleteQueryLogConfig: builder.mutation<void, string>({
      query: (configKey) => ({
        url: `plus/query-log-config/${configKey}`,
        method: "DELETE",
      }),
      invalidatesTags: ["QueryLogConfig"],
    }),
    testQueryLogConnection: builder.mutation<TestConnectionResponse, string>({
      query: (configKey) => ({
        url: `plus/query-log-config/${configKey}/test`,
        method: "POST",
      }),
    }),
    triggerQueryLogPoll: builder.mutation<PollResponse, string>({
      query: (configKey) => ({
        url: `plus/query-log-config/${configKey}/poll`,
        method: "POST",
      }),
    }),
  }),
});
```

#### Table columns

| Column | Source | Notes |
|--------|--------|-------|
| Name | `name` | Text |
| Key | `key` | Monospace |
| Status | `enabled` | Ant `<Switch>` toggle (calls update mutation) |
| Poll interval | `poll_interval_seconds` | Human-readable from `POLL_INTERVAL_LABELS` |
| Last poll | `watermark` | Formatted timestamp or "Never" |
| Actions | — | Test / Poll / Edit / Delete |

#### Modal form fields

- **Name** (required, Ant `<Input>`)
- **Key** (auto-generated from name, disabled on edit, Ant `<Input>`)
- **Enabled** (Ant `<Switch>`, default true)
- **Poll interval** (Ant `<Select>` — options: 1min, 5min, 15min, 1hr, 6hr, 24hr)

The `connection_config_key` is set automatically from the parent integration — the user doesn't select it.

#### Actions cell

- **Test**: calls `testQueryLogConnection` mutation, shows `message.success`/`message.error`
- **Poll now**: calls `triggerQueryLogPoll` mutation, shows entries processed count
- **Edit**: opens modal pre-populated with config
- **Delete**: `Modal.confirm()` → calls `deleteQueryLogConfig`

### 11. Scope Registration

Add to `ScopeRegistryEnum` (frontend):
```ts
DATA_PURPOSE_CREATE = "data_purpose:create",
DATA_PURPOSE_READ = "data_purpose:read",
DATA_PURPOSE_UPDATE = "data_purpose:update",
DATA_PURPOSE_DELETE = "data_purpose:delete",
DATA_CONSUMER_CREATE = "data_consumer:create",
DATA_CONSUMER_READ = "data_consumer:read",
DATA_CONSUMER_UPDATE = "data_consumer:update",
DATA_CONSUMER_DELETE = "data_consumer:delete",
QUERY_LOG_SOURCE_CREATE = "query_log_source:create",
QUERY_LOG_SOURCE_READ = "query_log_source:read",
QUERY_LOG_SOURCE_UPDATE = "query_log_source:update",
QUERY_LOG_SOURCE_DELETE = "query_log_source:delete",
```

### 12. Cache Tag Registration

Add `"DataPurpose"`, `"DataConsumer"`, and `"QueryLogConfig"` to the `tagTypes` array in `api.slice.ts`.

## Repository Split

| Component | Repository | Rationale |
|-----------|------------|-----------|
| Pages, features, routes, RTK slices | Fides OSS | Frontend lives in fides |
| Scope enum additions | Fides OSS | `ScopeRegistryEnum` is in fides |
| `IntegrationFeature.QUERY_LOGGING` enum value | Fides OSS | Enum lives in fides models |
| BigQuery/test_datastore feature flag registration | Fidesplus | Connection type features configured in fidesplus |
| API endpoints (already exist) | Fidesplus | Backend already built |

## Story Breakdown

| # | Story | Repo | Type | Estimate | Dependencies |
|---|-------|------|------|----------|--------------|
| 1 | Add scope enums + cache tags + `IntegrationFeature.QUERY_LOGGING` | Fides | Task | S | - |
| 2 | Add types, constants, and RTK Query slices for data purposes and data consumers | Fides | Story | S | #1 |
| 3 | Data purposes list page (table + search + pagination) | Fides | Story | M | #2 |
| 4 | Data purposes add/edit form pages + delete modal | Fides | Story | M | #2, #3 |
| 5 | Data consumers list page (table + search + filters) | Fides | Story | M | #2 |
| 6 | Data consumers add/edit form pages (including purpose assignment) + delete modal | Fides | Story | M | #2, #4, #5 |
| 7 | Nav registration + route constants for data purposes and data consumers | Fides | Task | S | #3, #5 |
| 8 | Query log config RTK slice + types + constants | Fides | Story | S | #1 |
| 9 | Query log config tab (table + modal form + actions) in integration detail | Fides | Story | M | #8 |
| 10 | Register `QUERY_LOGGING` feature for BigQuery and test_datastore connection types | Fidesplus | Task | S | #1 |

## Testing Strategy

- **Unit tests**: Table hooks return correct columns, form validation works, constants map all enum values
- **Component tests**: Tables render with mock data, forms submit correct payloads, delete modals call mutations
- **Integration tests (query log tab)**: Tab appears only when `QUERY_LOGGING` feature enabled; create/edit/delete/test/poll actions work
- **E2E (Cardea/Playwright)**: Create a purpose → create a consumer → assign purpose → verify in table → delete; create integration → add query log config → test connection → poll

## Out of Scope

- Data producers management UI (lower priority, fewer fields)
- Access control dashboard (already has its own routes)
- Inline purpose assignment from the consumer table (v2 — for now, assignment is on the edit form)
- Query log ingest endpoint UI (push-based, no UI needed)
