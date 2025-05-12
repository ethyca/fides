import {
  ConsentMethod,
  FidesInitOptionsOverrides,
  NoticeConsent,
  OtToFidesConsentMapping,
} from "../consent-types";
import { getCookieByName } from "../cookie";
import { ConsentMigrationProvider } from "./types";

/**
 * OneTrust implementation of consent migration
 */
export class OneTrustProvider implements ConsentMigrationProvider {
  readonly cookieName = "OptanonConsent";

  readonly migrationMethod = ConsentMethod.OT_MIGRATION;

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
}
