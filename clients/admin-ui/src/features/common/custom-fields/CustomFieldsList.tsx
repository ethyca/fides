import { Center, Flex, Spinner } from "@fidesui/react";
import { Field, FieldInputProps } from "formik";

import SystemFormInputGroup from "~/features/system/SystemFormInputGroup";
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
    <SystemFormInputGroup heading="Custom fields">
      <Flex flexDir="column" data-testid="custom-fields-list">
        <Flex flexDir="column" gap="24px">
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
                            variant="stacked"
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
                          variant="stacked"
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
    </SystemFormInputGroup>
  );
};
