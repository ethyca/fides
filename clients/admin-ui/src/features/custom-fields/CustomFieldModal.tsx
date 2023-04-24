import {
  Box,
  Button,
  Flex,
  IconButton,
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
  Text,
} from "@fidesui/react";
import {
  FIELD_TYPE_OPTIONS,
  RESOURCE_TYPE_OPTIONS,
} from "common/custom-fields";
import CustomInput, {
  CUSTOM_LABEL_STYLES,
} from "common/custom-fields/form/CustomInput";
import { AddIcon } from "common/custom-fields/icons/AddIcon";
import FormSection from "common/form/FormSection";
import { CustomSelect } from "common/form/inputs";
import { getErrorMessage } from "common/helpers";
import { useAlert } from "common/hooks";
import { TrashCanSolidIcon } from "common/Icon/TrashCanSolidIcon";
import { FieldArray, Form, Formik, FormikHelpers } from "formik";
import * as Yup from "yup";

import {
  useAddCustomFieldDefinitionMutation,
  useUpsertAllowListMutation,
  useGetAllowListQuery,
  useUpdateCustomFieldDefinitionMutation,
} from "~/features/plus/plus.slice";
import {
  AllowedTypes,
  AllowListUpdate,
  CustomFieldDefinition,
  CustomFieldDefinitionWithId,
  ResourceTypes,
} from "~/types/api";

const CustomFieldLabelStyles = {
  ...CUSTOM_LABEL_STYLES,
  minWidth: "unset",
};

type ModalProps = {
  isOpen: boolean;
  onClose: () => void;
  isLoading: boolean;
  customField?: CustomFieldDefinitionWithId;
};

type FormValues = CustomFieldDefinition & {
  allow_list: AllowListUpdate;
};

const initialValuesTemplate: FormValues = {
  description: "",
  field_type: AllowedTypes.STRING,
  name: "",
  resource_type: ResourceTypes.SYSTEM,
  allow_list: {
    name: "",
    description: "",
    allowed_values: [],
  },
};

const validationSchema = Yup.object().shape({
  name: Yup.string().required("Name is required").trim(),
  allow_list: Yup.object().shape({
    name: Yup.string().required("Name is required").trim(),
    allowed_values: Yup.array(Yup.string().required("List item is required"))
      .min(1, "Must add at least one list value")
      .label("allowed_values"),
  }),
});

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

  if (isLoadingAllowList || !isOpen) {
    return null;
  }

  const initialValues = customField
    ? ({
        ...customField,
        allow_list: {
          ...allowList,
        },
      } as FormValues)
    : initialValuesTemplate;

  const handleSubmit = async (
    values: FormValues,
    helpers: FormikHelpers<FormValues>
  ) => {
    if (
      [AllowedTypes.STRING_, AllowedTypes.STRING].includes(values.field_type)
    ) {
      const uniqueValues = new Set(
        values.allow_list?.allowed_values
          .map((v) => v.toLowerCase().trim())
          .map((v) => v)
      );
      if (uniqueValues.size < values.allow_list!.allowed_values.length) {
        errorAlert("List item value must be unique");
        return;
      }

      const allowListPayload: AllowListUpdate = {
        ...values.allow_list!,
      };

      if (values.allow_list_id) {
        allowListPayload.id = values.allow_list_id;
      }

      const result = await upsertAllowList(allowListPayload);
      if (!("error" in result) && !values.allow_list_id) {
        // eslint-disable-next-line no-param-reassign
        values.allow_list_id = result.data?.id;
      }
      //Add error handling here
    }

    const result = customField
      ? await updateCustomFieldDefinition(values)
      : await addCustomFieldDefinition(values);

    if ("error" in result) {
      errorAlert(
        getErrorMessage(result.error),
        `Custom field has failed to save due to the following:`
      );
    } else {
      onClose();
      successAlert(`Custom field successfully saved`);
    }
  };
  console.log("initialValues", initialValues);
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
        textAlign="center"
        data-testid="custom-field-modal"
        maxHeight="80%"
        overflowY="auto"
      >
        <ModalHeader
          id="modal-header"
          fontWeight="semibold"
          lineHeight={5}
          fontSize="sm"
          textAlign="left"
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
          Edit Custom Field
        </ModalHeader>
        <ModalBody px={6} py={0}>
          <Formik
            initialValues={initialValues}
            validationSchema={validationSchema}
            onSubmit={handleSubmit}
          >
            {({ dirty, isValid, isSubmitting, values, errors }) => (
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
                    />
                  </FormSection>
                </Box>
                <Box py={3}>
                  <FormSection title="Configuration">
                    <CustomSelect
                      label="Field Type"
                      name="field_type"
                      options={FIELD_TYPE_OPTIONS}
                    />
                    <Flex
                      flexDirection="column"
                      gap="12px"
                      paddingTop="6px"
                      paddingBottom="24px"
                    >
                      <CustomInput
                        displayHelpIcon={false}
                        isRequired
                        label="Name"
                        name="allow_list.name"
                        placeholder=""
                      />
                      <CustomInput
                        displayHelpIcon={false}
                        height="100px"
                        label="Description"
                        name="allow_list.description"
                        placeholder=""
                        type="textarea"
                      />
                      <FieldArray
                        name="allow_list.allowed_values"
                        render={(fieldArrayProps) => {
                          // eslint-disable-next-line @typescript-eslint/naming-convention
                          const { allowed_values } = values.allow_list;
                          // @ts-ignore
                          return (
                            <Flex flexDirection="column" gap="24px" pl="24px">
                              <Flex flexDirection="column">
                                {allowed_values.map((_value, index) => (
                                  <Flex
                                    flexGrow={1}
                                    gap="12px"
                                    // eslint-disable-next-line react/no-array-index-key
                                    key={index}
                                    mt={index > 0 ? "12px" : undefined}
                                    // ref={fieldRef}
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
                                      onClick={() =>
                                        fieldArrayProps.remove(index)
                                      }
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
                                {allowed_values.length === 0 &&
                                errors?.allow_list ? (
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
                    {/* <CreateCustomLists */}
                    {/*   onSubmitComplete={() => {}} */}
                    {/*   ref={createCustomListsRef} */}
                    {/* /> */}
                  </FormSection>
                </Box>

                <SimpleGrid columns={2} width="100%">
                  <Button
                    variant="outline"
                    mr={3}
                    onClick={onClose}
                    data-testid="cancel-btn"
                    isDisabled={isLoading || isSubmitting}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    colorScheme="primary"
                    data-testid="save-btn"
                    isLoading={isLoading}
                    isDisabled={!dirty || !isValid || isSubmitting}
                  >
                    Save
                  </Button>
                </SimpleGrid>
              </Form>
            )}
          </Formik>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
