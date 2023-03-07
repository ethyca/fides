import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { produce } from "immer";

import type { RootState } from "~/app/store";
import { config as initialConfig } from "~/constants";
import { Consent, ConsentPreferences } from "~/types/api";
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

    /**
     * When consent preferences are returned from the API, they include the up-to-date description
     * of the related data use. This overrides the statically configured data use info.
     */
    updateConsentOptionsFromApi(
      draftState,
      { payload }: PayloadAction<ConsentPreferences>
    ) {
      const consentPreferencesMap = new Map<string, Consent>(
        (payload.consent ?? []).map((consent) => [consent.data_use, consent])
      );

      draftState.consent?.consentOptions?.forEach((draftOption) => {
        const apiConsent = consentPreferencesMap.get(
          draftOption.fidesDataUseKey
        );
        if (!apiConsent) {
          return;
        }

        if (apiConsent.data_use_description) {
          draftOption.description = apiConsent.data_use_description;
        }
      });
    },
  },
});

export const { reducer } = configSlice;
export const { updateConsentOptionsFromApi } = configSlice.actions;

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
