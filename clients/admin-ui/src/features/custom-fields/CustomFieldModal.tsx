import { FieldTypes } from "common/custom-fields";
import { getErrorMessage } from "common/helpers";
import { useAlert } from "common/hooks";
import {
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  ModalOverlay,
} from "fidesui";
import { Formik } from "formik";
import { useState } from "react";
import * as Yup from "yup";

import { CustomFieldForm } from "~/features/custom-fields/CustomFieldForm";
import {
  useAddCustomFieldDefinitionMutation,
  useGetAllowListQuery,
  useUpdateCustomFieldDefinitionMutation,
  useUpsertAllowListMutation,
} from "~/features/plus/plus.slice";
import {
  AllowedTypes,
  AllowList,
  AllowListUpdate,
  CustomFieldDefinition,
  CustomFieldDefinitionWithId,
  ResourceTypes,
} from "~/types/api";

type ModalProps = {
  isOpen: boolean;
  onClose: () => void;
  isLoading: boolean;
  customField?: CustomFieldDefinitionWithId;
};

export type FormValues = Omit<CustomFieldDefinition, "field_type"> & {
  allow_list: AllowListUpdate;
  field_type: FieldTypes;
};

const initialValuesTemplate: FormValues = {
  description: "",
  field_type: FieldTypes.OPEN_TEXT,
  name: "",
  resource_type: ResourceTypes.SYSTEM,
  allow_list: {
    name: "",
    description: "",
    allowed_values: [],
  },
};

const optionalAllowValues = Yup.array(
  Yup.string().optional().label("allowed_values"),
);
const requiredAllowedValues = Yup.array(
  Yup.string().required("List item is required"),
)
  .min(1, "Must add at least one list value")
  .label("allowed_values");

const optionalValidationSchema = Yup.object().shape({
  name: Yup.string().required("Name is required").trim(),
  allow_list: Yup.object().shape({
    allowed_values: optionalAllowValues,
  }),
});

const requiredValidationSchema = Yup.object().shape({
  name: Yup.string().required("Name is required").trim(),
  allow_list: Yup.object().shape({
    allowed_values: requiredAllowedValues,
  }),
});

const transformCustomField = (
  customField: CustomFieldDefinitionWithId | undefined,
  allowList: AllowList | undefined,
): FormValues | undefined => {
  if (!customField) {
    return undefined;
  }

  let fieldType;

  if (
    customField.field_type === AllowedTypes.STRING &&
    !customField.allow_list_id
  ) {
    fieldType = FieldTypes.OPEN_TEXT;
  }

  if (
    customField.field_type === AllowedTypes.STRING &&
    customField.allow_list_id
  ) {
    fieldType = FieldTypes.SINGLE_SELECT;
  }

  if (
    // eslint-disable-next-line no-underscore-dangle
    customField.field_type === AllowedTypes.STRING_ &&
    customField.allow_list_id
  ) {
    fieldType = FieldTypes.MULTIPLE_SELECT;
  }
  const parsedAllowList = allowList
    ? {
        name: allowList.name ?? "",
        description: allowList.description ?? "",
        allowed_values: allowList.allowed_values ?? [],
      }
    : initialValuesTemplate.allow_list;
  return {
    ...customField,
    field_type: fieldType || FieldTypes.OPEN_TEXT,
    allow_list: parsedAllowList,
  };
};

export const CustomFieldModal = ({
  isOpen,
  onClose,
  isLoading,
  customField,
}: ModalProps) => {
  const { errorAlert, successAlert } = useAlert();
  const [addCustomFieldDefinition] = useAddCustomFieldDefinitionMutation();
  const [updateCustomFieldDefinition] =
    useUpdateCustomFieldDefinitionMutation();
  const [upsertAllowList] = useUpsertAllowListMutation();

  const { data: allowList, isLoading: isLoadingAllowList } =
    useGetAllowListQuery(customField?.allow_list_id as string, {
      skip: !customField?.allow_list_id,
    });

  const [validationSchema, setNewValidationSchema] = useState(
    optionalValidationSchema,
  );

  if (isLoadingAllowList || !isOpen) {
    return null;
  }

  const transformedCustomField = transformCustomField(customField, allowList);
  const isEditing = !!transformedCustomField;
  const initialValues = transformedCustomField || initialValuesTemplate;

  const handleDropdownChange = (value: FieldTypes) => {
    if (value === FieldTypes.OPEN_TEXT) {
      setNewValidationSchema(optionalValidationSchema);
    } else {
      setNewValidationSchema(requiredValidationSchema);
    }
  };

  const handleSubmit = async (values: FormValues) => {
    if (
      [FieldTypes.SINGLE_SELECT, FieldTypes.MULTIPLE_SELECT].includes(
        values.field_type,
      )
    ) {
      const uniqueValues = new Set(
        values.allow_list?.allowed_values
          .map((v) => v.toLowerCase().trim())
          .map((v) => v),
      );
      if (uniqueValues.size < values.allow_list!.allowed_values.length) {
        errorAlert("List item value must be unique");
        return;
      }

      const { allow_list: allowListPayload } = values;

      if (values.allow_list_id) {
        allowListPayload.id = values.allow_list_id;
      }

      if (!allowListPayload.name) {
        // The UI no longer surfaces this field. It's a required field in the
        // backend and must be unique. We generate a random name to avoid collisions.
        allowListPayload.name =
          Date.now().toString() + Math.random().toString();
      }

      const result = await upsertAllowList(allowListPayload);
      if (!("error" in result) && !values.allow_list_id) {
        // Handles the creation case. Only assigns ID if new
        // eslint-disable-next-line no-param-reassign
        values.allow_list_id = result.data?.id;
      }
      // Add error handling here
    }

    if (values.field_type === FieldTypes.OPEN_TEXT) {
      // eslint-disable-next-line no-param-reassign
      values.allow_list_id = undefined;
    }

    if (
      [FieldTypes.SINGLE_SELECT, FieldTypes.OPEN_TEXT].includes(
        values.field_type,
      )
    ) {
      // eslint-disable-next-line no-param-reassign
      values.field_type = AllowedTypes.STRING as unknown as FieldTypes;
    }

    if (values.field_type === FieldTypes.MULTIPLE_SELECT) {
      // eslint-disable-next-line no-param-reassign,no-underscore-dangle
      values.field_type = AllowedTypes.STRING_ as unknown as FieldTypes;
    }

    const payload = { ...values } as unknown as CustomFieldDefinitionWithId;
    // @ts-ignore - allow_list needs to be removed from custom field payload
    delete payload.allow_list;
    const result = customField
      ? await updateCustomFieldDefinition(payload)
      : await addCustomFieldDefinition(payload);

    if ("error" in result) {
      errorAlert(
        getErrorMessage(result.error),
        `Custom field has failed to save due to the following:`,
      );
    } else {
      onClose();
      successAlert(`Custom field successfully saved`);
    }
  };

  return (
    <Modal
      id="custom-field-modal-hello-world"
      isOpen={isOpen}
      onClose={onClose}
      size="lg"
      returnFocusOnClose={false}
      isCentered
    >
      <ModalOverlay />
      <ModalContent
        id="modal-content"
        data-testid="custom-field-modal"
        maxHeight="80%"
        overflowY="auto"
      >
        <ModalHeader
          id="modal-header"
          fontWeight="semibold"
          lineHeight={5}
          fontSize="sm"
          py="18px"
          px={6}
          height="56px"
          backgroundColor="gray.50"
          borderColor="gray.200"
          borderWidth="0px 0px 1px 1p"
          borderTopRightRadius="8px"
          borderTopLeftRadius="8px"
          boxSizing="border-box"
        >
          {customField ? "Manage Custom Field" : "Add a custom field"}
        </ModalHeader>
        <ModalBody px={6} py={0}>
          <Formik
            initialValues={initialValues}
            validationSchema={validationSchema}
            onSubmit={handleSubmit}
            enableReinitialize
            validateOnChange
          >
            {(props) => (
              <CustomFieldForm
                isEditing={isEditing}
                validationSchema={validationSchema}
                isLoading={isLoading}
                onClose={onClose}
                handleDropdownChange={handleDropdownChange}
                {...props}
              />
            )}
          </Formik>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
