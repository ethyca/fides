import {
  Center,
  Flex,
  FormControl,
  FormLabel,
  forwardRef,
  Spacer,
  Spinner,
  Switch,
} from "fidesui";
import {
  Field,
  FieldArray,
  FieldInputProps,
  Form,
  Formik,
  FormikHelpers,
  FormikProps,
} from "formik";
import { ChangeEvent, useImperativeHandle, useMemo, useRef } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import {
  useGetCustomFieldDefinitionsByResourceTypeQuery,
  useUpdateCustomFieldDefinitionMutation,
} from "~/features/plus/plus.slice";
import { CustomFieldDefinitionWithId, ResourceTypes } from "~/types/api";

import { Layout } from "./Layout";

const initialValues = {
  customFieldDefinitions: [] as CustomFieldDefinitionWithId[],
};

type FormValues = typeof initialValues;

type ChooseFromLibraryProps = {
  onSubmitComplete: () => void;
  resourceType: ResourceTypes;
};

const ChooseFromLibrary = forwardRef(
  ({ onSubmitComplete, resourceType }: ChooseFromLibraryProps, ref) => {
    const { errorAlert, successAlert } = useAlert();
    const formRef = useRef(null);

    const { data, isFetching, isLoading, isSuccess } =
      useGetCustomFieldDefinitionsByResourceTypeQuery(resourceType);

    const [updateCustomFieldDefinition] =
      useUpdateCustomFieldDefinitionMutation();

    initialValues.customFieldDefinitions = useMemo(() => data || [], [data]);

    const handleSubmit = async (
      values: FormValues,
      helpers: FormikHelpers<FormValues>,
    ) => {
      const dirtyFields = values.customFieldDefinitions.filter((item) =>
        initialValues.customFieldDefinitions.some(
          (cfd) => cfd.id === item.id && cfd.active !== item.active,
        ),
      );
      if (dirtyFields.length === 0) {
        return;
      }
      const updateResults = await Promise.all(
        dirtyFields.map((item) => updateCustomFieldDefinition(item)),
      );
      const updateResult =
        updateResults.find((result) => "error" in result) ?? updateResults[0];
      if ("error" in updateResult) {
        errorAlert(
          getErrorMessage(updateResult.error),
          `One or more custom field(s) failed to update due to the following:`,
          { containerStyle: { maxWidth: "max-content" } },
        );
      } else {
        helpers.resetForm();
        successAlert(`Custom field(s) successfully saved`);
      }
      onSubmitComplete();
    };

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
      [],
    );

    return (
      <Layout>
        {(isFetching || isLoading) && (
          <Center>
            <Spinner />
          </Center>
        )}
        {isSuccess && data && (
          <Formik
            enableReinitialize
            initialValues={initialValues}
            innerRef={formRef}
            onSubmit={handleSubmit}
            validationOnBlur={false}
            validationOnChange={false}
          >
            {(props: FormikProps<FormValues>) => (
              <Form data-testid="choose-from-library-form" noValidate>
                <Flex
                  flexDirection="column"
                  gap="12px"
                  paddingTop="6px"
                  paddingBottom="24px"
                >
                  <FieldArray
                    name="customFieldDefinitions"
                    render={() => {
                      const { customFieldDefinitions } = props.values;
                      return (
                        <Flex flexDirection="column" gap="24px">
                          <Flex flexDirection="column">
                            {customFieldDefinitions.map((value, index) => (
                              <Flex
                                alignItems="baseline"
                                flexGrow={1}
                                gap="12px"
                                key={value.id}
                                mt={index > 0 ? "12px" : undefined}
                                mr="16px"
                              >
                                <FormControl display="flex">
                                  <FormLabel
                                    htmlFor={`customFieldDefinitions[${index}]`}
                                    {...{
                                      color: "gray.600",
                                      fontSize: "14px",
                                      fontWeight: "medium",
                                      minWidth: "150px",
                                    }}
                                  >
                                    {value.name}
                                  </FormLabel>
                                </FormControl>
                                <Spacer />
                                <Field
                                  name={`customFieldDefinitions[${index}].active`}
                                >
                                  {({
                                    field,
                                  }: {
                                    field: FieldInputProps<string>;
                                  }) => (
                                    <Switch
                                      {...field}
                                      colorScheme="secondary"
                                      isChecked={value.active}
                                      onChange={(
                                        event: ChangeEvent<HTMLInputElement>,
                                      ) => {
                                        field.onChange(event);
                                      }}
                                      size="sm"
                                    />
                                  )}
                                </Field>
                              </Flex>
                            ))}
                          </Flex>
                        </Flex>
                      );
                    }}
                  />
                </Flex>
              </Form>
            )}
          </Formik>
        )}
      </Layout>
    );
  },
);

export { ChooseFromLibrary };
