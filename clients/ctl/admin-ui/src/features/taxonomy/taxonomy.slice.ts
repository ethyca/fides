import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { AppState } from "~/app/store";
import { DataCategory } from "~/types/api";

import { TaxonomyType } from "./types";

export interface State {
  dataCategories: DataCategory[];
  addTaxonomyType: TaxonomyType | null;
}

const initialState: State = {
  dataCategories: [],
  addTaxonomyType: null,
};

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
  }),
});

export const {
  useGetAllDataCategoriesQuery,
  useUpdateDataCategoryMutation,
  useCreateDataCategoryMutation,
} = taxonomyApi;

export const taxonomySlice = createSlice({
  name: "taxonomy",
  initialState,
  reducers: {
    setDataCategories: (state, action: PayloadAction<DataCategory[]>) => ({
      ...state,
      dataCategories: action.payload,
    }),
    setAddTaxonomyType: (
      state,
      action: PayloadAction<TaxonomyType | null>
    ) => ({
      ...state,
      addTaxonomyType: action.payload,
    }),
  },
});

export const { setDataCategories, setAddTaxonomyType } = taxonomySlice.actions;
export const selectDataCategories = (state: AppState) =>
  state.taxonomy.dataCategories;
export const selectAddTaxonomyType = (state: AppState) =>
  state.taxonomy.addTaxonomyType;

export const { reducer } = taxonomySlice;
