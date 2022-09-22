import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { AppState } from "~/app/store";
import { DataCategory } from "~/types/api";

export const taxonomyApi = createApi({
  reducerPath: "taxonomyApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
  }),
  tagTypes: ["Data Categories"],
  endpoints: (build) => ({
    getAllDataCategories: build.query<DataCategory[], void>({
      query: () => ({ url: `data_category/` }),
      providesTags: () => ["Data Categories"],
      transformResponse: (categories: DataCategory[]) =>
        categories.sort((a, b) => a.fides_key.localeCompare(b.fides_key)),
    }),
    updateDataCategory: build.mutation<
      DataCategory,
      Partial<DataCategory> & Pick<DataCategory, "fides_key">
    >({
      query: (dataCategory) => ({
        url: `data_category/`,
        params: { resource_type: "data_category" },
        method: "PUT",
        body: dataCategory,
      }),
      invalidatesTags: ["Data Categories"],
    }),

    createDataCategory: build.mutation<DataCategory, DataCategory>({
      query: (dataCategory) => ({
        url: `data_category/`,
        method: "POST",
        body: dataCategory,
      }),
      invalidatesTags: ["Data Categories"],
    }),

    deleteDataCategory: build.mutation<string, string>({
      query: (key) => ({
        url: `data_category/${key}`,
        params: { resource_type: "data_category" },
        method: "DELETE",
      }),
      invalidatesTags: ["Data Categories"],
    }),
  }),
});

export const {
  useGetAllDataCategoriesQuery,
  useUpdateDataCategoryMutation,
  useDeleteDataCategoryMutation,
  useCreateDataCategoryMutation,
} = taxonomyApi;

export interface State {
  isAddFormOpen: boolean;
}

const initialState: State = {
  isAddFormOpen: false,
};

export const taxonomySlice = createSlice({
  name: "taxonomy",
  initialState,
  reducers: {
    setIsAddFormOpen: (draftState, action: PayloadAction<boolean>) => {
      draftState.isAddFormOpen = action.payload;
    },
  },
});

export const { setIsAddFormOpen } = taxonomySlice.actions;

const emptyDataCategories: DataCategory[] = [];
export const selectDataCategories: (state: AppState) => DataCategory[] =
  createSelector(
    taxonomyApi.endpoints.getAllDataCategories.select(),
    ({ data }) => data ?? emptyDataCategories
  );

const selectTaxonomy = (state: AppState) => state.taxonomy;

export const selectIsAddFormOpen = createSelector(
  selectTaxonomy,
  (state) => state.isAddFormOpen
);

export const { reducer } = taxonomySlice;
