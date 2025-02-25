import { CmpApi } from "@iabgpp/cmpapi";

import { FIDES_SEPARATOR } from "./tcf/constants";
import { VendorSources } from "./tcf/vendors";

/** Default GPP string to use when no CmpApi is provided or when it returns no string */
export const DEFAULT_GPP_STRING = "DBAA";

/**
 * Decodes a Fides string into its component parts.
 *
 * The Fides string format is: `TC_STRING,AC_STRING,GPP_STRING` where:
 * - TC_STRING: The TCF (Transparency & Consent Framework) string
 * - AC_STRING: The Additional Consent string, which is derived from TC_STRING
 * - GPP_STRING: The Global Privacy Platform string
 *
 * Rules:
 * 1. If the string is empty or undefined, all parts are empty strings
 * 2. If only one part exists, it's treated as the TC string
 * 3. AC string can only exist if TC string exists (as it's derived from TC)
 * 4. GPP string is independent and can exist with or without TC/AC strings
 *
 * @example
 * // Complete string with all parts
 * decodeFidesString("CPzvOIA.IAAA,1~2.3.4,DBABLA~BVAUAAAAAWA.QA")
 * // Returns { tc: "CPzvOIA.IAAA", ac: "1~2.3.4", gpp: "DBABLA~BVAUAAAAAWA.QA" }
 *
 * // TC string only
 * decodeFidesString("CPzvOIA.IAAA")
 * // Returns { tc: "CPzvOIA.IAAA", ac: "", gpp: "" }
 *
 * // GPP string only (with empty TC and AC)
 * decodeFidesString(",,DBABLA~BVAUAAAAAWA.QA")
 * // Returns { tc: "", ac: "", gpp: "DBABLA~BVAUAAAAAWA.QA" }
 *
 * @param fidesString - The combined Fides string to decode
 * @returns An object containing the decoded TC, AC, and GPP strings
 */
export const decodeFidesString = (fidesString: string) => {
  if (!fidesString) {
    return { tc: "", ac: "", gpp: "" };
  }

  const split = fidesString.split(FIDES_SEPARATOR);

  if (split.length === 1) {
    return { tc: split[0], ac: "", gpp: "" };
  }

  const [tc = "", ac = "", gpp = ""] = split;
  if (tc === "") {
    return { tc: "", ac: "", gpp };
  }

  return { tc, ac, gpp };
};

/**
 * Given an AC string, return a list of its ids, encoded
 *
 * @example
 * // returns [gacp.1, gacp.2, gacp.3]
 * idsFromAcString("1~1.2.3")
 */
export const idsFromAcString = (acString: string) => {
  const isValidAc = /\d~/;
  if (!acString) {
    return [];
  }
  if (!isValidAc.test(acString)) {
    fidesDebugger(`Received invalid AC string "${acString}", returning no ids`);
    return [];
  }
  const split = acString.split("~");
  if (split.length !== 2) {
    return [];
  }

  const ids = split[1].split(".");
  if (ids.length === 1 && ids[0] === "") {
    return [];
  }
  return ids.map((id) => `${VendorSources.AC}.${id}`);
};

/**
 * Formats the fides_string with the GPP string from the CMP API.
 * In a TCF experience, appends the GPP string as the third part.
 * In a non-TCF experience, uses empty strings for TCF and AC parts.
 * @param cmpApi Optional GPP CMP API instance. If not provided, uses DEFAULT_GPP_STRING
 * @returns The formatted fides_string
 */
export const formatFidesStringWithGpp = (cmpApi?: CmpApi): string => {
  const gppString = cmpApi?.getGppString() || DEFAULT_GPP_STRING;

  // In a TCF experience, append to existing string
  if (window.Fides.options.tcfEnabled) {
    const parts = window.Fides.fides_string?.split(FIDES_SEPARATOR) || [];
    // Ensure we have at least 2 parts (TCF and AC strings)
    while (parts.length < 2) {
      parts.push("");
    }
    // Add GPP string as third part
    parts[2] = gppString;
    return parts.join(FIDES_SEPARATOR);
  }

  // In a non-TCF experience, use empty strings for TCF and AC parts
  return `,,${gppString}`;
};
