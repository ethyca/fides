import React, { useCallback, useEffect, useState } from "react";
import {
  Button,
  chakra,
  FormControl,
  FormErrorMessage,
  HStack,
  Input,
  ModalBody,
  ModalFooter,
  ModalHeader,
  Stack,
  Text,
  VStack,
} from "@fidesui/react";

import { useFormik } from "formik";

import { Headers } from "headers-polyfill";
import type { AlertState } from "../../types/AlertState";
import { ModalViews } from "./types";
import { addCommonHeaders } from "../../common/CommonHeaders";

import config from "../../config/config.json";
import { hostUrl } from "../../constants";

const useVerificationForm = ({
  onClose,
  action,
  setAlert,
  privacyRequestId,
  setCurrentView,
}: {
  onClose: () => void;
  action: typeof config.actions[0] | null;
  setAlert: (state: AlertState) => void;
  privacyRequestId: string;
  setCurrentView: (view: ModalViews) => void;
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const resetVerificationProcess = useCallback(() => {
    setCurrentView(ModalViews.PrivacyRequest);
  }, [setCurrentView]);

  const formik = useFormik({
    initialValues: {
      code: "",
    },
    onSubmit: async (values) => {
      if (!action) {
        // somehow we've reached a broken state, return
        return;
      }

      setIsLoading(true);

      const body = {
        code: values.code,
      };

      const handleError = (detail: string | undefined) => {
        const fallbackMessage =
          "An error occured while verifying your request.";
        setAlert({
          status: "error",
          description: detail || fallbackMessage,
        });
        onClose();
      };
      try {
        const headers: Headers = new Headers();
        addCommonHeaders(headers, null);

        const response = await fetch(
          `${hostUrl}/privacy-request/${privacyRequestId}/verify`,
          {
            method: "POST",
            headers,
            body: JSON.stringify(body),
          }
        );
        const data = await response.json();

        if (!response.ok) {
          handleError(data?.detail);
          return;
        }

        setCurrentView(ModalViews.RequestSubmitted);
      } catch (error) {
        handleError("");
      }
    },
    validate: (values) => {
      const errors: {
        code?: string;
      } = {};

      if (!values.code) {
        errors.code = "Required";
        return errors;
      }
      if (!values.code.match(/^\d+$/g)) {
        errors.code = "Verification code must be all numbers";
      }

      return errors;
    },
  });

  return { ...formik, isLoading, resetVerificationProcess };
};

type VerificationFormProps = {
  isOpen: boolean;
  onClose: () => void;
  openAction: string | null;
  setAlert: (state: AlertState) => void;
  privacyRequestId: string;
  setCurrentView: (view: ModalViews) => void;
};

const VerificationForm: React.FC<VerificationFormProps> = ({
  isOpen,
  onClose,
  openAction,
  setAlert,
  privacyRequestId,
  setCurrentView,
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
    resetVerificationProcess,
  } = useVerificationForm({
    onClose,
    action,
    setAlert,
    privacyRequestId,
    setCurrentView,
  });

  useEffect(() => resetForm(), [isOpen, resetForm]);

  if (!action) return null;

  return (
    <>
      <ModalHeader pt={6} pb={0}>
        Enter verification code
      </ModalHeader>
      <chakra.form onSubmit={handleSubmit}>
        <ModalBody>
          <Text fontSize="sm" color="gray.500" mb={4}>
            We have sent a verification code to your email address. Please check
            your email, then return to this window and the code below.
          </Text>
          <Stack spacing={3}>
            {action.identity_inputs.name ? (
              <FormControl
                id="code"
                isInvalid={touched.code && Boolean(errors.code)}
              >
                <Input
                  id="code"
                  name="code"
                  focusBorderColor="primary.500"
                  placeholder="Verification Code"
                  isRequired
                  onChange={handleChange}
                  onBlur={handleBlur}
                  value={values.code}
                  isInvalid={touched.code && Boolean(errors.code)}
                />
                <FormErrorMessage>{errors.code}</FormErrorMessage>
              </FormControl>
            ) : null}
          </Stack>
        </ModalBody>

        <ModalFooter pb={6}>
          <VStack id="test" width="100%">
            <HStack width="100%">
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
                Submit code
              </Button>
            </HStack>
            <HStack pt="8px" width="100%">
              <Text
                fontSize="sm"
                fontWeight="normal"
                lineHeight={5}
                color="gray.500"
              >
                Didn&apos;t receive a code?
              </Text>{" "}
              <Text
                fontSize="sm"
                fontWeight="normal"
                lineHeight={5}
                color="primary.700"
                textDecoration="underline"
                cursor="pointer"
                _active={{ bg: "primary.500" }}
                onClick={resetVerificationProcess}
              >
                Click here to try again
              </Text>
            </HStack>
          </VStack>
        </ModalFooter>
      </chakra.form>
    </>
  );
};

export default VerificationForm;
