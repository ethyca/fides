import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { DatasetConfigSchema } from "~/types/api";

interface DatasetTestState {
  privacyRequestId: string | null;
  currentDataset: DatasetConfigSchema | null;
  isReachable: boolean;
  testInputs: Record<string, Record<string, any>>;
  testResults: Record<string, string>;
  isTestRunning: boolean;
  currentPolicyKey: string | null;
}

const initialState: DatasetTestState = {
  privacyRequestId: null,
  currentDataset: null,
  isReachable: false,
  testInputs: {},
  currentPolicyKey: null,
  testResults: {},
  isTestRunning: false,
};

export const datasetTestSlice = createSlice({
  name: "datasetTest",
  initialState,
  reducers: {
    startTest: (draftState, action: PayloadAction<string>) => {
      draftState.testResults = {
        ...draftState.testResults,
        [action.payload]: "",
      };
      draftState.isTestRunning = true;
    },
    setPrivacyRequestId: (draftState, action: PayloadAction<string>) => {
      draftState.privacyRequestId = action.payload;
    },
    finishTest: (draftState) => {
      draftState.privacyRequestId = null;
      draftState.isTestRunning = false;
    },
    setTestInputs: (
      draftState,
      action: PayloadAction<{
        datasetKey: string;
        values: Record<string, any>;
      }>,
    ) => {
      const existingValues =
        draftState.testInputs[action.payload.datasetKey] || {};
      const inputsData = action.payload.values || {};

      // Skip processing if we're trying to set empty values over existing ones
      if (
        Object.keys(existingValues).length > 0 &&
        Object.keys(inputsData).length === 0
      ) {
        return;
      }

      // Start with input data
      const mergedValues = { ...inputsData };

      // For each key in the existing values
      Object.entries(existingValues).forEach(([key, existingValue]) => {
        // If the new value is null and we have an existing non-null value, keep the existing value
        if (
          key in mergedValues &&
          mergedValues[key] === null &&
          existingValue !== null
        ) {
          mergedValues[key] = existingValue;
        }
      });

      draftState.testInputs = {
        ...draftState.testInputs,
        [action.payload.datasetKey]: mergedValues,
      };
    },
    setCurrentPolicyKey: (draftState, action: PayloadAction<string | null>) => {
      draftState.currentPolicyKey = action.payload;
    },
    setCurrentDataset: (
      draftState,
      action: PayloadAction<DatasetConfigSchema | null>,
    ) => {
      draftState.currentDataset = action.payload;
      draftState.privacyRequestId = null;
    },
    setReachability: (draftState, action: PayloadAction<boolean>) => {
      draftState.isReachable = action.payload;
    },
    setTestResults: (
      draftState,
      action: PayloadAction<{
        datasetKey: string;
        values: string;
      }>,
    ) => {
      draftState.testResults = {
        ...draftState.testResults,
        [action.payload.datasetKey]: action.payload.values,
      };
    },
  },
});

export const {
  startTest,
  setPrivacyRequestId,
  finishTest,
  setTestInputs,
  setCurrentPolicyKey,
  setCurrentDataset,
  setReachability,
  setTestResults,
} = datasetTestSlice.actions;

export const selectPrivacyRequestId = (state: RootState) =>
  state.datasetTest.privacyRequestId;
export const selectDatasetTestPrivacyRequestId = (state: RootState) =>
  state.datasetTest.privacyRequestId;
export const selectCurrentDataset = (state: RootState) =>
  state.datasetTest.currentDataset;
export const selectIsReachable = (state: RootState) =>
  state.datasetTest.isReachable;
export const selectTestInputs = (state: RootState) => {
  const { currentDataset } = state.datasetTest;
  return currentDataset
    ? state.datasetTest.testInputs[currentDataset.fides_key] || {}
    : {};
};
export const selectCurrentPolicyKey = (state: RootState) =>
  state.datasetTest.currentPolicyKey;
export const selectTestResults = (state: RootState) => {
  const { currentDataset } = state.datasetTest;
  return currentDataset
    ? state.datasetTest.testResults[currentDataset.fides_key] || ""
    : "";
};
export const selectIsTestRunning = (state: RootState) =>
  state.datasetTest.isTestRunning;

export const { reducer } = datasetTestSlice;
