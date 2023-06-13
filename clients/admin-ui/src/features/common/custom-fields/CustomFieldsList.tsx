import { Center, Divider, Flex, Spinner, Text } from "@fidesui/react";
import { Field, FieldInputProps } from "formik";

import { AllowedTypes, ResourceTypes } from "~/types/api";

import { CustomSelect, CustomTextInput } from "../form/inputs";
import { useCustomFields } from "./hooks";

type CustomFieldsListProps = {
  resourceFidesKey?: string;
  resourceType: ResourceTypes;
};

export const CustomFieldsList = ({
  resourceFidesKey,
  resourceType,
}: CustomFieldsListProps) => {
  const {
    idToAllowListWithOptions,
    idToCustomFieldDefinition,
    isEnabled,
    isLoading,
    sortedCustomFieldDefinitionIds,
  } = useCustomFields({
    resourceFidesKey,
    resourceType,
  });

  if (!isEnabled || sortedCustomFieldDefinitionIds.length === 0) {
    return null;
  }

  return (
    <Flex
      flexDir="column"
      mt={resourceType === ResourceTypes.SYSTEM ? "28px" : ""}
      data-testid="custom-fields-list"
    >
      <Flex flexDir="column" gap="24px">
        <Divider color="gray.200" />
        <Flex flexDir="column" gap="12px">
          <Text
            color="gray.900"
            fontSize="md"
            fontWeight="semibold"
            lineHeight="24px"
          >
            Custom fields
          </Text>
        </Flex>
        {isLoading ? (
          <Center>
            <Spinner />
          </Center>
        ) : (
          sortedCustomFieldDefinitionIds.length > 0 && (
            <Flex flexDirection="column" gap="12px" paddingBottom="24px">
              {sortedCustomFieldDefinitionIds.map((definitionId) => {
                const customFieldDefinition =
                  idToCustomFieldDefinition.get(definitionId);
                if (!customFieldDefinition) {
                  // This should never happen.
                  return null;
                }

                const name = `customFieldValues.${customFieldDefinition.id}`;
                if (
                  !customFieldDefinition.allow_list_id &&
                  customFieldDefinition.field_type === AllowedTypes.STRING
                ) {
                  return (
                    <Field key={definitionId} name={name}>
                      {({ field }: { field: FieldInputProps<string> }) => (
                        <CustomTextInput
                          {...field}
                          label={customFieldDefinition.name}
                          tooltip={customFieldDefinition.description}
                        />
                      )}
                    </Field>
                  );
                }

                const allowList = idToAllowListWithOptions.get(
                  customFieldDefinition.allow_list_id!
                );
                if (!allowList) {
                  // This would only happen if the field definitions load before
                  // the allow list data.
                  return null;
                }

                const { options } = allowList;

                return (
                  <Field key={definitionId} name={name}>
                    {({
                      field,
                    }: {
                      field: FieldInputProps<string | string[]>;
                    }) => (
                      <CustomSelect
                        {...field}
                        isClearable
                        isFormikOnChange
                        isMulti={
                          customFieldDefinition.field_type !==
                          AllowedTypes.STRING
                        }
                        label={customFieldDefinition.name}
                        options={options}
                        tooltip={customFieldDefinition.description}
                      />
                    )}
                  </Field>
                );
              })}
            </Flex>
          )
        )}
      </Flex>
    </Flex>
  );
};
