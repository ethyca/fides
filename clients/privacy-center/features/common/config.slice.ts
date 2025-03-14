import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { useAppSelector } from "~/app/hooks";
import type { RootState } from "~/app/store";
import { Consent, ConsentPreferences, PrivacyCenterConfig } from "~/types/api";
import { Config } from "~/types/config";

interface ConfigState {
  config?: Config | PrivacyCenterConfig;
}
const initialState: ConfigState = {};

export const configSlice = createSlice({
  name: "config",
  initialState,
  reducers: {
    /**
     * Load a new configuration, replacing the current state entirely.
     */
    loadConfig(
      draftState,
      { payload }: PayloadAction<Config | PrivacyCenterConfig | undefined>,
    ) {
      if (process.env.NODE_ENV === "development") {
        // eslint-disable-next-line no-console
        console.log(
          "Loading Privacy Center configuration into Redux store...",
          payload?.title,
        );
      }
      draftState.config = payload;
    },
    /**
     * When consent preferences are returned from the API, they include the up-to-date description
     * of the related data use. This overrides the currently configured data use info.
     */
    updateConsentOptionsFromApi(
      draftState,
      { payload }: PayloadAction<ConsentPreferences>,
    ) {
      if (!draftState.config) {
        throw new Error(
          "Cannot apply updateConsentOptionsFromApi into uninitialized Redux state; must use loadConfig first!",
        );
      }
      const consentPreferencesMap = new Map<string, Consent>(
        (payload.consent ?? []).map((consent) => [consent.data_use, consent]),
      );

      draftState.config.consent?.page.consentOptions?.forEach((draftOption) => {
        const apiConsent = consentPreferencesMap.get(
          draftOption.fidesDataUseKey,
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

const selectConfig = (state: RootState) => state.config;

export const { reducer } = configSlice;
export const { loadConfig, updateConsentOptionsFromApi } = configSlice.actions;
export const useConfig = (): Config | PrivacyCenterConfig => {
  const { config } = useAppSelector(selectConfig);
  if (!config) {
    throw new Error("Unable to load Privacy Center configuration!");
  }
  return config;
};
export const useHasConfig = (): boolean => {
  const { config } = useAppSelector(selectConfig);
  return !!config;
};
