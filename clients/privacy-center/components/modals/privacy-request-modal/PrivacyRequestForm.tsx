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
import { CustomIdentity, PrivacyRequestOption } from "~/types/config";
import { defaultIdentityInput } from "~/constants";
import { PhoneInput } from "~/components/phone-input";
import { ModalViews } from "~/components/modals/types";
import { FormErrorMessage } from "~/components/FormErrorMessage";
import {
  emailValidation,
  phoneValidation,
} from "~/components/modals/validation";
import { useConfig } from "~/features/common/config.slice";
import { useSettings } from "~/features/common/settings.slice";

type FormValues = {
  [key: string]: any;
};

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
  const customPrivacyRequestFields =
    action?.custom_privacy_request_fields ?? {};
  const toast = useToast();
  const formik = useFormik<FormValues>({
    initialValues: {
      ...Object.fromEntries(
        Object.entries(identityInputs).map(([key]) => [key, ""])
      ),
      ...Object.fromEntries(
        Object.entries(customPrivacyRequestFields)
          .filter(([, field]) => !field.hidden)
          .map(([key, field]) => [key, field.default_value || ""])
      ),
    },
    onSubmit: async (values) => {
      if (!action) {
        // somehow we've reached a broken state, return
        return;
      }

      // extract identity input values
      const identityInputValues = Object.fromEntries(
        Object.entries(action.identity_inputs ?? {}).map(([key, field]) => {
          const value = values[key] ?? null;
          if (typeof field === "string") {
            return [key, value];
          }
          return [key, { label: field.label, value }];
        })
      );

      // extract custom privacy request field values
      const customPrivacyRequestFieldValues = Object.fromEntries(
        Object.entries(action.custom_privacy_request_fields ?? {})
          .map(([key, field]) => [
            key,
            {
              label: field.label,
              value: field.hidden ? field.default_value : values[key] ?? null,
            },
          ])
          // @ts-ignore
          .filter(([, { value }]) => value !== null)
      );

      const body = [
        {
          identity: identityInputValues,
          ...(Object.keys(customPrivacyRequestFieldValues).length > 0 && {
            custom_privacy_request_fields: customPrivacyRequestFieldValues,
          }),
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
      ...Object.fromEntries(
        Object.entries(identityInputs)
          .filter(([key]) => key !== "email" && key !== "phone")
          .map(([key, value]) => {
            const customIdentity = value as CustomIdentity;
            return [
              key,
              Yup.string().required(`${customIdentity.label} is required`),
            ];
          })
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
          })
      ),
    }),
  });

  return { ...formik, identityInputs, customPrivacyRequestFields };
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
    customPrivacyRequestFields,
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
      <Text fontSize="sm" color="gray.600" mb={4} ml={6}>
        {action.description}
      </Text>
      <chakra.form onSubmit={handleSubmit} data-testid="privacy-request-form">
        <ModalBody maxHeight={400} overflowY="auto">
          {action.description_subtext?.map((paragraph, index) => (
            // eslint-disable-next-line react/no-array-index-key
            <Text fontSize="sm" color="gray.600" mb={4} key={index}>
              {paragraph}
            </Text>
          ))}
          <Stack>
            {Object.entries(identityInputs).map(([key, item]) => (
              <FormControl
                key={key}
                id={key}
                isInvalid={touched[key] && Boolean(errors[key])}
                isRequired
              >
                <FormLabel fontSize="sm">
                  {typeof item === "string"
                    ? key[0].toUpperCase() + key.slice(1)
                    : item.label}
                </FormLabel>
                {key === "phone" ? (
                  <PhoneInput
                    id={key}
                    name={key}
                    onChange={(value) => {
                      setFieldValue(key, value, true);
                    }}
                    onBlur={handleBlur}
                    value={values[key]}
                  />
                ) : (
                  <Input
                    id={key}
                    name={key}
                    focusBorderColor="primary.500"
                    onChange={handleChange}
                    onBlur={handleBlur}
                    value={values[key]}
                  />
                )}
                <FormErrorMessage>{errors[key]}</FormErrorMessage>
              </FormControl>
            ))}
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
                  <FormErrorMessage>{errors[key]}</FormErrorMessage>
                </FormControl>
              ))}
          </Stack>
        </ModalBody>

        <ModalFooter pb={6}>
          <Button variant="outline" flex="1" mr={3} size="sm" onClick={onClose}>
            {action.cancelButtonText || "Cancel"}
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
            {action.confirmButtonText || "Continue"}
          </Button>
        </ModalFooter>
      </chakra.form>
    </>
  );
};

export default PrivacyRequestForm;
