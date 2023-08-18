import { ContainerNode, render, h } from "preact";
import TcfOverlay from "../../components/tcf/TcfOverlay";
import { OverlayProps } from "../../components/types";

export const renderOverlay = (props: OverlayProps, parent: ContainerNode) => {
  render(<TcfOverlay {...props} />, parent);
};
