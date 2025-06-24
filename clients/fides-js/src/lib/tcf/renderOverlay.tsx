import { h, render } from "preact";

import { PrivacyExperienceMinimal } from "~/fides";

import { TcfOverlay } from "../../components/tcf/TcfOverlay";
import { RenderOverlayType } from "../../components/types";
import { I18nProvider } from "../i18n/i18n-context";
import { EventProvider } from "../providers/event-context";
import { GVLProvider } from "./gvl-context";
import { loadTcfMessagesFromFiles } from "./i18n/tcf-i18n-utils";
import { VendorButtonProvider } from "./vendor-button-context";

export const renderOverlay: RenderOverlayType = (props, parent) => {
  /**
   * Prior to rendering the TcfOverlay, load all the TCF-specific static strings
   * into the i18n message catalog. By deferring this until now, we allow the
   * base bundle to fully initialize i18n with the generic strings, but only
   * load the TCF-specific ones when needed, which reduces the default fides.js
   * bundle size by over 20kb!
   */
  const { i18n, ...overlayProps } = props;
  loadTcfMessagesFromFiles(i18n);

  render(
    <I18nProvider i18nInstance={i18n}>
      <GVLProvider>
        <VendorButtonProvider>
          <EventProvider>
            <TcfOverlay
              experienceMinimal={
                overlayProps.experience as PrivacyExperienceMinimal
              }
              {...overlayProps}
            />
          </EventProvider>
        </VendorButtonProvider>
      </GVLProvider>
    </I18nProvider>,
    parent,
  );
};
