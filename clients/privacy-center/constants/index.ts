/* eslint-disable import/prefer-default-export */
import dangerousStaticDefaultConfig from "~/config/config.json";
import {
  isV1ConsentConfig,
  translateV1ConfigToV2,
} from "~/features/consent/helpers";
import {
  LegacyConfig,
  IdentityInputs,
  LegacyConsentConfig,
  Config,
  ConsentConfig,
} from "~/types/config";

export function getDefaultConfig(): Config {
  return transformConfig(dangerousStaticDefaultConfig);
}

/**
 * Transform the config to the latest version so that components can
 * reference config variables uniformly.
 */
const transformConfig = (config: LegacyConfig): Config => {
  if (isV1ConsentConfig(config.consent)) {
    const v1ConsentConfig: LegacyConsentConfig = config.consent;
    const translatedConsent: ConsentConfig = translateV1ConfigToV2({
      v1ConsentConfig,
    });
    return { ...config, consent: translatedConsent };
  }
  return { ...config, consent: config.consent };
};

export const defaultIdentityInput: IdentityInputs = { email: "optional" };
