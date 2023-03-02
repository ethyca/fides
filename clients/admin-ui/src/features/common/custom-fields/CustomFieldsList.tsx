import { Center, Divider, Flex, Spinner, Text } from "@fidesui/react";

import { ResourceTypes } from "~/types/api";

import { CustomFieldSelector } from "./CustomFieldSelector";
import { CustomFieldsModal } from "./CustomFieldsModal";
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
    definitionIdToCustomField,
    idToAllowListWithOptions,
    idToCustomFieldDefinition,
    isEnabled,
    isLoading,
    sortedCustomFieldDefinitionIds,
  } = useCustomFields({
    resourceFidesKey,
    resourceType,
  });

  if (!isEnabled) {
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
        <CustomFieldsModal resourceType={resourceType} />
        {isLoading ? (
          <Center>
            <Spinner />
          </Center>
        ) : (
          <Flex flexDirection="column" gap="12px" paddingBottom="24px">
            {sortedCustomFieldDefinitionIds.map((definitionId) => {
              const customFieldDefinition =
                idToCustomFieldDefinition.get(definitionId);
              if (!customFieldDefinition) {
                // This should never happen.
                return null;
              }

              const allowList = idToAllowListWithOptions.get(
                customFieldDefinition.allow_list_id!
              );
              if (!allowList) {
                // This would only happen if the field definitions load before
                // the allow list data.
                return null;
              }

              // This will be undefined when no value has been saved for this field.
              const customField = definitionIdToCustomField.get(definitionId);

              return (
                <CustomFieldSelector
                  allowList={allowList}
                  customField={customField}
                  customFieldDefinition={customFieldDefinition}
                  key={`${definitionId}-${customField?.id}`}
                />
              );
            })}
          </Flex>
        )}
      </Flex>
    </Flex>
  );
};
