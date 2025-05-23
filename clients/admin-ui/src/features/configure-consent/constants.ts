import { PrivacyDeclaration } from "~/types/api";

export interface MinimalPrivacyDeclaration {
  name: string;
  consent_use?: string;
  data_use: PrivacyDeclaration["data_use"];
  data_categories: PrivacyDeclaration["data_categories"];
  /**
   * Because we only allow inputting a string for cookies, we use cookieNames
   * to make the form easier to handle. However, we also keep the full `cookies`
   * object because the dictionary could potentially give us more than just the names
   * and we want a place to keep that information.
   */
}

export interface FormValues {
  name: string;
  vendor_id?: string;
  privacy_declarations: MinimalPrivacyDeclaration[];
}

export const EMPTY_DECLARATION: MinimalPrivacyDeclaration = {
  name: "",
  consent_use: "",
  data_use: "",
  // TODO(fides#4059): data categories will eventually be optional
  data_categories: ["user"],
};

export const CONSENT_USE_OPTIONS = [
  {
    label: "Analytics",
    value: "analytics",
    description:
      "Provides analytics for activities such as system and advertising performance reporting, insights and fraud detection.",
  },
  {
    label: "Essential",
    value: "essential",
    description:
      "Operates the service or product, including legal obligations, support and basic system operations.",
  },
  {
    label: "Functional",
    value: "functional",
    description: "Used for specific, necessary, and legitimate purposes.",
  },
  {
    label: "Marketing",
    value: "marketing",
    description:
      "Enables marketing, promotion, advertising and sales activities for the product, service, application or system.",
  },
];
