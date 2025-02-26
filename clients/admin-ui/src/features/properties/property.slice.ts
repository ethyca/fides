import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { Page_Property_, Property } from "~/types/api";

export interface State {
  page?: number;
  pageSize?: number;
}

const initialState: State = {
  page: 1,
  pageSize: 50,
};

interface PropertyParams {
  search?: string;
  page?: number;
  size?: number;
}

export const propertiesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAllProperties: builder.query<Page_Property_, PropertyParams>({
      query: (params) => ({
        url: `plus/properties`,
        params,
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
      { id: string; property: Partial<Property> }
    >({
      query: ({ id, property }) => ({
        url: `plus/property/${id}`,
        method: "PUT",
        body: property,
      }),
      invalidatesTags: ["Property", "Privacy Experience Configs"],
    }),
    deleteProperty: builder.mutation<Property, string>({
      query: (id) => ({
        url: `plus/property/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Property", "Privacy Experience Configs"],
    }),
  }),
});

export const {
  useGetAllPropertiesQuery,
  useGetPropertyByIdQuery,
  useCreatePropertyMutation,
  useUpdatePropertyMutation,
  useDeletePropertyMutation,
} = propertiesApi;

export const propertySlice = createSlice({
  name: "properties",
  initialState,
  reducers: {},
});
export const { reducer } = propertySlice;

const selectProperties = (state: RootState) => state.properties;

export const selectPage = createSelector(
  selectProperties,
  (state) => state.page,
);

export const selectPageSize = createSelector(
  selectProperties,
  (state) => state.pageSize,
);

const emptyProperties: Property[] = [];
export const selectAllProperties = createSelector(
  [(RootState) => RootState, selectPage, selectPageSize],
  (RootState, page, pageSize) => {
    const data = propertiesApi.endpoints.getAllProperties.select({
      page,
      size: pageSize,
    })(RootState)?.data;
    return data ? data.items : emptyProperties;
  },
);
