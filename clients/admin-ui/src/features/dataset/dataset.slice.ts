import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { HYDRATE } from "next-redux-wrapper";

import type { AppState } from "~/app/store";

import { FidesKey } from "../common/fides-types";
import { Dataset } from "./types";

export interface State {
  datasets: Dataset[];
  activeDataset: Dataset | null;
  // collections and fields don't have unique IDs, so we have to use their index
  activeCollectionIndex: number | null;
  activeFieldIndex: number | null;
}

const initialState: State = {
  datasets: [],
  activeDataset: null,
  activeCollectionIndex: null,
  activeFieldIndex: null,
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
    updateDataset: build.mutation<
      Dataset,
      Partial<Dataset> & Pick<Dataset, "fides_key">
    >({
      query: (dataset) => ({
        url: `dataset/${dataset.fides_key}`,
        method: "PUT",
        body: dataset,
      }),
      invalidatesTags: ["Dataset"],
    }),
  }),
});

export const {
  useGetAllDatasetsQuery,
  useGetDatasetByKeyQuery,
  useUpdateDatasetMutation,
} = datasetApi;

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
    setActiveCollectionIndex: (
      state,
      action: PayloadAction<number | null>
    ) => ({
      ...state,
      activeCollectionIndex: action.payload,
    }),
    setActiveFieldIndex: (state, action: PayloadAction<number | null>) => ({
      ...state,
      activeFieldIndex: action.payload,
    }),
  },
  extraReducers: {
    [HYDRATE]: (state, action) => ({
      ...state,
      ...action.payload.datasets,
    }),
  },
});

export const {
  setDatasets,
  setActiveDataset,
  setActiveCollectionIndex,
  setActiveFieldIndex,
} = datasetSlice.actions;
export const selectActiveDataset = (state: AppState) =>
  state.dataset.activeDataset;
export const selectActiveCollectionIndex = (state: AppState) =>
  state.dataset.activeCollectionIndex;
export const selectActiveFieldIndex = (state: AppState) =>
  state.dataset.activeFieldIndex;

export const { reducer } = datasetSlice;
