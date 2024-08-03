import { Flex, forwardRef, Spacer, Switch, Text } from "fidesui";
import {
  Field,
  FieldInputProps,
  Form,
  Formik,
  FormikHelpers,
  FormikProps,
} from "formik";
import { satisfier } from "narrow-minded";
import React, {
  ChangeEvent,
  useImperativeHandle,
  useMemo,
  useRef,
} from "react";
import * as Yup from "yup";

import { CustomSelect } from "~/features/common/form/inputs";
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

import { FIELD_TYPE_OPTIONS, RESOURCE_TYPE_OPTIONS } from "./constants";
import CustomInput, { CUSTOM_LABEL_STYLES } from "./form/CustomInput";
import { Layout } from "./Layout";

const initialValuesTemplate: CustomFieldDefinition = {
  active: true,
  allow_list_id: undefined,
  description: undefined,
  field_type: AllowedTypes.STRING,
  name: "",
  resource_type: ResourceTypes.DATA_CATEGORY,
};

const validationSchema = Yup.object().shape({
  allow_list_id: Yup.string().required("Select custom list is required"),
  name: Yup.string().required("Name is required").trim(),
});

type CreateCustomFieldProps = {
  onSubmitComplete: () => void;
  resourceType: ResourceTypes;
};

const CreateCustomFields = forwardRef(
  (
    { onSubmitComplete, resourceType }: CreateCustomFieldProps,
    ref,
  ): React.JSX.Element => {
    const { errorAlert, successAlert } = useAlert();
    const formRef = useRef(null);

    const { data } = useGetAllAllowListQuery(false);
    const [addCustomFieldDefinition] = useAddCustomFieldDefinitionMutation();

    const handleSubmit = async (
      values: CustomFieldDefinition,
      helpers: FormikHelpers<CustomFieldDefinition>,
    ) => {
      const result = await addCustomFieldDefinition(values);
      if ("error" in result) {
        errorAlert(
          getErrorMessage(result.error),
          `Custom field has failed to save due to the following:`,
        );
      } else {
        helpers.resetForm();
        successAlert(`Custom field successfully saved`);
      }
      onSubmitComplete();
    };

    const allowListOptions = useMemo(
      () =>
        (data ?? [])
          .filter(satisfier({ name: "string", id: "string" }))
          .map((allowList) => ({
            label: allowList.name,
            value: allowList.id,
          })),
      [data],
    );

    useImperativeHandle(
      ref,
      () => ({
        getDirty() {
          let value = false;
          if (formRef.current) {
            value = (formRef.current as FormikProps<CustomFieldDefinition>)
              .dirty;
          }
          return value;
        },
        submitForm() {
          if (formRef.current) {
            (
              formRef.current as FormikProps<CustomFieldDefinition>
            ).submitForm();
          }
        },
      }),
      [],
    );

    const initialValues: CustomFieldDefinition = {
      ...initialValuesTemplate,
      resource_type: resourceType,
      allow_list_id: allowListOptions[0]?.value,
    };

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
          {(props: FormikProps<CustomFieldDefinition>) => (
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
                <CustomSelect
                  label="Field type"
                  labelProps={CUSTOM_LABEL_STYLES}
                  name="field_type"
                  options={FIELD_TYPE_OPTIONS}
                />
                <CustomSelect
                  isRequired
                  label="Select custom list"
                  labelProps={CUSTOM_LABEL_STYLES}
                  menuPosition="fixed"
                  name="allow_list_id"
                  options={allowListOptions}
                />
                <CustomSelect
                  isDisabled
                  label="Resource type"
                  labelProps={CUSTOM_LABEL_STYLES}
                  name="resource_type"
                  options={RESOURCE_TYPE_OPTIONS}
                />
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
  },
);

export { CreateCustomFields };
