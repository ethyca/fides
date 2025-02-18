import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { useAppSelector } from "~/app/hooks";
import type { RootState } from "~/app/store";
import { Property } from "~/types/api";

interface PropertyState {
  property?: Property | null;
}
const initialState: PropertyState = {};

export const propertySlice = createSlice({
  name: "property",
  initialState,
  reducers: {
    /**
     * Load property, replacing the current state entirely.
     */
    loadProperty(
      draftState,
      { payload }: PayloadAction<Property | undefined | null>,
    ) {
      if (process.env.NODE_ENV === "development") {
        // eslint-disable-next-line no-console
        console.log("Loading Privacy Center property into Redux store...");
      }
      draftState.property = payload;
    },
  },
});

const selectProperty = (state: RootState) => state.property;
export const selectPropertyId = (state: RootState) =>
  state.property?.property?.id;
export const { reducer } = propertySlice;
export const { loadProperty } = propertySlice.actions;
export const useProperty = (): Property | undefined | null => {
  const { property } = useAppSelector(selectProperty);

  return property;
};
