import { NOTIFICATIONS_TEMPLATES_ROUTE } from "common/nav/routes";
import { Button, Card, Flex, Form, Input, Switch } from "fidesui";
import NextLink from "next/link";

import { useAppSelector } from "~/app/hooks";
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
  handleSubmit: (values: FormValues) => Promise<boolean>;
  handleDelete?: () => void;
  isSaving?: boolean;
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

interface PropertiesListProps {
  value?: MinimalProperty[];
  onChange?: (value: MinimalProperty[]) => void;
}

const PropertiesList = ({ value, onChange }: PropertiesListProps) => {
  const propertyPage = useAppSelector(selectPropertyPage);
  const propertyPageSize = useAppSelector(selectPropertyPageSize);
  useGetAllPropertiesQuery({ page: propertyPage, size: propertyPageSize });
  const allProperties = useAppSelector(selectAllProperties);

  return (
    <ScrollableList
      addButtonLabel="Add property"
      idField="id"
      nameField="name"
      allItems={allProperties.reduce<MinimalProperty[]>((acc, property) => {
        if (property.id) {
          acc.push({ id: property.id, name: property.name });
        }
        return acc;
      }, [])}
      values={value ?? []}
      setValues={(newValues) => onChange?.(newValues)}
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
  isSaving,
}: Props) => {
  const [form] = Form.useForm<FormValues>();

  const initialValues: FormValues = {
    type: template.type,
    content: template.content,
    properties: template.properties || [],
    is_enabled: template.is_enabled,
    id: template.id || "",
  };

  // Re-mount the form only when the underlying template identity changes, not
  // on every content update. Scoping the key this narrowly avoids discarding
  // in-progress edits if a background refetch returns data that differs from
  // what the user has typed.
  const formKey = template.id || template.type;

  const onFinish = async (values: FormValues) => {
    const succeeded = await handleSubmit(values);
    if (succeeded) {
      // Re-baseline after a successful save so `isFieldsTouched()` flips back
      // to false and Save becomes disabled again until the next edit.
      form.resetFields();
      form.setFieldsValue(values);
    }
  };

  return (
    <Form
      key={formKey}
      form={form}
      layout="vertical"
      initialValues={initialValues}
      onFinish={onFinish}
      className="py-3"
    >
      <Card
        title={
          CustomizableMessagingTemplatesLabelEnum[
            initialValues.type as CustomizableMessagingTemplatesEnum
          ]
        }
        className="my-3"
      >
        <Form.Item
          name={["content", "subject"]}
          label="Email subject"
          rules={[{ required: true, message: "Subject is required" }]}
        >
          <Input data-testid="input-content.subject" />
        </Form.Item>
        <Form.Item
          name={["content", "body"]}
          label="Message body"
          rules={[{ required: true, message: "Body is required" }]}
        >
          <Input.TextArea
            autoSize={{ minRows: 3 }}
            data-testid="input-content.body"
          />
        </Form.Item>
        <Form.Item name="properties" label="Associated properties">
          <PropertiesList />
        </Form.Item>
        <Form.Item
          name="is_enabled"
          label="Enable message"
          valuePropName="checked"
        >
          <Switch data-testid="input-is_enabled" />
        </Form.Item>
      </Card>
      <Flex justify="space-between" className="w-full pt-2">
        {initialValues.id && handleDelete && (
          <Button
            data-testid="delete-template-button"
            className="mr-3"
            onClick={handleDelete}
          >
            Delete
          </Button>
        )}
        <Flex justify="flex-end" className="w-full pt-2">
          <NextLink href={NOTIFICATIONS_TEMPLATES_ROUTE} passHref>
            <Button className="mr-3">Cancel</Button>
          </NextLink>
          <Form.Item shouldUpdate noStyle>
            {() => (
              <Button
                htmlType="submit"
                type="primary"
                disabled={
                  !form.isFieldsTouched() ||
                  form.getFieldsError().some(({ errors }) => errors.length > 0)
                }
                loading={isSaving}
                data-testid="submit-btn"
              >
                Save
              </Button>
            )}
          </Form.Item>
        </Flex>
      </Flex>
    </Form>
  );
};

export default PropertySpecificMessagingTemplateForm;
