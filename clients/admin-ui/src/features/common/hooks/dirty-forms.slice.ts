import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";

type FormState = {
  id: string;
  name: string;
  isDirty: boolean;
};

type DirtyFormStates = {
  forms: FormState[];
  isModalOpen: boolean;
};

const initialState: DirtyFormStates = {
  forms: [],
  isModalOpen: false,
};

// Settings slice
export const dirtyFormsSlice = createSlice({
  name: "dirtyForms",
  initialState,
  reducers: {
    registerForm(
      draftState,
      { payload }: PayloadAction<Pick<FormState, "name" | "id">>,
    ) {
      if (draftState.forms.filter((f) => f.id === payload.id).length === 0) {
        draftState.forms.push({ isDirty: false, ...payload });
      }
    },
    unregisterForm(
      draftState,
      { payload }: PayloadAction<Pick<FormState, "id">>,
    ) {
      const index = draftState.forms.map((f) => f.id).indexOf(payload.id);
      if (index > -1) {
        draftState.forms.splice(index, 1);
      }
    },
    /*
     * Updates the `dirty` state for any registered
     * form that is currently being tracked.
     */
    updateDirtyFormState(
      draftState,
      { payload }: PayloadAction<Pick<FormState, "id" | "isDirty">>,
    ) {
      const idx = draftState.forms.map((f) => f.id).indexOf(payload.id);
      if (idx > -1) {
        draftState.forms[idx].isDirty = payload.isDirty;
      }
    },
    openModal(draftState) {
      draftState.isModalOpen = true;
    },
    closeModal(draftState) {
      draftState.isModalOpen = false;
    },
  },
});

export const dirtyForms = (state: RootState) => state.dirtyForms;

export const selectAnyDirtyForms = createSelector(dirtyForms, (state) =>
  state.forms
    .filter((f) => f.isDirty === true)
    .map((f) => f.isDirty)
    .some((f) => f === true),
);

export const selectDirtyForms = createSelector(dirtyForms, (state) =>
  state.forms.filter((f) => f.isDirty === true),
);

export const selectIsModalOpen = createSelector(
  dirtyForms,
  (state) => state.isModalOpen,
);

export const {
  registerForm,
  unregisterForm,
  updateDirtyFormState,
  closeModal,
  openModal,
} = dirtyFormsSlice.actions;

export const { reducer } = dirtyFormsSlice;
