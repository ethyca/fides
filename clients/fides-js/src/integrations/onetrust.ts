/**
 * OneTrust Integration
 *
 * Utilities for reading OneTrust consent state and diagnostics.
 */

import { OneTrustProvider } from "../lib/consent-migration/onetrust";
import { getCookieByName } from "../lib/cookie";

export interface OneTrustStatus {
  detected: boolean;
  cookiePresent: boolean;
  activeGroups?: string[];
  categoriesConsent?: Record<string, boolean>;
  rawCookieValue?: string;
  parseError?: string;
}

/**
 * Get OneTrust status and diagnostics.
 *
 * Checks for OptanonConsent cookie and parses active consent groups.
 *
 * @returns OneTrust status object
 *
 * @example
 * ```javascript
 * const status = Fides.onetrust.status();
 *
 * if (status.detected) {
 *   console.log('OneTrust categories:', status.activeGroups);
 *   // ['C0001', 'C0002', 'C0003', 'C0004']
 *
 *   console.log('Consent by category:', status.categoriesConsent);
 *   // { C0001: true, C0002: false, C0003: true, C0004: false }
 * } else {
 *   console.log('OneTrust not detected');
 * }
 * ```
 */
export const status = (): OneTrustStatus => {
  const provider = new OneTrustProvider();
  const cookieValue = provider.getConsentCookie();

  if (!cookieValue) {
    return {
      detected: false,
      cookiePresent: false,
    };
  }

  const result: OneTrustStatus = {
    detected: true,
    cookiePresent: true,
    rawCookieValue: cookieValue,
  };

  try {
    // Parse the groups parameter
    const params = cookieValue.split("&");
    let groupsParam = "";

    params.forEach((param) => {
      const [key, value] = param.split("=");
      if (key === "groups") {
        groupsParam = value;
      }
    });

    if (groupsParam) {
      const groups = groupsParam.split(",");
      const activeGroups: string[] = [];
      const categoriesConsent: Record<string, boolean> = {};

      groups.forEach((group) => {
        const [category, status] = group.split(":");
        activeGroups.push(category);
        categoriesConsent[category] = status === "1";
      });

      result.activeGroups = activeGroups;
      result.categoriesConsent = categoriesConsent;
    } else {
      result.parseError = "No 'groups' parameter found in OptanonConsent cookie";
    }
  } catch (error) {
    result.parseError = `Failed to parse OneTrust cookie: ${error}`;
  }

  return result;
};
