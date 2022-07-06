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

interface DatasetDeleteResponse {
  message: string;
  resource: Dataset;
}

export const datasetApi = createApi({
  reducerPath: "datasetApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
  }),
  tagTypes: ["Dataset", "Datasets"],
  endpoints: (build) => ({
    getAllDatasets: build.query<Dataset[], void>({
      query: () => ({ url: `dataset/` }),
      providesTags: () => ["Datasets"],
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
        url: `dataset/`,
        params: { resource_type: "dataset" },
        method: "PUT",
        body: dataset,
      }),
      invalidatesTags: ["Dataset"],
    }),
    // we accept 'unknown' as well since the user can paste anything in, and we rely
    // on the backend to do the validation for us
    createDataset: build.mutation<Dataset, Dataset | unknown>({
      query: (dataset) => ({
        url: `dataset/`,
        method: "POST",
        body: dataset,
      }),
      invalidatesTags: ["Datasets"],
    }),
    deleteDataset: build.mutation<DatasetDeleteResponse, FidesKey>({
      query: (key) => ({
        url: `dataset/${key}`,
        params: { resource_type: "dataset" },
        method: "DELETE",
      }),
      invalidatesTags: ["Datasets"],
    }),
  }),
});

export const {
  useGetAllDatasetsQuery,
  useGetDatasetByKeyQuery,
  useUpdateDatasetMutation,
  useCreateDatasetMutation,
  useDeleteDatasetMutation,
} = datasetApi;

export const datasetSlice = createSlice({
  name: "dataset",
  initialState,
  reducers: {
    setDatasets: (state, action: PayloadAction<Dataset[]>) => ({
      ...state,
      datasets: action.payload,
    }),
    setActiveDataset: (state, action: PayloadAction<Dataset | null>) => {
      if (action.payload != null) {
        return { ...state, activeDataset: action.payload };
      }
      // clear out child fields when a dataset becomes null
      return {
        ...state,
        activeDataset: action.payload,
        activeCollectionIndex: null,
        activeFieldIndex: null,
      };
    },
    setActiveCollectionIndex: (state, action: PayloadAction<number | null>) => {
      if (action.payload != null) {
        return {
          ...state,
          activeCollectionIndex: action.payload,
        };
      }
      // clear our child fields when a collection becomes null
      return {
        ...state,
        activeCollectionIndex: action.payload,
        activeFieldIndex: null,
      };
    },
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
