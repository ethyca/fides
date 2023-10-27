import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import { type RootState } from "~/app/store";

// `initial` is like `hiding`, although it helps to know when we are setting
// an initial value vs reverting to a previous value
export type Suggestions = "showing" | "hiding" | "initial";

type State = {
  suggestions: Suggestions;
};
const initialState: State = {
  suggestions: "initial",
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
  },
});

export const { toggleSuggestions, setSuggestions } =
  dictSuggestionsSlice.actions;

const selectDictSuggestionSlice = (state: RootState) => state.dictSuggestions;

export const selectSuggestions = createSelector(
  selectDictSuggestionSlice,
  (state) => state.suggestions
);
