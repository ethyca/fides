/* eslint-disable @typescript-eslint/no-unused-vars */
import {
  Center,
  Flex,
  forwardRef,
  Input,
  Spacer,
  Spinner,
  Switch,
} from "@fidesui/react";
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

import { useAlert } from "~/features/common/hooks";
import { useGetCustomFieldDefinitionsByResourceTypeQuery } from "~/features/plus/plus.slice";
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

    const handleSubmit = async (
      values: FormValues,
      helpers: FormikHelpers<FormValues>
    ) => {
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
      []
    );

    initialValues.customFieldDefinitions = useMemo(() => data || [], [data]);

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
                    render={(fieldArrayProps) => {
                      const { customFieldDefinitions } = props.values;
                      return (
                        <Flex flexDirection="column" gap="24px">
                          <Flex flexDirection="column">
                            {customFieldDefinitions.map((value, index) => (
                              <Flex
                                alignItems="baseline"
                                flexGrow={1}
                                gap="12px"
                                // eslint-disable-next-line react/no-array-index-key
                                key={index}
                                mt={index > 0 ? "12px" : undefined}
                                mr="16px"
                              >
                                {/*  <FormControl display="flex">
                                  <FormLabel
                                    htmlFor={`customFieldDefinitions[${index}]`}
                                    {...CUSTOM_LABEL_STYLES}
                                  >
                                    {value.name}
                                  </FormLabel>
                                </FormControl> */}
                                <Input
                                  color="gray.700"
                                  isDisabled
                                  size="sm"
                                  value={value.name}
                                />
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
                                        event: ChangeEvent<HTMLInputElement>
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
  }
);

export { ChooseFromLibrary };
