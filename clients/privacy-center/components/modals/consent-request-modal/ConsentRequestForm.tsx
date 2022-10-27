import React, { useEffect, useState } from "react";
import {
  Button,
  chakra,
  FormControl,
  FormErrorMessage,
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

import { hostUrl } from "~/constants";
import { ModalViews, VerificationType } from "../types";

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
    },
    onSubmit: async (values) => {
      setIsLoading(true);

      const body = {
        email: values.email,
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
    validate: (values) => {
      const errors: {
        email?: string;
        phone?: string;
      } = {};

      if (!values.email) {
        errors.email = "Required";
      }

      return errors;
    },
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
      <chakra.form onSubmit={handleSubmit}>
        <ModalBody>
          {isVerificationRequired ? (
            <Text fontSize="sm" color="gray.500" mb={4}>
              We will email you a verification code.
            </Text>
          ) : null}
          <Stack spacing={3}>
            <FormControl
              id="email"
              isInvalid={touched.email && Boolean(errors.email)}
            >
              <Input
                id="email"
                name="email"
                type="email"
                focusBorderColor="primary.500"
                placeholder="Email*"
                isRequired
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.email}
                isInvalid={touched.email && Boolean(errors.email)}
              />
              <FormErrorMessage>{errors.email}</FormErrorMessage>
            </FormControl>
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
