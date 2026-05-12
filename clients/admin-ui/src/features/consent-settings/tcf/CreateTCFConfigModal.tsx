import {
  Button,
  Form,
  Input,
  Modal,
  Space,
  Typography,
  useMessage,
} from "fidesui";
import isEqual from "lodash/isEqual";
import { useEffect, useMemo, useState } from "react";

import { useCreateTCFConfigurationMutation } from "~/features/consent-settings/tcf/tcf-config.slice";
import { isErrorResult } from "~/types/errors";

import { getErrorMessage } from "../../common/helpers";

interface CreateTCFConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (configId: string) => void;
}

const defaultInitialValues = { name: "" };

export const CreateTCFConfigModal = ({
  isOpen,
  onClose,
  onSuccess,
}: CreateTCFConfigModalProps) => {
  const message = useMessage();
  const [createTCFConfiguration] = useCreateTCFConfigurationMutation();
  const [form] = Form.useForm<{ name: string }>();

  const allValues = Form.useWatch([], form);
  const [submittable, setSubmittable] = useState(false);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, allValues]);

  const isDirty = useMemo(
    () => !isEqual(allValues, defaultInitialValues),
    [allValues],
  );

  const handleSubmit = async (values: { name: string }) => {
    const result = await createTCFConfiguration({ name: values.name });
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      message.success("Successfully created TCF configuration");
      onSuccess?.(result.data.id);
      onClose();
    }
  };

  return (
    <Modal
      title="Create a new TCF configuration"
      open={isOpen}
      onCancel={onClose}
      centered
      destroyOnHidden
      footer={null}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={defaultInitialValues}
      >
        <Space orientation="vertical" size="small" className="w-full">
          <Typography.Text>
            TCF configurations allow you to define unique sets of publisher
            restrictions. These configurations can be added to privacy
            experiences.
          </Typography.Text>
          <Form.Item
            name="name"
            label="Name"
            rules={[{ required: true, message: "Name is required" }]}
          >
            <Input data-testid="input-name" />
          </Form.Item>
          <Space className="w-full justify-end pt-6">
            <Button onClick={onClose}>Cancel</Button>
            <Button
              type="primary"
              htmlType="submit"
              disabled={!submittable || !isDirty}
              data-testid="save-config-button"
            >
              Save
            </Button>
          </Space>
        </Space>
      </Form>
    </Modal>
  );
};
