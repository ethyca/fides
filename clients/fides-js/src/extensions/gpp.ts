/**
 * Extension for GPP
 *
 * Usage:
 * Include as a script tag as early as possible (even before fides.js)
 */

import { makeStub } from "../lib/gpp/stub";

export const initializeGppCmpApi = () => {
  makeStub();

  // TODO: instantiate a real (non-stubbed) GPP CMP API and set up listeners
};

initializeGppCmpApi();
