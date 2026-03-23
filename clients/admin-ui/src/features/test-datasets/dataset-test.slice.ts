import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { DatasetConfigSchema } from "~/types/api";

interface DatasetTestState {
  currentDataset: DatasetConfigSchema | null;
  currentPolicyKey?: string;
}

const initialState: DatasetTestState = {
  currentDataset: null,
};

export const datasetTestSlice = createSlice({
  name: "datasetTest",
  initialState,
  reducers: {
    setCurrentPolicyKey: (draftState, action: PayloadAction<string>) => {
      draftState.currentPolicyKey = action.payload;
    },
    setCurrentDataset: (
      draftState,
      action: PayloadAction<DatasetConfigSchema | null>,
    ) => {
      draftState.currentDataset = action.payload;
    },
  },
});

export const { setCurrentPolicyKey, setCurrentDataset } =
  datasetTestSlice.actions;

export const selectCurrentDataset = (state: RootState) =>
  state.datasetTest.currentDataset;
export const selectCurrentPolicyKey = (state: RootState) =>
  state.datasetTest.currentPolicyKey;

export const { reducer } = datasetTestSlice;
