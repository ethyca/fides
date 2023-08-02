import { PayloadAction, createSelector, createSlice } from "@reduxjs/toolkit";
import { RootState } from "~/app/store";
import { plusApi } from "~/features/plus/plus.slice";
import { DictEntry, Page } from "~/features/plus/types";
import { TestStatus } from "~/types/api";

type State = {
  isShowingSuggestions: boolean;
};
const initialState: State = {
  isShowingSuggestions: false,
};

export const dictSuggestionsSlice = createSlice({
  name: "dictSuggestions",
  initialState,
  reducers: {
    toggleIsShowingSuggestions: (
      draftState
      // action: PayloadAction<void>
    ) => {
      draftState.isShowingSuggestions = !draftState.isShowingSuggestions;
    },
  },
});

export const { toggleIsShowingSuggestions } = dictSuggestionsSlice.actions;

const selectDictSuggestionSlice = (state: RootState) => state.dictSuggestions;

const EMPTY_DICT_ENTRY = null;
export const selectDictEntry = (vendorId: number) =>
  createSelector(
    [
      (RootState) => RootState,
      plusApi.endpoints.getAllDictionaryEntries.select(),
    ],
    (RootState, { data }) =>
      data
        ? data.items.find((d) => d.id.toString() === vendorId.toString())
        : EMPTY_DICT_ENTRY
  );
