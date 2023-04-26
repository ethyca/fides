import React, { useEffect } from "react";
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
import { useFormik } from "formik";
import { Headers } from "headers-polyfill";
import * as Yup from "yup";

import { ErrorToastOptions } from "~/common/toast-options";
import { addCommonHeaders } from "~/common/CommonHeaders";
import { config, defaultIdentityInput, hostUrl } from "~/constants";
import { PhoneInput } from "~/components/phone-input";
import { FormErrorMessage } from "~/components/FormErrorMessage";
import {
  emailValidation,
  phoneValidation,
} from "~/components/modals/validation";
import { ModalViews, VerificationType } from "~/components/modals/types";
import { useFidesUserDeviceIdCookie } from "~/common/hooks/useCookie";

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
  const identityInputs =
    config.consent?.button.identity_inputs ?? defaultIdentityInput;
  const fidesUserDeviceId = useFidesUserDeviceIdCookie();
  const toast = useToast();
  const formik = useFormik({
    initialValues: {
      email: undefined,
      phone: undefined,
    },
    onSubmit: async (values) => {
      const body = {
        email: values.email,
        phone_number: values.phone,
        fides_user_device_id: fidesUserDeviceId
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
          `${hostUrl}/${VerificationType.ConsentRequest}`,
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

  useEffect(() => resetForm(), [isOpen, resetForm]);

  return (
    <>
      <ModalHeader pt={6} pb={0}>
        Manage your consent
      </ModalHeader>
      <chakra.form onSubmit={handleSubmit} data-testid="consent-request-form">
        <ModalBody>
          {isVerificationRequired ? (
            <Text fontSize="sm" color="gray.500" mb={4}>
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
                <FormLabel>Email</FormLabel>
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
                <FormLabel>Phone</FormLabel>
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
            // isDisabled={isSubmitting || !(isValid && dirty)}
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
