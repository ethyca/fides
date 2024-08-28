import { ContainerNode, h, render } from "preact";

import NoticeOverlay from "../components/notices/NoticeOverlay";
import { OverlayProps } from "../components/types";
import { I18nProvider } from "./i18n/i18n-context";

export const renderOverlay = (props: OverlayProps, parent: ContainerNode) => {
  const { i18n } = props;
  render(
    <I18nProvider i18nInstance={i18n}>
      <NoticeOverlay {...props} />
    </I18nProvider>,
    parent,
  );
};
