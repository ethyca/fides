import { MenuPosition } from "chakra-react-select";
import { Center, Flex, Spinner } from "fidesui";
import { Field, FieldInputProps } from "formik";

import SystemFormInputGroup from "~/features/system/SystemFormInputGroup";
import { AllowedTypes, ResourceTypes } from "~/types/api";

import { ControlledSelect } from "../form/ControlledSelect";
import { CustomTextInput } from "../form/inputs";
import { useCustomFields } from "./hooks";

type CustomFieldsListProps = {
  resourceFidesKey?: string;
  resourceType: ResourceTypes;
  menuPosition?: MenuPosition;
};

export const CustomFieldsList = ({
  resourceFidesKey,
  resourceType,
  menuPosition,
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
                    customFieldDefinition.allow_list_id!,
                  );
                  if (!allowList) {
                    // This would only happen if the field definitions load before
                    // the allow list data.
                    return null;
                  }

                  const { options } = allowList;

                  return (
                    <ControlledSelect
                      key={definitionId}
                      name={name}
                      allowClear
                      mode={
                        customFieldDefinition.field_type !== AllowedTypes.STRING
                          ? "multiple"
                          : undefined
                      }
                      label={customFieldDefinition.name}
                      options={options}
                      tooltip={customFieldDefinition.description}
                      layout="stacked"
                      className="w-full"
                    />
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
