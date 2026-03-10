import { FidesEvent } from "../events";
import { decodeFidesString } from "../fides-string";

/**
 * Extract just the TC string from a FidesEvent.
 *
 * Returns a string to be used for the `CmpApi` class from `@iabtechlabtcf/cmpapi`, which expects one of three input strings:
 *  - Encoded TC string (e.g. "CP1sGZVP1..."), which will be decoded into `TCData` and set `gdprApplies = true`
 *  - Empty string (e.g. `""`), which will populate an empty `TCData`, but importantly set `gdprApplies = true`
 *  - Null string (e.g. `null`), which will also populate an empty `TCData`, but set `gdprApplies = false`
 *
 * Therefore we should only use a `null` string when we specifically want to set `gdprApplies = false`!
 *
 * See the `CmpApi` docs for more details: https://github.com/InteractiveAdvertisingBureau/iabtcf-es/blob/master/modules/cmpapi/README.md#trigger-change-event
 */
export const extractTCStringForCmpApi = (event: FidesEvent): string | null => {
  // Only return null (gdprApplies = false) if explicitly set to false.
  // For TCF experiences, gdprApplies should default to true.
  if (window.Fides?.options?.fidesTcfGdprApplies === false) {
    // A `null` TC string means gdpr does not apply
    return null;
  }
  const { fides_string: cookieString } = event.detail;
  if (!cookieString) {
    return "";
  }
  const { tc } = decodeFidesString(cookieString);
  return tc ?? "";
};
