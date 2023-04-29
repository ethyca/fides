import React, { useEffect, useMemo } from "react";
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
} from "@fidesui/react";
import { getOrMakeFidesCookie, saveFidesCookie } from "fides-consent";
import { useFormik } from "formik";
import { Headers } from "headers-polyfill";
import * as Yup from "yup";

import { getPrivacyCenterEnvironment } from "~/app/server-environment";
import { ErrorToastOptions } from "~/common/toast-options";
import { addCommonHeaders } from "~/common/CommonHeaders";
import { defaultIdentityInput } from "~/constants";
import { PhoneInput } from "~/components/phone-input";
import { FormErrorMessage } from "~/components/FormErrorMessage";
import {
  emailValidation,
  phoneValidation,
} from "~/components/modals/validation";
import { ModalViews, VerificationType } from "~/components/modals/types";
import { useConfig } from "~/features/common/config.slice";

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
  // TODO: this "defaultIdentityInput" feels unnecessary and could be handled in the redux state?
  const identityInputs =
    config.consent?.button.identity_inputs ?? defaultIdentityInput;
  const environment = getPrivacyCenterEnvironment();
  const toast = useToast();
  const cookie = useMemo(() => getOrMakeFidesCookie(), []);
  const formik = useFormik({
    initialValues: {
      email: "",
      phone: "",
    },
    onSubmit: async (values) => {
      const body = {
        // Marshall empty strings back to `undefined` so the backend will not try to validate
        email: values.email === "" ? undefined : values.email,
        phone_number: values.phone === "" ? undefined : values.phone,
        fides_user_device_id: cookie.identity.fides_user_device_id,
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
          `${environment.fidesApiUrl}/${VerificationType.ConsentRequest}`,
          {
            method: "POST",
            headers,
            body: JSON.stringify(body),
          }
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
          saveFidesCookie(cookie);
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
      email: emailValidation(identityInputs?.email).test(
        "one of email or phone entered",
        "You must enter either email or phone",
        (value, context) => {
          if (
            identityInputs?.email === "optional" &&
            identityInputs?.phone === "optional"
          ) {
            return Boolean(context.parent.phone || context.parent.email);
          }
          return true;
        }
      ),
      phone: phoneValidation(identityInputs?.phone).test(
        "one of email or phone entered",
        "You must enter either email or phone",
        (value, context) => {
          if (
            identityInputs?.email === "optional" &&
            identityInputs?.phone === "optional"
          ) {
            return Boolean(context.parent.phone || context.parent.email);
          }
          return true;
        }
      ),
    }),
  });

  return { ...formik, identityInputs };
};

type ConsentRequestFormProps = {
  isOpen: boolean;
  onClose: () => void;
  setCurrentView: (view: ModalViews) => void;
  setConsentRequestId: (id: string) => void;
  isVerificationRequired: boolean;
  successHandler: () => void;
};

const ConsentRequestForm: React.FC<ConsentRequestFormProps> = ({
  isOpen,
  onClose,
  setCurrentView,
  setConsentRequestId,
  isVerificationRequired,
  successHandler,
}) => {
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
  } = useConsentRequestForm({
    onClose,
    setCurrentView,
    setConsentRequestId,
    isVerificationRequired,
    successHandler,
  });

  const requiredInputs = Object.entries(identityInputs).filter(
    ([, required]) => required === "required"
  );
  // it's ok to bypass the dirty check if there are no required inputs
  const dirtyCheck = requiredInputs.length === 0 ? true : dirty;

  useEffect(() => resetForm(), [isOpen, resetForm]);

  return (
    <>
      <ModalHeader pt={6} pb={0}>
        {config.consent?.button.title}
      </ModalHeader>
      <chakra.form onSubmit={handleSubmit} data-testid="consent-request-form">
        <ModalBody>
          <Text fontSize="sm" color="gray.600" mb={4}>
            {config.consent?.button.description}
          </Text>
          {config.consent?.button.description_subtext?.map(
            (paragraph, index) => (
              // eslint-disable-next-line react/no-array-index-key
              <Text fontSize="sm" color="gray.600" mb={4} key={index}>
                {paragraph}
              </Text>
            )
          )}
          {isVerificationRequired ? (
            <Text fontSize="sm" color="gray.600" mb={4}>
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
                  isDisabled={Boolean(
                    typeof values.phone !== "undefined" && values.phone
                  )}
                />
                <FormErrorMessage>{errors.email}</FormErrorMessage>
              </FormControl>
            ) : null}
            {identityInputs?.phone ? (
              <FormControl
                id="phone"
                isInvalid={touched.phone && Boolean(errors.phone)}
                isRequired={identityInputs.phone === "required"}
                isDisabled={Boolean(
                  typeof values.email !== "undefined" && values.email
                )}
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
          </Stack>
        </ModalBody>

        <ModalFooter pb={6}>
          <Button variant="outline" flex="1" mr={3} size="sm" onClick={onClose}>
            Cancel
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
            Continue
          </Button>
        </ModalFooter>
      </chakra.form>
    </>
  );
};

export default ConsentRequestForm;
