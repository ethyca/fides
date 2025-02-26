import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { useAppSelector } from "~/app/hooks";
import type { Styles } from "~/app/server-environment";
import type { RootState } from "~/app/store";

interface StylesState {
  styles?: Styles;
}
const initialState: StylesState = {};

export const stylesSlice = createSlice({
  name: "styles",
  initialState,
  reducers: {
    /**
     * Load new styles, replacing the current state entirely.
     */
    loadStyles(draftState, { payload }: PayloadAction<Styles | undefined>) {
      if (process.env.NODE_ENV === "development") {
        // eslint-disable-next-line no-console
        console.log("Loading Privacy Center styles into Redux store...");
      }
      draftState.styles = payload;
    },
  },
});

const selectStyles = (state: RootState) => state.styles;

export const { reducer } = stylesSlice;
export const { loadStyles } = stylesSlice.actions;
export const useStyles = (): Styles => {
  const { styles } = useAppSelector(selectStyles);
  if (!styles) {
    throw new Error("Unable to load Privacy Center styles!");
  }
  return styles;
};
