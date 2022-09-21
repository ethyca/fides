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
import { PrivacyRequestStatus } from "../../../types";
import { addCommonHeaders } from "../../../common/CommonHeaders";

import config from "../../../config/config.json";

import { ModalViews } from "../types";
import { hostUrl } from "../../../constants";

const usePrivacyRequestForm = ({
  onClose,
  action,
  setAlert,
  setCurrentView,
  setPrivacyRequestId,
  isVerificationRequired,
}: {
  onClose: () => void;
  action: typeof config.actions[0] | null;
  setAlert: (state: AlertState) => void;
  setCurrentView: (view: ModalViews) => void;
  setPrivacyRequestId: (id: string) => void;
  isVerificationRequired: boolean;
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const formik = useFormik({
    initialValues: {
      name: "",
      email: "",
      phone: "",
    },
    onSubmit: async (values) => {
      if (!action) {
        // somehow we've reached a broken state, return
        return;
      }

      setIsLoading(true);

      const body = [
        {
          identity: {
            email: values.email,
            phone_number: values.phone,
            // enable this when name field is supported on the server
            // name: values.name
          },
          policy_key: action.policy_key,
        },
      ];

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

        const response = await fetch(`${hostUrl}/privacy-request`, {
          method: "POST",
          headers,
          body: JSON.stringify(body),
        });

        if (!response.ok) {
          handleError();
          return;
        }

        const data = await response.json();

        if (!isVerificationRequired && data.succeeded.length) {
          setAlert({
            status: "success",
            description:
              "Your request was successful, please await further instructions.",
          });
        } else if (
          isVerificationRequired &&
          data.succeeded.length &&
          data.succeeded[0].status === PrivacyRequestStatus.IDENTITY_UNVERIFIED
        ) {
          setPrivacyRequestId(data.succeeded[0].id);
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
      if (!action) return {};
      const errors: {
        name?: string;
        email?: string;
        phone?: string;
      } = {};

      if (!values.email && action.identity_inputs.email === "required") {
        errors.email = "Required";
      }

      if (!values.name && action.identity_inputs.name === "required") {
        errors.name = "Required";
      }

      if (!values.phone && action.identity_inputs.phone === "required") {
        errors.phone = "Required";
      }

      return errors;
    },
  });

  return { ...formik, isLoading };
};

type PrivacyRequestFormProps = {
  isOpen: boolean;
  onClose: () => void;
  openAction: string | null;
  setAlert: (state: AlertState) => void;
  setCurrentView: (view: ModalViews) => void;
  setPrivacyRequestId: (id: string) => void;
  isVerificationRequired: boolean;
};

const PrivacyRequestForm: React.FC<PrivacyRequestFormProps> = ({
  isOpen,
  onClose,
  openAction,
  setAlert,
  setCurrentView,
  setPrivacyRequestId,
  isVerificationRequired,
}) => {
  const action = openAction
    ? config.actions.filter(({ policy_key }) => policy_key === openAction)[0]
    : null;

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
  } = usePrivacyRequestForm({
    onClose,
    action,
    setAlert,
    setCurrentView,
    setPrivacyRequestId,
    isVerificationRequired,
  });

  useEffect(() => resetForm(), [isOpen, resetForm]);

  if (!action) return null;

  return (
    <>
      <ModalHeader pt={6} pb={0}>
        {action.title}
      </ModalHeader>
      <chakra.form onSubmit={handleSubmit}>
        <ModalBody>
          <Text fontSize="sm" color="gray.500" mb={4}>
            {action.description}
          </Text>
          <Stack spacing={3}>
            {action.identity_inputs.name ? (
              <FormControl
                id="name"
                isInvalid={touched.name && Boolean(errors.name)}
              >
                <Input
                  id="name"
                  name="name"
                  focusBorderColor="primary.500"
                  placeholder={
                    action.identity_inputs.name === "required"
                      ? "Name*"
                      : "Name"
                  }
                  isRequired={action.identity_inputs.name === "required"}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  value={values.name}
                  isInvalid={touched.name && Boolean(errors.name)}
                />
                <FormErrorMessage>{errors.name}</FormErrorMessage>
              </FormControl>
            ) : null}
            {action.identity_inputs.email ? (
              <FormControl
                id="email"
                isInvalid={touched.email && Boolean(errors.email)}
              >
                <Input
                  id="email"
                  name="email"
                  type="email"
                  focusBorderColor="primary.500"
                  placeholder={
                    action.identity_inputs.email === "required"
                      ? "Email*"
                      : "Email"
                  }
                  isRequired={action.identity_inputs.email === "required"}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  value={values.email}
                  isInvalid={touched.email && Boolean(errors.email)}
                />
                <FormErrorMessage>{errors.email}</FormErrorMessage>
              </FormControl>
            ) : null}
            {action.identity_inputs.phone ? (
              <FormControl
                id="phone"
                isInvalid={touched.phone && Boolean(errors.phone)}
              >
                <Input
                  id="phone"
                  name="phone"
                  type="phone"
                  focusBorderColor="primary.500"
                  placeholder={
                    action.identity_inputs.phone === "required"
                      ? "Phone*"
                      : "Phone"
                  }
                  isRequired={action.identity_inputs.phone === "required"}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  value={values.phone}
                  isInvalid={touched.phone && Boolean(errors.phone)}
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

export default PrivacyRequestForm;
