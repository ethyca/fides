import {
  ChakraBox as Box,
  ChakraCheckbox as Checkbox,
  ChakraFlex as Flex,
  ChakraFormLabel as FormLabel,
  ChakraStack as Stack,
  ChakraText as Text,
} from "fidesui";
import { useFormikContext } from "formik";
import { useMemo } from "react";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { CustomTextInput } from "~/features/common/form/inputs";
import { useGetPoliciesQuery } from "~/features/policies/policy.slice";

import type { PropertyFormValues } from "../PropertyForm";
import CustomPrivacyFieldsArray from "./CustomPrivacyFieldsArray";
import { POLICY_KEY_DEFAULT_ICONS } from "./helpers";

interface Props {
  index: number;
}

const IDENTITY_KEYS = ["email", "phone"] as const;

const ActionEntryForm = ({ index }: Props) => {
  const basePath = `privacy_center_config.actions[${index}]`;
  const { data: policiesPage } = useGetPoliciesQuery();

  const policyOptions = useMemo(
    () =>
      (policiesPage?.items ?? []).map((p) => ({
        value: p.key ?? "",
        label: p.name,
      })),
    [policiesPage],
  );

  const { values, setFieldValue } = useFormikContext<PropertyFormValues>();
  const action = values.privacy_center_config?.actions?.[index];
  const identityInputs = (action?.identity_inputs ?? {}) as Record<
    string,
    string
  >;

  const currentPolicyKey = action?.policy_key ?? "";
  const defaultIconForKey = POLICY_KEY_DEFAULT_ICONS[currentPolicyKey];

  const handlePolicyKeyChange = (newKey: string) => {
    const defaultIcon = POLICY_KEY_DEFAULT_ICONS[newKey];
    // Auto-fill icon_path with the default for this policy key, but only
    // when the user hasn't already set a custom value.
    if (defaultIcon && !action?.icon_path) {
      setFieldValue(`${basePath}.icon_path`, defaultIcon);
    }
  };

  const handleIdentityToggle = (key: string, checked: boolean) => {
    const updated = { ...identityInputs };
    if (checked) {
      updated[key] = "required";
    } else {
      delete updated[key];
    }
    setFieldValue(`${basePath}.identity_inputs`, updated);
  };

  const handleIdentityRequired = (key: string, required: boolean) => {
    setFieldValue(
      `${basePath}.identity_inputs.${key}`,
      required ? "required" : "optional",
    );
  };

  return (
    <Stack spacing={4}>
      <ControlledSelect
        label="Policy key"
        name={`${basePath}.policy_key`}
        options={policyOptions}
        layout="stacked"
        onChange={handlePolicyKeyChange}
      />
      <CustomTextInput
        label="Icon path"
        name={`${basePath}.icon_path`}
        variant="stacked"
        placeholder={defaultIconForKey ?? "https://example.com/icon.svg"}
        tooltip={
          defaultIconForKey
            ? `Default icon for this policy type: ${defaultIconForKey}`
            : undefined
        }
      />
      <CustomTextInput
        isRequired
        label="Title"
        name={`${basePath}.title`}
        variant="stacked"
      />
      <CustomTextInput
        isRequired
        label="Description"
        name={`${basePath}.description`}
        variant="stacked"
      />
      <CustomTextInput
        label="Confirm button text"
        name={`${basePath}.confirmButtonText`}
        variant="stacked"
      />
      <CustomTextInput
        label="Cancel button text"
        name={`${basePath}.cancelButtonText`}
        variant="stacked"
      />

      <Box>
        <FormLabel fontSize="sm" fontWeight="medium">
          Identity inputs
        </FormLabel>
        <Stack spacing={2} mt={1}>
          {IDENTITY_KEYS.map((key) => {
            const isEnabled = key in identityInputs;
            const isRequired = identityInputs[key] === "required";
            return (
              <Flex key={key} gap={4} alignItems="center">
                <Checkbox
                  isChecked={isEnabled}
                  onChange={(e) => handleIdentityToggle(key, e.target.checked)}
                  data-testid={`identity-${key}-enabled-${index}`}
                >
                  <Text fontSize="sm" textTransform="capitalize">
                    {key}
                  </Text>
                </Checkbox>
                <Checkbox
                  isChecked={isRequired}
                  isDisabled={!isEnabled}
                  onChange={(e) =>
                    handleIdentityRequired(key, e.target.checked)
                  }
                  data-testid={`identity-${key}-required-${index}`}
                >
                  <Text fontSize="sm">Required</Text>
                </Checkbox>
              </Flex>
            );
          })}
        </Stack>
      </Box>

      <Box>
        <FormLabel fontSize="sm" fontWeight="medium">
          Custom fields
        </FormLabel>
        <CustomPrivacyFieldsArray actionIndex={index} />
      </Box>
    </Stack>
  );
};

export default ActionEntryForm;
