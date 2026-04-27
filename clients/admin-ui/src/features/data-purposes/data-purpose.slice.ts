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
      providesTags: (result) => [
        { type: "DataPurpose" as const, id: "LIST" },
        ...(result?.items ?? []).map((purpose) => ({
          type: "DataPurpose" as const,
          id: purpose.fides_key,
        })),
      ],
    }),
    getDataPurposeByKey: builder.query<DataPurpose, string>({
      query: (fidesKey) => ({
        url: `data-purpose/${fidesKey}`,
      }),
      providesTags: (_result, _error, fidesKey) => [
        { type: "DataPurpose", id: fidesKey },
      ],
    }),
    createDataPurpose: builder.mutation<DataPurpose, Partial<DataPurpose>>({
      query: (body) => ({
        url: `data-purpose`,
        method: "POST",
        body,
      }),
      invalidatesTags: [{ type: "DataPurpose", id: "LIST" }],
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
      invalidatesTags: (_result, _error, { fidesKey }) => [
        { type: "DataPurpose", id: fidesKey },
        { type: "DataPurpose", id: "LIST" },
      ],
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
      invalidatesTags: (_result, _error, { fidesKey }) => [
        { type: "DataPurpose", id: fidesKey },
        { type: "DataPurpose", id: "LIST" },
        "DataConsumer",
      ],
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
        { type: "PurposeSystems" as const, id: "LIST" },
        { type: "PurposeDatasets" as const, id: "LIST" },
        ...(result ?? []).flatMap((summary) => [
          { type: "PurposeSystems" as const, id: summary.fides_key },
          { type: "PurposeDatasets" as const, id: summary.fides_key },
        ]),
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
      providesTags: (_result, _error, fidesKey) => [
        { type: "PurposeSystems", id: fidesKey },
      ],
    }),
    getPurposeAvailableDatasets: builder.query<AvailableDataset[], string>({
      query: (fidesKey) => ({
        url: `plus/data-purpose/${fidesKey}/available-datasets`,
      }),
      providesTags: (_result, _error, fidesKey) => [
        { type: "PurposeDatasets", id: fidesKey },
      ],
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
      invalidatesTags: (_result, _error, { fidesKey }) => [
        { type: "PurposeSystems", id: fidesKey },
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
      invalidatesTags: (_result, _error, { fidesKey }) => [
        { type: "PurposeSystems", id: fidesKey },
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
      invalidatesTags: (_result, _error, { fidesKey }) => [
        { type: "PurposeDatasets", id: fidesKey },
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
      invalidatesTags: (_result, _error, { fidesKey }) => [
        { type: "PurposeDatasets", id: fidesKey },
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
      invalidatesTags: (_result, _error, { fidesKey }) => [
        { type: "DataPurpose", id: fidesKey },
        { type: "PurposeDatasets", id: fidesKey },
      ],
    }),
    markPurposeCategoriesMisclassified: builder.mutation<
      PurposeDatasetAssignment[],
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
      invalidatesTags: (_result, _error, { fidesKey }) => [
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
