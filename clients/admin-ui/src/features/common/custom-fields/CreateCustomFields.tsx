/* eslint-disable @typescript-eslint/no-unused-vars */
import {
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  forwardRef,
  Spacer,
  Switch,
  Text,
  VStack,
} from "@fidesui/react";
import {
  Field,
  FieldInputProps,
  FieldMetaProps,
  Form,
  Formik,
  FormikHelpers,
  FormikProps,
} from "formik";
import { ChangeEvent, useCallback, useImperativeHandle, useRef } from "react";
import * as Yup from "yup";

import SelectDropdown from "~/features/common/dropdown/SelectDropdown";
import { ItemOption } from "~/features/common/dropdown/types";
import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import {
  useAddCustomFieldDefinitionMutation,
  useGetAllAllowListQuery,
} from "~/features/plus/plus.slice";
import {
  AllowedTypes,
  CustomFieldDefinition,
  ResourceTypes,
} from "~/types/api";

import { FIELD_TYPE_MAP, RESOURCE_TYPE_MAP } from "./constants";
import CustomInput from "./form/CustomInput";
import { Layout } from "./Layout";

const initialValues: CustomFieldDefinition = {
  active: true,
  allow_list_id: undefined,
  description: undefined,
  field_type: AllowedTypes.STRING,
  name: "",
  resource_type: ResourceTypes.DATA_CATEGORY,
};

type FormValues = typeof initialValues;

const validationSchema = Yup.object().shape({
  allow_list_id: Yup.string().required("Select custom list is required"),
  name: Yup.string().required("Name is required").trim(),
});

type CreateCustomFieldsProps = {
  onSubmitComplete: () => void;
  resourceType: ResourceTypes;
};

const CreateCustomFields = forwardRef(
  ({ onSubmitComplete, resourceType }, ref) => {
    initialValues.resource_type = resourceType;
    const { errorAlert, successAlert } = useAlert();
    const formRef = useRef(null);

    const { data } = useGetAllAllowListQuery(false);
    const [addCustomFieldDefinition] = useAddCustomFieldDefinitionMutation();

    const handleSubmit = async (
      values: FormValues,
      helpers: FormikHelpers<FormValues>
    ) => {
      const result = await addCustomFieldDefinition(values);
      if ("error" in result) {
        errorAlert(
          getErrorMessage(result.error),
          `Custom field has failed to save due to the following:`
        );
      } else {
        helpers.resetForm();
        successAlert(`Custom field successfully saved`);
      }
      onSubmitComplete();
    };

    const loadList = useCallback((): Map<string, ItemOption> => {
      const list = new Map<string, ItemOption>();
      if (data?.length) {
        data.forEach((value, index) => {
          if (value?.id && value?.name) {
            list.set(value.name, { value: value.id });
            if (index === 0) {
              initialValues.allow_list_id = value.id;
            }
          }
        });
      }
      list.set("Select...", { value: "" });
      return list;
    }, [data]);

    const list = loadList();

    useImperativeHandle(
      ref,
      () => ({
        getDirty() {
          let value = false;
          if (formRef.current) {
            value = (formRef.current as FormikProps<FormValues>).dirty;
          }
          return value;
        },
        submitForm() {
          if (formRef.current) {
            (formRef.current as FormikProps<FormValues>).submitForm();
          }
        },
      }),
      []
    );

    return (
      <Layout>
        <Formik
          enableReinitialize
          initialValues={initialValues}
          innerRef={formRef}
          onSubmit={handleSubmit}
          validationOnBlur={false}
          validationOnChange={false}
          validationSchema={validationSchema}
        >
          {(props: FormikProps<FormValues>) => (
            <Form data-testid="create-custom-fields-form" noValidate>
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
                  name="name"
                  placeholder=""
                />
                <CustomInput
                  displayHelpIcon={false}
                  height="100px"
                  label="Description"
                  name="description"
                  placeholder=""
                  type="textarea"
                />
                <Field name="field_type">
                  {({ field }: { field: FieldInputProps<string> }) => (
                    <FormControl display="flex">
                      <FormLabel
                        color="gray.600"
                        fontSize="14px"
                        fontWeight="semibold"
                        minWidth="150px"
                      >
                        Field type
                      </FormLabel>
                      <VStack align="flex-start" flexGrow={1}>
                        <SelectDropdown
                          enableSorting={false}
                          hasClear={false}
                          label=""
                          list={FIELD_TYPE_MAP}
                          menuButtonProps={{
                            textAlign: "left",
                            width: "100%",
                          }}
                          onChange={(value: string | undefined) => {
                            props.setFieldValue("field_type", value);
                          }}
                          selectedValue={props.values.field_type}
                        />
                      </VStack>
                    </FormControl>
                  )}
                </Field>
                <Field name="allow_list_id">
                  {({
                    field,
                    meta,
                  }: {
                    field: FieldInputProps<string>;
                    meta: FieldMetaProps<string>;
                  }) => (
                    <FormControl
                      display="flex"
                      isRequired
                      isInvalid={!!(meta.error && meta.touched)}
                    >
                      <FormLabel
                        color="gray.600"
                        fontSize="14px"
                        fontWeight="semibold"
                        minWidth="150px"
                      >
                        Select custom list
                      </FormLabel>
                      <VStack align="flex-start" flexGrow={1}>
                        <SelectDropdown
                          enableSorting={false}
                          hasClear={false}
                          label="Select..."
                          list={list}
                          menuButtonProps={{
                            textAlign: "left",
                            width: "100%",
                          }}
                          onChange={(value: string | undefined) => {
                            props.setFieldValue("allow_list_id", value);
                          }}
                          selectedValue={props.values.allow_list_id || ""}
                        />

                        <FormErrorMessage>{meta.error}</FormErrorMessage>
                      </VStack>
                    </FormControl>
                  )}
                </Field>
                <Field name="resource_type">
                  {({ field }: { field: FieldInputProps<string> }) => (
                    <FormControl display="flex">
                      <FormLabel
                        color="gray.600"
                        fontSize="14px"
                        fontWeight="semibold"
                        minWidth="150px"
                      >
                        Resource type
                      </FormLabel>
                      <VStack align="flex-start" flexGrow={1}>
                        <SelectDropdown
                          disabled
                          enableSorting={false}
                          hasClear={false}
                          label=""
                          list={RESOURCE_TYPE_MAP}
                          menuButtonProps={{
                            textAlign: "left",
                            width: "100%",
                          }}
                          onChange={(value: string | undefined) => {
                            props.setFieldValue("resource_type", value);
                          }}
                          selectedValue={props.values.resource_type}
                        />
                      </VStack>
                    </FormControl>
                  )}
                </Field>
              </Flex>
              <Flex
                background="gray.50"
                border="1px solid"
                borderColor="gray.200"
                borderRadius="6px"
                flexDirection="column"
                gap="4px"
                padding="16px"
              >
                <Flex>
                  <Text
                    color="gray.600"
                    fontWeight="semibold"
                    lineHeight="20px"
                    size="sm"
                  >
                    Show in forms and reports
                  </Text>
                  <Spacer />
                  <Field name="active">
                    {({ field }: { field: FieldInputProps<string> }) => (
                      <Switch
                        {...field}
                        colorScheme="secondary"
                        isChecked={props.values.active}
                        onChange={(event: ChangeEvent<HTMLInputElement>) => {
                          field.onChange(event);
                        }}
                        size="sm"
                      />
                    )}
                  </Field>
                </Flex>
                <Text
                  color="gray.600"
                  fontWeight="light"
                  lineHeight="20px"
                  size="sm"
                >
                  Turn this off to hide this field from this form and data map
                  reports. You can turn hidden fields back on at any time from
                  the library tab.
                </Text>
              </Flex>
            </Form>
          )}
        </Formik>
      </Layout>
    );
  }
);

export { CreateCustomFields };
