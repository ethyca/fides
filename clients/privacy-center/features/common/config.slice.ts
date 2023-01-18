import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { config as initialConfig } from "~/constants";

const initialState = initialConfig;

export const slice = createSlice({
  name: "config",
  initialState,
  reducers: {},
});

export const { reducer } = slice;

export const selectConfig = (state: RootState) => state.config;
export const selectConfigConsent = createSelector(
  selectConfig,
  (config) => config.consent
);
