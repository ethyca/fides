/* eslint-disable import/prefer-default-export */
// DEFER: remove this import part of removing default config state (see https://github.com/ethyca/fides/issues/3212)
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

/**
 * Transform the config to the latest version so that components can
 * reference config variables uniformly.
 * 
 * DEFER: move this to config.slice as part of removing default config state (see https://github.com/ethyca/fides/issues/3212)
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

// DEFER: remove this import part of removing default config state (see https://github.com/ethyca/fides/issues/3212)
export function getDefaultConfig(): Config {
  return transformConfig(dangerousStaticDefaultConfig);
}

export const defaultIdentityInput: IdentityInputs = { email: "optional" };
