declare global {
  interface Window {
    dataLayer?: any[];
  }
}

/**
 * Call Fides.gtm to configure Google Tag Manager. The user's consent choices will be
 * pushed into GTM's `dataLayer` under `Fides.consent`.
 */
export const gtm = () => {
  const dataLayer = window.dataLayer ?? [];
  window.dataLayer = dataLayer;
  dataLayer.push({
    Fides: {
      consent: window.Fides.consent,
    },
  });
};
