import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { HYDRATE } from "next-redux-wrapper";

import type { AppState } from "~/app/store";

import { DataCategory } from "./types";

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
  extraReducers: {
    [HYDRATE]: (state, action) => ({
      ...state,
      ...action.payload.dataCategories,
    }),
  },
});

export const { setDataCategories } = dataCategoriesSlice.actions;
export const selectDataCategories = (state: AppState) => state;

export const { reducer } = dataCategoriesSlice;
