import { FidesEvent } from "../events";
import { FIDES_SEPARATOR } from "./constants";

/**
 * Extract just the TC string from a FidesEvent. This will also remove parts of the
 * TC string that we do not want to surface with our CMP API events, such as
 * `vendors_disclosed` and our own AC string addition.
 */
export const fidesEventToTcString = (event: FidesEvent) => {
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
