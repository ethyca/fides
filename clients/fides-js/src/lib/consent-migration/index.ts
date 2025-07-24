import {
  ConsentMethod,
  FidesInitOptionsOverrides,
  NoticeConsent,
} from "../consent-types";
import { OneTrustProvider } from "./onetrust";
import {
  ConsentMigrationProvider,
  ConsentMigrationProviderName,
} from "./types";

/**
 * Registry of consent migration providers
 */
const providers: Map<ConsentMigrationProviderName, ConsentMigrationProvider> =
  new Map();

/**
 * Register a new consent migration provider
 * @param name Unique identifier for the provider
 * @param provider Implementation of ConsentMigrationProvider
 */
export function registerProvider(
  name: ConsentMigrationProviderName,
  provider: ConsentMigrationProvider,
) {
  providers.set(name, provider);
}

/**
 * Register default providers
 */
export function registerDefaultProviders(
  optionsOverrides: Partial<FidesInitOptionsOverrides>,
) {
  // Register OneTrust provider if configured
  if (optionsOverrides.otFidesMapping) {
    registerProvider(
      ConsentMigrationProviderName.ONETRUST,
      new OneTrustProvider(),
    );
  }
}

/**
 * Try to read consent from all registered providers
 * @param optionsOverrides Configuration options containing provider mappings
 * @returns Object containing the mapped consent and migration method from the first successful provider
 */
export function readConsentFromAnyProvider(
  optionsOverrides: Partial<FidesInitOptionsOverrides>,
): { consent: NoticeConsent | undefined; method: ConsentMethod | undefined } {
  // Try each registered provider
  let foundConsent: NoticeConsent | undefined;
  let foundProviderName: ConsentMigrationProviderName | undefined;

  // Find the first provider that can provide consent
  Array.from(providers).some(([name, provider]) => {
    const cookieValue = provider.getConsentCookie();
    if (!cookieValue) {
      fidesDebugger(`No consent cookie found for provider: ${name}`);
      return false;
    }

    // Let the provider determine if it can handle these options
    const consent = provider.convertToFidesConsent(
      cookieValue,
      optionsOverrides,
    );
    if (consent) {
      foundConsent = consent;
      foundProviderName = name;
      return true;
    }
    return false;
  });

  if (!foundProviderName) {
    return { consent: undefined, method: undefined };
  }

  // Get the provider using the Map's get method
  const provider = providers.get(foundProviderName);
  return { consent: foundConsent, method: provider!.migrationMethod };
}
