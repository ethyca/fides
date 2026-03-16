import {
  Button,
  ChakraBox as Box,
  ChakraDeleteIcon as DeleteIcon,
  ChakraFlex as Flex,
  ChakraSmallAddIcon as SmallAddIcon,
} from "fidesui";
import { FieldArray, useFormikContext } from "formik";

import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput } from "~/features/common/form/inputs";

import type { PropertyFormValues } from "../PropertyForm";
import ActionsFieldArray from "./ActionsFieldArray";

const DescriptionSubtextFieldArray = ({
  fieldPath,
  label,
}: {
  fieldPath: string;
  label: string;
}) => {
  const { values } = useFormikContext<PropertyFormValues>();
  const subtext: string[] =
    (fieldPath
      .split(".")
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .reduce((acc: any, key) => acc?.[key], values) as string[]) ?? [];

  return (
    <FieldArray
      name={fieldPath}
      render={(arrayHelpers) => (
        <Flex flexDir="column" gap={2}>
          {subtext.map((_, index) => (
            // eslint-disable-next-line react/no-array-index-key
            <Flex key={index} flexDir="row" gap={2} alignItems="flex-end">
              <Flex flex={1}>
                <CustomTextInput
                  name={`${fieldPath}[${index}]`}
                  label={index === 0 ? label : undefined}
                  variant="stacked"
                />
              </Flex>
              <Button
                aria-label={`Remove ${label.toLowerCase()} entry`}
                icon={<DeleteIcon />}
                onClick={() => arrayHelpers.remove(index)}
                loading={false}
                className="mb-1"
                data-testid={`remove-${fieldPath}-${index}`}
              />
            </Flex>
          ))}
          <Box>
            <Button
              icon={<SmallAddIcon />}
              onClick={() => arrayHelpers.push("")}
              loading={false}
              data-testid={`add-${fieldPath}-button`}
            >
              Add {label.toLowerCase()} entry
            </Button>
          </Box>
        </Flex>
      )}
    />
  );
};

const PrivacyCenterConfigForm = () => {
  const { values } = useFormikContext<PropertyFormValues>();
  const hasConfig =
    values.privacy_center_config !== null &&
    values.privacy_center_config !== undefined;

  if (!hasConfig) {
    return null;
  }

  return (
    <>
      <Box py={3}>
        <FormSection title="Privacy Center — General">
          <CustomTextInput
            isRequired
            label="Title"
            name="privacy_center_config.title"
            variant="stacked"
          />
          <CustomTextInput
            isRequired
            label="Description"
            name="privacy_center_config.description"
            variant="stacked"
          />
          <DescriptionSubtextFieldArray
            fieldPath="privacy_center_config.description_subtext"
            label="Description subtext"
          />
          <CustomTextInput
            label="Logo path"
            name="privacy_center_config.logo_path"
            variant="stacked"
          />
          <CustomTextInput
            label="Logo URL"
            name="privacy_center_config.logo_url"
            variant="stacked"
          />
          <CustomTextInput
            label="Favicon path"
            name="privacy_center_config.favicon_path"
            variant="stacked"
          />
          <CustomTextInput
            label="Privacy policy URL"
            name="privacy_center_config.privacy_policy_url"
            variant="stacked"
          />
          <CustomTextInput
            label="Privacy policy URL text"
            name="privacy_center_config.privacy_policy_url_text"
            variant="stacked"
          />
        </FormSection>
      </Box>
      <Box py={3}>
        <FormSection title="Privacy Center — Actions">
          <ActionsFieldArray />
        </FormSection>
      </Box>
    </>
  );
};

export default PrivacyCenterConfigForm;
