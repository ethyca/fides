import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import { type RootState } from "~/app/store";

// `initial` is like `hiding`, although it helps to know when we are setting
// an initial value vs reverting to a previous value
export type Suggestions = "showing" | "hiding" | "initial";

type State = {
  suggestions: Suggestions;
  lockedForGVL: boolean;
};
const initialState: State = {
  suggestions: "initial",
  lockedForGVL: false,
};

export const dictSuggestionsSlice = createSlice({
  name: "dictSuggestions",
  initialState,
  reducers: {
    toggleSuggestions: (draftState) => {
      if (draftState.suggestions === "initial") {
        draftState.suggestions = "showing";
      } else {
        draftState.suggestions =
          draftState.suggestions === "hiding" ? "showing" : "hiding";
      }
    },
    setSuggestions: (draftState, action: PayloadAction<Suggestions>) => {
      draftState.suggestions = action.payload;
    },
    setLockedForGVL: (draftState, action: PayloadAction<boolean>) => {
      draftState.lockedForGVL = action.payload;
    },
  },
});

export const { toggleSuggestions, setSuggestions, setLockedForGVL } =
  dictSuggestionsSlice.actions;

const selectDictSuggestionSlice = (state: RootState) => state.dictSuggestions;

export const selectSuggestions = createSelector(
  selectDictSuggestionSlice,
  (state) => state.suggestions,
);

export const selectLockedForGVL = createSelector(
  selectDictSuggestionSlice,
  (state) => state.lockedForGVL,
);
