import { useSidePanelContext } from "../SidePanelContext";

export const useSidePanelCollapse = () => {
  const { collapsed, toggleCollapsed, isOverlay } = useSidePanelContext();
  return { collapsed, toggleCollapsed, isOverlay };
};
