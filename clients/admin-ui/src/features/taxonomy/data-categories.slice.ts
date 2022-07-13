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
  tagTypes: ["Data Category"],
  endpoints: (build) => ({
    getAllDataCategories: build.query<DataCategory[], void>({
      query: () => ({ url: `data_category/` }),
      providesTags: () => ["Data Category"],
    }),
  }),
});

export const { useGetAllDataCategoriesQuery } = dataCategoriesApi;

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
