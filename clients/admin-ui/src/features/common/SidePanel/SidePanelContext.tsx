import React, { useCallback, useEffect } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";

import {
  selectCollapsed,
  selectIsOverlay,
  selectPanelWidth,
  setCollapsed,
  setIsOverlay,
  toggleCollapsed as toggleCollapsedAction,
} from "./sidepanel.slice";

interface SidePanelContextValue {
  collapsed: boolean;
  toggleCollapsed: () => void;
  isOverlay: boolean;
  panelWidth: number;
}

/**
 * Hook to access side panel state from the Redux store.
 * Also sets up the resize listener for responsive behavior.
 */
export const useSidePanelContext = (): SidePanelContextValue => {
  const dispatch = useAppDispatch();
  const collapsed = useAppSelector(selectCollapsed);
  const isOverlay = useAppSelector(selectIsOverlay);
  const panelWidth = useAppSelector(selectPanelWidth);

  const toggleCollapsed = useCallback(() => {
    dispatch(toggleCollapsedAction());
  }, [dispatch]);

  return { collapsed, toggleCollapsed, isOverlay, panelWidth };
};

/**
 * Provider that sets up the resize listener for responsive panel behavior.
 * Must be rendered inside the Redux Provider.
 */
export const SidePanelProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const dispatch = useAppDispatch();

  useEffect(() => {
    const handleResize = () => {
      const shouldOverlay = window.innerWidth < 992;
      dispatch(setIsOverlay(shouldOverlay));
      if (shouldOverlay) {
        dispatch(setCollapsed(true));
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [dispatch]);

  return <>{children}</>;
};
