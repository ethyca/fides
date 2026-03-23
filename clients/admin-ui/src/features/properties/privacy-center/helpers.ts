import { PrivacyCenterConfig, PrivacyRequestOption } from "~/types/api";

/**
 * Default icon URLs for the three standard policy keys.
 * When a user selects one of these policy keys and hasn't set a custom icon,
 * the matching URL is auto-populated into the icon_path field.
 */
export const POLICY_KEY_DEFAULT_ICONS: Record<string, string> = {
  default_access_policy: "/download.svg",
  default_erasure_policy: "/delete.svg",
  default_consent_policy: "/consent.svg",
};

export const DEFAULT_ACTION: PrivacyRequestOption = {
  policy_key: "",
  icon_path: "",
  title: "",
  description: "",
  description_subtext: [],
  confirmButtonText: "Continue",
  cancelButtonText: "Cancel",
  identity_inputs: { email: "required" },
  custom_privacy_request_fields: {},
};

export const DEFAULT_PRIVACY_CENTER_CONFIG: PrivacyCenterConfig = {
  title: "",
  description: "",
  description_subtext: [],
  logo_path: null,
  logo_url: null,
  favicon_path: null,
  privacy_policy_url: null,
  privacy_policy_url_text: null,
  actions: [{ ...DEFAULT_ACTION }],
  includeConsent: false,
  consent: {
    button: {
      description: "",
      icon_path: "",
      identity_inputs: { email: "optional" },
      title: "",
    },
    page: {
      consentOptions: [],
      description: "",
      title: "",
    },
  },
  links: [],
};
