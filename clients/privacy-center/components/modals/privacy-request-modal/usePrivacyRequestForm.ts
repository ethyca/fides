import { useToast } from "fidesui";
import { useFormik } from "formik";
import { Headers } from "headers-polyfill";
import { useSearchParams } from "next/navigation";
import * as Yup from "yup";

import { addCommonHeaders } from "~/common/CommonHeaders";
import { ErrorToastOptions, SuccessToastOptions } from "~/common/toast-options";
import { ModalViews } from "~/components/modals/types";
import {
  emailValidation,
  nameValidation,
  phoneValidation,
} from "~/components/modals/validation";
import { DEFAULT_IDENTITY_INPUTS } from "~/constants";
import { useProperty } from "~/features/common/property.slice";
import { useSettings } from "~/features/common/settings.slice";
import { useCustomFieldsForm } from "~/hooks/useCustomFieldsForm";
import { PrivacyRequestStatus } from "~/types";
import { PrivacyRequestSource } from "~/types/api/models/PrivacyRequestSource";
import { PrivacyRequestOption as ConfigPrivacyRequestOption } from "~/types/config";
import { FormValues, MultiselectFieldValue } from "~/types/forms";

/**
 *
 * @param value
 * @returns Default to null if the value is undefined or an empty string
 */
const fallbackNull = (value: string | MultiselectFieldValue) =>
  value === undefined || value === "" ? null : value;

const usePrivacyRequestForm = ({
  onClose,
  action,
  setCurrentView,
  setPrivacyRequestId,
  isVerificationRequired,
}: {
  onClose: () => void;
  action?: ConfigPrivacyRequestOption;
  setCurrentView: (view: ModalViews) => void;
  setPrivacyRequestId: (id: string) => void;
  isVerificationRequired: boolean;
}) => {
  const settings = useSettings();
  const {
    phone: phoneInput,
    email: emailInput,
    name: nameInput,
    ...restIdentityFields
  } = action?.identity_inputs ?? DEFAULT_IDENTITY_INPUTS;
  const identityFields = {
    phone: phoneInput,
    email: emailInput,
    name: nameInput,
    ...Object.fromEntries(
      Object.entries(restIdentityFields).flatMap(([key, value]) =>
        typeof value === "string" ? [[key, value]] : [],
      ),
    ),
  };
  const customPrivacyRequestFields =
    action?.custom_privacy_request_fields ?? {};
  const toast = useToast();
  const searchParams = useSearchParams();

  const property = useProperty();
  const params = useSearchParams();
  // Use our custom hook for form field logic
  const { getInitialValues, getValidationSchema } = useCustomFieldsForm({
    customPrivacyRequestFields,
    searchParams,
  });

  const formik = useFormik<FormValues>({
    initialValues: {
      ...Object.fromEntries(
        Object.entries(identityFields).map(([key]) => [key, ""]),
      ),
      ...getInitialValues(),
      ...Object.fromEntries(
        Object.entries(identityFields).map(([key]) => {
          const value = params?.get(key) ?? "";
          return [key, value];
        }),
      ),
    },

    onSubmit: async (values) => {
      if (!action) {
        // somehow we've reached a broken state, return
        return;
      }

      // extract identity input values
      const identityInputValues = Object.fromEntries(
        Object.entries(action.identity_inputs ?? {})
          // we have to support name as an identity_input for legacy purposes
          // but we ignore it since it's not unique enough to be treated as an identity
          .filter(([key, field]) => key !== "name" && !!field)
          .map(([key, field]) => {
            const value = fallbackNull(values[key]);
            if (typeof field === "string") {
              if (key === "phone") {
                // eslint-disable-next-line no-param-reassign
                key = "phone_number";
              }
              return [key, value];
            }
            return [key, { label: field?.label, value }];
          }),
      );

      const customPrivacyRequestFieldValues =
        action.custom_privacy_request_fields
          ? Object.fromEntries(
              Object.entries(action.custom_privacy_request_fields).map(
                ([key, field]) => {
                  const paramValue =
                    field.query_param_key &&
                    searchParams?.get(field.query_param_key);
                  const hiddenValue = paramValue ?? field.default_value;

                  return [
                    key,
                    {
                      // only include label and value
                      label: field.label,
                      value: !field.hidden ? values[key] : hiddenValue,
                    },
                  ];
                },
              ),
            )
          : {};

      const body = [
        {
          identity: identityInputValues,
          ...(Object.keys(customPrivacyRequestFieldValues).length > 0 && {
            custom_privacy_request_fields: customPrivacyRequestFieldValues,
          }),
          policy_key: action.policy_key,
          property_id: property?.id || null,
          source: PrivacyRequestSource.PRIVACY_CENTER,
        },
      ];

      const handleError = ({
        title,
        error,
      }: {
        title: string;
        error?: any;
      }) => {
        toast({
          title,
          description: error,
          ...ErrorToastOptions,
        });
        onClose();
      };

      try {
        const headers: Headers = new Headers();
        addCommonHeaders(headers, null);

        const response = await fetch(
          `${settings.FIDES_API_URL}/privacy-request`,
          {
            method: "POST",
            headers,
            body: JSON.stringify(body),
          },
        );
        const data = await response.json();
        if (!response.ok) {
          handleError({
            title: "An error occurred while creating your privacy request",
            error: data?.detail,
          });
          return;
        }

        if (!isVerificationRequired && data.succeeded.length) {
          toast({
            title:
              "Your request was successful, please await further instructions.",
            ...SuccessToastOptions,
          });
        } else if (
          isVerificationRequired &&
          data.succeeded.length &&
          data.succeeded[0].status === PrivacyRequestStatus.IDENTITY_UNVERIFIED
        ) {
          setPrivacyRequestId(data.succeeded[0].id);
          setCurrentView(ModalViews.IdentityVerification);
        } else {
          handleError({
            title:
              "An unhandled error occurred while processing your privacy request",
          });
        }
      } catch (error) {
        handleError({
          title:
            "An unhandled error occurred while creating your privacy request",
        });
        return;
      }

      if (!isVerificationRequired) {
        onClose();
      }
    },
    validationSchema: Yup.object().shape({
      name: nameValidation(nameInput),
      email: emailValidation(emailInput).test(
        "one of email or phone entered",
        "You must enter either email or phone",
        (_value, context) => {
          if (emailInput === "optional" && phoneInput === "optional") {
            return Boolean(context.parent.phone || context.parent.email);
          }
          return true;
        },
      ),
      phone: phoneValidation(phoneInput).test(
        "one of email or phone entered",
        "You must enter either email or phone",
        (_value, context) => {
          if (emailInput === "optional" && phoneInput === "optional") {
            return Boolean(context.parent.phone || context.parent.email);
          }
          return true;
        },
      ),
      ...getValidationSchema().fields,
    }),
  });

  return {
    ...formik,
    identityInputs: identityFields,
    customPrivacyRequestFields,
  };
};

export default usePrivacyRequestForm;
