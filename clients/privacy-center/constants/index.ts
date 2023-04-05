/* eslint-disable import/prefer-default-export */
import configJson from "~/config/config.json";
import {
  isV1ConsentConfig,
  translateV1ConfigToV2,
} from "~/features/consent/helpers";
import {
  Config,
  IdentityInputs,
  V1Consent,
  V2Config,
  V2Consent,
} from "~/types/config";

const transformConfig = (config: Config): V2Config => {
  if (isV1ConsentConfig(config.consent)) {
    const v1ConsentConfig: V1Consent = config.consent;
    const translatedConsent: V2Consent = translateV1ConfigToV2({
      v1ConsentConfig,
    });
    const temp: V2Config = { ...config, consent: translatedConsent };
    return temp;
  }
  return { ...config, consent: config.consent };
};

// if (isV1ConsentConfig(importedConfig.consent)) {
//   const v1ConsentConfig: V1Consent = importedConfig.consent;
//   const translatedConsent: V2Consent = translateV1ConfigToV2({ v1ConsentConfig });
//   const temp: V2Config = { ...importedConfig, consent: translatedConsent };
//   importedConfig = temp;
// }
export const config: V2Config = transformConfig(configJson);

// Compute the host URL for the server, while being backwards compatible with
// the previous "fidesops_host_***" configuration
// DEFER: remove backwards compatibility (see https://github.com/ethyca/fides/issues/1264)
export const hostUrl =
  process.env.NODE_ENV === "development" || process.env.NODE_ENV === "test"
    ? config.server_url_development || (config as any).fidesops_host_development
    : config.server_url_production || (config as any).fidesops_host_production;

export const defaultIdentityInput: IdentityInputs = { email: "optional" };
