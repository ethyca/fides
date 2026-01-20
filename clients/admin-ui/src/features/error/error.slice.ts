import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type ErrorState = {
  errors: any[];
};

const initialState: ErrorState = {
  errors: [],
};

export const errorSlice = createSlice({
  name: "error",
  initialState,
  reducers: {
    addError(draftState, { payload }: PayloadAction<any>) {
      draftState.errors = [...draftState.errors, payload];
    },
  },
});
