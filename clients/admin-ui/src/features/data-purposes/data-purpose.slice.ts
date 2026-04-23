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
 * Per-purpose enrichment used by the list grid. Served in a single batched
 * call to avoid N+1 requests across cards. The per-purpose system/dataset
 * read and mutation endpoints referenced here land with the detail-page PR;
 * for now only `system_count`, `dataset_count`, and `detected_data_categories`
 * are consumed by the grid.
 */
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
    // TODO: replace with real endpoint once fidesplus ships it.
    getPurposeSummaries: builder.query<PurposeSummary[], void>({
      query: () => ({
        url: `plus/data-purpose/summaries`,
      }),
      providesTags: ["DataPurpose"],
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
} = dataPurposesApi;
