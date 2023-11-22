import { FidesEvent } from "../events";
import { FIDES_SEPARATOR } from "./constants";

/**
 * Extract just the TC string from a FidesEvent. This will also remove parts of the
 * TC string that we do not want to surface with our CMP API events, such as
 * `vendors_disclosed` and our own AC string addition.
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
  if (!window.Fides.options.fidesTcfGdprApplies) {
    // A `null` TC string means gdpr does not apply
    return null;
  }
  const { fides_string: cookieString } = event.detail;
  if (cookieString) {
    // Remove the AC portion which is separated by FIDES_SEPARATOR
    const [tcString] = cookieString.split(FIDES_SEPARATOR);
    // We only want to return the first part of the tcString, which is separated by '.'
    // This means Publisher TC is not sent either, which is okay for now since we do not set it.
    // However, if we do one day set it, we would have to decode the string and encode it again
    // without vendorsDisclosed
    return tcString.split(".")[0];
  }
  return cookieString ?? "";
};
