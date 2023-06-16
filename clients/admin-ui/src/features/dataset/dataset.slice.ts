import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  BulkPutDataset,
  Dataset,
  GenerateRequestPayload,
  GenerateResponse,
} from "~/types/api";

import { EditableType } from "./types";

export interface State {
  activeDatasetFidesKey?: string;
  // collections and fields don't have unique IDs, so we have to use their index
  activeCollectionIndex?: number;
  activeFieldIndex?: number;
  // Controls whether the edit drawer is open and what is being edited.
  activeEditor?: EditableType;
}

const initialState: State = {};

interface DatasetDeleteResponse {
  message: string;
  resource: Dataset;
}

const datasetApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllDatasets: build.query<Dataset[], void>({
      query: () => ({ url: `dataset/` }),
      providesTags: () => ["Datasets"],
    }),
    getAllFilteredDatasets: build.query<
      Dataset[],
      { onlyUnlinkedDatasets: boolean }
    >({
      query: ({ onlyUnlinkedDatasets }) => ({
        url: `/filter/dataset`,
        params: { only_unlinked_datasets: onlyUnlinkedDatasets },
      }),
      providesTags: () => ["Datasets"],
    }),
    getDatasetByKey: build.query<Dataset, string>({
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
    /**
     * Also accepts unknown for the same reason as above
     */
    upsertDatasets: build.mutation<BulkPutDataset, Dataset[] | unknown>({
      query: (datasets) => ({
        url: `dataset/upsert`,
        method: "POST",
        body: datasets,
      }),
      invalidatesTags: ["Datasets"],
    }),
    deleteDataset: build.mutation<DatasetDeleteResponse, string>({
      query: (key) => ({
        url: `dataset/${key}`,
        params: { resource_type: "dataset" },
        method: "DELETE",
      }),
      invalidatesTags: ["Datasets"],
    }),
    generateDataset: build.mutation<GenerateResponse, GenerateRequestPayload>({
      query: (payload) => ({
        url: `generate/`,
        method: "POST",
        body: payload,
      }),
    }),
  }),
});

export const {
  useGetAllDatasetsQuery,
  useGetAllFilteredDatasetsQuery,
  useGetDatasetByKeyQuery,
  useUpdateDatasetMutation,
  useUpsertDatasetsMutation,
  useCreateDatasetMutation,
  useDeleteDatasetMutation,
  useGenerateDatasetMutation,
} = datasetApi;

export const datasetSlice = createSlice({
  name: "dataset",
  initialState,
  reducers: {
    setActiveDatasetFidesKey: (
      draftState,
      action: PayloadAction<string | undefined>
    ) => {
      if (draftState.activeDatasetFidesKey === action.payload) {
        return;
      }

      // Clear out the related fields when the dataset is changed.
      draftState.activeDatasetFidesKey = action.payload;
      draftState.activeCollectionIndex = 0;
      draftState.activeFieldIndex = undefined;
    },
    setActiveCollectionIndex: (
      draftState,
      action: PayloadAction<number | undefined>
    ) => {
      if (draftState.activeCollectionIndex === action.payload) {
        return;
      }

      // Clear out the related fields when the collection is changed.
      draftState.activeCollectionIndex = action.payload;
      draftState.activeFieldIndex = undefined;
    },
    setActiveFieldIndex: (
      draftState,
      action: PayloadAction<number | undefined>
    ) => {
      draftState.activeFieldIndex = action.payload;
    },
    setActiveEditor: (
      draftState,
      action: PayloadAction<EditableType | undefined>
    ) => {
      draftState.activeEditor = action.payload;
    },
  },
});

export const {
  setActiveDatasetFidesKey,
  setActiveCollectionIndex,
  setActiveFieldIndex,
  setActiveEditor,
} = datasetSlice.actions;

export const { reducer } = datasetSlice;

const selectDataset = (state: RootState) => state.dataset;

const emptyDatasets: Dataset[] = [];
export const selectAllDatasets: (state: RootState) => Dataset[] =
  createSelector(
    [(RootState) => RootState, datasetApi.endpoints.getAllDatasets.select()],
    (RootState, { data }) => data ?? emptyDatasets
  );

export const selectAllFilteredDatasets: (state: RootState) => Dataset[] =
  createSelector(
    [
      (RootState) => RootState,
      datasetApi.endpoints.getAllFilteredDatasets.select({
        onlyUnlinkedDatasets: false,
      }),
    ],
    (RootState, { data }) => data ?? emptyDatasets
  );
export const selectActiveDatasetFidesKey = createSelector(
  selectDataset,
  (state) => state.activeDatasetFidesKey
);
export const selectActiveDataset: (state: RootState) => Dataset | undefined =
  createSelector(
    [(RootState) => RootState, selectActiveDatasetFidesKey],
    (RootState, fidesKey) =>
      fidesKey !== undefined
        ? datasetApi.endpoints.getDatasetByKey.select(fidesKey)(RootState)?.data
        : undefined
  );

export const selectActiveCollections = createSelector(
  selectActiveDataset,
  (dataset) => dataset?.collections
);
export const selectActiveCollectionIndex = createSelector(
  selectDataset,
  (state) => state.activeCollectionIndex
);
export const selectActiveCollection = createSelector(
  [selectActiveCollectionIndex, selectActiveCollections],
  (index, collections) =>
    index !== undefined && collections ? collections[index] : undefined
);

export const selectActiveFields = createSelector(
  [selectActiveCollection],
  (collection) => collection?.fields
);
export const selectActiveFieldIndex = createSelector(
  selectDataset,
  (state) => state.activeFieldIndex
);
export const selectActiveField = createSelector(
  [selectActiveFieldIndex, selectActiveFields],
  (index, fields) => (index !== undefined && fields ? fields[index] : undefined)
);

export const selectActiveEditor = createSelector(
  selectDataset,
  (state) => state.activeEditor
);
