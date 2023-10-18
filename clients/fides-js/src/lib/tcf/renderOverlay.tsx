import { ContainerNode, render, h } from "preact";
import TcfOverlay from "../../components/tcf/TcfOverlay";
import NoticeOverlay from "../../components/notices/NoticeOverlay";
import { OverlayProps } from "../../components/types";
import { isTcfExperience } from "./utils";

export const renderOverlay = (props: OverlayProps, parent: ContainerNode) => {
  if (isTcfExperience(props.experience)) {
    render(<TcfOverlay {...props} />, parent);
    return;
  }
  render(<NoticeOverlay {...props} />, parent);
};
