/**
 * The path where the GPP extension bundle is located,
 * likely served by the privacy center
 */
const GPP_EXT_PATH = "/gpp-ext.js";

export const setupExtensions = () => {
  if (window.Fides.options.gppEnabled) {
    import(GPP_EXT_PATH).catch((e) => {
      // eslint-disable-next-line no-console
      console.error("Unable to import GPP extension", e);
    });
  }
};
