import {
  ConsentMethod,
  FidesInitOptionsOverrides,
  NoticeConsent,
  TranscendToFidesConsentMapping,
} from "../consent-types";
import { getCookieByName } from "../cookie";
import { ConsentMigrationProvider } from "./types";

/**
 * Transcend implementation of consent migration
 */
export class TranscendProvider implements ConsentMigrationProvider {
  readonly cookieName = "tcm";

  readonly migrationMethod = ConsentMethod.EXTERNAL_PROVIDER;

  getConsentCookie(): string | undefined {
    return getCookieByName(this.cookieName);
  }

  convertToFidesConsent(
    cookieValue: string,
    options: Partial<FidesInitOptionsOverrides>,
  ): NoticeConsent | undefined {
    // Only proceed if we have a mapping
    if (!options.transcendFidesMapping) {
      return undefined;
    }

    try {
      const decodedString = decodeURIComponent(options.transcendFidesMapping);
      const strippedString = decodedString.replace(/^'|'$/g, "");
      const mappingParsed: TranscendToFidesConsentMapping =
        JSON.parse(strippedString);
      const fidesConsent = this.parseCookieValue(cookieValue, mappingParsed);

      if (fidesConsent) {
        fidesDebugger(
          `Fides consent built based on Transcend consent: ${JSON.stringify(fidesConsent)}`,
        );
      }
      return fidesConsent;
    } catch (e) {
      fidesDebugger(
        `Failed to map Transcend consent to Fides consent due to: ${e}`,
      );
      return undefined;
    }
  }

  // eslint-disable-next-line class-methods-use-this
  private parseCookieValue(
    cookieValue: string,
    mapping: TranscendToFidesConsentMapping,
  ): NoticeConsent | undefined {
    // Initialize an empty Fides consent object
    const fidesConsent: NoticeConsent = {};

    try {
      // Parse the Transcend cookie JSON
      const transcendCookie = JSON.parse(cookieValue);

      // Extract the purposes object
      const { purposes } = transcendCookie;

      if (!purposes || typeof purposes !== "object") {
        return fidesConsent; // Return empty object if purposes not found
      }

      // Process each purpose in the cookie
      Object.entries(purposes).forEach(([purposeName, consentValue]) => {
        // Skip if purpose is not in our mapping
        if (!mapping[purposeName]) {
          return;
        }

        // Determine consent status
        // Handle boolean true/false and string "Auto" (treat as truthy)
        const isConsented =
          consentValue === true ||
          (typeof consentValue === "string" && consentValue === "Auto");

        // Add the corresponding Fides keys to the result with appropriate consent value
        mapping[purposeName].forEach((fidesKey: string) => {
          // Set fides key based on current consent
          if (fidesConsent[fidesKey] === undefined) {
            fidesConsent[fidesKey] = isConsented;
          }
        });
      });

      return fidesConsent;
    } catch (e) {
      fidesDebugger(`Failed to parse Transcend cookie value: ${e}`);
      return fidesConsent; // Return empty object on parse error
    }
  }
}
