import { CmpApi } from "@iabgpp/cmpapi";

import { isValidAcString } from "./consent-utils";
import { FIDES_SEPARATOR } from "./tcf/constants";
import { VendorSources } from "./tcf/vendors";

export interface NoticeConsentData {
  [noticeKey: string]: boolean;
}

export interface DecodedFidesString {
  tc: string;
  ac: string;
  gpp: string;
  nc: string;
}

/**
 * Decodes a Fides string into its component parts.
 *
 * The Fides string format is: `TC_STRING,AC_STRING,GPP_STRING,NC_STRING` where:
 * - TC_STRING: The TCF (Transparency & Consent Framework) string
 * - AC_STRING: The Additional Consent string
 * - GPP_STRING: The Global Privacy Platform string
 * - NC_STRING: A Base64 encoded stringified JSON object containing Notice Consent preferences
 *
 * Rules:
 * 1. If the string is empty or undefined, all parts are empty strings
 * 2. If only one part exists, it's treated as the TC string
 * 3. AC string can only exist if TC string exists. An AC string will not be processed if the TC string is not present.
 * 4. GPP string is independent and can exist with or without other string parts
 * 5. Notice Consent String is an optional part that can be used to pass notice consent preferences programatically. This can also exist independently.
 *
 * @example
 * // Complete string with all parts
 * decodeFidesString("CPzvOIA.IAAA,2~2.3.4~dv.1.5,DBABLA~BVAUAAAAAWA.QA,eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjoxLCJhbmFseXRpY3MiOjB9")
 * // Returns { tc: "CPzvOIA.IAAA", ac: "2~2.3.4~dv.1.5", gpp: "DBABLA~BVAUAAAAAWA.QA", nc: "eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjoxLCJhbmFseXRpY3MiOjB9" }
 *
 * // TC string only
 * decodeFidesString("CPzvOIA.IAAA")
 * // Returns { tc: "CPzvOIA.IAAA", ac: "", gpp: "", nc: "" }
 *
 * // GPP string only (with empty TC and AC)
 * decodeFidesString(",,DBABLA~BVAUAAAAAWA.QA")
 * // Returns { tc: "", ac: "", gpp: "DBABLA~BVAUAAAAAWA.QA", nc: "" }
 *
 * // Notice Consent String only
 * decodeFidesString(",,,eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjoxLCJhbmFseXRpY3MiOjB9")
 * // Returns { tc: "", ac: "", gpp: "", nc: "eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjoxLCJhbmFseXRpY3MiOjB9" }
 *
 * @param fidesString - The combined Fides string to decode
 * @returns An object containing the decoded TC, AC, GPP, and Notice Consent strings
 */
export const decodeFidesString = (fidesString: string): DecodedFidesString => {
  if (!fidesString) {
    return { tc: "", ac: "", gpp: "", nc: "" };
  }

  const [tc = "", ac = "", gpp = "", nc = ""] =
    fidesString.split(FIDES_SEPARATOR);
  // If there's no TC, remove AC
  return tc ? { tc, ac, gpp, nc } : { tc: "", ac: "", gpp, nc };
};

/**
 * Given an AC string, return a list of its ids, encoded.
 * V2 AC strings include a list of disclosed vendors which we can ignore for the return value but
 * we do use to validate the AC string format. The consent id list is formatted the same as V1.
 *
 * @example // V1 AC string
 * consentIdsFromAcString("1~1.2.3")
 * // returns [gacp.1, gacp.2, gacp.3]
 *
 * @example // V2 AC string
 * consentIdsFromAcString("2~1.2.3~dv.4.5")
 * // returns [gacp.1, gacp.2, gacp.3]
 */
export const consentIdsFromAcString = (acString: string) => {
  const isValid = isValidAcString(acString);
  if (!isValid) {
    fidesDebugger(
      acString && `Received invalid AC string "${acString}", returning no ids`,
    );
    return [];
  }

  const [, ids = ""] = acString.split("~");
  return ids ? ids.split(".").map((id) => `${VendorSources.AC}.${id}`) : [];
};

/**
 * Formats the fides_string with the GPP string from the CMP API.
 * In a TCF experience, appends the GPP string as the third part.
 * In a non-TCF experience, uses empty strings for TCF and AC parts.
 * If the Notice Consent String is present, it will be preserved as the fourth part.
 * @param cmpApi Optional GPP CMP API instance.
 * @returns The formatted fides_string
 *
 * @example
 * TCF with Notice Consent: "TC,AC,GPP,NC" → Output: "TC,AC,GPP,NC"
 * TCF without Notice Consent: "TC,AC,GPP" → Output: "TC,AC,GPP"
 * Non-TCF with GPP: ",,GPP" → Output: ",,GPP"
 * Non-TCF with GPP and Notice Consent: ",,GPP,NC" → Output: ",,GPP,NC"
 */
export const formatFidesStringWithGpp = (
  cmpApi: CmpApi,
): string | undefined => {
  const gppString = cmpApi.getGppString();
  if (!gppString) {
    return window.Fides.fides_string;
  }
  const emptyStrings = new Array(4).fill("");
  const existingParts = (
    window.Fides.fides_string?.split(FIDES_SEPARATOR) || []
  ).concat(emptyStrings);
  const newParts = emptyStrings.map((part, index) => {
    if (index < 2) {
      return `${existingParts[index]},`;
    }
    if (index === 2) {
      return gppString;
    }
    if (index === 3 && existingParts[3]) {
      return `,${existingParts[3]}`;
    }
    return part;
  });
  return newParts.join("");
};
