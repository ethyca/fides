import { ContainerNode, render, h } from "preact";
import { I18nProvider } from "../../lib/i18n/i18n-context";
import TcfOverlay from "../../components/tcf/TcfOverlay";
import { OverlayProps } from "../../components/types";

import { loadTcfMessagesFromFiles } from "./i18n/tcf-i18n-utils";

export const renderOverlay = (props: OverlayProps, parent: ContainerNode) => {
  /**
   * Prior to rendering the TcfOverlay, load all the TCF-specific static strings
   * into the i18n message catalog. By deferring this until now, we allow the
   * base bundle to fully initialize i18n with the generic strings, but only
   * load the TCF-specific ones when needed, which reduces the default fides.js
   * bundle size by over 20kb!
   */
  const { i18n } = props;
  loadTcfMessagesFromFiles(i18n);

  render(
    <I18nProvider>
      <TcfOverlay {...props} />
    </I18nProvider>,
    parent
  );
};
