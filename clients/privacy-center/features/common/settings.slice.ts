import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { useAppSelector } from "~/app/hooks";
import { PrivacyCenterClientSettings } from "~/app/server-environment";
import type { RootState } from "~/app/store";

interface SettingsState {
  settings?: PrivacyCenterClientSettings;
}
const initialState: SettingsState = {};

export const settingsSlice = createSlice({
  name: "settings",
  initialState,
  reducers: {
    /**
     * Load new settings, replacing the current state entirely.
     */
    loadSettings(
      draftState,
      { payload }: PayloadAction<PrivacyCenterClientSettings | undefined>
    ) {
      if (process.env.NODE_ENV === "development") {
        // eslint-disable-next-line no-console
        console.log("Loading Privacy Center settings into Redux store...");
      }
      draftState.settings = payload;
    },
  },
});

export const selectSettings = (state: RootState) => state.settings;
export const { reducer } = settingsSlice;
export const { loadSettings } = settingsSlice.actions;
export const useSettings = (): PrivacyCenterClientSettings => {
  const { settings } = useAppSelector(selectSettings);
  if (!settings) {
    throw new Error("Unable to load Privacy Center settings!");
  }
  return settings;
};
