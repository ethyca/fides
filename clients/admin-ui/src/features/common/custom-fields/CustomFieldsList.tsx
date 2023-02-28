import { Center, Divider, Flex, Spinner, Text } from "@fidesui/react";
import { Field, FieldInputProps, useFormikContext } from "formik";
import { useCallback, useEffect, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { plusApi } from "~/features/plus/plus.slice";
import { AllowedTypes, ResourceTypes } from "~/types/api";

import { CustomSelect } from "../form/inputs";
import { CustomFieldsModal } from "./CustomFieldsModal";
import { filterWithId } from "./helpers";
import { useCustomFields } from "./hooks";

type CustomFieldsListProps = {
  resourceFidesKey?: string;
  resourceType: ResourceTypes;
};

export const CustomFieldsList = ({
  resourceFidesKey,
  resourceType,
}: CustomFieldsListProps) => {
  const dispatch = useAppDispatch();
  const [selectedKey, setSelectedKey] = useState<string | undefined>();
  const { isSubmitting, setValues, values } = useFormikContext();

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

  const handleReload = useCallback(() => {
    setValues({ ...(values as any) });
  }, [setValues, values]);

  useEffect(() => {
    if (!isEnabled || !resourceFidesKey) {
      return;
    }
    // Append the custom field selections to the Formik form
    if (selectedKey !== resourceFidesKey) {
      setSelectedKey(resourceFidesKey);
      dispatch(
        plusApi.endpoints.getCustomFieldsForResource.initiate(resourceFidesKey)
      ).then((response) => {
        const data = new Map(
          filterWithId(response.data).map((fd) => [
            fd.custom_field_definition_id,
            fd,
          ])
        );
        const formValues: Record<string, string | string[]> = {};
        data.forEach((value, key) => {
          formValues[`${key}`] = value.value.toString();
        });
        setValues(
          {
            ...(values as any),
            ...{ definitionIdToCustomFieldValue: formValues },
          },
          false
        );
      });
    }
  }, [dispatch, isEnabled, resourceFidesKey, selectedKey, setValues, values]);

  useEffect(() => {
    // Re-render the custom field selections after a Formik form submission
    if (isSubmitting) {
      setTimeout(() => {
        handleReload();
      });
    }
  }, [handleReload, isSubmitting, values]);

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
        <CustomFieldsModal reload={handleReload} resourceType={resourceType} />
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

                const allowList = idToAllowListWithOptions.get(
                  customFieldDefinition.allow_list_id!
                );
                if (!allowList) {
                  // This would only happen if the field definitions load before
                  // the allow list data.
                  return null;
                }

                const { options } = allowList;
                const name = `definitionIdToCustomFieldValue.${customFieldDefinition.id}`;

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
