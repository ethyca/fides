import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { DEFAULT_ORGANIZATION_FIDES_KEY } from "~/features/organization";
import { Organization, System } from "~/types/api";

import { REVIEW_STEPS, STEPS } from "./constants";

export interface State {
  step: number;
  reviewStep: number;
  organization?: Organization;
  /**
   * The system that the user is currently manually creating.
   */
  systemToCreate: System | null;
  /**
   * The systems that were returned by a system scan, some of which the user will select for review.
   * These are persisted to the backend after the "Describe" step.
   */
  systemsForReview?: System[];
}

const initialState: State = {
  step: 1,
  reviewStep: 1,
  systemToCreate: null,
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
    setOrganization: (draftState, action: PayloadAction<Organization>) => {
      draftState.organization = action.payload;
    },
    setSystemToCreate: (draftState, action: PayloadAction<System>) => {
      draftState.systemToCreate = action.payload;
    },
    setSystemsForReview: (draftState, action: PayloadAction<System[]>) => {
      draftState.systemsForReview = action.payload;
    },
    chooseSystemsForReview: (draftState, action: PayloadAction<string[]>) => {
      const fidesKeySet = new Set(action.payload);
      draftState.systemsForReview = (draftState.systemsForReview ?? []).filter(
        (system) => fidesKeySet.has(system.fides_key)
      );
    },
  },
});

export const {
  changeStep,
  changeReviewStep,
  setSystemToCreate,
  setOrganization,
  setSystemsForReview,
  chooseSystemsForReview,
} = slice.actions;

export const { reducer } = slice;

const selectConfigWizard = (state: RootState) => state.configWizard;

export const selectStep = createSelector(
  selectConfigWizard,
  (state) => state.step
);

export const selectReviewStep = createSelector(
  selectConfigWizard,
  (state) => state.reviewStep
);

export const selectOrganizationFidesKey = createSelector(
  selectConfigWizard,
  (state) => state.organization?.fides_key ?? DEFAULT_ORGANIZATION_FIDES_KEY
);

export const selectSystemToCreate = createSelector(
  selectConfigWizard,
  (state) => state.systemToCreate
);

export const selectSystemsForReview = createSelector(
  selectConfigWizard,
  (state) => state.systemsForReview ?? []
);
