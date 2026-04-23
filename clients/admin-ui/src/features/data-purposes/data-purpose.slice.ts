import { baseApi } from "~/features/common/api.slice";

interface DataPurposeParams {
  page?: number;
  size?: number;
  search?: string;
  data_use?: string;
}

export interface DataPurpose {
  id?: string;
  fides_key: string;
  name: string;
  description?: string | null;
  data_use: string;
  data_subject?: string | null;
  data_categories?: string[];
  legal_basis_for_processing?: string | null;
  flexible_legal_basis_for_processing?: boolean;
  special_category_legal_basis?: string | null;
  impact_assessment_location?: string | null;
  retention_period?: string | null;
  features?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface DataPurposePage {
  items: DataPurpose[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

/**
 * UI-extension response types for endpoints that don't yet exist on the
 * backend. MSW serves them in dev (see src/mocks/data-purposes/). Once
 * fidesplus ships real endpoints, these move into generated types/api.
 */
export interface PurposeCoverage {
  fides_key: string;
  systems: { assigned: number; total: number };
  datasets: { assigned: number; total: number };
  tables: { assigned: number; total: number };
  fields: { assigned: number; total: number };
  detected_data_categories: string[];
}

export interface PurposeSystemAssignment {
  system_id: string;
  system_name: string;
  system_type: string;
  assigned: boolean;
  consumer_category?: "system" | "group";
}

export interface PurposeDatasetAssignment {
  dataset_fides_key: string;
  dataset_name: string;
  system_name: string;
  collection_count: number;
  data_categories: string[];
  updated_at: string;
  steward: string;
}

export interface AvailableSystem {
  system_id: string;
  system_name: string;
  system_type: string;
}

export interface AvailableDataset {
  dataset_fides_key: string;
  dataset_name: string;
  system_name: string;
}

/**
 * Per-purpose enrichment used by the list grid and network view. Served
 * in a single batched call to avoid N+1 requests across cards.
 */
export interface PurposeSummary {
  fides_key: string;
  system_count: number;
  dataset_count: number;
  detected_data_categories: string[];
  systems: PurposeSystemAssignment[];
  datasets: PurposeDatasetAssignment[];
}

export const dataPurposesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAllDataPurposes: builder.query<DataPurposePage, DataPurposeParams>({
      query: (params) => ({
        url: `data-purpose`,
        params,
      }),
      providesTags: ["DataPurpose"],
    }),
    getDataPurposeByKey: builder.query<DataPurpose, string>({
      query: (fidesKey) => ({
        url: `data-purpose/${fidesKey}`,
      }),
      providesTags: ["DataPurpose"],
    }),
    createDataPurpose: builder.mutation<DataPurpose, Partial<DataPurpose>>({
      query: (body) => ({
        url: `data-purpose`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["DataPurpose"],
    }),
    updateDataPurpose: builder.mutation<
      DataPurpose,
      { fidesKey: string } & Partial<DataPurpose>
    >({
      query: ({ fidesKey, ...body }) => ({
        url: `data-purpose/${fidesKey}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: ["DataPurpose"],
    }),
    deleteDataPurpose: builder.mutation<
      void,
      { fidesKey: string; force?: boolean }
    >({
      query: ({ fidesKey, force }) => ({
        url: `data-purpose/${fidesKey}`,
        method: "DELETE",
        params: force ? { force: true } : undefined,
      }),
      invalidatesTags: ["DataPurpose", "DataConsumer"],
    }),

    // Plus-only, MSW-mocked for now.
    // TODO: replace with real endpoints once fidesplus ships them.
    getPurposeSummaries: builder.query<PurposeSummary[], void>({
      query: () => ({
        url: `plus/data-purpose/summaries`,
      }),
      // Provide both list-level and per-id tags so scoped invalidations from
      // per-purpose mutations (e.g. `{type: "PurposeSystems", id}`) flow
      // through to the list grid's batched summary.
      providesTags: (result) => [
        { type: "PurposeCoverage" as const, id: "LIST" },
        { type: "PurposeSystems" as const, id: "LIST" },
        { type: "PurposeDatasets" as const, id: "LIST" },
        ...(result ?? []).flatMap((s) => [
          { type: "PurposeCoverage" as const, id: s.fides_key },
          { type: "PurposeSystems" as const, id: s.fides_key },
          { type: "PurposeDatasets" as const, id: s.fides_key },
        ]),
      ],
    }),
    getPurposeCoverage: builder.query<PurposeCoverage, string>({
      query: (fidesKey) => ({
        url: `plus/data-purpose/${fidesKey}/coverage`,
      }),
      providesTags: (_result, _error, fidesKey) => [
        { type: "PurposeCoverage", id: fidesKey },
      ],
    }),
    getPurposeSystems: builder.query<PurposeSystemAssignment[], string>({
      query: (fidesKey) => ({
        url: `plus/data-purpose/${fidesKey}/systems`,
      }),
      providesTags: (_result, _error, fidesKey) => [
        { type: "PurposeSystems", id: fidesKey },
      ],
    }),
    getPurposeDatasets: builder.query<PurposeDatasetAssignment[], string>({
      query: (fidesKey) => ({
        url: `plus/data-purpose/${fidesKey}/datasets`,
      }),
      providesTags: (_result, _error, fidesKey) => [
        { type: "PurposeDatasets", id: fidesKey },
      ],
    }),
    getPurposeAvailableSystems: builder.query<AvailableSystem[], string>({
      query: (fidesKey) => ({
        url: `plus/data-purpose/${fidesKey}/available-systems`,
      }),
    }),
    getPurposeAvailableDatasets: builder.query<AvailableDataset[], string>({
      query: (fidesKey) => ({
        url: `plus/data-purpose/${fidesKey}/available-datasets`,
      }),
    }),
    assignSystemsToPurpose: builder.mutation<
      PurposeSystemAssignment[],
      { fidesKey: string; systemIds: string[] }
    >({
      query: ({ fidesKey, systemIds }) => ({
        url: `plus/data-purpose/${fidesKey}/systems`,
        method: "PUT",
        body: { system_ids: systemIds },
      }),
      invalidatesTags: (_r, _e, { fidesKey }) => [
        { type: "PurposeSystems", id: fidesKey },
        { type: "PurposeCoverage", id: fidesKey },
      ],
    }),
    removeSystemsFromPurpose: builder.mutation<
      PurposeSystemAssignment[],
      { fidesKey: string; systemIds: string[] }
    >({
      query: ({ fidesKey, systemIds }) => ({
        url: `plus/data-purpose/${fidesKey}/systems`,
        method: "DELETE",
        body: { system_ids: systemIds },
      }),
      invalidatesTags: (_r, _e, { fidesKey }) => [
        { type: "PurposeSystems", id: fidesKey },
        { type: "PurposeCoverage", id: fidesKey },
      ],
    }),
    addDatasetsToPurpose: builder.mutation<
      PurposeDatasetAssignment[],
      { fidesKey: string; datasetFidesKeys: string[] }
    >({
      query: ({ fidesKey, datasetFidesKeys }) => ({
        url: `plus/data-purpose/${fidesKey}/datasets`,
        method: "PUT",
        body: { dataset_fides_keys: datasetFidesKeys },
      }),
      invalidatesTags: (_r, _e, { fidesKey }) => [
        { type: "PurposeDatasets", id: fidesKey },
        { type: "PurposeCoverage", id: fidesKey },
      ],
    }),
    removeDatasetsFromPurpose: builder.mutation<
      PurposeDatasetAssignment[],
      { fidesKey: string; datasetFidesKeys: string[] }
    >({
      query: ({ fidesKey, datasetFidesKeys }) => ({
        url: `plus/data-purpose/${fidesKey}/datasets`,
        method: "DELETE",
        body: { dataset_fides_keys: datasetFidesKeys },
      }),
      invalidatesTags: (_r, _e, { fidesKey }) => [
        { type: "PurposeDatasets", id: fidesKey },
        { type: "PurposeCoverage", id: fidesKey },
      ],
    }),
    acceptPurposeCategories: builder.mutation<
      DataPurpose,
      { fidesKey: string; categories: string[] }
    >({
      query: ({ fidesKey, categories }) => ({
        url: `plus/data-purpose/${fidesKey}/categories/accept`,
        method: "POST",
        body: { categories },
      }),
      invalidatesTags: (_r, _e, { fidesKey }) => [
        "DataPurpose",
        { type: "PurposeCoverage", id: fidesKey },
      ],
    }),
    markPurposeCategoriesMisclassified: builder.mutation<
      { coverage: PurposeCoverage; datasets: PurposeDatasetAssignment[] },
      { fidesKey: string; categories: string[]; datasetFidesKeys?: string[] }
    >({
      query: ({ fidesKey, categories, datasetFidesKeys }) => ({
        url: `plus/data-purpose/${fidesKey}/categories/misclassified`,
        method: "POST",
        body: {
          categories,
          dataset_fides_keys: datasetFidesKeys,
        },
      }),
      invalidatesTags: (_r, _e, { fidesKey }) => [
        { type: "PurposeCoverage", id: fidesKey },
        { type: "PurposeDatasets", id: fidesKey },
      ],
    }),
  }),
});

export const {
  useGetAllDataPurposesQuery,
  useGetDataPurposeByKeyQuery,
  useCreateDataPurposeMutation,
  useUpdateDataPurposeMutation,
  useDeleteDataPurposeMutation,
  useGetPurposeSummariesQuery,
  useGetPurposeCoverageQuery,
  useGetPurposeSystemsQuery,
  useGetPurposeDatasetsQuery,
  useGetPurposeAvailableSystemsQuery,
  useGetPurposeAvailableDatasetsQuery,
  useAssignSystemsToPurposeMutation,
  useRemoveSystemsFromPurposeMutation,
  useAddDatasetsToPurposeMutation,
  useRemoveDatasetsFromPurposeMutation,
  useAcceptPurposeCategoriesMutation,
  useMarkPurposeCategoriesMisclassifiedMutation,
} = dataPurposesApi;
