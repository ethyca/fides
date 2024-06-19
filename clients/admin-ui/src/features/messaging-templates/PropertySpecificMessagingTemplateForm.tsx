import { MESSAGING_ROUTE } from "common/nav/v2/routes";
import { Box, Button, Flex } from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import FormSection from "~/features/common/form/FormSection";
import {
  CustomSwitch,
  CustomTextArea,
  CustomTextInput,
} from "~/features/common/form/inputs";
import ScrollableList from "~/features/common/ScrollableList";
import { MessagingTemplateResponse } from "~/features/messaging-templates/messaging-templates.slice";
import MessagingActionTypeLabelEnum from "~/features/messaging-templates/MessagingActionTypeLabelEnum";
import {
  selectAllProperties,
  selectPage as selectPropertyPage,
  selectPageSize as selectPropertyPageSize,
  useGetAllPropertiesQuery,
} from "~/features/properties";
import { MessagingActionType, MinimalProperty } from "~/types/api";

interface Props {
  template: MessagingTemplateResponse;
  handleSubmit: (values: FormValues) => Promise<void>;
  handleDelete?: () => void;
}

export interface FormValues {
  type: string;
  id?: string;
  is_enabled: boolean;
  content: {
    subject: string;
    body: string;
  };
  properties?: MinimalProperty[];
}

const PropertySpecificMessagingTemplateForm = ({
  template,
  handleSubmit,
  handleDelete,
}: Props) => {
  const router = useRouter();
  const propertyPage = useAppSelector(selectPropertyPage);
  const propertyPageSize = useAppSelector(selectPropertyPageSize);
  useGetAllPropertiesQuery({ page: propertyPage, size: propertyPageSize });
  const allProperties = useAppSelector(selectAllProperties);

  const handleCancel = () => {
    router.push(MESSAGING_ROUTE);
  };

  const initialValues = useMemo(
    () => ({
      type: template.type,
      content: template.content,
      properties: template.properties,
      is_enabled: template.is_enabled,
      id: template.id,
    }),
    [template]
  );

  return (
    <Formik<FormValues>
      enableReinitialize
      initialValues={initialValues}
      onSubmit={handleSubmit}
    >
      {({ dirty, isValid, isSubmitting, setFieldValue }) => (
        <Form
          style={{
            paddingTop: "12px",
            paddingBottom: "12px",
          }}
        >
          <Box py={3}>
            <FormSection
              title={`${
                MessagingActionTypeLabelEnum[
                  initialValues.type as MessagingActionType
                ]
              }`}
            >
              <CustomTextInput
                isRequired
                label="Message subject"
                name="content.subject"
                tooltip="Email subject to display"
                variant="stacked"
              />
              <CustomTextArea
                isRequired
                label="Message body"
                name="content.body"
                value="test"
                variant="stacked"
                resize
              />
              <Box py={3}>
                <ScrollableList
                  label="Associated properties"
                  addButtonLabel="Add property"
                  idField="id"
                  nameField="name"
                  allItems={allProperties.map((property) => ({
                    id: property.id,
                    name: property.name,
                  }))}
                  values={initialValues.properties ?? []}
                  // fixme- setFieldValue is not working properly
                  setValues={(newValues) =>
                    setFieldValue("properties", newValues)
                  }
                  draggable
                  maxHeight={100}
                  baseTestId="property"
                />
              </Box>
              <CustomSwitch
                name="is_enabled"
                label="Message enabled"
                tooltip="Configure whether this messaging template is enabled"
                variant="switchFirst"
              />
            </FormSection>
          </Box>
          <Flex justifyContent="space-between" width="100%" paddingTop={2}>
            {initialValues.id && handleDelete && (
              <Button
                data-testid="delete-template-button"
                size="sm"
                variant="outline"
                isLoading={false}
                mr={3}
                onClick={handleDelete}
              >
                Delete
              </Button>
            )}
            <Flex justifyContent="right" width="100%" paddingTop={2}>
              <Button
                size="sm"
                variant="outline"
                isLoading={false}
                mr={3}
                onClick={handleCancel}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                type="submit"
                colorScheme="primary"
                isDisabled={isSubmitting || !dirty || !isValid}
                isLoading={isSubmitting}
              >
                Save
              </Button>
            </Flex>
          </Flex>
        </Form>
      )}
    </Formik>
  );
};

export default PropertySpecificMessagingTemplateForm;
