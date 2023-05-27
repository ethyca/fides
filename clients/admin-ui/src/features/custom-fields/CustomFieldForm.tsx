import { Box, Button, Flex, IconButton, Text } from "@fidesui/react";
import {
  FIELD_TYPE_OPTIONS_NEW,
  FieldTypes,
  RESOURCE_TYPE_OPTIONS,
} from "common/custom-fields";
import CustomInput, {
  CUSTOM_LABEL_STYLES,
} from "common/custom-fields/form/CustomInput";
import { AddIcon } from "common/custom-fields/icons/AddIcon";
import FormSection from "common/form/FormSection";
import { CustomSelect } from "common/form/inputs";
import { TrashCanSolidIcon } from "common/Icon/TrashCanSolidIcon";
import { FieldArray, Form, FormikProps, useFormikContext } from "formik";
import { useEffect } from "react";

import type { FormValues } from "~/features/custom-fields/CustomFieldModal";

const CustomFieldLabelStyles = {
  ...CUSTOM_LABEL_STYLES,
  minWidth: "unset",
};

type Props = FormikProps<FormValues> & {
  validationSchema: any;
  isLoading: boolean;
  onClose: () => void;
  handleDropdownChange: (value: FieldTypes) => void;
  isEditing: boolean;
};

export const CustomFieldForm = ({
  values,
  validationSchema,
  errors,
  dirty,
  isValid,
  isSubmitting,
  isLoading,
  onClose,
  handleDropdownChange,
  isEditing,
}: Props) => {
  const { validateForm } = useFormikContext<FormValues>();
  useEffect(() => {
    validateForm();
  }, [validationSchema, validateForm]);

  return (
    <Form
      style={{
        paddingTop: "12px",
        paddingBottom: "12px",
      }}
    >
      <Box py={3}>
        <FormSection title="Field Information">
          <CustomInput
            displayHelpIcon
            isRequired
            label="Name"
            name="name"
            customLabelProps={CustomFieldLabelStyles}
          />
          <CustomInput
            displayHelpIcon
            label="Description"
            name="description"
            customLabelProps={CustomFieldLabelStyles}
          />
          <CustomSelect
            label="Location"
            name="resource_type"
            options={RESOURCE_TYPE_OPTIONS}
            labelProps={CustomFieldLabelStyles}
            isDisabled={isEditing}
          />
        </FormSection>
      </Box>
      <Box py={3}>
        <FormSection title="Configuration">
          <CustomSelect
            label="Field Type"
            name="field_type"
            options={FIELD_TYPE_OPTIONS_NEW}
            onChange={async (e: any) => {
              handleDropdownChange(e.value);
            }}
          />
          {values.field_type !== FieldTypes.OPEN_TEXT ? (
            <Flex
              flexDirection="column"
              gap="12px"
              paddingTop="6px"
              paddingBottom="24px"
            >
              <FieldArray
                name="allow_list.allowed_values"
                render={(fieldArrayProps) => {
                  // eslint-disable-next-line @typescript-eslint/naming-convention
                  const { allowed_values } = values.allow_list;

                  return (
                    <Flex flexDirection="column" gap="6" pl="6">
                      <Flex flexDirection="column">
                        {allowed_values.map((_value, index) => (
                          <Flex
                            flexGrow={1}
                            gap="3"
                            // eslint-disable-next-line react/no-array-index-key
                            key={index}
                            mt={index > 0 ? 3 : undefined}
                          >
                            <CustomInput
                              customLabelProps={{
                                color: "gray.600",
                                fontSize: "sm",
                                fontWeight: "500",
                                lineHeight: "20px",
                                minW: "126px",
                                pr: "8px",
                              }}
                              displayHelpIcon={false}
                              isRequired
                              label={`List item ${index + 1}`}
                              name={`allow_list.allowed_values[${index}]`}
                            />
                            <IconButton
                              aria-label="Remove this list value"
                              data-testid={`remove-list-value-btn-${index}`}
                              icon={<TrashCanSolidIcon />}
                              isDisabled={allowed_values.length <= 1}
                              onClick={() => fieldArrayProps.remove(index)}
                              size="sm"
                              variant="ghost"
                            />
                          </Flex>
                        ))}
                      </Flex>
                      <Flex alignItems="center">
                        <Text
                          color="gray.600"
                          fontSize="xs"
                          fontWeight="500"
                          lineHeight="16px"
                          pr="8px"
                        >
                          Add a list value
                        </Text>
                        <IconButton
                          aria-label="Add a list value"
                          data-testid="add-list-value-btn"
                          icon={<AddIcon h="7px" w="7px" />}
                          onClick={() => {
                            fieldArrayProps.push("");
                          }}
                          size="xs"
                          variant="outline"
                        />
                        {allowed_values.length === 0 && errors?.allow_list ? (
                          <Text color="red.500" pl="18px" size="sm">
                            {errors.allow_list.allowed_values}
                          </Text>
                        ) : null}
                      </Flex>
                    </Flex>
                  );
                }}
              />
            </Flex>
          ) : null}
        </FormSection>
      </Box>

      <Flex justifyContent="space-between" width="100%">
        <Button
          size="sm"
          variant="outline"
          mr={3}
          onClick={onClose}
          data-testid="cancel-btn"
          isDisabled={isLoading || isSubmitting}
        >
          Cancel
        </Button>
        <Button
          size="sm"
          type="submit"
          colorScheme="primary"
          data-testid="save-btn"
          isLoading={isLoading}
          isDisabled={!dirty || !isValid || isSubmitting}
        >
          Save
        </Button>
      </Flex>
    </Form>
  );
};
