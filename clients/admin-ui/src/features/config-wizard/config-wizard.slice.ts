import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { DEFAULT_ORGANIZATION_FIDES_KEY } from "~/features/organization";
import { Organization, System } from "~/types/api";

import { STEPS } from "./constants";
import { AddSystemMethods, SystemMethods } from "./types";

export interface State {
  step: number;
  organization?: Organization;
  /**
   * The systems that were returned by a system scan, some of which the user will select for review.
   * These are persisted to the backend after the "Describe" step.
   */
  systemsForReview?: System[];
  addSystemsMethod: AddSystemMethods;
}

const initialState: State = {
  step: 0,
  addSystemsMethod: SystemMethods.MANUAL,
};

export const configWizardSlice = createSlice({
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
      } else if (STEPS.length < draftState.step) {
        draftState.step = STEPS.length - 1;
      }
    },
    setOrganization: (draftState, action: PayloadAction<Organization>) => {
      draftState.organization = action.payload;
    },
    setSystemsForReview: (draftState, action: PayloadAction<System[]>) => {
      draftState.systemsForReview = action.payload;
    },
    chooseSystemsForReview: (draftState, action: PayloadAction<string[]>) => {
      const fidesKeySet = new Set(action.payload);
      draftState.systemsForReview = (draftState.systemsForReview ?? []).filter(
        (system) => fidesKeySet.has(system.fides_key),
      );
    },
    setAddSystemsMethod: (
      draftState,
      action: PayloadAction<AddSystemMethods>,
    ) => {
      draftState.addSystemsMethod = action.payload;
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
  reset,
  setOrganization,
  setSystemsForReview,
  chooseSystemsForReview,
  setAddSystemsMethod,
} = configWizardSlice.actions;

export const { reducer } = configWizardSlice;

const selectConfigWizard = (state: RootState) => state.configWizard;

export const selectStep = createSelector(
  selectConfigWizard,
  (state) => state.step,
);

export const selectOrganizationFidesKey = createSelector(
  selectConfigWizard,
  (state) => state.organization?.fides_key ?? DEFAULT_ORGANIZATION_FIDES_KEY,
);

export const selectSystemsForReview = createSelector(
  selectConfigWizard,
  (state) => state.systemsForReview ?? [],
);

export const selectAddSystemsMethod = createSelector(
  selectConfigWizard,
  (state) => state.addSystemsMethod,
);
