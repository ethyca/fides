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
import { ModalViews, VerificationType } from "./types";
import { addCommonHeaders } from "../../common/CommonHeaders";
import { useLocalStorage } from "../../common/hooks";

import { hostUrl } from "../../constants";

const useVerificationForm = ({
  onClose,
  setAlert,
  requestId,
  setCurrentView,
  resetView,
  verificationType,
  successHandler,
}: {
  onClose: () => void;
  setAlert: (state: AlertState) => void;
  requestId: string;
  setCurrentView: (view: ModalViews) => void;
  resetView: ModalViews;
  verificationType: VerificationType;
  successHandler: () => void;
}) => {
  const [isLoading, setIsLoading] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [verificationCode, setVerificationCode] = useLocalStorage(
    "verificationCode",
    ""
  );
  const resetVerificationProcess = useCallback(() => {
    setCurrentView(resetView);
  }, [setCurrentView, resetView]);

  const formik = useFormik({
    initialValues: {
      code: "",
    },
    onSubmit: async (values) => {
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
          `${hostUrl}/${verificationType}/${requestId}/verify`,
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
        setVerificationCode(values.code);
        successHandler();
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
  setAlert: (state: AlertState) => void;
  requestId: string;
  setCurrentView: (view: ModalViews) => void;
  resetView: ModalViews;
  verificationType: VerificationType;
  successHandler: () => void;
};

const VerificationForm: React.FC<VerificationFormProps> = ({
  isOpen,
  onClose,
  setAlert,
  requestId,
  setCurrentView,
  resetView,
  verificationType,
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
    resetVerificationProcess,
  } = useVerificationForm({
    onClose,
    setAlert,
    requestId,
    setCurrentView,
    resetView,
    verificationType,
    successHandler,
  });

  useEffect(() => resetForm(), [isOpen, resetForm]);

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
