import { baseApi } from "~/features/common/api.slice";
import type { DataPurposeResponse } from "~/types/api/models/DataPurposeResponse";

interface DataPurposeParams {
  search?: string;
  data_use?: string;
  consumer?: string;
  category?: string;
  status?: string;
}

export type DataPurpose = DataPurposeResponse;

export interface DataPurposeFilterOption {
  value: string;
  label: string;
}

export interface DataPurposeFilterOptions {
  consumers: DataPurposeFilterOption[];
  data_uses: DataPurposeFilterOption[];
  categories: DataPurposeFilterOption[];
  statuses: DataPurposeFilterOption[];
}

export interface DataPurposeListResponse {
  items: DataPurpose[];
  total: number;
  filter_options: DataPurposeFilterOptions;
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

export interface PurposeFeatureOption {
  value: string;
  label: string;
}

export interface PurposeOverviewResponse {
  purpose: DataPurpose;
  systems: PurposeSystemAssignment[];
  datasets: PurposeDatasetAssignment[];
  available_systems: AvailableSystem[];
  available_datasets: AvailableDataset[];
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
    getAllDataPurposes: builder.query<
      DataPurposeListResponse,
      DataPurposeParams
    >({
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
        { type: "PurposeOverview", id: fidesKey },
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
      providesTags: (result) => [
        { type: "DataPurpose" as const, id: "LIST" },
        ...(result ?? []).map((summary) => ({
          type: "DataPurpose" as const,
          id: summary.fides_key,
        })),
      ],
    }),
    getPurposeOverview: builder.query<PurposeOverviewResponse, string>({
      query: (fidesKey) => ({
        url: `plus/data-purpose/${fidesKey}/overview`,
      }),
      providesTags: (_result, _error, fidesKey) => [
        { type: "PurposeOverview", id: fidesKey },
      ],
    }),
    getPurposeFeatureOptions: builder.query<PurposeFeatureOption[], void>({
      query: () => ({
        url: `plus/data-purpose/feature-options`,
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
      invalidatesTags: (_result, _error, { fidesKey }) => [
        { type: "PurposeOverview", id: fidesKey },
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
        { type: "PurposeOverview", id: fidesKey },
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
        { type: "PurposeOverview", id: fidesKey },
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
        { type: "PurposeOverview", id: fidesKey },
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
        { type: "PurposeOverview", id: fidesKey },
        { type: "DataPurpose", id: "LIST" },
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
        { type: "PurposeOverview", id: fidesKey },
        { type: "DataPurpose", id: "LIST" },
      ],
    }),

    downloadDataPurposesCsv: builder.query<Blob, DataPurposeParams>({
      query: (params) => ({
        url: `data-purpose`,
        params: { ...params, download_csv: true },
        responseHandler: "content-type",
      }),
    }),
  }),
});

export const {
  useGetAllDataPurposesQuery,
  useCreateDataPurposeMutation,
  useUpdateDataPurposeMutation,
  useDeleteDataPurposeMutation,
  useGetPurposeSummariesQuery,
  useGetPurposeOverviewQuery,
  useGetPurposeFeatureOptionsQuery,
  useAssignSystemsToPurposeMutation,
  useRemoveSystemsFromPurposeMutation,
  useAddDatasetsToPurposeMutation,
  useRemoveDatasetsFromPurposeMutation,
  useAcceptPurposeCategoriesMutation,
  useMarkPurposeCategoriesMisclassifiedMutation,
  useLazyDownloadDataPurposesCsvQuery,
} = dataPurposesApi;
