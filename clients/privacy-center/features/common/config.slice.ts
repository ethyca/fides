import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { useAppSelector } from "~/app/hooks";
import type { RootState } from "~/app/store";
import { getDefaultConfig } from "~/constants";
import { Consent, ConsentPreferences } from "~/types/api";
import { Config } from "~/types/config";

// TODO: by statically loading the config here, we *guarantee* that the initial
// state is never undefined. This is convenient for all the Typescript checking,
// but is probably not wise - do we *really* want to ever show the "default"
// prebuilt config?
//
// We should refactor this to initialize the slice when the store is initialized
// (at runtime) and then set the initial state then. That would allow us to define the type as:
// ```
// type State = Config | undefined
// ```
//
// ...and then update all the code to handle that.
type State = Config
const initialState: State = getDefaultConfig();

export const configSlice = createSlice({
  name: "config",
  initialState,
  reducers: {
    /**
     * When consent preferences are returned from the API, they include the up-to-date description
     * of the related data use. This overrides the currently configured data use info.
     */
    updateConsentOptionsFromApi(
      draftState,
      { payload }: PayloadAction<ConsentPreferences>
    ) {
      const consentPreferencesMap = new Map<string, Consent>(
        (payload.consent ?? []).map((consent) => [consent.data_use, consent])
      );

      draftState?.consent?.page.consentOptions?.forEach((draftOption) => {
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
export const { updateConsentOptionsFromApi } = configSlice.actions;
export const useConfig = (): State => { 
  const config = useAppSelector(selectConfig);
  return config;
}