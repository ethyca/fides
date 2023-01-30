import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { produce } from "immer";

import type { RootState } from "~/app/store";
import { config as initialConfig } from "~/constants";
import { ConfigConsentOption } from "~/types/config";

type State = {
  consent?: {
    consentOptions?: ConfigConsentOption[];
  };
};
const initialState: State = {};

export const configSlice = createSlice({
  name: "config",
  initialState,
  reducers: {
    overrideConsentOptions(
      draftState,
      { payload }: PayloadAction<ConfigConsentOption[]>
    ) {
      if (!draftState.consent) {
        draftState.consent = {};
      }
      draftState.consent.consentOptions = payload;
    },
  },
});

export const { reducer } = configSlice;

/**
 * The stored config state, which is the subset of configs options that can be modified at runtime.
 */
export const selectConfigState = (state: RootState) => state.config;

/**
 * The app config with all runtime overrides applied.
 */
export const selectConfig = createSelector(selectConfigState, (configState) =>
  produce(initialConfig, (draft) => {
    Object.assign(draft, configState);
  })
);

export const selectConfigConsentOptions = createSelector(
  selectConfig,
  (config) => config.consent?.consentOptions ?? []
);
