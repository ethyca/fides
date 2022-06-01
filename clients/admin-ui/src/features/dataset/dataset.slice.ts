import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { HYDRATE } from "next-redux-wrapper";

import type { AppState } from "~/app/store";

import { FidesKey } from "../common/fides-types";
import { Dataset } from "./types";

export interface State {
  datasets: Dataset[];
  activeDataset: Dataset | null;
}

const initialState: State = {
  datasets: [],
  activeDataset: null,
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
      ...state,
      datasets: action.payload,
    }),
    setActiveDataset: (state, action: PayloadAction<Dataset | null>) => ({
      ...state,
      activeDataset: action.payload,
    }),
  },
  extraReducers: {
    [HYDRATE]: (state, action) => ({
      ...state,
      ...action.payload.datasets,
    }),
  },
});

export const { setDatasets, setActiveDataset } = datasetSlice.actions;
export const selectActiveDataset = (state: AppState) =>
  state.dataset.activeDataset;

export const { reducer } = datasetSlice;
