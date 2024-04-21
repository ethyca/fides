import { ContainerNode, render, h } from "preact";
import { I18nProvider } from "../lib/i18n/i18n-context";
import NoticeOverlay from "../components/notices/NoticeOverlay";
import { OverlayProps } from "../components/types";

// TODO: remove
let _mounted: boolean = false;
let _parent: any = null;

export const renderOverlay = (props: OverlayProps, parent: ContainerNode) => {
  if (_mounted) {
    // eslint-disable-next-line no-console
    console.error("renderOverlay called when already mounted!");
    // Unmount any existing overlay 
    render(null, _parent);
  }

  render(
    <I18nProvider>
      <NoticeOverlay {...props} />
    </I18nProvider>,
    parent
  );
  //TODO: remove
  _mounted = true;
  _parent = parent;
};
