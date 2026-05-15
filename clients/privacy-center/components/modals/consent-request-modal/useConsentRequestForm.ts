import { getOrMakeFidesCookie, saveFidesCookie } from "fides-js";
import { useChakraToast as useToast } from "fidesui";
import { useFormik } from "formik";
import { Headers } from "headers-polyfill";
import { useEffect, useRef, useState } from "react";
import * as Yup from "yup";

import { addCommonHeaders } from "~/common/CommonHeaders";
import { ErrorToastOptions } from "~/common/toast-options";
import { ModalViews, VerificationType } from "~/components/modals/types";
import {
  emailValidation,
  phoneValidation,
} from "~/components/modals/validation";
import { DEFAULT_IDENTITY_INPUTS } from "~/constants";
import { useConfig } from "~/features/common/config.slice";
import { useSettings } from "~/features/common/settings.slice";
import { useApplicableFields } from "~/hooks/useApplicableFields";
import { useCustomFieldsForm } from "~/hooks/useCustomFieldsForm";
import { PrivacyRequestSource } from "~/types/api/models/PrivacyRequestSource";
import type { CustomConfigField } from "~/types/config";
import { FormValues } from "~/types/forms";

const useConsentRequestForm = ({
  onClose,
  setCurrentView,
  setConsentRequestId,
  isVerificationRequired,
  successHandler,
}: {
  onClose: () => void;
  setCurrentView: (view: ModalViews) => void;
  setConsentRequestId: (id: string) => void;
  isVerificationRequired: boolean;
  successHandler: () => void;
}) => {
  const config = useConfig();
  const identityInputs =
    config.consent?.button.identity_inputs ?? DEFAULT_IDENTITY_INPUTS;
  const customPrivacyRequestFields =
    (config.consent?.button.custom_privacy_request_fields ??
      {}) as Record<string, CustomConfigField>;
  const settings = useSettings();
  const { BASE_64_COOKIE } = settings;
  const toast = useToast();
  const [cookie, setCookie] = useState<Awaited<
    ReturnType<typeof getOrMakeFidesCookie>
  > | null>(null);
  const [validationError, setValidationError] = useState(false);

  useEffect(() => {
    const loadCookie = async () => {
      const loadedCookie = await getOrMakeFidesCookie();
      setCookie(loadedCookie);
    };
    loadCookie();
  }, []);

  // Use our custom hook for form field logic
  const { getInitialValues, getValidationSchema } = useCustomFieldsForm({
    customPrivacyRequestFields,
    searchParams: null, // ConsentRequestForm doesn't use URL params
  });

  const initialValues = getInitialValues();

  // Ref to hold current applicable fields — read inside validate/onSubmit closures
  const applicableFieldsRef = useRef<Set<string>>(
    new Set(Object.keys(customPrivacyRequestFields)),
  );

  // Build the static portion of the validation schema (identity fields)
  const identityValidationSchema = Yup.object().shape({
    email: emailValidation(identityInputs?.email!).test(
      "one of email or phone entered",
      "You must enter an email",
      (_value, context) => {
        if (identityInputs?.email === "required") {
          return Boolean(context.parent.email);
        }
        return true;
      },
    ),
    phone: phoneValidation(identityInputs?.phone!).test(
      "one of email or phone entered",
      "You must enter a phone number",
      (_value, context) => {
        if (identityInputs?.phone === "required") {
          return Boolean(context.parent.phone);
        }
        return true;
      },
    ),
  });

  // Cache the last applicable-aware schema
  const schemaCache = useRef<{
    applicableKey: string;
    schema: Yup.AnyObjectSchema;
  } | null>(null);

  const formik = useFormik<FormValues>({
    initialValues: {
      email: "",
      phone: "",
      ...initialValues,
    },
    onSubmit: async (values) => {
      if (!cookie) {
        return;
      }

      const { email, phone, ...customPrivacyRequestFieldValues } = values;

      // populate the values from the form or from the field's default value,
      // excluding fields gated off by display_condition
      const transformedCustomPrivacyRequestFields = Object.fromEntries(
        Object.entries(customPrivacyRequestFields ?? {})
          .filter(([key, field]) => {
            // Keep hidden fields (they use default_value)
            if (field.hidden) {
              return true;
            }
            // Exclude fields gated off by display_condition
            return applicableFieldsRef.current.has(key);
          })
          .map(([key, field]) => [
            key,
            {
              label: field.label,
              value: field.hidden
                ? field.default_value
                : customPrivacyRequestFieldValues[key] || "",
            },
          ]),
      );

      const body = {
        // Marshall empty strings back to `undefined` so the backend will not try to validate
        identity: {
          email: email === "" ? undefined : email,
          phone_number: phone === "" ? undefined : phone,
          fides_user_device_id: cookie.identity.fides_user_device_id,
        },
        custom_privacy_request_fields: transformedCustomPrivacyRequestFields,
        source: PrivacyRequestSource.PRIVACY_CENTER,
      };
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
          `${settings.FIDES_API_URL}/${VerificationType.ConsentRequest}`,
          {
            method: "POST",
            headers: headers as unknown as HeadersInit,
            body: JSON.stringify(body),
          },
        );
        const data = await response.json();
        if (!response.ok) {
          handleError({
            title: "An error occurred while creating your consent request",
            error: data?.detail,
          });
          return;
        }

        if (!data.consent_request_id) {
          handleError({ title: "No consent request id found" });
          return;
        }

        // After successfully initializing a consent request, save the current
        // cookie with our unique fides_user_device_id, etc.
        try {
          await saveFidesCookie(cookie, { base64Cookie: BASE_64_COOKIE });
        } catch (error) {
          handleError({ title: "Could not save consent cookie" });
          return;
        }

        if (!isVerificationRequired) {
          setConsentRequestId(data.consent_request_id);
          successHandler();
        } else {
          setConsentRequestId(data.consent_request_id);
          setCurrentView(ModalViews.IdentityVerification);
        }
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error(error);
        handleError({ title: "An unhandled exception occurred." });
      }
    },

    validate: (values) => {
      setValidationError(false);
      const currentApplicable = applicableFieldsRef.current;
      const applicableKey = Array.from(currentApplicable).sort().join(",");
      let combinedSchema: Yup.AnyObjectSchema;

      if (schemaCache.current?.applicableKey === applicableKey) {
        combinedSchema = schemaCache.current.schema;
      } else {
        const customFieldSchema = getValidationSchema(currentApplicable);
        combinedSchema = identityValidationSchema.concat(
          customFieldSchema,
        ) as Yup.AnyObjectSchema;
        schemaCache.current = { applicableKey, schema: combinedSchema };
      }

      try {
        combinedSchema.validateSync(values, { abortEarly: false });
        return {};
      } catch (err) {
        if (err instanceof Yup.ValidationError) {
          const errors: Record<string, string> = {};
          err.inner.forEach((e) => {
            if (e.path && !errors[e.path]) {
              errors[e.path] = e.message;
            }
          });
          return errors;
        }
        setValidationError(true);
        return { _form: "An unexpected error occurred." };
      }
    },
  });

  // Resolve which custom fields are applicable based on current form values
  const applicableFields = useApplicableFields(
    customPrivacyRequestFields,
    formik.values,
  );
  useEffect(() => {
    applicableFieldsRef.current = applicableFields;
  }, [applicableFields]);

  // Clear values when fields become non-applicable
  const prevApplicable = useRef<Set<string>>(applicableFields);
  useEffect(() => {
    const prev = prevApplicable.current;
    prevApplicable.current = applicableFields;

    prev.forEach((key) => {
      if (!applicableFields.has(key) && key in customPrivacyRequestFields) {
        const fieldInitial = initialValues[key];
        if (formik.values[key] !== fieldInitial) {
          formik.setFieldValue(key, fieldInitial ?? "");
        }
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [applicableFields]);

  return {
    ...formik,
    identityInputs,
    customPrivacyRequestFields,
    applicableFields,
    validationError,
  };
};

export default useConsentRequestForm;
