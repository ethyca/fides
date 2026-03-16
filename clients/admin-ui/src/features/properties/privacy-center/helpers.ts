import { PrivacyCenterConfig, PrivacyRequestOption } from "~/types/api";

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
