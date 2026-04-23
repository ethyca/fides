import type { FormRule } from "fidesui";

import { PrivacyRequestOption } from "~/types/api";

export const findActionFromPolicyKey = (
  key: string,
  allActions?: PrivacyRequestOption[],
) => allActions?.find((action) => action.policy_key === key);

/**
 * Generates antd Form.Item rules for each field based on the selected action.
 * Returns a record mapping field name paths to their validation rules.
 */
export const generateFormRulesFromAction = (
  action?: PrivacyRequestOption,
): Record<string, FormRule[]> => {
  const rules: Record<string, FormRule[]> = {
    policy_key: [{ required: true, message: "Request type is required" }],
  };

  if (!action) {
    return rules;
  }

  if (action.identity_inputs?.email === "required") {
    rules["identity.email"] = [
      { required: true, message: "Email address is required" },
      { type: "email", message: "Email address must be a valid email" },
    ];
  } else if (action.identity_inputs?.email) {
    rules["identity.email"] = [
      { type: "email", message: "Email address must be a valid email" },
    ];
  }

  const phonePattern = /^\+?[1-9]\d{1,14}$/;
  const phoneMessage =
    "Phone number must be formatted correctly (e.g. 15555555555)";

  if (action.identity_inputs?.phone === "required") {
    rules["identity.phone_number"] = [
      { required: true, message: "Phone number is required" },
      { pattern: phonePattern, message: phoneMessage },
    ];
  } else if (action.identity_inputs?.phone) {
    rules["identity.phone_number"] = [
      { pattern: phonePattern, message: phoneMessage },
    ];
  }

  if (action.custom_privacy_request_fields) {
    Object.entries(action.custom_privacy_request_fields).forEach(
      ([fieldName, fieldInfo]) => {
        const isLocation =
          "field_type" in fieldInfo && fieldInfo.field_type === "location";
        if (isLocation) {
          if (fieldInfo.required) {
            rules[fieldName] = [
              { required: true, message: `${fieldInfo.label} is required` },
            ];
          }
        } else if (fieldInfo.required && !fieldInfo.hidden) {
          rules[`custom_privacy_request_fields.${fieldName}.value`] = [
            { required: true, message: `${fieldInfo.label} is required` },
          ];
        }
      },
    );
  }

  return rules;
};
