import { ContainerNode, render, h } from "preact";
import { I18nProvider } from "../lib/i18n/i18n-context";
import NoticeOverlay from "../components/notices/NoticeOverlay";
import { OverlayProps } from "../components/types";

export const renderOverlay = (props: OverlayProps, parent: ContainerNode) => {
  render(
    <I18nProvider>
      <NoticeOverlay {...props} />
    </I18nProvider>,
    parent
  );
};
