import React, { useEffect, useState } from "react";
import {
  Button,
  chakra,
  FormControl,
  FormErrorMessage,
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

import { ErrorToastOptions } from "~/common/toast-options";

import { Headers } from "headers-polyfill";
import { addCommonHeaders } from "~/common/CommonHeaders";

import { config, hostUrl } from "~/constants";
import dynamic from "next/dynamic";
import * as Yup from "yup";
import { ModalViews, VerificationType } from "../types";

const PhoneInput = dynamic(() => import("react-phone-number-input"), {
  ssr: false,
});

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
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();
  const formik = useFormik({
    initialValues: {
      email: "",
      phone: "",
    },
    onSubmit: async (values) => {
      setIsLoading(true);

      const body = {
        email: values.email,
        phone_number: values.phone,
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
      email: (() => {
        let validation = Yup.string();
        if (config.consent?.identity_inputs?.email === "required") {
          validation = validation
            .email("Email is invalid")
            .required("Email is required");
        }
        return validation;
      })(),
      phone: (() => {
        let validation = Yup.string();
        if (config.consent?.identity_inputs?.phone === "required") {
          validation = validation
            .required("Phone is required")
            // E.164 international standard format
            .matches(/^\+[1-9]\d{1,14}$/, "Phone is invalid");
        }
        return validation;
      })(),
    }),
  });

  return { ...formik, isLoading };
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
    dirty,
    setFieldValue,
    resetForm,
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
          <Stack spacing={3}>
            {config.consent?.identity_inputs?.email ? (
              <FormControl
                id="email"
                isInvalid={touched.email && Boolean(errors.email)}
              >
                <FormLabel>
                  {config.consent?.identity_inputs.email === "required"
                    ? "Email*"
                    : "Email"}
                </FormLabel>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  focusBorderColor="primary.500"
                  placeholder="test-email@example.com"
                  onChange={handleChange}
                  onBlur={handleBlur}
                  value={values.email}
                  isInvalid={touched.email && Boolean(errors.email)}
                />
                <FormErrorMessage>{errors.email}</FormErrorMessage>
              </FormControl>
            ) : null}
            {config.consent?.identity_inputs?.phone ? (
              <FormControl
                id="phone"
                isInvalid={touched.phone && Boolean(errors.phone)}
              >
                <FormLabel>
                  {config.consent?.identity_inputs.phone === "required"
                    ? "Phone*"
                    : "Phone"}
                </FormLabel>
                <Input
                  as={PhoneInput}
                  id="phone"
                  name="phone"
                  type="tel"
                  focusBorderColor="primary.500"
                  placeholder="000 000 0000"
                  defaultCountry="US"
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
            disabled={!(isValid && dirty)}
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
