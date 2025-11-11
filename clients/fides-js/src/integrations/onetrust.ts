/**
 * OneTrust Integration
 *
 * Utilities for reading OneTrust consent state and diagnostics.
 */

import { OneTrustProvider } from "../lib/consent-migration/onetrust";
import { NoticeConsent } from "../lib/consent-types";

/**
 * Standard OneTrust category to Fides notice mapping
 * Used for reading OneTrust consent during migration
 */
export const DEFAULT_ONETRUST_TO_FIDES_MAPPING: Record<string, string> = {
  C0001: "essential",
  C0002: "performance",
  C0003: "functional",
  C0004: "advertising",
};

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

/**
 * Read OneTrust consent and convert to Fides format.
 *
 * Uses standard C0001-C0004 → essential/performance/functional/advertising mapping.
 *
 * @returns Fides-compatible consent object, or null if OneTrust not found
 *
 * @example
 * ```javascript
 * const consent = Fides.onetrust.readConsent();
 * if (consent) {
 *   console.log('OneTrust consent:', consent);
 *   // { essential: true, performance: false, functional: true, advertising: false }
 * }
 * ```
 */
export const readConsent = (): NoticeConsent | null => {
  const provider = new OneTrustProvider();

  try {
    const cookieValue = provider.getConsentCookie();
    if (!cookieValue) {
      return null;
    }

    // Use OneTrustProvider's parsing logic with default mapping
    const fidesConsent = provider.convertToFidesConsent(cookieValue, {
      otFidesMapping: JSON.stringify(
        Object.entries(DEFAULT_ONETRUST_TO_FIDES_MAPPING).reduce(
          (acc, [otCat, fidesKey]) => {
            acc[otCat] = [fidesKey]; // OneTrustProvider expects array of keys
            return acc;
          },
          {} as Record<string, string[]>,
        ),
      ),
    });

    return fidesConsent || null;
  } catch (error) {
    console.error("[Fides OneTrust] Error reading consent:", error);
    return null;
  }
};
