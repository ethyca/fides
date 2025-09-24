import { getOrMakeFidesCookie, saveFidesCookie } from "fides-js";
import { useToast } from "fidesui";
import { useFormik } from "formik";
import { Headers } from "headers-polyfill";
import { useMemo } from "react";
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
import { useCustomFieldsForm } from "~/hooks/useCustomFieldsForm";
import { PrivacyRequestSource } from "~/types/api/models/PrivacyRequestSource";
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
    config.consent?.button.custom_privacy_request_fields ?? {};
  const settings = useSettings();
  const { BASE_64_COOKIE } = settings;
  const toast = useToast();
  const cookie = useMemo(() => getOrMakeFidesCookie(), []);

  // Use our custom hook for form field logic
  const { getInitialValues, getValidationSchema } = useCustomFieldsForm({
    customPrivacyRequestFields: customPrivacyRequestFields as any,
    searchParams: null, // ConsentRequestForm doesn't use URL params
  });

  const formik = useFormik<FormValues>({
    initialValues: {
      email: "",
      phone: "",
      ...getInitialValues(),
    },
    onSubmit: async (values) => {
      const { email, phone, ...customPrivacyRequestFieldValues } = values;

      // populate the values from the form or from the field's default value
      const transformedCustomPrivacyRequestFields = Object.fromEntries(
        Object.entries(customPrivacyRequestFields ?? {}).map(([key, field]) => [
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
            headers,
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
          saveFidesCookie(cookie, BASE_64_COOKIE);
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
    validationSchema: Yup.object().shape({
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
      ...getValidationSchema().fields,
    }),
  });

  return { ...formik, identityInputs, customPrivacyRequestFields };
};

export default useConsentRequestForm;
