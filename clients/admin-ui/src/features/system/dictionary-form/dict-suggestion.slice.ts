import { createSelector, createSlice,PayloadAction } from "@reduxjs/toolkit";

import { RootState } from "~/app/store";
import { plusApi } from "~/features/plus/plus.slice";
import { DictEntry, Page } from "~/features/plus/types";
import { TestStatus } from "~/types/api";

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

const EMPTY_DICT_ENTRY = undefined;
export const selectDictEntry = (vendorId: number) =>
  createSelector(
    [
      (RootState) => RootState,
      plusApi.endpoints.getAllDictionaryEntries.select(),
    ],
    (RootState, { data }) => {
      const dictEntry = data?.items.find(
        (d) => d.id.toString() === vendorId.toString()
      );

      return dictEntry || EMPTY_DICT_ENTRY;
    }
  );
