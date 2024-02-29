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
    getPropertyById: builder.query<Property, string>({
      query: (id) => ({
        url: `plus/property/${id}`,
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
    updateProperty: builder.mutation<
      Property,
      { key: string; property: Partial<Property> }
    >({
      query: ({ id, property }) => ({
        url: `plus/property/${id}`,
        method: "PUT",
        body: property,
      }),
      invalidatesTags: ["Property"],
    }),
  }),
});

export const {
  useGetPropertiesQuery,
  useGetPropertyByIdQuery,
  useCreatePropertyMutation,
  useUpdatePropertyMutation,
} = propertiesApi;
