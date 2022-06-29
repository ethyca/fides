import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { AppState } from "~/app/store";

import { REVIEW_STEPS, STEPS } from "./constants";

export interface State {
  step: number;
  reviewStep: number;
  systemFidesKey: string;
}

const initialState: State = {
  step: 1,
  reviewStep: 1,
  systemFidesKey: "",
};

export const slice = createSlice({
  name: "configWizard",
  initialState,
  reducers: {
    /**
     * With no argument: increment to the next step.
     * With an argument: switch to that step.
     */
    changeStep: (draftState, action: PayloadAction<number | undefined>) => {
      const step = action.payload;

      if (step === undefined) {
        draftState.step += 1;
      } else {
        draftState.step = step;
      }

      // Ensure the step number stays in the valid range.
      if (draftState.step < 1) {
        draftState.step = 1;
      } else if (STEPS.length <= draftState.step) {
        draftState.step = STEPS.length - 1;
      }
    },
    /**
     * With no argument: increment to the next review step.
     * With an argument: switch to that review step.
     */
    changeReviewStep: (
      draftState,
      action: PayloadAction<number | undefined>
    ) => {
      const reviewStep = action.payload;

      if (reviewStep === undefined) {
        draftState.reviewStep += 1;
      } else {
        draftState.reviewStep = reviewStep;
      }

      // Ensure the number stays in the valid range.
      if (draftState.reviewStep < 1) {
        draftState.reviewStep = 1;
      } else if (REVIEW_STEPS <= draftState.reviewStep) {
        draftState.reviewStep = REVIEW_STEPS - 1;
      }
    },
    setSystemFidesKey: (draftState, action: PayloadAction<string>) => {
      draftState.systemFidesKey = action.payload;
    },
  },
});

export const { changeStep, changeReviewStep, setSystemFidesKey } =
  slice.actions;

export const { reducer } = slice;

export const selectStep = (state: AppState) => state.configWizard.step;
export const selectReviewStep = (state: AppState) =>
  state.configWizard.reviewStep;
export const selectSystemFidesKey = (state: AppState) =>
  state.configWizard.systemFidesKey;
