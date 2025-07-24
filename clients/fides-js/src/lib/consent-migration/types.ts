import {
  ConsentMethod,
  FidesInitOptionsOverrides,
  NoticeConsent,
} from "../consent-types";

/**
 * Enum of supported consent migration providers
 */
export enum ConsentMigrationProviderName {
  ONETRUST = "onetrust",
}

/**
 * Interface for consent migration providers
 */
export interface ConsentMigrationProvider {
  /**
   * The name of the cookie used by this provider
   */
  readonly cookieName: string;

  /**
   * The consent method used by this provider
   */
  readonly migrationMethod: ConsentMethod;

  /**
   * Get the consent cookie value for this provider
   */
  getConsentCookie(): string | undefined;

  /**
   * Convert the provider's consent format to Fides consent format
   * @param cookieValue The raw cookie value
   * @param options The Fides options containing provider-specific mappings
   */
  convertToFidesConsent(
    cookieValue: string,
    options: Partial<FidesInitOptionsOverrides>,
  ): NoticeConsent | undefined;
}
