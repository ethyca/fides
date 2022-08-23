import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { AppState } from "~/app/store";
import { DataCategory } from "~/types/api";

export interface State {
  dataCategories: DataCategory[];
}

const initialState: State = {
  dataCategories: [],
};

export const dataCategoriesApi = createApi({
  reducerPath: "dataCategoriesApi",
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
  }),
});

export const { useGetAllDataCategoriesQuery, useUpdateDataCategoryMutation } =
  dataCategoriesApi;

export const dataCategoriesSlice = createSlice({
  name: "dataCategories",
  initialState,
  reducers: {
    setDataCategories: (state, action: PayloadAction<DataCategory[]>) => ({
      ...state,
      dataCategories: action.payload,
    }),
  },
});

export const { setDataCategories } = dataCategoriesSlice.actions;
export const selectDataCategories = (state: AppState) =>
  state.dataCategories.dataCategories;

export const { reducer } = dataCategoriesSlice;
