import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { HYDRATE } from "next-redux-wrapper";

import { FidesKey } from "../common/fides-types";
import { Dataset } from "./types";

export interface State {
  datasets: Dataset[];
}

const initialState: State = {
  datasets: [],
};

export const datasetApi = createApi({
  reducerPath: "datasetApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
  }),
  tagTypes: ["Dataset"],
  endpoints: (build) => ({
    getAllDatasets: build.query<Dataset[], void>({
      query: () => ({ url: `dataset/` }),
      providesTags: () => ["Dataset"],
    }),
    getDatasetByKey: build.query<Dataset, FidesKey>({
      query: (key) => ({ url: `dataset/${key}` }),
      providesTags: () => ["Dataset"],
    }),
  }),
});

export const { useGetAllDatasetsQuery, useGetDatasetByKeyQuery } = datasetApi;

export const datasetSlice = createSlice({
  name: "dataset",
  initialState,
  reducers: {
    setDatasets: (state, action: PayloadAction<Dataset[]>) => ({
      datasets: action.payload,
    }),
  },
  extraReducers: {
    [HYDRATE]: (state, action) => ({
      ...state,
      ...action.payload.datasets,
    }),
  },
});

export const { setDatasets } = datasetSlice.actions;

export const { reducer } = datasetSlice;
