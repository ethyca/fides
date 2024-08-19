import { ContainerNode, h, render } from "preact";

import NoticeOverlay from "../components/notices/NoticeOverlay";
import { OverlayProps } from "../components/types";
import { I18nProvider } from "./i18n/i18n-context";

export const renderOverlay = (props: OverlayProps, parent: ContainerNode) => {
  render(
    <I18nProvider>
      <NoticeOverlay {...props} />
    </I18nProvider>,
    parent,
  );
};
