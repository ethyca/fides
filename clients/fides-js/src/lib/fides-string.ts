import { CmpApi } from "@iabgpp/cmpapi";

import { FIDES_SEPARATOR } from "./tcf/constants";
import { VendorSources } from "./tcf/vendors";

export interface NoticeConsentData {
  [noticeKey: string]: boolean;
}

export interface DecodedFidesString {
  tc: string;
  ac: string;
  gpp: string;
  noticeConsent: string; // Base64 encoded Notice Consent String
}

/**
 * Decodes a Fides string into its component parts.
 *
 * The Fides string format is: `TC_STRING,AC_STRING,GPP_STRING,NOTICE_CONSENT_STRING` where:
 * - TC_STRING: The TCF (Transparency & Consent Framework) string
 * - AC_STRING: The Additional Consent string, which is derived from TC_STRING
 * - GPP_STRING: The Global Privacy Platform string
 * - NOTICE_CONSENT_STRING: A Base64 encoded stringified JSON object containing notice consent preferences
 *
 * Rules:
 * 1. If the string is empty or undefined, all parts are empty strings
 * 2. If only one part exists, it's treated as the TC string
 * 3. AC string can only exist if TC string exists (as it's derived from TC)
 * 4. GPP string is independent and can exist with or without TC/AC strings
 * 5. Notice Consent String is an optional part that can be used to pass notice consent preferences programatically
 *
 * @example
 * // Complete string with all parts
 * decodeFidesString("CPzvOIA.IAAA,1~2.3.4,DBABLA~BVAUAAAAAWA.QA,eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjoxLCJhbmFseXRpY3MiOjB9")
 * // Returns { tc: "CPzvOIA.IAAA", ac: "1~2.3.4", gpp: "DBABLA~BVAUAAAAAWA.QA", noticeConsent: "eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjoxLCJhbmFseXRpY3MiOjB9" }
 *
 * // TC string only
 * decodeFidesString("CPzvOIA.IAAA")
 * // Returns { tc: "CPzvOIA.IAAA", ac: "", gpp: "", noticeConsent: "" }
 *
 * // GPP string only (with empty TC and AC)
 * decodeFidesString(",,DBABLA~BVAUAAAAAWA.QA")
 * // Returns { tc: "", ac: "", gpp: "DBABLA~BVAUAAAAAWA.QA", noticeConsent: "" }
 *
 * @param fidesString - The combined Fides string to decode
 * @returns An object containing the decoded TC, AC, GPP, and Notice Consent strings
 */
export const decodeFidesString = (fidesString: string): DecodedFidesString => {
  if (!fidesString) {
    return { tc: "", ac: "", gpp: "", noticeConsent: "" };
  }

  const [tc = "", ac = "", gpp = "", noticeConsent = ""] =
    fidesString.split(FIDES_SEPARATOR);
  // If there's no TC, remove AC
  return tc
    ? { tc, ac, gpp, noticeConsent }
    : { tc: "", ac: "", gpp, noticeConsent };
};

/**
 * Given an AC string, return a list of its ids, encoded
 *
 * @example
 * // returns [gacp.1, gacp.2, gacp.3]
 * idsFromAcString("1~1.2.3")
 */
export const idsFromAcString = (acString: string) => {
  if (!acString?.match(/\d~[0-9.]+$/)) {
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
 * @param cmpApi Optional GPP CMP API instance.
 * @returns The formatted fides_string
 */
export const formatFidesStringWithGpp = (cmpApi: CmpApi): string => {
  const gppString = cmpApi.getGppString();
  return window.Fides.options.tcfEnabled
    ? [...(window.Fides.fides_string?.split(FIDES_SEPARATOR) || []), "", ""]
        .slice(0, 2)
        .concat(gppString || "")
        .join(FIDES_SEPARATOR)
    : `,${gppString ? `,${gppString}` : ""}`;
};
