/**
 * The path where the GPP extension bundle is located,
 * likely served by the privacy center
 */
const GPP_EXT_PATH = "/gpp-ext.js";

// DEFER(PROD#1361): Get if GPP is enabled from the backend
const GPP_ENABLED = false;

export const setupExtensions = () => {
  if (GPP_ENABLED) {
    import(GPP_EXT_PATH).catch((e) => {
      // eslint-disable-next-line no-console
      console.error("Unable to import GPP extension", e);
    });
  }
};
