import { baseApi } from "~/features/common/api.slice";

interface DataPurposeParams {
  search?: string;
  data_use?: string;
  consumer?: string;
  category?: string;
  status?: string;
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

export interface DataPurposeFilterOption {
  value: string;
  label: string;
}

export interface DataPurposeFilterOptions {
  consumers: DataPurposeFilterOption[];
  data_uses: DataPurposeFilterOption[];
  categories: DataPurposeFilterOption[];
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
  useGetDataPurposeByKeyQuery,
  useCreateDataPurposeMutation,
  useUpdateDataPurposeMutation,
  useDeleteDataPurposeMutation,
  useGetPurposeSummariesQuery,
  useLazyDownloadDataPurposesCsvQuery,
} = dataPurposesApi;
