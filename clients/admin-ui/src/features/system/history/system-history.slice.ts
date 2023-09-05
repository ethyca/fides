import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import { type RootState } from "~/app/store";

type State = {
  currentPage: number;
};

const initialState: State = {
  currentPage: 1,
};

export const systemHistorySlice = createSlice({
  name: 'systemHistory',
  initialState,
  reducers: {
    setCurrentPage: (draftState, action: PayloadAction<number>) => {
      draftState.currentPage = action.payload;
    },
  }
});

export const { setCurrentPage } = systemHistorySlice.actions;

const selectSystemHistorySlice = (state: RootState) => state.systemHistory;

export const selectCurrentSystemHistoryPage = createSelector(
  selectSystemHistorySlice,
  (state) => state.currentPage
);
