import {
  ConsentMethod,
  FidesInitOptionsOverrides,
  NoticeConsent,
  OtToFidesConsentMapping,
} from "../consent-types";
import { getCookieByName } from "../cookie";
import { ConsentMigrationProvider } from "./types";

/**
 * Standard OneTrust category to Fides notice mapping
 * Can be customized via otFidesMapping option
 */
export const DEFAULT_ONETRUST_TO_FIDES_MAPPING: Record<string, string> = {
  C0001: "essential",
  C0002: "performance",
  C0003: "functional",
  C0004: "advertising",
};

/**
 * OneTrust implementation of consent migration
 * Handles both reading OneTrust consent and writing Fides consent back to OneTrust
 */
export class OneTrustProvider implements ConsentMigrationProvider {
  readonly cookieName = "OptanonConsent";

  readonly migrationMethod = ConsentMethod.EXTERNAL_PROVIDER;

  getConsentCookie(): string | undefined {
    return getCookieByName(this.cookieName);
  }

  convertToFidesConsent(
    cookieValue: string,
    options: Partial<FidesInitOptionsOverrides>,
  ): NoticeConsent | undefined {
    // Only proceed if we have a mapping
    if (!options.otFidesMapping) {
      return undefined;
    }

    try {
      const decodedString = decodeURIComponent(options.otFidesMapping);
      const strippedString = decodedString.replace(/^'|'$/g, "");
      const mappingParsed: OtToFidesConsentMapping = JSON.parse(strippedString);
      const fidesConsent = this.parseCookieValue(cookieValue, mappingParsed);

      if (fidesConsent) {
        fidesDebugger(
          `Fides consent built based on OneTrust consent: ${JSON.stringify(fidesConsent)}`,
        );
      }
      return fidesConsent;
    } catch (e) {
      fidesDebugger(
        `Failed to map OneTrust consent to Fides consent due to: ${e}`,
      );
      return undefined;
    }
  }

  // eslint-disable-next-line class-methods-use-this
  private parseCookieValue(
    cookieValue: string,
    mapping: OtToFidesConsentMapping,
  ): NoticeConsent | undefined {
    // Initialize an empty Fides consent object
    const fidesConsent: NoticeConsent = {};

    // Extract the groups parameter
    const groupsMatch = cookieValue.match(/groups=([^&]*)/);

    if (!groupsMatch || !groupsMatch[1]) {
      return fidesConsent; // Return empty object if groups not found
    }

    // Parse the groups string into an object
    const groupsStr = groupsMatch[1];
    const groupPairs = groupsStr.split(",");

    // Process only the categories found in the cookie
    groupPairs.forEach((pair) => {
      const [category, consentValue] = pair.split(":");

      // Skip if category is not in our mapping
      if (!mapping[category]) {
        return;
      }

      // Add the corresponding Fides keys to the result with appropriate consent value
      mapping[category].forEach((fidesKey: string) => {
        const isConsented = consentValue === "1";

        // Set fides key based on current consent
        if (fidesConsent[fidesKey] === undefined) {
          fidesConsent[fidesKey] = isConsented;
        }
      });
    });

    return fidesConsent;
  }

  /**
   * Write Fides consent back to OneTrust cookie
   * Updates the OptanonConsent cookie's groups parameter
   *
   * @param fidesConsent - Fides consent object to write
   * @param mapping - Optional custom mapping (defaults to standard mapping)
   * @returns true if write succeeded, false otherwise
   */
  writeConsentToOneTrust(
    fidesConsent: NoticeConsent,
    mapping?: Record<string, string>,
  ): boolean {
    try {
      const cookieValue = this.getConsentCookie();
      if (!cookieValue) {
        fidesDebugger(
          "[OneTrust] Cannot write consent - OptanonConsent cookie not found",
        );
        return false;
      }

      // Use provided mapping or default
      const categoryMapping = mapping || DEFAULT_ONETRUST_TO_FIDES_MAPPING;

      // Invert the mapping: fidesKey -> otCategory
      const invertedMapping: Record<string, string> = {};
      Object.entries(categoryMapping).forEach(([otCat, fidesKey]) => {
        invertedMapping[fidesKey] = otCat;
      });

      // Build new groups string from Fides consent
      const groupsArray: string[] = [];
      Object.entries(invertedMapping).forEach(([fidesKey, otCategory]) => {
        const consentValue = fidesConsent[fidesKey];
        // Convert to boolean: true/"opt_in"/"acknowledge" → "1", false/"opt_out"/"not_applicable" → "0"
        const hasConsent =
          consentValue === true ||
          consentValue === "opt_in" ||
          consentValue === "acknowledge";
        const status = hasConsent ? "1" : "0";
        groupsArray.push(`${otCategory}:${status}`);
      });

      const newGroups = groupsArray.join(",");

      // Replace groups parameter using regex (preserves other params exactly)
      const updatedCookie = cookieValue.replace(
        /groups=([^&]*)/,
        `groups=${newGroups}`,
      );

      // Write cookie (preserve existing expiry/domain/path)
      document.cookie = `OptanonConsent=${encodeURIComponent(updatedCookie)}; path=/`;

      fidesDebugger(
        `[OneTrust] Updated consent in cookie: ${newGroups}`,
      );
      return true;
    } catch (error) {
      fidesDebugger(`[OneTrust] Error writing consent: ${error}`);
      return false;
    }
  }
}
