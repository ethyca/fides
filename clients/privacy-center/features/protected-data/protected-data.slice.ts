import { baseApi } from "~/features/common/api.slice";

// Define your types
export interface ProtectedDataResponse {
  id: string;
  name: string;
  data: any;
  created_at: string;
  updated_at: string;
}

export interface ProtectedDataRequest {
  name: string;
  data?: any;
}

export interface ProtectedDataListResponse {
  items: ProtectedDataResponse[];
  total: number;
  page: number;
  size: number;
}

/**
 * Protected Data API endpoints that require authentication
 *
 * These endpoints call the Fides API backend directly and require
 * proper authentication tokens to be passed.
 */
export const protectedDataApi = baseApi.injectEndpoints({
  endpoints: (build) => ({

    // Get protected data with optional filtering
    getProtectedData: build.query<
      ProtectedDataListResponse,
      { id?: string; page?: number; size?: number; token?: string }
    >({
      query: ({ id, page = 1, size = 10, token, ...params }) => ({
        url: "your-protected-endpoint", // Replace with actual Fides API endpoint
        params: {
          ...(id && { id }),
          page,
          size,
          ...params,
        },
        headers: token ? { authorization: `Bearer ${token}` } : {},
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.items.map(({ id }) => ({ type: "ProtectedData" as const, id })),
              { type: "ProtectedData", id: "LIST" },
            ]
          : [{ type: "ProtectedData", id: "LIST" }],
    }),

    // Get single protected data item
    getProtectedDataById: build.query<
      ProtectedDataResponse,
      { id: string; token?: string }
    >({
      query: ({ id, token }) => ({
        url: `your-protected-endpoint/${id}`, // Replace with actual endpoint
        headers: token ? { authorization: `Bearer ${token}` } : {},
      }),
      providesTags: (result, error, arg) => [{ type: "ProtectedData", id: arg.id }],
    }),

    // Create new protected data
    createProtectedData: build.mutation<
      ProtectedDataResponse,
      { data: ProtectedDataRequest; token?: string }
    >({
      query: ({ data, token }) => ({
        url: "your-protected-endpoint", // Replace with actual endpoint
        method: "POST",
        body: data,
        headers: token ? { authorization: `Bearer ${token}` } : {},
      }),
      invalidatesTags: [{ type: "ProtectedData", id: "LIST" }],
    }),

    // Update protected data
    updateProtectedData: build.mutation<
      ProtectedDataResponse,
      { id: string; data: Partial<ProtectedDataRequest>; token?: string }
    >({
      query: ({ id, data, token }) => ({
        url: `your-protected-endpoint/${id}`, // Replace with actual endpoint
        method: "PATCH",
        body: data,
        headers: token ? { authorization: `Bearer ${token}` } : {},
      }),
      invalidatesTags: (result, error, arg) => [
        { type: "ProtectedData", id: arg.id },
        { type: "ProtectedData", id: "LIST" },
      ],
    }),

    // Delete protected data
    deleteProtectedData: build.mutation<
      void,
      { id: string; token?: string }
    >({
      query: ({ id, token }) => ({
        url: `your-protected-endpoint/${id}`, // Replace with actual endpoint
        method: "DELETE",
        headers: token ? { authorization: `Bearer ${token}` } : {},
      }),
      invalidatesTags: (result, error, arg) => [
        { type: "ProtectedData", id: arg.id },
        { type: "ProtectedData", id: "LIST" },
      ],
    }),

  }),
});

// Export hooks for use in components
export const {
  useGetProtectedDataQuery,
  useGetProtectedDataByIdQuery,
  useCreateProtectedDataMutation,
  useUpdateProtectedDataMutation,
  useDeleteProtectedDataMutation,
} = protectedDataApi;
