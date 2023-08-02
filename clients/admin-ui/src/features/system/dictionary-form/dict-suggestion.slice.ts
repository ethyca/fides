import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import { type RootState } from "~/app/store";

export type Suggestions = "showing" | "hiding" | "reset";

type State = {
  suggestions: Suggestions;
};
const initialState: State = {
  suggestions: "hiding",
};

export const dictSuggestionsSlice = createSlice({
  name: "dictSuggestions",
  initialState,
  reducers: {
    toggleSuggestions: (draftState) => {
      draftState.suggestions =
        draftState.suggestions === "hiding" ? "showing" : "hiding";
    },
    setSuggestions: (draftState, action: PayloadAction<Suggestions>) => {
      draftState.suggestions = action.payload;
    },
    resetSuggestions: (draftState) => {
      draftState.suggestions = "reset";
    },
  },
});

export const { toggleSuggestions, setSuggestions, resetSuggestions } =
  dictSuggestionsSlice.actions;

const selectDictSuggestionSlice = (state: RootState) => state.dictSuggestions;

export const selectSuggestions = createSelector(
  selectDictSuggestionSlice,
  (state) => state.suggestions
);
