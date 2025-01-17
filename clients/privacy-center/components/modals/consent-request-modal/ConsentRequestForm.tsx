import { getOrMakeFidesCookie, saveFidesCookie } from "fides-js";
import {
  Button,
  chakra,
  FormControl,
  FormLabel,
  Input,
  ModalBody,
  ModalFooter,
  ModalHeader,
  Stack,
  Text,
  useToast,
} from "fidesui";
import { useFormik } from "formik";
import { Headers } from "headers-polyfill";
import React, { ReactNode, useEffect, useMemo } from "react";
import * as Yup from "yup";

import { addCommonHeaders } from "~/common/CommonHeaders";
import { ErrorToastOptions } from "~/common/toast-options";
import { FormErrorMessage } from "~/components/FormErrorMessage";
import { ModalViews, VerificationType } from "~/components/modals/types";
import {
  emailValidation,
  phoneValidation,
} from "~/components/modals/validation";
import { PhoneInput } from "~/components/phone-input";
import { defaultIdentityInput } from "~/constants";
import { useConfig } from "~/features/common/config.slice";
import { useSettings } from "~/features/common/settings.slice";
import { PrivacyRequestSource } from "~/types/api/models/PrivacyRequestSource";

type KnownKeys = {
  email: string;
  phone: string;
};

type FormValues = KnownKeys & {
  [key: string]: any;
};

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
    config.consent?.button.identity_inputs ?? defaultIdentityInput;
  const customPrivacyRequestFields =
    config.consent?.button.custom_privacy_request_fields ?? {};
  const settings = useSettings();
  const { BASE_64_COOKIE } = settings;
  const toast = useToast();
  const cookie = useMemo(() => getOrMakeFidesCookie(), []);
  const formik = useFormik<FormValues>({
    initialValues: {
      email: "",
      phone: "",
      ...Object.fromEntries(
        Object.entries(customPrivacyRequestFields)
          .filter(([, field]) => !field.hidden)
          .map(([key, field]) => [key, field.default_value || ""]),
      ),
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
        (value, context) => {
          if (identityInputs?.email === "required") {
            return Boolean(context.parent.email);
          }
          return true;
        },
      ),
      phone: phoneValidation(identityInputs?.phone!).test(
        "one of email or phone entered",
        "You must enter a phone number",
        (value, context) => {
          if (identityInputs?.phone === "required") {
            return Boolean(context.parent.phone);
          }
          return true;
        },
      ),
      ...Object.fromEntries(
        Object.entries(customPrivacyRequestFields)
          .filter(([, field]) => !field.hidden)
          .map(([key, { label, required }]) => {
            const isRequired = required !== false;
            return [
              key,
              isRequired
                ? Yup.string().required(`${label} is required`)
                : Yup.string().notRequired(),
            ];
          }),
      ),
    }),
  });

  return { ...formik, identityInputs, customPrivacyRequestFields };
};

type ConsentRequestFormProps = {
  isOpen: boolean;
  onClose: () => void;
  setCurrentView: (view: ModalViews) => void;
  setConsentRequestId: (id: string) => void;
  isVerificationRequired: boolean;
  successHandler: () => void;
};

const ConsentRequestForm = ({
  isOpen,
  onClose,
  setCurrentView,
  setConsentRequestId,
  isVerificationRequired,
  successHandler,
}: ConsentRequestFormProps) => {
  const {
    errors,
    handleBlur,
    handleChange,
    handleSubmit,
    touched,
    values,
    isValid,
    isSubmitting,
    dirty,
    setFieldValue,
    resetForm,
    identityInputs,
    customPrivacyRequestFields,
  } = useConsentRequestForm({
    onClose,
    setCurrentView,
    setConsentRequestId,
    isVerificationRequired,
    successHandler,
  });

  const config = useConfig();

  const requiredInputs = Object.entries(identityInputs).filter(
    ([, required]) => required === "required",
  );
  // it's ok to bypass the dirty check if there are no required inputs
  const dirtyCheck = requiredInputs.length === 0 ? true : dirty;

  useEffect(() => resetForm(), [isOpen, resetForm]);

  return (
    <>
      <ModalHeader pt={6} pb={0}>
        {config.consent?.button.modalTitle || config.consent?.button.title}
      </ModalHeader>
      <chakra.form onSubmit={handleSubmit} data-testid="consent-request-form">
        <ModalBody>
          <Text fontSize="sm" color="gray.800" mb={4}>
            {config.consent?.button.description}
          </Text>
          {config.consent?.button.description_subtext?.map(
            (paragraph, index) => (
              // eslint-disable-next-line react/no-array-index-key
              <Text fontSize="sm" color="gray.800" mb={4} key={index}>
                {paragraph}
              </Text>
            ),
          )}
          {isVerificationRequired ? (
            <Text fontSize="sm" color="gray.800" mb={4}>
              We will send you a verification code.
            </Text>
          ) : null}
          <Stack>
            {identityInputs.email ? (
              <FormControl
                id="email"
                isInvalid={touched.email && Boolean(errors.email)}
                isRequired={identityInputs.email === "required"}
              >
                <FormLabel fontSize="sm">Email</FormLabel>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  focusBorderColor="primary.500"
                  placeholder="your-email@example.com"
                  onChange={handleChange}
                  onBlur={handleBlur}
                  value={values.email}
                  isInvalid={touched.email && Boolean(errors.email)}
                />
                <FormErrorMessage>{errors.email}</FormErrorMessage>
              </FormControl>
            ) : null}
            {identityInputs?.phone ? (
              <FormControl
                id="phone"
                isInvalid={touched.phone && Boolean(errors.phone)}
                isRequired={identityInputs.phone === "required"}
              >
                <FormLabel fontSize="sm">Phone</FormLabel>
                <PhoneInput
                  id="phone"
                  name="phone"
                  onChange={(value) => {
                    setFieldValue("phone", value, true);
                  }}
                  onBlur={handleBlur}
                  value={values.phone}
                />
                <FormErrorMessage>{errors.phone}</FormErrorMessage>
              </FormControl>
            ) : null}
            {Object.entries(customPrivacyRequestFields)
              .filter(([, field]) => !field.hidden)
              .map(([key, item]) => (
                <FormControl
                  key={key}
                  id={key}
                  isInvalid={touched[key] && Boolean(errors[key])}
                  isRequired={item.required !== false}
                >
                  <FormLabel fontSize="sm">{item.label}</FormLabel>
                  <Input
                    id={key}
                    name={key}
                    focusBorderColor="primary.500"
                    onChange={handleChange}
                    onBlur={handleBlur}
                    value={values[key]}
                  />
                  <FormErrorMessage>
                    {errors[key] as ReactNode}
                  </FormErrorMessage>
                </FormControl>
              ))}
          </Stack>
        </ModalBody>

        <ModalFooter pb={6}>
          <Button variant="outline" flex="1" mr={3} size="sm" onClick={onClose}>
            {config.consent?.button.cancelButtonText || "Cancel"}
          </Button>
          <Button
            type="submit"
            flex="1"
            bg="primary.800"
            _hover={{ bg: "primary.400" }}
            _active={{ bg: "primary.500" }}
            colorScheme="primary"
            isLoading={isSubmitting}
            isDisabled={isSubmitting || !(isValid && dirtyCheck)}
            size="sm"
          >
            {config.consent?.button.confirmButtonText || "Continue"}
          </Button>
        </ModalFooter>
      </chakra.form>
    </>
  );
};

export default ConsentRequestForm;
