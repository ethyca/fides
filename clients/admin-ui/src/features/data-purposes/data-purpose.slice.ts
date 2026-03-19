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
  description?: string;
  data_use: string;
  data_subject?: string;
  data_categories?: string[];
  legal_basis_for_processing?: string;
  flexible_legal_basis_for_processing?: boolean;
  special_category_legal_basis?: string;
  impact_assessment_location?: string;
  retention_period?: string;
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
  }),
});

export const {
  useGetAllDataPurposesQuery,
  useGetDataPurposeByKeyQuery,
  useCreateDataPurposeMutation,
  useUpdateDataPurposeMutation,
  useDeleteDataPurposeMutation,
} = dataPurposesApi;
