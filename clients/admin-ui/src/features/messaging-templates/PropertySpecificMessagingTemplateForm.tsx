import { MESSAGING_ROUTE } from "common/nav/v2/routes";
import { AntButton as Button, Box, Flex } from "fidesui";
import { Form, Formik, useFormikContext } from "formik";
import { useRouter } from "next/router";

import { useAppSelector } from "~/app/hooks";
import FormSection from "~/features/common/form/FormSection";
import {
  CustomSwitch,
  CustomTextArea,
  CustomTextInput,
} from "~/features/common/form/inputs";
import ScrollableList from "~/features/common/ScrollableList";
import { CustomizableMessagingTemplatesEnum } from "~/features/messaging-templates/CustomizableMessagingTemplatesEnum";
import CustomizableMessagingTemplatesLabelEnum from "~/features/messaging-templates/CustomizableMessagingTemplatesLabelEnum";
import { MessagingTemplateResponse } from "~/features/messaging-templates/messaging-templates.slice";
import {
  selectAllProperties,
  selectPage as selectPropertyPage,
  selectPageSize as selectPropertyPageSize,
  useGetAllPropertiesQuery,
} from "~/features/properties";
import { MinimalProperty } from "~/types/api";

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

const PropertiesList = () => {
  const propertyPage = useAppSelector(selectPropertyPage);
  const propertyPageSize = useAppSelector(selectPropertyPageSize);
  useGetAllPropertiesQuery({ page: propertyPage, size: propertyPageSize });
  const allProperties = useAppSelector(selectAllProperties);
  const { values, setFieldValue } = useFormikContext<FormValues>();

  return (
    <ScrollableList
      label="Associated properties"
      addButtonLabel="Add property"
      idField="id"
      nameField="name"
      allItems={allProperties.map((property) => ({
        id: property.id,
        name: property.name,
      }))}
      values={values.properties ?? []}
      setValues={(newValues) => setFieldValue("properties", newValues)}
      draggable
      maxHeight={100}
      baseTestId="property"
    />
  );
};

const PropertySpecificMessagingTemplateForm = ({
  template,
  handleSubmit,
  handleDelete,
}: Props) => {
  const router = useRouter();

  const handleCancel = () => {
    router.push(MESSAGING_ROUTE);
  };

  const initialValues: MessagingTemplateResponse = {
    type: template.type,
    content: template.content,
    properties: template.properties || [],
    is_enabled: template.is_enabled,
    id: template.id || "",
  };

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={handleSubmit}
    >
      {({ dirty, isValid, isSubmitting }) => (
        <Form
          style={{
            paddingTop: "12px",
            paddingBottom: "12px",
          }}
        >
          <Box py={3}>
            <FormSection
              title={`${
                CustomizableMessagingTemplatesLabelEnum[
                  initialValues.type as CustomizableMessagingTemplatesEnum
                ]
              }`}
            >
              <CustomTextInput
                isRequired
                label="Email subject"
                name="content.subject"
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
                <PropertiesList />
              </Box>
              <CustomSwitch
                name="is_enabled"
                label="Enable message"
                variant="switchFirst"
              />
            </FormSection>
          </Box>
          <Flex justifyContent="space-between" width="100%" paddingTop={2}>
            {initialValues.id && handleDelete && (
              <Button
                data-testid="delete-template-button"
                loading={false}
                className="mr-3"
                onClick={handleDelete}
              >
                Delete
              </Button>
            )}
            <Flex justifyContent="right" width="100%" paddingTop={2}>
              <Button loading={false} className="mr-3" onClick={handleCancel}>
                Cancel
              </Button>
              <Button
                htmlType="submit"
                type="primary"
                disabled={isSubmitting || !dirty || !isValid}
                loading={isSubmitting}
                data-testid="submit-btn"
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
