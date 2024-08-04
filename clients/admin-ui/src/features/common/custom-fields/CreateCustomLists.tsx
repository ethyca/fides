import { Flex, forwardRef, IconButton, Text } from "fidesui";
import { FieldArray, Form, Formik, FormikHelpers, FormikProps } from "formik";
import { useEffect, useImperativeHandle, useRef, useState } from "react";
import * as Yup from "yup";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { TrashCanSolidIcon } from "~/features/common/Icon/TrashCanSolidIcon";
import { useUpsertAllowListMutation } from "~/features/plus/plus.slice";
import { AllowListUpdate } from "~/types/api";

import CustomInput from "./form/CustomInput";
import { AddIcon } from "./icons/AddIcon";
import { Layout } from "./Layout";

const initialValues: AllowListUpdate = {
  allowed_values: [""] as string[],
  description: undefined,
  id: undefined,
  name: "",
};

type FormValues = typeof initialValues;

const validationSchema = Yup.object().shape({
  name: Yup.string().required("Name is required").trim(),
  allowed_values: Yup.array(Yup.string().required("List item is required"))
    .min(1, "Must add at least one list value")
    .label("allowed_values"),
});

type CreateCustomListProps = {
  onSubmitComplete: () => void;
};

const CreateCustomLists = forwardRef(
  ({ onSubmitComplete }: CreateCustomListProps, ref) => {
    const { errorAlert, successAlert } = useAlert();
    const formRef = useRef(null);
    const fieldRef = useRef<HTMLInputElement>(null);
    const [hasAutoScroll, setHasAutoScroll] = useState(false);

    const [upsertAllowList] = useUpsertAllowListMutation();

    const handleSubmit = async (
      values: FormValues,
      helpers: FormikHelpers<FormValues>,
    ) => {
      const uniqueValues = new Set(
        values.allowed_values.map((v) => v.toLowerCase().trim()).map((v) => v),
      );
      if (uniqueValues.size < values.allowed_values.length) {
        errorAlert("List item value must be unique");
        return;
      }

      // Save the form data
      const result = await upsertAllowList(values);
      if ("error" in result) {
        errorAlert(
          getErrorMessage(result.error),
          `Custom list has failed to save due to the following:`,
        );
      } else {
        helpers.resetForm();
        successAlert(`Custom list successfully saved`);
      }
      onSubmitComplete();
    };

    useEffect(() => {
      if (hasAutoScroll && fieldRef.current) {
        fieldRef.current.scrollIntoView({ behavior: "smooth" });
        setHasAutoScroll(false);
      }
    }, [hasAutoScroll]);

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
            <Form data-testid="create-custom-lists-form" noValidate>
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
                <FieldArray
                  name="allowed_values"
                  render={(fieldArrayProps) => {
                    // eslint-disable-next-line @typescript-eslint/naming-convention
                    const { allowed_values } = props.values;
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
                              ref={fieldRef}
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
                                name={`allowed_values[${index}]`}
                              />
                              <IconButton
                                aria-label="Remove this list value"
                                data-testid={`remove-list-value-btn-${index}`}
                                icon={<TrashCanSolidIcon />}
                                isDisabled={allowed_values.length <= 1}
                                onClick={() => fieldArrayProps.remove(index)}
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
                              setHasAutoScroll(true);
                            }}
                            size="xs"
                            variant="outline"
                          />
                          {allowed_values.length === 0 && (
                            <Text color="red.500" pl="18px" size="sm">
                              {props.errors.allowed_values}
                            </Text>
                          )}
                        </Flex>
                      </Flex>
                    );
                  }}
                />
              </Flex>
            </Form>
          )}
        </Formik>
      </Layout>
    );
  },
);

export { CreateCustomLists };
