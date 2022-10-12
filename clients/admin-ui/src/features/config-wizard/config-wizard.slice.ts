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
   * The systems that were returned by a system scan, some of which the user will select for review.
   * These are persisted to the backend after the "Describe" step.
   */
  systemsForReview?: System[];
  /**
   * The system that is currently being put through the review steps. It is persisted
   * on the "Describe" step and then updated with additional info. Once it's registered,
   * the next `systemForReview` is swapped in, if any.
   */
  systemInReview?: System;
}

const initialState: State = {
  step: 0,
  reviewStep: 1,
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
    reviewManualSystem: (draftState) => {
      draftState.systemInReview = undefined;
      draftState.reviewStep = 1;
    },
    /**
     * Move to the next system that needs review, if any.
     */
    continueReview: (draftState) => {
      const { systemInReview, systemsForReview } = draftState;
      if (!(systemInReview && systemsForReview)) {
        throw new Error(
          "Can't finish system review when there is no review in progress."
        );
      }

      const reviewIndex = systemsForReview.findIndex(
        (s) => s.fides_key === systemInReview.fides_key
      );
      if (reviewIndex < 0) {
        throw new Error("The system in review couldn't be found by fides key.");
      }

      const nextIndex = reviewIndex + 1;
      if (nextIndex < systemsForReview.length) {
        // If there is another system to review, swap it in.
        draftState.systemInReview = systemsForReview[nextIndex];
      } else {
        // Otherwise move to the next wizard step.
        draftState.systemInReview = undefined;
        draftState.step += 1;
      }

      // Always reset the review step
      draftState.reviewStep = 1;
    },
    setOrganization: (draftState, action: PayloadAction<Organization>) => {
      draftState.organization = action.payload;
    },
    setSystemInReview: (draftState, action: PayloadAction<System>) => {
      const systemInReview = action.payload;
      const { systemsForReview = [] } = draftState;

      // Whenever the in-progress system is updated, ensure the object in the array
      // is updated in tandem.
      const reviewIndex = systemsForReview.findIndex(
        (s) => s.fides_key === systemInReview.fides_key
      );
      if (reviewIndex < 0) {
        systemsForReview.push(systemInReview);
      } else {
        systemsForReview[reviewIndex] = systemInReview;
      }

      draftState.systemInReview = systemInReview;
      draftState.systemsForReview = systemsForReview;
    },
    setSystemsForReview: (draftState, action: PayloadAction<System[]>) => {
      draftState.systemsForReview = action.payload;
    },
    chooseSystemsForReview: (draftState, action: PayloadAction<string[]>) => {
      const fidesKeySet = new Set(action.payload);
      draftState.systemsForReview = (draftState.systemsForReview ?? []).filter(
        (system) => fidesKeySet.has(system.fides_key)
      );
      // Start reviewing the first system. (ESLint false positive.)
      // eslint-disable-next-line prefer-destructuring
      draftState.systemInReview = draftState.systemsForReview[0];
    },
    /**
     * Reset the wizard to its initial state, except for the organization which will probably
     * be the same if the user comes back.
     */
    reset: (draftState) => ({
      ...initialState,
      organization: draftState.organization,
    }),
  },
});

export const {
  changeStep,
  changeReviewStep,
  continueReview,
  reset,
  reviewManualSystem,
  setSystemInReview,
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

export const selectSystemInReview = createSelector(
  selectConfigWizard,
  (state) => state.systemInReview
);

export const selectSystemsForReview = createSelector(
  selectConfigWizard,
  (state) => state.systemsForReview ?? []
);
