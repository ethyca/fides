import { h, render } from "preact";

import NoticeOverlay from "../components/notices/NoticeOverlay";
import { RenderOverlayType } from "../components/types";
import { I18nProvider } from "./i18n/i18n-context";
import { EventProvider } from "./providers/event-context";

export const renderOverlay: RenderOverlayType = (props, parent) => {
  const { i18n, ...overlayProps } = props;
  render(
    <I18nProvider i18nInstance={i18n}>
      <EventProvider>
        <NoticeOverlay {...overlayProps} />
      </EventProvider>
    </I18nProvider>,
    parent,
  );
};
