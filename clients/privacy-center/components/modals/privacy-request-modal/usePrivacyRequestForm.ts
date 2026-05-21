import { useChakraToast as useToast } from "fidesui";
import { useFormik } from "formik";
import { Headers } from "headers-polyfill";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import * as Yup from "yup";

import { addCommonHeaders } from "~/common/CommonHeaders";
import { ErrorToastOptions, SuccessToastOptions } from "~/common/toast-options";
import { ModalViews } from "~/components/modals/types";
import {
  dateFieldValidation,
  emailValidation,
  nameValidation,
  phoneValidation,
} from "~/components/modals/validation";
import { DEFAULT_IDENTITY_INPUTS } from "~/constants";
import { useProperty } from "~/features/common/property.slice";
import { useSettings } from "~/features/common/settings.slice";
import {
  useApplicabilitySync,
  useConditionalValidate,
} from "~/hooks/useConditionalValidation";
import { useCustomFieldsForm } from "~/hooks/useCustomFieldsForm";
import { PrivacyRequestStatus } from "~/types";
import { PrivacyRequestSource } from "~/types/api/models/PrivacyRequestSource";
import {
  CustomConfigField,
  PrivacyRequestOption as ConfigPrivacyRequestOption,
} from "~/types/config";
import {
  FormFieldValue,
  FormValues,
  MultiselectFieldValue,
} from "~/types/forms";

import { buildOrderedFields } from "./buildOrderedFields";
import { uploadAllFiles } from "./fileUploadUtils";

export type { OrderedField } from "./buildOrderedFields";
export {
  uploadAllFiles,
  uploadFieldFiles,
  uploadFile,
} from "./fileUploadUtils";

/**
 *
 * @param value
 * @returns Default to null if the value is undefined or an empty string
 */
const fallbackNull = (
  value: string | MultiselectFieldValue | null | undefined,
) => (value === undefined || value === "" ? null : value);

const usePrivacyRequestForm = ({
  onExit,
  action,
  setCurrentView,
  setPrivacyRequestId,
  isVerificationRequired,
  onSuccessWithoutVerification,
}: {
  onExit: () => void;
  action?: ConfigPrivacyRequestOption;
  setCurrentView: (view: ModalViews) => void;
  setPrivacyRequestId: (id: string) => void;
  isVerificationRequired: boolean;
  onSuccessWithoutVerification?: () => void;
}) => {
  const settings = useSettings();
  const {
    phone: phoneInput,
    email: emailInput,
    name: nameInput,
    ...customIdentityInputs
  } = action?.identity_inputs ?? DEFAULT_IDENTITY_INPUTS;
  const legacyIdentityFields = {
    phone: phoneInput,
    email: emailInput,
    name: nameInput,
    ...Object.fromEntries(
      Object.entries(customIdentityInputs).flatMap(([key, value]) =>
        typeof value === "string" ? [[key, value]] : [],
      ),
    ),
  };

  const customIdentityFields = Object.fromEntries(
    Object.entries(customIdentityInputs).flatMap(([key, value]) =>
      typeof value !== "string" ? [[key, value]] : [],
    ),
  );

  const customPrivacyRequestFields =
    action?.custom_privacy_request_fields ?? {};
  const toast = useToast();
  const [isSubmitPending, setIsSubmitPending] = useState(false);
  const searchParams = useSearchParams();

  const property = useProperty();
  const params = useSearchParams();
  // Use our custom hook for form field logic
  const { getInitialValues, getValidationSchema } = useCustomFieldsForm({
    customPrivacyRequestFields,
    searchParams,
  });

  const initialValues = useMemo(() => getInitialValues(), [getInitialValues]);

  // Build the static portion of the validation schema (identity fields)
  const identityValidationSchema = useMemo(
    () =>
      Yup.object().shape({
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
        ...Object.fromEntries(
          Object.entries(customIdentityFields).flatMap(([key, value]) => {
            if (!value) {
              return [];
            }
            if (value.field_type === "date") {
              return [
                [
                  key,
                  dateFieldValidation(
                    value,
                    value.label,
                    value.required !== false,
                  ),
                ],
              ];
            }
            return [[key, Yup.string().required(`${value.label} is required`)]];
          }),
        ),
      }),
    [emailInput, phoneInput, nameInput, customIdentityFields],
  );

  const { validate, applicableFieldsRef, validationError } =
    useConditionalValidate({
      customPrivacyRequestFields,
      identityValidationSchema,
      getValidationSchema,
    });

  const formik = useFormik<FormValues>({
    enableReinitialize: true,
    initialValues: {
      ...Object.fromEntries(
        Object.entries({
          ...legacyIdentityFields,
          ...customIdentityFields,
        }).map(([key]) => [key, ""]),
      ),
      ...initialValues,
      ...Object.fromEntries(
        Object.entries({
          ...legacyIdentityFields,
          ...customIdentityFields,
        }).map(([key]) => {
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
      setIsSubmitPending(true);

      const handleError = ({
        title,
        error,
      }: {
        title: string;
        error?: unknown;
      }) => {
        setIsSubmitPending(false);
        const errorMessage = typeof error === "string" ? error : undefined;
        toast({
          title,
          description: errorMessage,
          ...ErrorToastOptions,
        });
      };

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

      // Upload files first, before building the submission payload
      let fileAttachmentIds: Record<string, string[]> = {};
      if (action.custom_privacy_request_fields) {
        try {
          fileAttachmentIds = await uploadAllFiles(
            values,
            action.custom_privacy_request_fields,
            settings.FIDES_API_URL,
            {
              propertyId: property?.id || "",
              policyKey: action.policy_key,
            },
          );
        } catch (uploadError) {
          handleError({
            title: "An error occurred while uploading your file",
            error:
              uploadError instanceof Error
                ? uploadError.message
                : "File upload failed",
          });
          return;
        }
      }

      const customPrivacyRequestFieldValues =
        action.custom_privacy_request_fields
          ? Object.fromEntries(
              Object.entries(action.custom_privacy_request_fields)
                .filter(([key, field]) => {
                  if (
                    field.field_type === "location" ||
                    field.field_type === "file"
                  ) {
                    return false;
                  }
                  // Exclude fields gated off by display_condition
                  if (!applicableFieldsRef.current.has(key) && !field.hidden) {
                    return false;
                  }
                  return true;
                })
                .map(([key, field]) => {
                  const paramValue =
                    field.query_param_key &&
                    searchParams?.get(field.query_param_key);
                  const hiddenValue = paramValue ?? field.default_value;
                  const value: FormFieldValue = !field.hidden
                    ? values[key]
                    : (hiddenValue ?? "");

                  let processedValue;
                  if (
                    field.field_type === "multiselect" ||
                    field.field_type === "checkbox_group"
                  ) {
                    processedValue = value || [];
                  } else if (field.field_type === "checkbox") {
                    processedValue = Boolean(value);
                  } else {
                    processedValue = fallbackNull(
                      value as
                        | string
                        | MultiselectFieldValue
                        | null
                        | undefined,
                    );
                  }

                  return [
                    key,
                    {
                      label: field.label,
                      value: processedValue,
                    },
                  ];
                })
                .filter(
                  ([, fieldData]) =>
                    typeof fieldData === "object" && fieldData.value !== null,
                ),
            )
          : {};

      // Add file field values as attachment ID arrays
      Object.entries(fileAttachmentIds).forEach(([key, ids]) => {
        const field = action.custom_privacy_request_fields?.[key];
        if (field) {
          customPrivacyRequestFieldValues[key] = {
            label: field.label,
            value: ids,
          };
        }
      });

      // Extract custom fields object for cleaner code
      const customFieldsPayload =
        Object.keys(customPrivacyRequestFieldValues).length > 0
          ? { custom_privacy_request_fields: customPrivacyRequestFieldValues }
          : {};

      const body = [
        {
          identity: identityInputValues,
          ...customFieldsPayload,
          policy_key: action.policy_key,
          property_id: property?.id || null,
          source: PrivacyRequestSource.PRIVACY_CENTER,
          location: values?.location ? values.location : undefined,
        },
      ];

      try {
        const headers: Headers = new Headers();
        addCommonHeaders(headers, null);

        const response = await fetch(
          `${settings.FIDES_API_URL}/privacy-request`,
          {
            method: "POST",
            headers: headers as unknown as HeadersInit,
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
          // Call success handler if provided (for page flow), otherwise just close
          if (onSuccessWithoutVerification) {
            onSuccessWithoutVerification();
          } else {
            onExit();
          }
        } else if (
          (isVerificationRequired &&
            data.succeeded.length &&
            data.succeeded[0].status ===
              PrivacyRequestStatus.IDENTITY_UNVERIFIED) ||
          data.succeeded[0].status === PrivacyRequestStatus.DUPLICATE
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
      }
    },

    validate,
  });

  const { applicableFields, conditionError } = useApplicabilitySync({
    customPrivacyRequestFields,
    applicableFieldsRef,
    initialValues,
    formValues: formik.values,
    setFieldValue: formik.setFieldValue,
  });

  const orderedFields = buildOrderedFields(
    legacyIdentityFields,
    customIdentityFields as Record<string, CustomConfigField>,
    customPrivacyRequestFields,
    action?.field_order,
  );

  return {
    ...formik,
    isSubmitting: formik.isSubmitting || isSubmitPending,
    legacyIdentityFields,
    customIdentityFields,
    customPrivacyRequestFields,
    orderedFields,
    applicableFields,
    validationError: validationError || conditionError,
  };
};

export default usePrivacyRequestForm;
