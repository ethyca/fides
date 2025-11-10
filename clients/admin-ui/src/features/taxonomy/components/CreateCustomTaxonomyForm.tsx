import {
  AntButton as Button,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntMessageInstance as MessageInstance,
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
  "Create and organize the core terminology your team uses to describe data and how it's handled. Custom taxonomies let you define domain-specific concepts and then apply them to other privacy objects throughout the platform";

const CreateCustomTaxonomyForm = ({
  onClose,
  messageApi,
}: {
  onClose: () => void;
  messageApi: MessageInstance;
}) => {
  const [createCustomTaxonomy, { isLoading: isSubmitting }] =
    useCreateCustomTaxonomyMutation();

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
      <Typography.Paragraph>{FORM_COPY}</Typography.Paragraph>
      <Form
        layout="vertical"
        onFinish={handleSubmit}
        validateTrigger={["onBlur", "onChange"]}
      >
        <Form.Item
          label="Taxonomy name"
          name="name"
          rules={[{ required: true, message: "Name is required" }]}
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
