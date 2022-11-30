/**
 * This script defines the browser script entrypoint for Fides consent logic. It is distributed
 * as `fides-consent.js` and is accessed from the `Fides` global variable.
 */

import { getConsentCookie } from "./lib/cookie";

const Fides = {
  consent: getConsentCookie(),
};

export default Fides;
