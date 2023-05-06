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
import React, { useEffect } from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import { Headers } from "headers-polyfill";

import { addCommonHeaders } from "~/common/CommonHeaders";
import { ErrorToastOptions, SuccessToastOptions } from "~/common/toast-options";
import { PrivacyRequestStatus } from "~/types";
import { PrivacyRequestOption } from "~/types/config";
import { defaultIdentityInput } from "~/constants";
import { PhoneInput } from "~/components/phone-input";
import { ModalViews } from "~/components/modals/types";
import { FormErrorMessage } from "~/components/FormErrorMessage";
import {
  emailValidation,
  nameValidation,
  phoneValidation,
} from "~/components/modals/validation";
import { useConfig } from "~/features/common/config.slice";
import { useSettings } from "~/features/common/settings.slice";

const usePrivacyRequestForm = ({
  onClose,
  action,
  setCurrentView,
  setPrivacyRequestId,
  isVerificationRequired,
}: {
  onClose: () => void;
  action: PrivacyRequestOption | null;
  setCurrentView: (view: ModalViews) => void;
  setPrivacyRequestId: (id: string) => void;
  isVerificationRequired: boolean;
}) => {
  const settings = useSettings();
  const identityInputs = action?.identity_inputs ?? defaultIdentityInput;
  const toast = useToast();
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
          `${settings.FIDES_API_URL}/privacy-request`,
          {
            method: "POST",
            headers,
            body: JSON.stringify(body),
          }
        );
        const data = await response.json();
        if (!response.ok) {
          handleError({
            title: "An error occurred while creating your privacy request",
            error: data?.detail,
          });
          return;
        }

        if (!isVerificationRequired && data.succeeded.length) {
          toast({
            title:
              "Your request was successful, please await further instructions.",
            ...SuccessToastOptions,
          });
        } else if (
          isVerificationRequired &&
          data.succeeded.length &&
          data.succeeded[0].status === PrivacyRequestStatus.IDENTITY_UNVERIFIED
        ) {
          setPrivacyRequestId(data.succeeded[0].id);
          setCurrentView(ModalViews.IdentityVerification);
        } else {
          handleError({
            title:
              "An unhandled error occurred while processing your privacy request",
          });
        }
      } catch (error) {
        handleError({
          title:
            "An unhandled error occurred while creating your privacy request",
        });
        return;
      }

      if (!isVerificationRequired) {
        onClose();
      }
    },
    validationSchema: Yup.object().shape({
      name: nameValidation(identityInputs?.name),
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

type PrivacyRequestFormProps = {
  isOpen: boolean;
  onClose: () => void;
  openAction: string | null;
  setCurrentView: (view: ModalViews) => void;
  setPrivacyRequestId: (id: string) => void;
  isVerificationRequired: boolean;
};

const PrivacyRequestForm: React.FC<PrivacyRequestFormProps> = ({
  isOpen,
  onClose,
  openAction,
  setCurrentView,
  setPrivacyRequestId,
  isVerificationRequired,
}) => {
  const config = useConfig();
  const action = openAction
    ? config.actions.filter(({ policy_key }) => policy_key === openAction)[0]
    : null;

  const {
    errors,
    handleBlur,
    handleChange,
    handleSubmit,
    setFieldValue,
    touched,
    values,
    isValid,
    isSubmitting,
    dirty,
    resetForm,
    identityInputs,
  } = usePrivacyRequestForm({
    onClose,
    action,
    setCurrentView,
    setPrivacyRequestId,
    isVerificationRequired,
  });

  useEffect(() => resetForm(), [isOpen, resetForm]);

  if (!action) {
    return null;
  }

  return (
    <>
      <ModalHeader pt={6} pb={0}>
        {action.title}
      </ModalHeader>
      <chakra.form onSubmit={handleSubmit} data-testid="privacy-request-form">
        <ModalBody>
          <Text fontSize="sm" color="gray.600" mb={4}>
            {action.description}
          </Text>
          {action.description_subtext?.map((paragraph, index) => (
            // eslint-disable-next-line react/no-array-index-key
            <Text fontSize="sm" color="gray.600" mb={4} key={index}>
              {paragraph}
            </Text>
          ))}
          <Stack>
            {identityInputs.name ? (
              <FormControl
                id="name"
                isInvalid={touched.name && Boolean(errors.name)}
                isRequired={identityInputs.name === "required"}
              >
                <FormLabel fontSize="sm">Name</FormLabel>
                <Input
                  id="name"
                  name="name"
                  focusBorderColor="primary.500"
                  placeholder="Michael Brown"
                  onChange={handleChange}
                  onBlur={handleBlur}
                  value={values.name}
                />
                <FormErrorMessage>{errors.name}</FormErrorMessage>
              </FormControl>
            ) : null}
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
                  isDisabled={Boolean(
                    typeof values.phone !== "undefined" && values.phone
                  )}
                />
                <FormErrorMessage>{errors.email}</FormErrorMessage>
              </FormControl>
            ) : null}
            {identityInputs.phone ? (
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
                  isDisabled={Boolean(
                    typeof values.email !== "undefined" && values.email
                  )}
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
            isDisabled={isSubmitting || !(isValid && dirty)}
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
