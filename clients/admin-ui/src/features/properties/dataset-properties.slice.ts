import { baseApi } from "~/features/common/api.slice";
import type {
  BulkDatasetPropertyResponse,
  BulkPropertyAssignment,
  BulkPropertyRemoval,
  DatasetPropertyIdsResponse,
} from "~/types/api";

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
