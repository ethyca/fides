import {
  AntButton as Button,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntMessage as message,
  AntTypography as Typography,
} from "fidesui";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import { useCreateCustomTaxonomyMutation } from "~/features/taxonomy/taxonomy.slice";

interface CreateCustomTaxonomyFormValues {
  name: string;
  description: string;
}

const FORM_COPY =
  "Define structured taxonomies like Data Categories or Data Uses. Each taxonomy can include required fields that users must complete when applying a label.";

const CreateCustomTaxonomyForm = ({ onClose }: { onClose: () => void }) => {
  const [createCustomTaxonomy, { isLoading: isSubmitting }] =
    useCreateCustomTaxonomyMutation();

  const [messageApi, messageContext] = message.useMessage();

  const handleSubmit = async (values: CreateCustomTaxonomyFormValues) => {
    const payload = {
      ...values,
      taxonomy_type: formatKey(values.name ?? ""),
    };
    const result = await createCustomTaxonomy(payload);
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success("Taxonomy created successfully");
    onClose();
  };

  return (
    <>
      {messageContext}
      <Typography.Paragraph>{FORM_COPY}</Typography.Paragraph>
      <Form
        layout="vertical"
        onFinish={handleSubmit}
        validateTrigger={["onBlur", "onChange"]}
      >
        <Form.Item
          label="Name"
          name="name"
          rules={[{ required: true, message: "Please enter a name" }]}
        >
          <Input data-testid="input-name" />
        </Form.Item>

        <Form.Item label="Description" name="description">
          <Input.TextArea rows={2} data-testid="input-description" />
        </Form.Item>

        <Flex gap="small" justify="space-between">
          <Button onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            loading={isSubmitting}
            disabled={isSubmitting}
            data-testid="save-btn"
          >
            Create taxonomy
          </Button>
        </Flex>
      </Form>
    </>
  );
};

export default CreateCustomTaxonomyForm;
