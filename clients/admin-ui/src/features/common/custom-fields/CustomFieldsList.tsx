/* eslint-disable @typescript-eslint/no-unused-vars */
import { Center, Divider, Flex, Spinner, Text } from "@fidesui/react";
import { FieldArray, useFormikContext } from "formik";
import { useCallback, useEffect, useMemo, useState } from "react";

import { CustomMultiSelect, CustomSelect } from "~/features/common/form/inputs";
import { useAlert } from "~/features/common/hooks";
import {
  useGetAllAllowListQuery,
  useGetCustomFieldDefinitionsByResourceTypeQuery,
  useGetCustomFieldsForResourceQuery,
  useUpsertCustomFieldMutation,
} from "~/features/plus/plus.slice";
import { AllowedTypes, ResourceTypes } from "~/types/api";

import { useFeatures } from "../features";
import { CustomFieldsModal } from "./CustomFieldsModal";
import { CustomFieldWithIdExtended } from "./types";

const initialValues = {
  customFields: [] as CustomFieldWithIdExtended[],
};

type FormValues = typeof initialValues;

type CustomFieldsListProps = {
  resourceId: string;
  resourceType: ResourceTypes;
};

const CustomFieldsList = ({
  resourceId,
  resourceType,
}: CustomFieldsListProps) => {
  const { errorAlert, successAlert } = useAlert();

  const { flags, plus } = useFeatures();
  const skip = !(flags.customFields && plus);
  const [isLoading, setIsLoading] = useState(!skip);

  const { data: allAllowList } = useGetAllAllowListQuery(true, { skip });
  const { data: customFieldDefinitions } =
    useGetCustomFieldDefinitionsByResourceTypeQuery(resourceType, { skip });
  const { data: customFields } = useGetCustomFieldsForResourceQuery(
    resourceId,
    { skip }
  );
  const [upsertCustomField] = useUpsertCustomFieldMutation();

  // Reference parent Formik context
  const {
    isSubmitting,
    setSubmitting,
    values: formValues,
  } = useFormikContext();

  const editCustomFieldList = useMemo(() => {
    let withIds: CustomFieldWithIdExtended[] =
      customFields?.filter((item) =>
        customFieldDefinitions?.some(
          (cfd) => cfd.id === item.custom_field_definition_id && cfd.active
        )
      ) || [];
    withIds = withIds.map((item) => ({
      ...item,
      allow_list_id: customFieldDefinitions!.find(
        (cfd) => cfd.id === item.custom_field_definition_id
      )!.allow_list_id,
    }));

    const unassigned =
      customFieldDefinitions?.filter(
        (item) =>
          !withIds.some(
            (existing) => existing.custom_field_definition_id === item.id
          )
      ) || [];

    const withNoIds: CustomFieldWithIdExtended[] = [];
    unassigned.forEach((item) => {
      withNoIds.push({
        allow_list_id: item.allow_list_id,
        custom_field_definition_id: item.id as string,
        resource_id: resourceId,
        resource_type: resourceType,
        value: item.field_type === AllowedTypes.STRING ? "" : [],
      });
    });

    return [...withIds, ...withNoIds];
  }, [customFieldDefinitions, customFields, resourceId, resourceType]);

  const getCustomFieldDefinition = useCallback(
    (item: CustomFieldWithIdExtended) =>
      customFieldDefinitions!.find(
        (cfd) => cfd.id === item.custom_field_definition_id
      ),
    [customFieldDefinitions]
  );

  const getListOptions = useCallback(
    (allow_list_id: string) => {
      const value = allAllowList?.find((item) => item.id === allow_list_id);
      const list = value?.allowed_values!.map((item) => ({
        value: item,
        label: item,
      }));
      return list;
    },
    [allAllowList]
  );

  const handleSubmit = useCallback(
    (values: FormValues) => {
      try {
        let hasError = false;
        values.customFields.forEach(async (customField) => {
          if (!customField.id && customField.value.length === 0) {
            return;
          }
          const clone = { ...customField };
          delete clone.allow_list_id;
          const result = await upsertCustomField(clone);
          if ("error" in result) {
            hasError = true;
          }
        });
        if (hasError) {
          errorAlert(
            `One or more custom field(s) has failed to save, please try again`
          );
        } else {
          successAlert(
            `Custom field(s) successfully saved and added to this ${resourceType} form`
          );
        }
      } finally {
        setSubmitting(false);
      }
    },
    [errorAlert, resourceType, setSubmitting, successAlert, upsertCustomField]
  );

  useEffect(() => {
    if ((isLoading && customFieldDefinitions) || customFields) {
      // Update the initial parent customFields
      (formValues as any).customFields = [...editCustomFieldList];
      setIsLoading(false);
    }
  }, [
    customFieldDefinitions,
    customFields,
    editCustomFieldList,
    formValues,
    isLoading,
  ]);

  useEffect(() => {
    if (isSubmitting && (formValues as any).customFields) {
      handleSubmit(formValues as FormValues);
    }
  }, [formValues, handleSubmit, isSubmitting]);

  return flags.customFields && plus ? (
    <Flex
      flexDir="column"
      mt={resourceType === ResourceTypes.SYSTEM ? "28px" : ""}
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
        {isLoading && (
          <Center>
            <Spinner />
          </Center>
        )}
        {!isLoading && (
          <FieldArray
            name="customFields"
            render={() => {
              const { customFields: list } = formValues as any;
              return (
                <Flex flexDirection="column" gap="12px" paddingBottom="24px">
                  {list?.map((item: CustomFieldWithIdExtended, index: number) =>
                    Array.isArray(item.value) ? (
                      <CustomMultiSelect
                        label={getCustomFieldDefinition(item)!.name}
                        key={JSON.stringify(item)}
                        name={`customFields[${index}].value`}
                        options={getListOptions(item.allow_list_id!) || []}
                        tooltip={getCustomFieldDefinition(item)!.description}
                      />
                    ) : (
                      <CustomSelect
                        isClearable
                        label={getCustomFieldDefinition(item)!.name}
                        key={JSON.stringify(item)}
                        name={`customFields[${index}].value`}
                        options={getListOptions(item.allow_list_id!) || []}
                        tooltip={getCustomFieldDefinition(item)!.description}
                      />
                    )
                  )}
                </Flex>
              );
            }}
          />
        )}
      </Flex>
    </Flex>
  ) : null;
};

export { CustomFieldsList };
