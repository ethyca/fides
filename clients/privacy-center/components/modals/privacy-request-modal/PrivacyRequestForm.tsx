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
} from "fidesui";
import { useFormik } from "formik";
import { Headers } from "headers-polyfill";
import { useSearchParams } from "next/navigation";
import React, { useEffect } from "react";
import * as Yup from "yup";

import { addCommonHeaders } from "~/common/CommonHeaders";
import { ErrorToastOptions, SuccessToastOptions } from "~/common/toast-options";
import { FormErrorMessage } from "~/components/FormErrorMessage";
import { ModalViews } from "~/components/modals/types";
import {
  emailValidation,
  nameValidation,
  phoneValidation,
} from "~/components/modals/validation";
import { PhoneInput } from "~/components/phone-input";
import { defaultIdentityInput } from "~/constants";
import { useConfig } from "~/features/common/config.slice";
import { useProperty } from "~/features/common/property.slice";
import { useSettings } from "~/features/common/settings.slice";
import { PrivacyRequestStatus } from "~/types";
import { PrivacyRequestSource } from "~/types/api/models/PrivacyRequestSource";
import { CustomIdentity, PrivacyRequestOption } from "~/types/config";

type FormValues = {
  [key: string]: any;
};

/**
 *
 * @param value
 * @returns Default to null if the value is undefined or an empty string
 */
const fallbackNull = (value: any) =>
  value === undefined || value === "" ? null : value;

const usePrivacyRequestForm = ({
  onClose,
  action,
  setCurrentView,
  setPrivacyRequestId,
  isVerificationRequired,
}: {
  onClose: () => void;
  action?: PrivacyRequestOption | null;
  setCurrentView: (view: ModalViews) => void;
  setPrivacyRequestId: (id: string) => void;
  isVerificationRequired: boolean;
}) => {
  const settings = useSettings();
  const identityInputs = action?.identity_inputs ?? defaultIdentityInput;
  const customPrivacyRequestFields =
    action?.custom_privacy_request_fields ?? {};
  const toast = useToast();
  const searchParams = useSearchParams();

  const property = useProperty();

  const formik = useFormik<FormValues>({
    initialValues: {
      ...Object.fromEntries(
        Object.entries(identityInputs)
          .filter(
            ([key, value]) =>
              key === "name" ||
              key === "phone" ||
              key === "email" ||
              (typeof value === "object" && value?.label),
          )
          .map(([key]) => [key, ""]),
      ),
      ...Object.fromEntries(
        Object.entries(customPrivacyRequestFields)
          .filter(([, field]) => !field.hidden)
          .map(([key, field]) => {
            const valueFromQueryParam =
              field.query_param_key &&
              (searchParams?.get(field.query_param_key) as string);

            const value = valueFromQueryParam || field.default_value || "";

            return [key, value];
          }),
      ),
    },
    onSubmit: async (values) => {
      if (!action) {
        // somehow we've reached a broken state, return
        return;
      }

      // extract identity input values
      const identityInputValues = Object.fromEntries(
        Object.entries(action.identity_inputs ?? {})
          // we have to support name as an identity_input for legacy purposes
          // but we ignore it since it's not unique enough to be treated as an identity
          .filter(([key]) => key !== "name")
          .map(([key, field]) => {
            const value = fallbackNull(values[key]);
            if (typeof field === "string") {
              if (key === "phone") {
                // eslint-disable-next-line no-param-reassign
                key = "phone_number";
              }
              return [key, value];
            }
            return [key, { label: field?.label, value }];
          }),
      );

      // extract custom privacy request field values
      const customPrivacyRequestFieldValues = Object.fromEntries(
        Object.entries(action.custom_privacy_request_fields ?? {})
          .map(([key, field]) => {
            if (!field.hidden) {
              return [
                key,
                {
                  label: field.label,
                  value: fallbackNull(values[key]),
                },
              ];
            }

            const valueFromQueryParam =
              field.query_param_key && searchParams?.get(field.query_param_key);

            const value = valueFromQueryParam || field.default_value || null;

            return [
              key,
              {
                label: field.label,
                value,
              },
            ];
          })
          // @ts-ignore
          .filter(([, { value }]) => value !== null),
      );

      const body = [
        {
          identity: identityInputValues,
          ...(Object.keys(customPrivacyRequestFieldValues).length > 0 && {
            custom_privacy_request_fields: customPrivacyRequestFieldValues,
          }),
          policy_key: action.policy_key,
          property_id: property?.id || null,
          source: PrivacyRequestSource.PRIVACY_CENTER,
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
          },
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
        },
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
        },
      ),
      ...Object.fromEntries(
        Object.entries(identityInputs)
          .filter(
            ([key, value]) =>
              key !== "email" &&
              key !== "phone" &&
              key !== "name" &&
              typeof value !== "string",
          )
          .map(([key, value]) => {
            const customIdentity = value as CustomIdentity;
            return [
              key,
              Yup.string().required(`${customIdentity.label} is required`),
            ];
          }),
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
          }),
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

const PrivacyRequestForm = ({
  isOpen,
  onClose,
  openAction,
  setCurrentView,
  setPrivacyRequestId,
  isVerificationRequired,
}: PrivacyRequestFormProps) => {
  const config = useConfig();

  const action = openAction
    ? (config.actions as PrivacyRequestOption[]).find(
        ({ policy_key }) => policy_key === openAction,
      )
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
      <Text fontSize="sm" color="gray.800" mb={4} ml={6}>
        {action.description}
      </Text>
      <chakra.form onSubmit={handleSubmit} data-testid="privacy-request-form">
        <ModalBody maxHeight={400} overflowY="auto">
          {action.description_subtext?.map((paragraph, index) => (
            // eslint-disable-next-line react/no-array-index-key
            <Text fontSize="sm" color="gray.800" mb={4} key={index}>
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
                <FormErrorMessage>
                  {JSON.stringify(errors.name)}
                </FormErrorMessage>
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
                />
                <FormErrorMessage>
                  {JSON.stringify(errors.email)}
                </FormErrorMessage>
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
                />
                <FormErrorMessage>
                  {JSON.stringify(errors.phone)}
                </FormErrorMessage>
              </FormControl>
            ) : null}
            {Object.entries(identityInputs)
              .filter(
                ([key, item]) =>
                  key !== "email" &&
                  key !== "phone" &&
                  key !== "name" &&
                  typeof item !== "string",
              )
              .map(([key, item]) => (
                <FormControl
                  key={key}
                  id={key}
                  isInvalid={touched[key] && Boolean(errors[key])}
                  isRequired
                >
                  <FormLabel fontSize="sm">
                    {(item as CustomIdentity).label}
                  </FormLabel>
                  <Input
                    id={key}
                    name={key}
                    focusBorderColor="primary.500"
                    onChange={handleChange}
                    onBlur={handleBlur}
                    value={values[key]}
                  />
                  <FormErrorMessage>
                    {JSON.stringify(errors[key])}
                  </FormErrorMessage>
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
                  <FormErrorMessage>
                    {JSON.stringify(errors[key])}
                  </FormErrorMessage>
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
