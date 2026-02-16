import { TCString } from "@iabtechlabtcf/core";

import {
  ConsentMethod,
  FidesInitOptionsOverrides,
  NoticeConsent,
  SourcePointToFidesConsentMapping,
} from "../consent-types";
import { getCookieByName } from "../cookie";
import { ConsentMigrationProvider } from "./types";

/**
 * SourcePoint (IAB TCF) implementation of consent migration.
 * SourcePoint stores consent via the IAB TCF; the TC string is typically in the euconsent cookie.
 */
export class SourcePointProvider implements ConsentMigrationProvider {
  /**
   * Common cookie name for the IAB TC (Transparency and Consent) string used by SourcePoint and other TCF CMPs.
   */
  readonly cookieName = "euconsent";

  readonly migrationMethod = ConsentMethod.EXTERNAL_PROVIDER;

  getConsentCookie(): string | undefined {
    return getCookieByName(this.cookieName);
  }

  convertToFidesConsent(
    cookieValue: string,
    options: Partial<FidesInitOptionsOverrides>,
  ): NoticeConsent | undefined {
    if (!options.sourcepointFidesMapping) {
      return undefined;
    }

    try {
      const decodedString = decodeURIComponent(options.sourcepointFidesMapping);
      const strippedString = decodedString.replace(/^'|'$/g, "");
      const mappingParsed: SourcePointToFidesConsentMapping =
        JSON.parse(strippedString);
      const fidesConsent = this.parseTcString(cookieValue, mappingParsed);

      if (fidesConsent && Object.keys(fidesConsent).length > 0) {
        fidesDebugger(
          `Fides consent built based on SourcePoint (TCF) consent: ${JSON.stringify(fidesConsent)}`,
        );
      }
      return fidesConsent;
    } catch (e) {
      fidesDebugger(
        `Failed to map SourcePoint consent to Fides consent due to: ${e}`,
      );
      return undefined;
    }
  }

  // eslint-disable-next-line class-methods-use-this
  private parseTcString(
    tcString: string,
    mapping: SourcePointToFidesConsentMapping,
  ): NoticeConsent {
    const fidesConsent: NoticeConsent = {};

    try {
      const tcModel = TCString.decode(tcString);

      Object.entries(mapping).forEach(([purposeIdStr, fidesKeys]) => {
        const purposeId = parseInt(purposeIdStr, 10);
        if (Number.isNaN(purposeId) || !fidesKeys?.length) {
          return;
        }

        const hasConsent = tcModel.purposeConsents.has(purposeId);
        const hasLegitimateInterest =
          tcModel.purposeLegitimateInterests.has(purposeId);
        const isConsented = hasConsent || hasLegitimateInterest;

        fidesKeys.forEach((fidesKey: string) => {
          if (fidesConsent[fidesKey] === undefined) {
            fidesConsent[fidesKey] = isConsented;
          }
        });
      });

      return fidesConsent;
    } catch (e) {
      fidesDebugger(`Failed to parse SourcePoint (TC) string: ${e}`);
      return fidesConsent;
    }
  }
}
