import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";

interface SidePanelState {
  collapsed: boolean;
  isOverlay: boolean;
  panelWidth: number;
}

const initialState: SidePanelState = {
  collapsed: false,
  isOverlay: false,
  panelWidth: 220,
};

export const sidePanelSlice = createSlice({
  name: "sidePanel",
  initialState,
  reducers: {
    toggleCollapsed(draftState) {
      draftState.collapsed = !draftState.collapsed;
    },
    setCollapsed(draftState, action) {
      draftState.collapsed = action.payload;
    },
    setIsOverlay(draftState, action) {
      draftState.isOverlay = action.payload;
    },
  },
});

const selectSidePanel = (state: RootState) => state.sidePanel;

export const selectCollapsed = createSelector(
  selectSidePanel,
  (state) => state.collapsed,
);

export const selectIsOverlay = createSelector(
  selectSidePanel,
  (state) => state.isOverlay,
);

export const selectPanelWidth = createSelector(
  selectSidePanel,
  (state) => state.panelWidth,
);

export const { toggleCollapsed, setCollapsed, setIsOverlay } =
  sidePanelSlice.actions;

export const { reducer } = sidePanelSlice;
