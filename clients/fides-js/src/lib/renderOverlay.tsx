import { render } from "preact";

import NoticeOverlay from "../components/notices/NoticeOverlay";
import { RenderOverlayType } from "../components/types";
import { I18nProvider } from "./i18n/i18n-context";
import { EventProvider } from "./providers/event-context";
import { FidesGlobalProvider } from "./providers/fides-global-context";
import { LiveRegionProvider } from "./providers/live-region-context";

export const renderOverlay: RenderOverlayType = (props, parent) => {
  const { i18n, initializedFides } = props;
  render(
    <I18nProvider i18nInstance={i18n}>
      <FidesGlobalProvider initializedFides={initializedFides}>
        <EventProvider>
          <LiveRegionProvider>
            <NoticeOverlay />
          </LiveRegionProvider>
        </EventProvider>
      </FidesGlobalProvider>
    </I18nProvider>,
    parent,
  );
};
