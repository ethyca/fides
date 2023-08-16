import { ContainerNode, render, h } from "preact";
import NoticeOverlay from "../components/notices/NoticeOverlay";
import { OverlayProps } from "../components/types";

export const renderOverlay = (props: OverlayProps, parent: ContainerNode) => {
  render(<NoticeOverlay {...props} />, parent);
};
