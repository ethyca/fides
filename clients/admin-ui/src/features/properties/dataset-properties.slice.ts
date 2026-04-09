import { baseApi } from "~/features/common/api.slice";

interface DatasetPropertyIdsResponse {
  property_ids: string[];
}

interface BulkPropertyAssignment {
  dataset_config_ids: string[];
  property_ids: string[];
}

interface BulkPropertyRemoval {
  dataset_config_ids: string[];
  property_ids: string[];
}

interface DatasetPropertyResponse {
  fides_key: string;
  property_ids: string[];
}

interface BulkDatasetPropertyResponse {
  succeeded: DatasetPropertyResponse[];
  failed?: Record<string, unknown>[] | null;
}

export const datasetPropertiesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getPropertyIdsForDataset: builder.query<DatasetPropertyIdsResponse, string>(
      {
        query: (fidesKey) => ({
          url: `plus/dataset-properties`,
          params: { fides_key: fidesKey },
        }),
        providesTags: ["Property"],
      },
    ),
    bulkAssignProperties: builder.mutation<
      BulkDatasetPropertyResponse,
      BulkPropertyAssignment
    >({
      query: (body) => ({
        url: `plus/dataset-properties/bulk-assign`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["Property"],
    }),
    bulkRemoveProperties: builder.mutation<
      BulkDatasetPropertyResponse,
      BulkPropertyRemoval
    >({
      query: (body) => ({
        url: `plus/dataset-properties/bulk-remove`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["Property"],
    }),
  }),
});

export const {
  useGetPropertyIdsForDatasetQuery,
  useBulkAssignPropertiesMutation,
  useBulkRemovePropertiesMutation,
} = datasetPropertiesApi;
