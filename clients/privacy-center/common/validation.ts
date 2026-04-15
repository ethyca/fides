import { URL } from "url";

import {
  isV1ConsentConfig,
  translateV1ConfigToV2,
} from "~/features/consent/helpers";
import { Config, LegacyConfig, PrivacyCenterLink } from "~/types/config";

/**
 * Check whether a string is a valid URL (http or https).
 */
export const isValidUrl = (value: string): boolean => {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
};

/**
 * Transform the config to the latest version so that components can
 * reference config variables uniformly.
 */
export const transformConfig = (config: LegacyConfig): Config => {
  if (isV1ConsentConfig(config.consent)) {
    const translatedConsent = translateV1ConfigToV2({
      v1ConsentConfig: config.consent,
    });

    return { ...config, consent: translatedConsent };
  }

  return { ...config, consent: config.consent };
};

/**
 * Validate the config object
 */
export const validateConfig = (
  input: Config | LegacyConfig,
): { isValid: boolean; message: string } => {
  // Validate required top-level fields exist and are non-empty strings
  const requiredStringFields: (keyof Config)[] = [
    "title",
    "description",
    "logo_path",
  ];
  const missingFields = requiredStringFields.filter((field) => {
    const value = (input as Record<string, unknown>)[field];
    return typeof value !== "string" || value.trim().length === 0;
  });
  if (missingFields.length > 0) {
    return {
      isValid: false,
      message: `Missing required field(s): ${missingFields.join(", ")}`,
    };
  }

  // Validate actions is an array when present
  if (input.actions !== undefined && !Array.isArray(input.actions)) {
    return {
      isValid: false,
      message: "Invalid field: actions (must be an array)",
    };
  }

  // Validate required fields within each action (if provided)
  if (Array.isArray(input.actions)) {
    const requiredActionFields: (keyof NonNullable<
      Config["actions"]
    >[number])[] = ["title", "description", "icon_path"];
    for (let i = 0; i < input.actions.length; i += 1) {
      const action = input.actions[i];
      const missingActionFields = requiredActionFields.filter((field) => {
        const value = (action as Record<string, unknown>)[field];
        return typeof value !== "string" || value.trim().length === 0;
      });
      if (missingActionFields.length > 0) {
        return {
          isValid: false,
          message: `Missing required field(s) in actions[${i}]: ${missingActionFields.join(", ")}`,
        };
      }
    }
  }

  // Validate URL fields have valid URL format when present
  const urlFields: (keyof Config)[] = [
    "server_url_development",
    "server_url_production",
    "logo_url",
    "privacy_policy_url",
  ];
  const invalidUrls = urlFields.filter((field) => {
    const value = (input as Record<string, unknown>)[field];
    return (
      typeof value === "string" && value.trim().length > 0 && !isValidUrl(value)
    );
  });
  if (invalidUrls.length > 0) {
    return {
      isValid: false,
      message: `Invalid URL(s): ${invalidUrls.join(", ")} (must use http or https)`,
    };
  }

  // Validate links URLs
  const links = (input as Record<string, unknown>).links as
    | PrivacyCenterLink[]
    | undefined;
  if (Array.isArray(links)) {
    const invalidLinks = links
      .map((link: PrivacyCenterLink, i: number) => ({
        index: i,
        url: link.url,
        label: link.label,
      }))
      .filter(
        ({ url }) =>
          typeof url === "string" && url.trim().length > 0 && !isValidUrl(url),
      );
    if (invalidLinks.length > 0) {
      const details = invalidLinks
        .map(({ index, label }) => `links[${index}] ("${label}")`)
        .join(", ");
      return {
        isValid: false,
        message: `Invalid URL(s) in ${details} (must use http or https)`,
      };
    }
  }

  // First, ensure we support LegacyConfig type if provided
  const config = transformConfig(input);

  // Cannot currently have more than one consent be executable
  if (config.consent) {
    const options = config.consent.page.consentOptions;
    const executables = options.filter((option) => option.executable);
    if (executables.length > 1) {
      return {
        isValid: false,
        message: "Cannot have more than one consent option be executable",
      };
    }
  }

  const invalidFieldMessages = (config.actions ?? []).flatMap((action) => {
    /*
      Validate that hidden fields must have a default_value or a query_param_key
      defined, otherwise the field would never get a value assigned.
    */
    const invalidFields = Object.entries(
      action.custom_privacy_request_fields || {},
    )
      .filter(
        ([, field]) =>
          field.hidden &&
          field.default_value === undefined &&
          field.query_param_key === undefined,
      )
      .map(([key]) => `'${key}'`);

    return invalidFields.length > 0
      ? [
          `${invalidFields.join(", ")} in the action with policy_key '${
            action.policy_key
          }'`,
        ]
      : [];
  });

  if (invalidFieldMessages.length > 0) {
    return {
      isValid: false,
      message: `A default_value or query_param_key is required for hidden field(s) ${invalidFieldMessages.join(
        ", ",
      )}`,
    };
  }

  return { isValid: true, message: "Config is valid" };
};
