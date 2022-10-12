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
} from "@fidesui/react";

import { useFormik } from "formik";

import { Headers } from "headers-polyfill";
import type { AlertState } from "../../../types/AlertState";
import { addCommonHeaders } from "../../../common/CommonHeaders";

import { ModalViews, VerificationType } from "../types";
import { hostUrl } from "../../../constants";

const useConsentRequestForm = ({
  onClose,
  setAlert,
  setCurrentView,
  setConsentRequestId,
  isVerificationRequired,
}: {
  onClose: () => void;
  setAlert: (state: AlertState) => void;
  setCurrentView: (view: ModalViews) => void;
  setConsentRequestId: (id: string) => void;
  isVerificationRequired: boolean;
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const formik = useFormik({
    initialValues: {
      email: "",
    },
    onSubmit: async (values) => {
      setIsLoading(true);

      const body = {
        email: values.email,
      };
      const handleError = () => {
        setAlert({
          status: "error",
          description: "Your request has failed. Please try again.",
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

        if (!response.ok) {
          handleError();
          return;
        }

        const data = await response.json();

        if (!isVerificationRequired && data.consent_request_id) {
          setAlert({
            status: "success",
            description:
              "Your request was successful, please await further instructions.",
          });
        } else if (isVerificationRequired && data.consent_request_id) {
          setConsentRequestId(data.consent_request_id);
          setCurrentView(ModalViews.IdentityVerification);
        } else {
          handleError();
        }
      } catch (error) {
        handleError();
        return;
      }

      if (!isVerificationRequired) {
        onClose();
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
  setAlert: (state: AlertState) => void;
  setCurrentView: (view: ModalViews) => void;
  setConsentRequestId: (id: string) => void;
  isVerificationRequired: boolean;
};

const ConsentRequestForm: React.FC<ConsentRequestFormProps> = ({
  isOpen,
  onClose,
  setAlert,
  setCurrentView,
  setConsentRequestId,
  isVerificationRequired,
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
    setAlert,
    setCurrentView,
    setConsentRequestId,
    isVerificationRequired,
  });

  useEffect(() => resetForm(), [isOpen, resetForm]);

  return (
    <>
      <ModalHeader pt={6} pb={0}>
        Manage your consent
      </ModalHeader>
      <chakra.form onSubmit={handleSubmit}>
        <ModalBody>
          <Text fontSize="sm" color="gray.500" mb={4}>
            We will email you a report of the data from your account.
          </Text>
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
