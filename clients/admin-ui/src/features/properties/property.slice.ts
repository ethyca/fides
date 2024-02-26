import { Page_Property_, Property } from "~/types/api";

import { baseApi } from "../common/api.slice";

export const propertiesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getProperties: builder.query<
      Page_Property_,
      { pageIndex: number; pageSize: number; search?: string }
    >({
      query: (params) => ({
        url: `plus/properties`,
        params: {
          page: params.pageIndex,
          size: params.pageSize,
          search: params.search,
        },
      }),
      providesTags: ["Property"],
    }),
    getPropertyByKey: builder.query<Property, string>({
      query: (key) => ({
        url: `plus/property/${key}`,
      }),
      providesTags: ["Property"],
    }),
    createProperty: builder.mutation<Property, Partial<Property>>({
      query: (params) => ({
        url: `plus/property`,
        method: "POST",
        body: params,
      }),
      invalidatesTags: ["Property"],
    }),
  }),
});

// Export hooks for using the endpoints
export const {
  useGetPropertiesQuery,
  useGetPropertyByKeyQuery,
  useCreatePropertyMutation,
} = propertiesApi;
