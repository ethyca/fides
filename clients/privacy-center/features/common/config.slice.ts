import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { useAppSelector } from "~/app/hooks";
import type { RootState } from "~/app/store";
import {
  isV1ConsentConfig,
  translateV1ConfigToV2,
} from "~/features/consent/helpers";
import { Consent, ConsentPreferences } from "~/types/api";
import {
  LegacyConfig,
  LegacyConsentConfig,
  Config,
  ConsentConfig,
} from "~/types/config";

interface ConfigState {
  config?: Config;
}
const initialState: ConfigState = {};

/**
 * Transform the config to the latest version so that components can
 * reference config variables uniformly.
 *
 * DEFER: move this to config.slice as part of removing default config state (see https://github.com/ethyca/fides/issues/3212)
 */
const transformConfig = (config: LegacyConfig): Config => {
  if (isV1ConsentConfig(config.consent)) {
    const v1ConsentConfig: LegacyConsentConfig = config.consent;
    const translatedConsent: ConsentConfig = translateV1ConfigToV2({
      v1ConsentConfig,
    });
    return { ...config, consent: translatedConsent };
  }
  return { ...config, consent: config.consent };
};

export const configSlice = createSlice({
  name: "config",
  initialState,
  reducers: {
    /**
     * Load a new configuration, replacing the current state entirely.
     */
    loadConfig(draftState, { payload }: PayloadAction<Config>) {
      draftState.config = payload;
    },
    /**
     * Modify the current configuration, by merging a partial config into the current state.
     */
    mergeConfig(draftState, { payload }: PayloadAction<Partial<Config>>) {
      if (!draftState.config) {
        throw new Error(
          "Cannot apply mergeConfig into uninitialized Redux state; must use loadConfig first!"
        );
      }
      draftState.config = { ...draftState.config, ...payload };
    },
    /**
     * When consent preferences are returned from the API, they include the up-to-date description
     * of the related data use. This overrides the currently configured data use info.
     */
    updateConsentOptionsFromApi(
      draftState,
      { payload }: PayloadAction<ConsentPreferences>
    ) {
      if (!draftState.config) {
        throw new Error(
          "Cannot apply updateConsentOptionsFromApi into uninitialized Redux state; must use loadConfig first!"
        );
      }
      const consentPreferencesMap = new Map<string, Consent>(
        (payload.consent ?? []).map((consent) => [consent.data_use, consent])
      );

      draftState.config.consent?.page.consentOptions?.forEach((draftOption) => {
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

const selectConfig = (state: RootState) => state.config;

export const { reducer } = configSlice;
export const { loadConfig, mergeConfig, updateConsentOptionsFromApi } =
  configSlice.actions;
export const useConfig = (): Config => {
  const config = useAppSelector(selectConfig).config;
  if (!config) {
    throw new Error("WUnable to load Privacy Center configuration!");
  }
  return config;
};
