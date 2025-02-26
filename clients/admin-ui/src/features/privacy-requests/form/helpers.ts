import * as Yup from "yup";

import { PrivacyRequestOption } from "~/types/api";

export const findActionFromPolicyKey = (
  key: string,
  allActions?: PrivacyRequestOption[],
) => allActions?.find((action) => action.policy_key === key);

export const generateValidationSchemaFromAction = (
  action?: PrivacyRequestOption,
) => {
  if (!action) {
    return Yup.object().shape({
      policy_key: Yup.string().required().label("Request type"),
    });
  }
  const customFieldsSchema = action.custom_privacy_request_fields
    ? Object.entries(action.custom_privacy_request_fields)
        .map(([fieldName, fieldInfo]) => ({
          [fieldName]: Yup.object().shape({
            value:
              fieldInfo.required && !fieldInfo.hidden
                ? Yup.string().required().label(fieldInfo.label)
                : Yup.string().nullable(),
          }),
        }))
        .reduce((acc, next) => ({ ...acc, ...next }), {})
    : {};

  return Yup.object().shape({
    policy_key: Yup.string().required().label("Request type"),
    identity: Yup.object().shape({
      email:
        action.identity_inputs?.email === "required"
          ? Yup.string().email().required().label("Email address")
          : Yup.string().nullable(),
      phone_number:
        action.identity_inputs?.phone === "required"
          ? Yup.string()
              .matches(
                /^\+?[1-9]\d{1,14}$/,
                "Phone number must be formatted correctly (e.g. 15555555555)",
              )
              .required()
              .label("Phone number")
          : Yup.string()
              .matches(
                /^\+?[1-9]\d{1,14}$/,
                "Phone number must be formatted correctly (e.g. 15555555555)",
              )
              .nullable(),
    }),
    custom_privacy_request_fields: Yup.object().shape(customFieldsSchema),
  });
};
